"""Security hardening utilities, middleware, rate limiting, and access control."""

import re
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple
from fastapi import Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.core.security")

# Maximum permitted payload size: 1 MB (1,048,576 bytes)
MAX_REQUEST_SIZE_BYTES = 1024 * 1024

# Sanitization regex for user identifier header
USER_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")


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
    """Protects against Denial-of-Service memory exhaustion via oversized request payloads."""

    def __init__(self, app, max_bytes: int = MAX_REQUEST_SIZE_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
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
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request payload exceeds maximum permitted size of {self.max_bytes // (1024*1024)}MB."
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per IP address."""

    def __init__(self):
        # Maps (ip, route_key) -> list of timestamp floats
        self._requests: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        # Default limits: (requests, window_seconds)
        self.default_limit = (120, 60)  # 120 req / minute
        self.route_limits: Dict[str, Tuple[int, int]] = {
            "/api/v1/health/ask": (20, 60),  # 20 AI queries / minute
            "/api/v1/air-quality/sync": (10, 60),  # 10 sync calls / minute
            "/api/v1/alerts/process": (10, 60),
            "/api/v1/forecast/generate": (10, 60),
            "/api/v1/aqi/process": (10, 60),
        }

    def check_rate_limit(self, client_ip: str, path: str, is_test_env: bool = False) -> Tuple[bool, int, int]:
        """Check if request is permitted. Returns (allowed, remaining, retry_after)."""
        if is_test_env:
            return True, 999, 0

        now = time.time()
        max_requests, window_seconds = self.route_limits.get(path, self.default_limit)
        key = (client_ip, path)

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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces per-client IP rate limits to mitigate brute-force and resource exhaustion."""

    def __init__(self, app, settings: Optional[Settings] = None):
        super().__init__(app)
        self.settings = settings or get_settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
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


def validate_user_id(
    x_user_id: str = Header(default="default_user", alias="X-User-Id"),
) -> str:
    """Validate and sanitize X-User-Id header to prevent injection or abuse."""
    clean = x_user_id.strip()
    if not clean or not USER_ID_REGEX.match(clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-Id header. Must be 1-64 alphanumeric characters, hyphens, underscores, or dots.",
        )
    return clean


def verify_admin_access(
    x_admin_secret: Optional[str] = Header(None, alias="X-Admin-Secret"),
    settings: Settings = Depends(get_settings),
) -> None:
    """Verify administrator secret header for privileged operations.
    
    In development mode, if administrative secret is unset, access is permitted.
    If secret is configured, X-Admin-Secret header must match.
    In non-development environments, an admin secret is strictly mandatory.
    """
    secret = (
        settings.ALERT_ADMIN_SECRET
        or settings.SYNC_ADMIN_SECRET
        or settings.FORECAST_ADMIN_SECRET
    )

    if secret:
        if not x_admin_secret or x_admin_secret != secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing X-Admin-Secret header.",
            )
    else:
        if settings.APP_ENV != "development":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin secret must be configured in non-development environments.",
            )

