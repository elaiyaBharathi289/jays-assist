"""Groq service wrapper used by the chat service."""

import logging

from django.conf import settings
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for expected LLM provider failures."""

    status_code = 502


class LLMRateLimitError(LLMServiceError):
    """Raised when the Groq API rate limit is reached."""

    status_code = 429


class LLMConfigurationError(LLMServiceError):
    """Raised when the Groq API is not configured."""

    status_code = 503


class OpenAIService:
    """Service wrapper using the OpenAI SDK with the Groq API."""

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise LLMConfigurationError(
                "The AI service is not configured."
            )

        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            timeout=60.0,
        )

    def generate_response(self, messages):
        """Generate one assistant response from conversation history."""

        input_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
            if message.role in {"user", "assistant", "system"}
        ]

        system_message = {
            "role": "system",
            "content": (
                "You are Jays Assist, a helpful conversational AI assistant. "
                "Answer clearly and accurately. "
                "If you are unsure, say so instead of inventing facts."
            ),
        }

        input_messages.insert(0, system_message)

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=input_messages,
            )

        except RateLimitError as exc:
            logger.warning(
                "Groq rate limit: request_id=%s",
                getattr(exc, "request_id", None),
            )

            raise LLMRateLimitError(
                "The AI service is temporarily rate limited."
            ) from exc

        except (APIConnectionError, APITimeoutError) as exc:
            logger.error(
                "Groq connection failure: %s",
                exc,
            )

            raise LLMServiceError(
                "The AI service could not be reached."
            ) from exc

        except APIStatusError as exc:
            logger.error(
                "Groq API failure: status=%s request_id=%s body=%s",
                exc.status_code,
                getattr(exc, "request_id", None),
                getattr(exc, "body", None),
            )

            raise LLMServiceError(
                "The AI service is temporarily unavailable."
            ) from exc

        if not response.choices:
            raise LLMServiceError(
                "The AI service returned an empty response."
            )

        text = response.choices[0].message.content

        if not text:
            raise LLMServiceError(
                "The AI service returned an empty response."
            )

        text = text.strip()

        if not text:
            raise LLMServiceError(
                "The AI service returned an empty response."
            )

        return text