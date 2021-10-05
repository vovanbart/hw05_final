from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, Group
User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostPagesTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
                        'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_list_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_context_contains_page(response.context)

    def test_post_on_the_home_page(self):
        """ Тест на появление поста на главной странице после создания """
        response = self.authorized_client.get(reverse('posts:index'))
        test_post = response.context['page_obj'].object_list[0]
        self.assertEqual(self.post, test_post, (
            "Пост не добавился на главную страницу"
        ))

    def test_post_on_the_group_page(self):
        """ Тест на появление поста на странице группы после создания """
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test_slug'}
        ))
        test_post = response.context['page_obj'].object_list[0]
        self.assertEqual(self.post, test_post, (
            "Пост не добавился на страницу группы"
        ))

    def test_post_not_belongs_to_someone_else_group(self):
        """ Тест на принадлежность поста нужной группе """
        alien_group = Group.objects.create(
            title='alien',
            slug='alien_slug',
            description='alien_desc'
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': alien_group.slug}))
        alien_posts = response.context['page_obj']
        self.assertNotIn(self.post, alien_posts, (
            ' Пост принадлежит чужой группе '
        ))

    def test_profile_correct_context(self):
        """ Тест на появление поста на странице пользователя """
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        test_author = response.context['author']
        posts = response.context['page_obj']
        self.assertEqual(test_author, self.user, (' Указан неверный автор '))
        self.assertIn(self.post, posts, (
            ' Пост автора не отображается на странице автора '
        ))

    def check_context_contains_page(self, context):
        self.assertIn('page_obj', context)
        post = context['page_obj'][0]
        self.assertEqual(post.author, PostPagesTests.user)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group.title, 'Тестовая группа')


class PaginatorViewsTest(TestCase):
    """Тестируем Paginator. Страница должна быть разбита на 10 постов"""
    POSTS_IN_PAGE = 10
    POSTS_COUNT = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        Post.objects.bulk_create([Post(
            text=f'Тестовое сообщение{i}',
            author=cls.user)
            for i in range(cls.POSTS_COUNT)])

    def test_first_page_contains_ten_records(self):
        """Тестируем Paginator.Первые 10 постов на первой странице index"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context.get('page_obj').object_list),
            self.POSTS_IN_PAGE)

    def test_second_page_contains_three_records(self):
        """Тестируем Paginator.Последние 3 поста на второй странице index"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context.get('page_obj').object_list),
            self.POSTS_COUNT - self.POSTS_IN_PAGE)
