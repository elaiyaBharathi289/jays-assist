from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import ChatThread, Message


class ChatAPITests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="StrongPass123!")
        self.user_b = User.objects.create_user(username="bob", password="StrongPass123!")
        self.thread_a = ChatThread.objects.create(user=self.user_a, title="Alice chat")
        self.thread_b = ChatThread.objects.create(user=self.user_b, title="Bob chat")
        Message.objects.create(thread=self.thread_b, role=Message.Role.USER, content="Private message")

    def test_unauthenticated_cannot_list_threads(self):
        response = self.client.get("/api/threads/")
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_can_create_thread(self):
        self.client.force_login(self.user_a)
        response = self.client.post("/api/threads/", {"title": "New work"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "New work")

    def test_user_can_list_only_own_threads(self):
        self.client.force_login(self.user_a)
        response = self.client.get("/api/threads/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.thread_a.id)

    def test_user_cannot_retrieve_other_users_thread(self):
        self.client.force_login(self.user_a)
        response = self.client.get(f"/api/threads/{self.thread_b.id}/")
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_retrieve_other_users_messages(self):
        self.client.force_login(self.user_a)
        response = self.client.get(f"/api/threads/{self.thread_b.id}/messages/")
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_delete_other_users_thread(self):
        self.client.force_login(self.user_a)
        response = self.client.delete(f"/api/threads/{self.thread_b.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ChatThread.objects.filter(id=self.thread_b.id).exists())

    def test_user_can_delete_own_thread(self):
        self.client.force_login(self.user_a)
        response = self.client.delete(f"/api/threads/{self.thread_a.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ChatThread.objects.filter(id=self.thread_a.id).exists())

    def test_empty_message_rejected(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            f"/api/threads/{self.thread_a.id}/messages/",
            {"content": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("chat.services.OpenAIService.generate_response", return_value="Hello from Jays Assist.")
    def test_message_and_assistant_response_are_persisted(self, mock_generate):
        self.client.force_login(self.user_a)
        response = self.client.post(
            f"/api/threads/{self.thread_a.id}/messages/",
            {"content": "Hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.filter(thread=self.thread_a).count(), 2)
        self.assertEqual(response.data["assistant_message"]["content"], "Hello from Jays Assist.")
        mock_generate.assert_called_once()

    @patch("chat.services.OpenAIService.generate_response", side_effect=Exception("provider down"))
    def test_unexpected_llm_failure_returns_500(self, mock_generate):
        self.client.force_login(self.user_a)
        response = self.client.post(
            f"/api/threads/{self.thread_a.id}/messages/",
            {"content": "Hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(Message.objects.filter(thread=self.thread_a).count(), 1)
        self.assertEqual(Message.objects.get(thread=self.thread_a).role, Message.Role.USER)
        mock_generate.assert_called_once()
