import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-group',
            description='Description test group',
        )
        cls.new_group = Group.objects.create(
            title='New test group',
            slug='new-test-group',
            description='Description test group',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_post(self):
        """Валидная форма создаёт запись в Post"""
        posts_count = Post.objects.count()
        post_data = {
            'text': 'New test text',
            'group': PostFormTest.group.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_data,
            follow=True,
        )

        kwargs_post = {
            'username': self.user.username,
        }

        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs=kwargs_post))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_posts(self):
        """Валидная форма изменяет запись в Post"""
        post_id = PostFormTest.post.id
        post_data = {
            'text': 'New test text',
            'group': PostFormTest.new_group.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=post_data,
            follow=True,
        )

        id_post = Post.objects.get(id=post_id)
        kwargs_post = {'post_id': 1}
        self.assertRedirects(response,
                             reverse('posts:post_detail', kwargs=kwargs_post))
        self.assertEqual(id_post.text, post_data['text'])
        self.assertEqual(id_post.group.id,
                         post_data['group'])
