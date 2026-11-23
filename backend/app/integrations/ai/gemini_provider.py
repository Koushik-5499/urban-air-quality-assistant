"""Google Gemini AI provider implementation using the official google-genai SDK."""

import asyncio
import logging

from google import genai
from google.genai import types

from app.core.config import Settings, get_settings
from app.integrations.ai.base import BaseAIProvider
from app.integrations.ai.exceptions import (
    AIAuthError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIUnavailableError,
)
from app.integrations.ai.schemas import AICompletionRequest, AICompletionResponse

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Integrates with Google's Gemini models via the google-genai Python SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        settings: Settings | None = None,
    ):
        cfg = settings or get_settings()
        self.api_key = api_key or cfg.GEMINI_API_KEY
        self.model = model or cfg.GEMINI_MODEL or "gemini-2.5-flash"
        self.timeout = timeout or cfg.AI_REQUEST_TIMEOUT or 30
        self.max_retries = max_retries or cfg.AI_MAX_RETRIES or 2
        self._client: genai.Client | None = None

    def is_configured(self) -> bool:
        """Check if a non-empty Gemini API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "gemini"

    def get_model_name(self) -> str:
        """Return active Gemini model name."""
        return self.model

    def _get_client(self) -> genai.Client:
        """Lazy initialization of the GenAI client."""
        if not self.is_configured():
            raise AIAuthError("GEMINI_API_KEY is not configured in the application environment.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _build_contents(self, request: AICompletionRequest) -> list[types.Content]:
        """Convert chat history and prompt into GenAI Content structures."""
        contents: list[types.Content] = []

        if request.conversation_history:
            for msg in request.conversation_history:
                # GenAI roles are "user" or "model"
                role = "model" if msg.role in ("assistant", "model") else "user"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=request.prompt)],
            )
        )
        return contents

    async def generate_response(self, request: AICompletionRequest) -> AICompletionResponse:
        """Generate response asynchronously with timeout and bounded retries."""
        if not self.is_configured():
            raise AIAuthError("Gemini API key is missing. Set GEMINI_API_KEY to enable AI assistance.")

        client = self._get_client()
        contents = self._build_contents(request)

        config = types.GenerateContentConfig(
            system_instruction=request.system_instruction,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                # Wrap asynchronous generation in strict timeout
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config,
                    ),
                    timeout=float(self.timeout),
                )

                text = response.text or ""
                return AICompletionResponse(
                    content=text,
                    model=self.model,
                    finish_reason="STOP",
                    usage_tokens=None,
                )

            except TimeoutError:
                logger.warning(
                    "Gemini API request timed out (attempt %d/%d) after %ds",
                    attempt + 1,
                    self.max_retries + 1,
                    self.timeout,
                )
                last_error = AITimeoutError(f"Gemini API request timed out after {self.timeout} seconds.")
                if attempt == self.max_retries:
                    raise last_error

            except Exception as exc:
                err_str = str(exc).lower()
                logger.warning(
                    "Gemini API invocation error (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    type(exc).__name__,
                )

                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    last_error = AIRateLimitError("Gemini API rate limit or quota exceeded.")
                elif "401" in err_str or "403" in err_str or "api_key" in err_str:
                    raise AIAuthError("Invalid or unauthorized Gemini API key.")
                elif "503" in err_str or "unavailable" in err_str:
                    last_error = AIUnavailableError("Gemini AI service is temporarily unavailable.")
                else:
                    last_error = AIProviderError(f"AI provider encountered an error: {type(exc).__name__}")

                if attempt == self.max_retries:
                    raise last_error

            # Exponential backoff before retry: 0.5s, 1.0s...
            await asyncio.sleep(0.5 * (2 ** attempt))

        raise last_error or AIProviderError("Gemini generation failed after retries.")

