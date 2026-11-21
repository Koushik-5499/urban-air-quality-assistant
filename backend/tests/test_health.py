"""Tests for health check endpoints, root endpoint, CORS, error handling, and security."""

from datetime import datetime

import pytest
from httpx import AsyncClient

from app.core.config import Settings


@pytest.mark.anyio
async def test_root_endpoint(client: AsyncClient):
    """Test that GET / returns 200 and the expected welcome schema."""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "online"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"
    assert data["redoc"] == "/redoc"
    assert data["api_v1_prefix"] == "/api/v1"
    assert "Urban Air Quality Assistant" in data["message"]


@pytest.mark.anyio
async def test_basic_health_endpoint(client: AsyncClient):
    """Test that GET /health returns 200 with service health metadata."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["service"] == "Urban Air Quality Assistant API"
    assert "environment" in data
    assert "timestamp" in data

    # Verify timestamp is a valid ISO 8601 string
    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert ts.year >= 2024


@pytest.mark.anyio
async def test_versioned_health_endpoint(client: AsyncClient):
    """Test that GET /api/v1/health returns 200 with versioned health response schema."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["service"] == "Urban Air Quality Assistant API"
    assert data["environment"] == "development"
    assert "timestamp" in data

    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert ts.year >= 2024


@pytest.mark.anyio
async def test_invalid_route_returns_404(client: AsyncClient):
    """Test that accessing an undefined route returns 404 with structured detail."""
    response = await client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Not Found"


@pytest.mark.anyio
async def test_cors_headers_for_configured_origin(client: AsyncClient):
    """Test that requests from configured frontend origin receive correct CORS headers."""
    response = await client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.anyio
async def test_cors_preflight_for_configured_origin(client: AsyncClient):
    """Test OPTIONS preflight requests from configured Vite frontend origin."""
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "GET" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.anyio
async def test_cors_disallows_unconfigured_origin(client: AsyncClient):
    """Test that an unconfigured external origin does NOT receive CORS allow origin headers."""
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://unauthorized-attacker.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPIs CORSMiddleware does not return allow-origin header for disallowed origins
    assert response.headers.get("access-control-allow-origin") != "https://unauthorized-attacker.com"


@pytest.mark.anyio
async def test_no_sensitive_data_exposure(client: AsyncClient):
    """Ensure health and root endpoints do not expose internal paths, secrets, or environment variables."""
    for path in ["/", "/health", "/api/v1/health"]:
        response = await client.get(path)
        content_str = response.text.lower()

        # Sensitive keywords that must never appear in response bodies
        sensitive_terms = ["api_key", "secret", "password", "token", "/home/", "/data/", "sqlite:"]
        for term in sensitive_terms:
            assert term not in content_str, f"Found sensitive term '{term}' in {path} response"


def test_cors_settings_parsing():
    """Verify Settings handles both JSON array and comma-separated string formats."""
    # Test JSON string parsing
    s1 = Settings(CORS_ORIGINS='["http://localhost:5173", "http://example.com"]')
    assert s1.CORS_ORIGINS == ["http://localhost:5173", "http://example.com"]

    # Test comma-separated string parsing
    s2 = Settings(CORS_ORIGINS="http://localhost:5173, http://127.0.0.1:5173")
    assert s2.CORS_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Test list directly
    s3 = Settings(CORS_ORIGINS=["http://localhost:5173"])
    assert s3.CORS_ORIGINS == ["http://localhost:5173"]


def test_environment_modes():
    """Verify is_development and is_production helpers."""
    dev_settings = Settings(APP_ENV="development")
    assert dev_settings.is_development is True
    assert dev_settings.is_production is False

    prod_settings = Settings(APP_ENV="production")
    assert prod_settings.is_development is False
    assert prod_settings.is_production is True

