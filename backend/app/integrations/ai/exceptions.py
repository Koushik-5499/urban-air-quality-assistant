"""Exceptions for AI health integration provider errors."""


class AIProviderError(Exception):
    """Base exception for all AI provider integration failures."""

    def __init__(self, message: str, status_code: int = 500, original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.original_error = original_error


class AIAuthError(AIProviderError):
    """Raised when the AI provider API key is missing, invalid, or unauthorized."""

    def __init__(self, message: str = "AI provider credentials are unconfigured or invalid."):
        super().__init__(message, status_code=401)


class AIRateLimitError(AIProviderError):
    """Raised when the AI provider rate limit or quota has been exceeded."""

    def __init__(self, message: str = "AI provider rate limit or quota exceeded."):
        super().__init__(message, status_code=429)


class AITimeoutError(AIProviderError):
    """Raised when an AI provider call times out."""

    def __init__(self, message: str = "AI provider request timed out."):
        super().__init__(message, status_code=504)


class AIValidationError(AIProviderError):
    """Raised when AI response fails safety validation or schema requirements."""

    def __init__(self, message: str = "AI output failed safety or format validation."):
        super().__init__(message, status_code=502)


class AIUnavailableError(AIProviderError):
    """Raised when the AI provider service is temporarily unreachable or offline."""

    def __init__(self, message: str = "AI provider service is currently unavailable."):
        super().__init__(message, status_code=503)

