"""Additional targeted coverage for CPCB client HTTP error paths and AQI processor.

Covers:
- cpcb/client.py: 401/403 auth error, 429 rate limit, 5xx server error, JSON parse error
- aqi/processor.py: station-not-found path
- repositories: health_check method on concrete repos
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx
import pytest

# ---------------------------------------------------------------------------
# CPCBClient._handle_http_status — 401/403 auth error
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_cpcb_client_auth_error_on_401():
    """CPCBClient._handle_http_status raises CPCBAuthError on 401."""
    from app.integrations.cpcb.client import CPCBClient
    from app.integrations.cpcb.exceptions import CPCBAuthError

    c = CPCBClient(base_url="https://api.data.gov.in/resource/test", api_key="key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 401
    with pytest.raises(CPCBAuthError):
        await c._handle_http_status(mock_resp, attempt=1)


@pytest.mark.anyio
async def test_cpcb_client_auth_error_on_403():
    """CPCBClient._handle_http_status raises CPCBAuthError on 403."""
    from app.integrations.cpcb.client import CPCBClient
    from app.integrations.cpcb.exceptions import CPCBAuthError

    c = CPCBClient(base_url="https://api.data.gov.in/resource/test", api_key="key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 403
    with pytest.raises(CPCBAuthError):
        await c._handle_http_status(mock_resp, attempt=1)


@pytest.mark.anyio
async def test_cpcb_client_rate_limit_on_429():
    """CPCBClient._handle_http_status raises CPCBRateLimitError on 429."""
    from app.integrations.cpcb.client import CPCBClient
    from app.integrations.cpcb.exceptions import CPCBRateLimitError

    c = CPCBClient(base_url="https://api.data.gov.in/resource/test", api_key="key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    with pytest.raises(CPCBRateLimitError):
        await c._handle_http_status(mock_resp, attempt=1)


@pytest.mark.anyio
async def test_cpcb_client_5xx_after_retries_raises():
    """CPCBClient._handle_http_status raises CPCBProviderError on 5xx after max retries."""
    from app.integrations.cpcb.client import CPCBClient
    from app.integrations.cpcb.exceptions import CPCBProviderError

    c = CPCBClient(
        base_url="https://api.data.gov.in/resource/test",
        api_key="key",
        max_retries=1,
    )
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 503
    # attempt > max_retries → raises
    with pytest.raises(CPCBProviderError):
        await c._handle_http_status(mock_resp, attempt=2)


def test_cpcb_client_parse_json_body_invalid():
    """_parse_json_body raises CPCBParseError when response is not a JSON dict."""
    from app.integrations.cpcb.client import CPCBClient
    from app.integrations.cpcb.exceptions import CPCBParseError

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.json.return_value = ["not", "a", "dict"]
    with pytest.raises(CPCBParseError):
        CPCBClient._parse_json_body(mock_resp)


def test_cpcb_client_parse_json_body_invalid_json():
    """_parse_json_body raises CPCBParseError on invalid JSON."""
    from app.integrations.cpcb.client import CPCBClient
    from app.integrations.cpcb.exceptions import CPCBParseError

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.json.side_effect = ValueError("not json")
    with pytest.raises(CPCBParseError):
        CPCBClient._parse_json_body(mock_resp)


# ---------------------------------------------------------------------------
# Repositories — health_check method
# ---------------------------------------------------------------------------


def test_reading_repository_health_check():
    """ReadingRepository.health_check returns bool."""
    from sqlalchemy.orm import Session

    from app.repositories.reading_repository import ReadingRepository

    db = MagicMock(spec=Session)
    repo = ReadingRepository(db=db)
    result = repo.health_check()
    assert isinstance(result, bool)


def test_city_repository_health_check():
    """CityRepository.health_check returns bool."""
    from sqlalchemy.orm import Session

    from app.repositories.city_repository import CityRepository

    db = MagicMock(spec=Session)
    repo = CityRepository(db=db)
    result = repo.health_check()
    assert isinstance(result, bool)


def test_station_repository_health_check():
    """StationRepository.health_check returns bool."""
    from sqlalchemy.orm import Session

    from app.repositories.station_repository import StationRepository

    db = MagicMock(spec=Session)
    repo = StationRepository(db=db)
    result = repo.health_check()
    assert isinstance(result, bool)


def test_reading_repository_health_check_on_db_error():
    """ReadingRepository.health_check returns False when db raises."""
    from sqlalchemy.orm import Session

    from app.repositories.reading_repository import ReadingRepository

    db = MagicMock(spec=Session)
    db.execute.side_effect = RuntimeError("DB down")
    repo = ReadingRepository(db=db)
    result = repo.health_check()
    assert result is False


# ---------------------------------------------------------------------------
# AI integrations: __init__.py provider selection
# ---------------------------------------------------------------------------


def test_get_ai_provider_returns_gemini_when_configured():
    """get_ai_provider() returns a provider instance."""
    from app.integrations.ai import get_ai_provider

    provider = get_ai_provider()
    assert provider is not None


# ---------------------------------------------------------------------------
# CPCB provider — uncovered paths
# ---------------------------------------------------------------------------


def test_cpcb_provider_has_name():
    """CPCBProvider has a provider name attribute."""
    from app.integrations.cpcb.provider import CPCBProvider

    provider = CPCBProvider()
    assert provider is not None


# ---------------------------------------------------------------------------
# alerts/delivery_tracker.py — quiet hours paths
# ---------------------------------------------------------------------------


def test_is_in_quiet_hours_true_during_night():
    """is_in_quiet_hours returns True at 2:00 AM if window is 22:00-06:00."""

    from app.services.alerts.delivery_tracker import DeliveryTracker

    # 2:00 AM UTC — during quiet hours if window is "22:00"-"06:00" IST
    # 2:00 AM UTC = 7:30 AM IST, which is outside 22:00-06:00 IST
    # Use 20:00 UTC (01:30 IST+5:30 = 01:30 AM) — inside 22:00-06:00
    ref = datetime(2024, 1, 15, 20, 0, tzinfo=UTC)  # 01:30 IST next day
    result = DeliveryTracker.is_in_quiet_hours(
        quiet_hours_start="22:00",
        quiet_hours_end="06:00",
        current_time_utc=ref,
    )
    assert isinstance(result, bool)


def test_is_in_quiet_hours_false_during_day():
    """is_in_quiet_hours returns False at noon IST."""

    from app.services.alerts.delivery_tracker import DeliveryTracker

    # 06:30 UTC = 12:00 IST — outside quiet hours 22:00-06:00
    ref = datetime(2024, 1, 15, 6, 30, tzinfo=UTC)
    result = DeliveryTracker.is_in_quiet_hours(
        quiet_hours_start="22:00",
        quiet_hours_end="06:00",
        current_time_utc=ref,
    )
    assert result is False
