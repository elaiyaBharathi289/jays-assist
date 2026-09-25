"""Business logic for conversation handling."""

from django.conf import settings
from django.utils.text import Truncator

from .llm_service import OpenAIService
from .models import ChatThread, Message


class ChatService:
    @staticmethod
    def create_thread(user, title="New conversation"):
        title = (title or "New conversation").strip()
        return ChatThread.objects.create(user=user, title=title[:settings.MAX_THREAD_TITLE_LENGTH])

    @staticmethod
    def update_title_from_first_message(thread, content):
        if thread.title != "New conversation":
            return
        title = " ".join(content.split())
        thread.title = Truncator(title).chars(settings.MAX_THREAD_TITLE_LENGTH)
        thread.save(update_fields=["title", "updated_at"])

    @staticmethod
    def send_message(thread, content):
        user_message = Message.objects.create(
            thread=thread,
            role=Message.Role.USER,
            content=content,
        )
        ChatService.update_title_from_first_message(thread, content)

        history = list(
            thread.messages.order_by("-created_at")[: settings.MAX_HISTORY_MESSAGES]
        )
        history.reverse()

        llm_service = OpenAIService()
        assistant_text = llm_service.generate_response(history)
        assistant_message = Message.objects.create(
            thread=thread,
            role=Message.Role.ASSISTANT,
            content=assistant_text,
        )
        return user_message, assistant_message
