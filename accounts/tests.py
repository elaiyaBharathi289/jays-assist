from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
    def test_registration_success(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "alice", "email": "alice@example.com", "password": "StrongPass123!", "password2": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_duplicate_registration(self):
        User.objects.create_user(username="alice", password="StrongPass123!")
        response = self.client.post(
            "/api/auth/register/",
            {"username": "alice", "email": "other@example.com", "password": "StrongPass123!", "password2": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_login_success(self):
        User.objects.create_user(username="alice", password="StrongPass123!")
        response = self.client.post("/api/auth/login/", {"username": "alice", "password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_invalid_login(self):
        User.objects.create_user(username="alice", password="StrongPass123!")
        response = self.client.post("/api/auth/login/", {"username": "alice", "password": "WrongPass123!"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_logout(self):
        user = User.objects.create_user(username="alice", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
