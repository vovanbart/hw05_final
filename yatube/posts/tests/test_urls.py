from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
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
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        url = [
            '/',
            '/group/test_slug/',
            '/profile/auth/',
            '/posts/1/',
            '/create/',
            '/posts/1/edit/',
        ]
        for adress in url:
            authorized_adress = ['/create/', '/posts/1/edit/']
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                if adress in authorized_adress:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.FOUND,
                        f'Адресс {adress} не доступен.')
                else:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                        f'Адресс {adress} не доступен.')

    def test_edit_author_post(self):
        author = PostURLTests.post.author
        if author != self.user:
            response = self.authorized_client.get(
                '/posts/1/edit/',
                follow=True)
            self.assertRedirects(response, '/posts/1/')
