"""Abstract base class for AI health providers."""

from abc import ABC, abstractmethod
from typing import Optional

from app.integrations.ai.schemas import AICompletionRequest, AICompletionResponse


class BaseAIProvider(ABC):
    """Abstract interface for AI language model integrations."""

    @abstractmethod
    async def generate_response(self, request: AICompletionRequest) -> AICompletionResponse:
        """Generate a contextual AI response from prompt and history."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check whether the provider has required credentials and configuration."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the friendly name of the AI provider."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the active model identifier."""
        pass

