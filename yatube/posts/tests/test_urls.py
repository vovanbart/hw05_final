from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from posts.models import Post, Group
from http import HTTPStatus
User = get_user_model()


class PostURLTest(TestCase):
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
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        adress_list = ['/create/',
                       '/follow/']
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                if adress in adress_list:
                    response = self.authorized_client.get(adress)
                    self.assertTemplateUsed(response, template)
                elif adress == f'/posts/{self.post.id}/edit/':
                    response = self.author_client.get(adress)
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.guest_client.get(adress)
                    self.assertTemplateUsed(response, template)

    def test_urls_exists_at_desired_location(self):
        url_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            f'/posts/{self.post.id}/comment': HTTPStatus.FOUND,
            f'/profile/{self.user}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user}/unfollow/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.OK,
        }
        adress_list = ['/create/',
                       f'/profile/{self.user}/unfollow/',
                       f'/profile/{self.user}/follow/',
                       f'/posts/{self.post.id}/comment/',
                       '/follow/']
        for adress, http_status in url_status.items():
            with self.subTest(adress=adress):
                if adress in adress_list:
                    response = self.authorized_client.get(adress)
                    self.assertEqual(response.status_code, http_status)
                elif adress == f'/posts/{self.post.id}/edit/':
                    response = self.author_client.get(adress)
                    self.assertEqual(response.status_code, http_status)
                else:
                    response = self.guest_client.get(adress)
                    self.assertEqual(response.status_code, http_status)
