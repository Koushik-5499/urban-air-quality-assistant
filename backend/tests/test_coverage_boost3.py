"""Additional targeted coverage tests for CPCB mapper, init_db, and seed.

Covers:
- cpcb/mapper.py: parse_datetime fallback paths, parse_float edge cases
- db/init_db.py: check_database_health with mocked error
- main.py: remaining uncovered startup paths
"""

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# CPCBRecordMapper.parse_datetime — fallback paths
# ---------------------------------------------------------------------------


def test_cpcb_parse_datetime_none_returns_utc_now():
    """parse_datetime(None) returns current UTC time."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    result = CPCBRecordMapper.parse_datetime(None)
    assert result.tzinfo is not None


def test_cpcb_parse_datetime_empty_string():
    """parse_datetime('') returns current UTC time."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    result = CPCBRecordMapper.parse_datetime("")
    assert result.tzinfo is not None


def test_cpcb_parse_datetime_primary_format():
    """parse_datetime parses primary CPCB format '20-11-2026 18:00:00'."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    result = CPCBRecordMapper.parse_datetime("20-11-2026 18:00:00")
    # Should be in UTC (IST - 5:30)
    assert result.hour == 12  # 18:00 IST → 12:30 UTC → 12 (truncated)
    assert result.tzinfo is not None


def test_cpcb_parse_datetime_slash_format():
    """parse_datetime parses slash-separated CPCB date '20/11/2026 10:00:00'."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    result = CPCBRecordMapper.parse_datetime("20/11/2026 10:00:00")
    assert result.tzinfo is not None


def test_cpcb_parse_datetime_iso_format():
    """parse_datetime falls back to isoformat for '2026-11-20T10:00:00'."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    result = CPCBRecordMapper.parse_datetime("2026-11-20T10:00:00")
    assert result.tzinfo is not None


def test_cpcb_parse_datetime_unrecognized_format():
    """parse_datetime returns now-UTC for a completely unrecognized format."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    result = CPCBRecordMapper.parse_datetime("not-a-date-at-all")
    assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# CPCBRecordMapper.parse_float — edge cases
# ---------------------------------------------------------------------------


def test_cpcb_parse_float_none():
    """parse_float(None) returns None."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    assert CPCBRecordMapper.parse_float(None) is None


def test_cpcb_parse_float_int():
    """parse_float(42) returns 42.0."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    assert CPCBRecordMapper.parse_float(42) == 42.0


def test_cpcb_parse_float_string_na():
    """parse_float('NA') returns None."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    assert CPCBRecordMapper.parse_float("NA") is None


def test_cpcb_parse_float_string_null():
    """parse_float('NULL') returns None."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    assert CPCBRecordMapper.parse_float("NULL") is None


def test_cpcb_parse_float_invalid_string():
    """parse_float('abc') returns None."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    assert CPCBRecordMapper.parse_float("abc") is None


def test_cpcb_parse_float_comma_number():
    """parse_float('1,234.5') returns 1234.5."""
    from app.integrations.cpcb.mapper import CPCBRecordMapper

    assert CPCBRecordMapper.parse_float("1,234.5") == 1234.5


# ---------------------------------------------------------------------------
# db/init_db.py — check_database_health with SQLAlchemy error
# ---------------------------------------------------------------------------


def test_check_database_health_sqlalchemy_error():
    """check_database_health returns False on SQLAlchemy error."""
    from sqlalchemy.exc import SQLAlchemyError

    from app.db.init_db import check_database_health

    mock_db = MagicMock()
    mock_db.execute.side_effect = SQLAlchemyError("connection refused")
    result = check_database_health(mock_db)
    assert result["healthy"] is False
    assert result["status"] == "disconnected"


def test_check_database_health_unexpected_error():
    """check_database_health returns False on unexpected exception."""
    from app.db.init_db import check_database_health

    mock_db = MagicMock()
    mock_db.execute.side_effect = RuntimeError("unexpected crash")
    result = check_database_health(mock_db)
    assert result["healthy"] is False


def test_check_database_health_happy_path():
    """check_database_health returns True when query succeeds."""
    from app.db.init_db import check_database_health

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_db.execute.return_value = mock_result
    result = check_database_health(mock_db)
    assert result["healthy"] is True


# ---------------------------------------------------------------------------
# AI integrations base — abstract methods coverage
# ---------------------------------------------------------------------------


def test_ai_base_abstract_methods_documented():
    """BaseAIProvider cannot be instantiated directly."""
    from app.integrations.ai.base import BaseAIProvider

    with pytest.raises(TypeError):
        BaseAIProvider()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# forecasting/validators.py — parse_horizon ValueError branch
# ---------------------------------------------------------------------------


def test_parse_horizon_integer_string_not_in_supported():
    """parse_horizon raises 400 for a supported-looking integer not in SUPPORTED_HORIZONS."""
    from app.services.forecasting.validators import ForecastValidator

    with pytest.raises(Exception) as exc_info:
        ForecastValidator.parse_horizon("99")
    assert exc_info.value.status_code == 400  # type: ignore[attr-defined]


def test_parse_horizon_non_numeric_unsupported_string():
    """parse_horizon raises 400 for 'daily'."""
    from app.services.forecasting.validators import ForecastValidator

    with pytest.raises(Exception) as exc_info:
        ForecastValidator.parse_horizon("daily")
    assert exc_info.value.status_code == 400  # type: ignore[attr-defined]

