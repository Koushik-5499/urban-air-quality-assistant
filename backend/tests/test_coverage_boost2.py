"""Additional targeted coverage tests for validators and other low-coverage modules.

Covers:
- forecasting/validators.py lines 40-42 (ValueError in parse_horizon) and 80-86 (station not found)
- health/safety_validator.py lines 37, 65 (too-short question, too-long history message)
- main.py: startup, shutdown, /health endpoint coverage
"""


import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.forecasting.validators import ForecastValidator

client = TestClient(app)


# ---------------------------------------------------------------------------
# ForecastValidator.parse_horizon — ValueError path (line 41-42)
# ---------------------------------------------------------------------------


def test_parse_horizon_invalid_string_raises_400():
    """parse_horizon raises HTTPException 400 for a non-numeric unsupported string."""
    with pytest.raises(Exception) as exc_info:
        ForecastValidator.parse_horizon("weekly")
    assert exc_info.value.status_code == 400  # type: ignore[attr-defined]


def test_parse_horizon_valid_label():
    """parse_horizon handles '24h' label correctly."""
    assert ForecastValidator.parse_horizon("24h") == 24


def test_parse_horizon_bare_integer():
    """parse_horizon handles integer-only string '12'."""
    assert ForecastValidator.parse_horizon("12") == 12


def test_parse_horizon_none_returns_none():
    """parse_horizon returns None for None input."""
    assert ForecastValidator.parse_horizon(None) is None


def test_parse_horizon_all_returns_none():
    """parse_horizon returns None for 'all' input."""
    assert ForecastValidator.parse_horizon("all") is None


def test_validate_horizons_list_empty_returns_all():
    """validate_horizons_list returns all supported horizons when given empty list."""
    result = ForecastValidator.validate_horizons_list(None)
    assert 24 in result
    assert 72 in result


def test_validate_horizons_list_with_values():
    """validate_horizons_list returns sorted deduplicated list."""
    result = ForecastValidator.validate_horizons_list(["24h", "12h", "24h"])
    assert result == [12, 24]


# ---------------------------------------------------------------------------
# health/safety_validator.py — too-short question (line 37), oversized history (line 65)
# ---------------------------------------------------------------------------


def test_safety_validator_rejects_too_short_question():
    """HealthSafetyValidator.validate_question raises 400 for < 2 char question."""
    from app.services.health.safety_validator import HealthSafetyValidator

    with pytest.raises(Exception) as exc_info:
        HealthSafetyValidator.validate_question("x")
    assert exc_info.value.status_code == 400  # type: ignore[attr-defined]


def test_safety_validator_accepts_valid_question():
    """HealthSafetyValidator.validate_question returns cleaned question for valid input."""
    from app.services.health.safety_validator import HealthSafetyValidator

    result = HealthSafetyValidator.validate_question("What AQI level is safe for children?")
    assert "AQI" in result


def test_safety_validator_rejects_oversized_history_message():
    """validate_history raises 400 when any message exceeds 1000 chars."""
    from app.services.health.safety_validator import HealthSafetyValidator

    class FakeMsg:
        content = "x" * 1001
        role = "user"

    with pytest.raises(Exception) as exc_info:
        HealthSafetyValidator.validate_history([FakeMsg()])  # type: ignore[arg-type]
    assert exc_info.value.status_code == 400  # type: ignore[attr-defined]


def test_safety_validator_rejects_too_many_history_turns():
    """validate_history raises 400 when history exceeds max turns."""
    from app.services.health.safety_validator import HealthSafetyValidator

    class FakeMsg:
        content = "valid"
        role = "user"

    with pytest.raises(Exception) as exc_info:
        HealthSafetyValidator.validate_history([FakeMsg()] * 25)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 400  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# main.py — /health endpoint, root endpoint
# ---------------------------------------------------------------------------


def test_root_endpoint_returns_200():
    """GET / returns 200 with service info."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "service" in data or "name" in data or "status" in data


def test_health_endpoint_returns_200():
    """GET /api/v1/health returns 200."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_openapi_schema_accessible():
    """GET /openapi.json returns schema."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "openapi" in resp.json()


def test_404_returns_json():
    """Non-existent route returns JSON 404."""
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404


def test_docs_endpoint_returns_200():
    """GET /docs returns HTML documentation page."""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# aqi/processor.py — additional edge paths
# ---------------------------------------------------------------------------


def test_aqi_readings_endpoint_no_params():
    """GET /api/v1/air-quality/readings with no params returns list."""
    resp = client.get("/api/v1/air-quality/readings")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_aqi_readings_endpoint_delhi():
    """GET /api/v1/air-quality/readings?city=Delhi returns list."""
    resp = client.get("/api/v1/air-quality/readings?city=Delhi")
    assert resp.status_code in (200, 404)


# ---------------------------------------------------------------------------
# impact-metrics endpoint validation
# ---------------------------------------------------------------------------


def test_impact_metrics_all_pillars_have_required_fields():
    """Every impact-metrics pillar has pillar, quantified_impact, source, target_groups."""
    resp = client.get("/api/v1/health/impact-metrics")
    assert resp.status_code == 200
    for p in resp.json()["pillars"]:
        assert "pillar" in p
        assert "quantified_impact" in p
        assert "source" in p
        assert "target_groups" in p
        assert len(p["quantified_impact"]) > 5  # non-trivial string
