"""AI health provider integration package."""

from typing import Optional

from app.core.config import Settings, get_settings
from app.integrations.ai.base import BaseAIProvider
from app.integrations.ai.exceptions import (
    AIAuthError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIUnavailableError,
    AIValidationError,
)
from app.integrations.ai.gemini_provider import GeminiProvider
from app.integrations.ai.schemas import (
    AICompletionRequest,
    AICompletionResponse,
    ChatMessage,
    RecommendationItem,
)


def get_ai_provider(settings: Optional[Settings] = None) -> BaseAIProvider:
    """Factory creating configured AI provider instance based on settings."""
    cfg = settings or get_settings()
    return GeminiProvider(settings=cfg)


__all__ = [
    "BaseAIProvider",
    "GeminiProvider",
    "get_ai_provider",
    "ChatMessage",
    "AICompletionRequest",
    "AICompletionResponse",
    "RecommendationItem",
    "AIProviderError",
    "AIAuthError",
    "AIRateLimitError",
    "AITimeoutError",
    "AIValidationError",
    "AIUnavailableError",
]

