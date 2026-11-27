"""Security hardening utilities, middleware, rate limiting, and access control."""

import hmac
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.core.security")

# Maximum permitted payload size: 1 MB (1,048,576 bytes)
MAX_REQUEST_SIZE_BYTES = 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defense-in-depth HTTP security headers on all responses."""

    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 1. Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. Clickjacking mitigation (deny framing)
        response.headers["X-Frame-Options"] = "DENY"

        # 3. Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 4. Permissions Policy (disable unneeded browser APIs)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )

        # 5. Content Security Policy (CSP)
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi.json")):
            # Allow Swagger UI / ReDoc resources on documentation paths
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            )
        else:
            # Strict API CSP policy
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
            )

        # 6. HTTP Strict Transport Security (HSTS) when on HTTPS
        if request.url.scheme == "https" or self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Protects against Denial-of-Service memory exhaustion via oversized request payloads.

    Enforces the limit on the actual body stream so that chunked requests
    (which omit Content-Length) are also caught.
    """

    def __init__(self, app, max_bytes: int = MAX_REQUEST_SIZE_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Fast path: reject on Content-Length header when present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_val = int(content_length)
                if length_val > self.max_bytes:
                    logger.warning(
                        "Rejected oversized payload from %s: %d bytes (limit: %d)",
                        request.client.host if request.client else "unknown",
                        length_val,
                        self.max_bytes,
                    )
                    return self._too_large_response()
            except ValueError:
                pass

        # 2. Buffer the body so downstream can read it, while enforcing size limit.
        # request.body() is cached by Starlette after first call, so call_next still works.
        body = await request.body()
        if len(body) > self.max_bytes:
            logger.warning(
                "Rejected oversized payload from %s: %d bytes (limit: %d)",
                request.client.host if request.client else "unknown",
                len(body),
                self.max_bytes,
            )
            return self._too_large_response()

        return await call_next(request)

    def _too_large_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={
                "detail": f"Request payload exceeds maximum permitted size of "
                f"{self.max_bytes // (1024 * 1024)}MB."
            },
        )


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per IP address."""

    def __init__(self):
        # Maps (ip, route_key) -> list of timestamp floats
        self._requests: dict[tuple[str, str], list[float]] = defaultdict(list)
        # Default limits: (requests, window_seconds)
        self.default_limit = (120, 60)  # 120 req / minute
        self.route_limits: dict[str, tuple[int, int]] = {
            "/api/v1/health/ask": (20, 60),  # 20 AI queries / minute
            "/api/v1/air-quality/sync": (10, 60),  # 10 sync calls / minute
            "/api/v1/alerts/process": (10, 60),
            "/api/v1/forecast/generate": (10, 60),
            "/api/v1/aqi/process": (10, 60),
        }
        self._call_count: int = 0

    def check_rate_limit(
        self, client_ip: str, path: str, is_test_env: bool = False
    ) -> tuple[bool, int, int]:
        """Check if request is permitted. Returns (allowed, remaining, retry_after)."""
        if is_test_env:
            return True, 999, 0

        now = time.time()
        max_requests, window_seconds = self.route_limits.get(path, self.default_limit)
        key = (client_ip, path)

        # Periodically prune expired entries (every 100 calls)
        self._call_count += 1
        if self._call_count % 100 == 0:
            _prune_expired_rate_limit_entries(self._requests, window_seconds)

        # Filter out expired timestamps
        timestamps = [ts for ts in self._requests[key] if now - ts < window_seconds]
        self._requests[key] = timestamps

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest)))
            return False, 0, retry_after

        # Record this request
        self._requests[key].append(now)
        remaining = max_requests - len(self._requests[key])
        return True, remaining, 0

    def clear(self) -> None:
        """Reset rate limiter state (useful in tests)."""
        self._requests.clear()


rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request, settings: Settings) -> str:
    """Extract client IP, respecting X-Forwarded-For only when TRUSTED_PROXY is enabled."""
    if getattr(settings, "TRUSTED_PROXY", False):
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            # Take the leftmost (original client) IP
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip
    return request.client.host if request.client else "unknown"


def _prune_expired_rate_limit_entries(store: dict, window_seconds: int) -> None:
    """Remove expired rate limit entries to prevent unbounded memory growth."""
    now = time.time()
    expired_keys = [k for k, v in store.items() if not v or now - v[0] > window_seconds * 2]
    for k in expired_keys:
        del store[k]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces per-client IP rate limits to mitigate brute-force and resource exhaustion."""

    def __init__(self, app, settings: Settings | None = None):
        super().__init__(app)
        self.settings = settings or get_settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = get_client_ip(request, self.settings)
        is_test = self.settings.APP_ENV == "test"

        allowed, remaining, retry_after = rate_limiter.check_rate_limit(
            client_ip=client_ip,
            path=request.url.path,
            is_test_env=is_test,
        )

        if not allowed:
            logger.warning("Rate limit exceeded for IP %s on %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please wait before retrying.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def _extract_provided_secret(
    x_admin_secret: str | None,
    x_api_key: str | None,
    authorization: str | None,
) -> str | None:
    """Extract the credential token from whichever supported header is present."""
    if isinstance(x_admin_secret, str) and x_admin_secret.strip():
        return x_admin_secret.strip()
    if isinstance(x_api_key, str) and x_api_key.strip():
        return x_api_key.strip()
    if isinstance(authorization, str) and authorization.strip():
        return _parse_authorization_token(authorization)
    return None


def _parse_authorization_token(authorization: str) -> str | None:
    """Parse a raw secret from an Authorization header value."""
    parts = authorization.strip().split()
    if len(parts) == 2 and parts[0].lower() in ("bearer", "apikey", "secret"):
        return parts[1]
    if len(parts) == 1:
        return parts[0]
    return None


def _verify_secret_match(provided_secret: str | None, secret: str) -> None:
    """Raise 403 when the provided secret does not match the configured admin secret."""
    if not provided_secret or not hmac.compare_digest(
        provided_secret.encode(), secret.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Admin-Secret header.",
        )


def verify_admin_access(
    x_admin_secret: str | None = Header(None, alias="X-Admin-Secret"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> None:
    """Verify administrator secret header for privileged operations.

    Accepts credentials via X-Admin-Secret, X-API-Key, or Bearer token in Authorization header.
    In development mode, if administrative secret is unset, access is permitted.
    If secret is configured, provided credentials must match using constant-time
    hmac.compare_digest.
    In non-development environments, an admin secret is strictly mandatory.
    """
    secret = (
        settings.ALERT_ADMIN_SECRET or settings.SYNC_ADMIN_SECRET or settings.FORECAST_ADMIN_SECRET
    )
    # Extract token from any supported header
    provided_secret = _extract_provided_secret(x_admin_secret, x_api_key, authorization)

    if secret:
        _verify_secret_match(provided_secret, secret)
    elif settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin secret must be configured in non-development environments.",
        )
