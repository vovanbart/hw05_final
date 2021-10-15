from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django import forms
from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class PaginatorViewsTest(TestCase):
    """Тестируем паджинатор."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='test-slug',
            description='description',
        )
        for i in range(1, 14):
            Post.objects.create(
                author=cls.user,
                text=f'Number of post - {i}',
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Первая страница должна содержать 10 записей."""
        posts_per_page_template = {
            reverse('posts:index'): 10,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 10,
            reverse('posts:profile',
                    kwargs={'username': self.user}): 10,
        }
        for reverse_name, count in posts_per_page_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)

    def test_second_page_contains_three_records(self):
        """Вторая страница должна содержать 3 записи."""
        posts_per_page_template = {
            reverse('posts:index'): 3,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 3,
            reverse('posts:profile',
                    kwargs={'username': self.user}): 3,
        }
        for reverse_name, count in posts_per_page_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name + '?page=2'
                )
                self.assertEqual(len(response.context['page_obj']), count)


class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_following = User.objects.create_user(username='following')
        cls.group = Group.objects.create(
            title='title',
            slug='test-slug',
            description='description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
            group=cls.group,
            image=SimpleUploadedFile(
                name='/posts/small.jpg/',
                content=b'\x47\x49',
                content_type='image/jpg'
            )
        )
        cls.comment = Comment.objects.create(
            text='text',
            author=cls.user,
            post=cls.post,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user_following)
        self.author_client = Client()
        self.author_client.force_login(PostViewTest.user)
        cache.clear()

    def test_about_page_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
                        'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
                        'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == reverse('posts:post_edit',
                                           kwargs={'post_id': self.post.id}):
                    response = self.author_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def assertions_for_test(self, context, posts):
        self.assertEqual(context.text, posts.text)
        self.assertEqual(context.group, posts.group)
        self.assertEqual(context.author, posts.author)
        self.assertEqual(context.image, posts.image)

    def test_index(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_object = response.context['page_obj'][0]
        all_posts = Post.objects.all()[0]
        self.assertions_for_test(page_object, all_posts)

    def test_group_list(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group = PostViewTest.group
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group.slug})
        )
        page_object = response.context['page_obj'][0]
        group_posts = group.posts.all()[0]
        self.assertions_for_test(page_object, group_posts)

    def test_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        author = PostViewTest.user
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        page_object = response.context['page_obj'][0]
        author_posts = author.posts.all()[0]
        self.assertions_for_test(page_object, author_posts)

    def test_post_detail(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewTest.post.id})
        )
        post_title = self.post.text[:30]
        posts_count = Post.objects.filter(author=self.post.author).count()
        self.assertEqual(
            response.context['post'], self.post
        )
        self.assertEqual(
            response.context['post'].text, post_title
        )
        self.assertEqual(
            response.context['post'].author.posts.count(), posts_count
        )
        self.assertEqual(response.context['post'].image,
                         PostViewTest.post.image)

    def test_create_post(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_with_group_displayed_correctly(self):
        """"Пост с указанной группой отображается на главной странице,
        на странице группы и в профайле пользователя."""
        created_post = PostViewTest.post
        url_list = (
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': self.user}),
        )
        for value in url_list:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertIn(created_post, response.context['page_obj'])

    def test_post_edit(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post = PostViewTest.post
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id})
        )
        form_fields = {
            'text': (forms.fields.CharField, post.text),
            'group': (forms.fields.ChoiceField, post.group.id),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_new_comment(self):
        """Тест правильного создания комментария."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewTest.post.id})
        )
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_cache_index_page(self):
        """Тест кэширования главной страницы."""
        response1 = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='test-text',
            group=self.group
        )
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response3.content, response1.content)
        self.assertEqual(response3.context['page_obj'][0].text, 'test-text')
        self.assertEqual(len(response3.context['page_obj'].object_list), 2)

    def test_follow_to_author(self):
        """"Тест подписки отписки от автора."""
        profile_rct = reverse('posts:profile',
                              kwargs={'username':
                                      PostViewTest.user_following.username})
        author_follow = Follow.objects.count()
        response = self.authorized_client2.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user}
        ))
        self.assertRedirects(response, profile_rct)
        self.assertEqual(Follow.objects.count(), author_follow + 1)

    def test_unfollow_to_author(self):
        profile_rct1 = reverse('posts:profile',
                               kwargs={'username':
                                       PostViewTest.user.username})
        author_unfollow = Follow.objects.count()
        response = self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user}
        ))
        self.assertRedirects(response, profile_rct1)
        self.assertEqual(Follow.objects.count(), author_unfollow)

    def test_follow_index(self):
        response1 = self.authorized_client.get(reverse('posts:follow_index'))
        post1 = response1.context['page_obj']
        response2 = self.authorized_client2.get(reverse('posts:follow_index'))
        post2 = response2.context['page_obj']
        self.assertTrue(Post.objects.get(
            text=self.post.text),
            post1
        )
        self.assertNotEqual(post2, Post.objects.get(
            text=self.post.text))


class PagesError(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404_page(self):
        """Тест кастомной 404 ошибки."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
