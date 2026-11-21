"""Custom exceptions for CPCB / data.gov.in integration."""


class CPCBProviderError(Exception):
    """Base exception for all CPCB integration errors."""

    pass


class CPCBAuthError(CPCBProviderError):
    """Raised when authentication fails (HTTP 401, 403 or missing API key)."""

    pass


class CPCBTimeoutError(CPCBProviderError):
    """Raised when request times out."""

    pass


class CPCBRateLimitError(CPCBProviderError):
    """Raised when rate limits are exceeded (HTTP 429)."""

    pass


class CPCBParseError(CPCBProviderError):
    """Raised when response schema or JSON cannot be parsed."""

    pass


class CPCBDataUnavailableError(CPCBProviderError):
    """Raised when requested city or station has no available telemetry records."""

    pass

