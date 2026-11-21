"""Comprehensive Security Hardening and Reliability Verification Tests."""

import pytest
from httpx import AsyncClient
from app.core.config import Settings, get_settings
from app.core.logging import redact_secrets
from app.core.security import InMemoryRateLimiter
from app.main import app


@pytest.mark.anyio
async def test_security_headers_present(client: AsyncClient):
    """Verify production security headers are set on API responses."""
    response = await client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert "default-src 'none'" in headers.get("Content-Security-Policy", "")


@pytest.mark.anyio
async def test_request_size_limit_rejection(client: AsyncClient):
    """Verify oversized request payloads (>1MB) are rejected with HTTP 413."""
    # Simulated 1.1 MB payload header
    large_payload = {"city": "Delhi", "question": "Are particulate levels safe today?"}
    response = await client.post(
        "/api/v1/health/ask",
        json=large_payload,
        headers={"Content-Length": str(1024 * 1024 + 500)},
    )
    assert response.status_code == 413
    assert "exceeds maximum permitted size" in response.json()["detail"]


@pytest.mark.anyio
async def test_user_id_validation(client: AsyncClient):
    """Verify X-User-Id header validation prevents path traversal and script injection."""
    # Valid user ID
    valid_res = await client.get("/api/v1/alerts", headers={"X-User-Id": "valid_user-123.test"})
    assert valid_res.status_code == 200

    # Path traversal attack
    bad_res1 = await client.get("/api/v1/alerts", headers={"X-User-Id": "../../etc/passwd"})
    assert bad_res1.status_code == 400
    assert "Invalid X-User-Id header" in bad_res1.json()["detail"]

    # XSS injection attempt
    bad_res2 = await client.get("/api/v1/alerts", headers={"X-User-Id": "<script>alert(1)</script>"})
    assert bad_res2.status_code == 400

    # Oversized user ID (> 64 chars)
    bad_res3 = await client.get("/api/v1/alerts", headers={"X-User-Id": "a" * 65})
    assert bad_res3.status_code == 400


@pytest.mark.anyio
async def test_admin_secret_enforcement_in_production(client: AsyncClient):
    """Verify administrative endpoints strictly reject unauthorized requests in production."""
    prod_settings = Settings(
        APP_ENV="production",
        ALERT_ADMIN_SECRET="super_secret_admin_key_999",
        SYNC_ADMIN_SECRET="super_secret_admin_key_999",
        FORECAST_ADMIN_SECRET="super_secret_admin_key_999",
        AQI_PROVIDER="mock",
    )
    app.dependency_overrides[get_settings] = lambda: prod_settings

    try:
        # 1. Missing secret
        res1 = await client.post("/api/v1/air-quality/sync")
        assert res1.status_code == 403

        # 2. Invalid secret
        res2 = await client.post("/api/v1/air-quality/sync", headers={"X-Admin-Secret": "wrong_key"})
        assert res2.status_code == 403

        # 3. Correct secret
        res3 = await client.post(
            "/api/v1/air-quality/sync",
            headers={"X-Admin-Secret": "super_secret_admin_key_999"},
        )
        assert res3.status_code != 403
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.anyio
async def test_admin_secret_mandatory_in_production_when_unset(client: AsyncClient):
    """Verify that if an admin secret is left empty in production, endpoints refuse execution."""
    prod_settings_no_secret = Settings(
        APP_ENV="production",
        ALERT_ADMIN_SECRET=None,
        SYNC_ADMIN_SECRET=None,
        FORECAST_ADMIN_SECRET=None,
    )
    app.dependency_overrides[get_settings] = lambda: prod_settings_no_secret

    try:
        res = await client.post("/api/v1/alerts/process")
        assert res.status_code == 403
        assert "must be configured in non-development environments" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_secret_redaction_utility():
    """Verify sensitive tokens and keys are sanitized from messages."""
    raw_message = (
        "Connecting with key AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6 and "
        "new key format AQ.TestSyntheticKey1234567890DummyKey and "
        "Resend key re_1234567890abcdef12345678, password: my_db_secret_pass "
        "at postgresql://user:super_pass123@db.example.com/mydb"
    )
    redacted = redact_secrets(raw_message)

    assert "AIzaSy" not in redacted
    assert "AQ.TestSynthetic" not in redacted
    assert "[REDACTED_GEMINI_KEY]" in redacted
    assert "re_12345678" not in redacted
    assert "[REDACTED_RESEND_KEY]" in redacted
    assert "super_pass123" not in redacted
    assert "user:***@db.example.com" in redacted


def test_rate_limiter_sliding_window():
    """Verify in-memory sliding window rate limiter blocks requests exceeding threshold."""
    limiter = InMemoryRateLimiter()
    limiter.route_limits["/test/route"] = (3, 60)  # max 3 requests per 60 seconds

    ip = "192.168.1.100"
    path = "/test/route"

    # 1. First 3 requests allowed
    ok1, rem1, _ = limiter.check_rate_limit(ip, path)
    assert ok1 is True
    assert rem1 == 2

    ok2, rem2, _ = limiter.check_rate_limit(ip, path)
    assert ok2 is True
    assert rem2 == 1

    ok3, rem3, _ = limiter.check_rate_limit(ip, path)
    assert ok3 is True
    assert rem3 == 0

    # 2. 4th request blocked with retry_after
    ok4, rem4, retry_after = limiter.check_rate_limit(ip, path)
    assert ok4 is False
    assert rem4 == 0
    assert retry_after > 0


@pytest.mark.anyio
async def test_historical_date_range_validation(client: AsyncClient):
    """Verify inverted dates and excessively long date ranges are rejected."""
    # 1. Inverted date range (start > end)
    res1 = await client.get(
        "/api/v1/history/aqi",
        params={
            "city": "Delhi",
            "start_date": "2026-11-20T12:00:00Z",
            "end_date": "2026-11-10T12:00:00Z",
        },
    )
    assert res1.status_code == 400
    assert "cannot be after end_date" in res1.json()["detail"]

    # 2. Excessively long raw query span (> 366 days)
    res2 = await client.get(
        "/api/v1/history/aqi",
        params={
            "city": "Delhi",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2026-11-20T00:00:00Z",
        },
    )
    assert res2.status_code == 400
    assert "exceeds maximum allowed limit" in res2.json()["detail"]


@pytest.mark.anyio
async def test_ai_health_safety_validation(client: AsyncClient):
    """Verify prompt length and content validation in Health Advisor."""
    # Empty question (triggers 422 schema validation)
    res1 = await client.post("/api/v1/health/ask", json={"city": "Delhi", "question": " "})
    assert res1.status_code in (400, 422)

    # Oversized question (> 500 chars)
    res2 = await client.post(
        "/api/v1/health/ask",
        json={"city": "Delhi", "question": "Tell me about pollution " * 35},
    )
    assert res2.status_code in (400, 422)


@pytest.mark.anyio
async def test_cors_preflight_and_headers(client: AsyncClient):
    """Verify CORS preflight handling and headers."""
    response = await client.options(
        "/api/v1/air-quality/cities",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
