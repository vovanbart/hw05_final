from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from posts.models import Post, Group, Comment
User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='test-slug',
            description='description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
            group=cls.group,
        )
        cls.picture = (b'\x47\x49')
        cls.image = SimpleUploadedFile(
            name='small.jpg',
            content=cls.picture,
            content_type='image/jpg',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='comment',
            post=cls.post,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.id,
            ).exists()
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user}))

    def test_edit_post(self):
        """Валидная форма редактирует запись."""
        form_data = {
            'text': 'Text',
            'group': self.group.id,
            'author': self.user
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.get(id=self.post.id).text,
                         form_data['text'])
        self.assertEqual(Post.objects.get(id=self.post.id).group.id,
                         form_data['group'])
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group,
                author=self.user
            ).exists()
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))

    def test_image(self):
        form_data = {
            'text': PostFormTest.post.text,
            'group': PostFormTest.group.pk,
            'image': PostFormTest.image,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(PostFormTest.image, form_data['image'])


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='test-slug',
            description='description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='comment',
            post=cls.post,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment(self):
        """Тестирование комментариев к постам."""
        comment_data = {'text': 'comment'}
        post_comment = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.comment.pk}
            ),
            data=comment_data,
            follow=True
        )
        self.assertRedirects(
            post_comment,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.comment.pk}
            )
        )
        self.assertEqual(CommentFormTest.comment.text, comment_data['text'])
