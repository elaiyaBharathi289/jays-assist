from django.conf import settings
from rest_framework import serializers

from .models import ChatThread, Message


class ChatThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatThread
        fields = ["id", "title", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Thread title cannot be empty.")
        return value[:settings.MAX_THREAD_TITLE_LENGTH]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = fields


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(
        max_length=settings.MAX_MESSAGE_LENGTH,
        trim_whitespace=True,
        allow_blank=False,
    )
