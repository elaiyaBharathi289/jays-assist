import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .llm_service import LLMConfigurationError, LLMRateLimitError, LLMServiceError
from .models import ChatThread
from .permissions import IsThreadOwner
from .serializers import ChatThreadSerializer, MessageCreateSerializer, MessageSerializer
from .services import ChatService

logger = logging.getLogger(__name__)


class ThreadListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threads = ChatThread.objects.filter(user=request.user)
        return Response(ChatThreadSerializer(threads, many=True).data)

    def post(self, request):
        serializer = ChatThreadSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        thread = ChatService.create_thread(request.user, serializer.validated_data.get("title"))
        return Response(ChatThreadSerializer(thread).data, status=status.HTTP_201_CREATED)


class ThreadDetailView(APIView):
    permission_classes = [IsAuthenticated, IsThreadOwner]

    def get_thread(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id)
        self.check_object_permissions(request, thread)
        return thread

    def get(self, request, thread_id):
        thread = self.get_thread(request, thread_id)
        return Response(ChatThreadSerializer(thread).data)

    def delete(self, request, thread_id):
        thread = self.get_thread(request, thread_id)
        thread.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ThreadMessagesView(APIView):
    permission_classes = [IsAuthenticated, IsThreadOwner]

    def get_thread(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id)
        self.check_object_permissions(request, thread)
        return thread

    def get(self, request, thread_id):
        thread = self.get_thread(request, thread_id)
        messages = thread.messages.all()
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, thread_id):
        thread = self.get_thread(request, thread_id)
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_message, assistant_message = ChatService.send_message(
                thread,
                serializer.validated_data["content"],
            )
        except LLMRateLimitError as exc:
            return Response({"error": str(exc)}, status=429)
        except LLMConfigurationError as exc:
            return Response({"error": str(exc)}, status=503)
        except LLMServiceError as exc:
            return Response({"error": str(exc)}, status=502)
        except Exception:
            logger.exception("Unexpected chat message failure for thread=%s", thread.id)
            return Response(
                {"error": "We could not complete that message. Please try again."},
                status=500,
            )

        return Response(
            {
                "user_message": MessageSerializer(user_message).data,
                "assistant_message": MessageSerializer(assistant_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
