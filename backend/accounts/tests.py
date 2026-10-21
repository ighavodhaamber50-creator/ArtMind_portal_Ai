"""Tests for registration, login, logout and the 'who am I' endpoint."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from gallery.factories import TEST_PASSWORD, make_user

User = get_user_model()


class AuthTests(APITestCase):
    def test_register_creates_a_hashed_account_and_logs_in(self):
        response = self.client.post(
            '/api/auth/register/',
            {'username': 'amber', 'email': 'amber@example.com', 'password': TEST_PASSWORD},
            format='json')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(username='amber')
        self.assertNotEqual(user.password, TEST_PASSWORD)  # never stored as plain text
        self.assertTrue(user.check_password(TEST_PASSWORD))
        self.assertTrue(hasattr(user, 'preference'))  # every user gets a preferences row

        me = self.client.get('/api/auth/me/')
        self.assertTrue(me.data['is_authenticated'])
        self.assertEqual(me.data['user']['username'], 'amber')
        self.assertFalse(me.data['user']['is_staff'])

    def test_register_ignores_attempts_to_become_staff(self):
        self.client.post(
            '/api/auth/register/',
            {'username': 'sneaky', 'password': TEST_PASSWORD, 'is_staff': True}, format='json')
        self.assertFalse(User.objects.get(username='sneaky').is_staff)

    def test_register_rejects_a_weak_password(self):
        response = self.client.post(
            '/api/auth/register/', {'username': 'weak', 'password': '12345'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(username='weak').exists())

    def test_register_rejects_a_duplicate_username_ignoring_case(self):
        make_user('Amber')
        response = self.client.post(
            '/api/auth/register/', {'username': 'amber', 'password': TEST_PASSWORD}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)

    def test_login_with_a_wrong_password_gives_a_friendly_error(self):
        make_user('amber')
        response = self.client.post(
            '/api/auth/login/', {'username': 'amber', 'password': 'wrong'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Incorrect username or password.')

    def test_login_then_logout(self):
        make_user('amber')
        login = self.client.post(
            '/api/auth/login/', {'username': 'amber', 'password': TEST_PASSWORD}, format='json')
        self.assertEqual(login.status_code, 200)
        self.assertTrue(self.client.get('/api/auth/me/').data['is_authenticated'])

        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 200)
        self.assertFalse(self.client.get('/api/auth/me/').data['is_authenticated'])