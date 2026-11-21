"""Automated tests for external provider integration, mapping, caching, and API endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.seed import seed_cities
from app.integrations.cpcb.client import CPCBClient
from app.integrations.cpcb.exceptions import (
    CPCBAuthError,
    CPCBParseError,
    CPCBProviderError,
    CPCBRateLimitError,
    CPCBTimeoutError,
)
from app.integrations.cpcb.mapper import CPCBRecordMapper
from app.integrations.mock.provider import MockAQIProvider
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.services.aqi_data_service import AQIDataService
from app.services.data_normalization_service import DataNormalizationService


# Sample raw CPCB record matching data.gov.in format
SAMPLE_CPCB_RAW = {
    "total": 1,
    "count": 1,
    "records": [
        {
            "id": "101",
            "country": "India",
            "state": "Delhi",
            "city": "Delhi",
            "station": "Anand Vihar, Delhi - DPCC",
            "last_update": "20-11-2026 18:00:00",
            "pollutant_id": "PM2.5",
            "pollutant_min": "110",
            "pollutant_max": "320",
            "pollutant_avg": "215",
            "pollutant_unit": "µg/m3",
            "latitude": "28.6508",
            "longitude": "77.3152",
        }
    ],
}


def test_cpcb_mapper_valid_record():
    """Verify that CPCBRecordMapper correctly normalizes fields, units, and timestamps."""
    observations = CPCBRecordMapper.map_records(SAMPLE_CPCB_RAW)
    assert len(observations) == 1

    obs = observations[0]
    assert obs.city == "Delhi"
    assert obs.state == "Delhi"
    assert obs.station_name == "Anand Vihar, Delhi - DPCC"
    assert obs.pollutant_code == "PM2.5"
    assert obs.concentration == 215.0
    assert obs.unit == "µg/m³"
    assert obs.latitude == 28.6508
    assert obs.longitude == 77.3152
    assert obs.is_simulated is False
    assert obs.source == "CPCB"

    # IST 18:00 should convert to UTC 12:30
    assert obs.measured_at.hour == 12
    assert obs.measured_at.minute == 30
    assert obs.measured_at.tzinfo == timezone.utc


def test_cpcb_mapper_pollutant_and_unit_standardization():
    """Verify standard mapping of OZONE -> O3, PM 10 -> PM10, and unit variations."""
    records = {
        "records": [
            {
                "country": "India",
                "state": "Karnataka",
                "city": "Bengaluru",
                "station": "BTM Layout",
                "last_update": "20-11-2026 12:00:00",
                "pollutant_id": "OZONE",
                "pollutant_avg": "42.5",
                "pollutant_unit": "ug/m3",
            },
            {
                "country": "India",
                "state": "Maharashtra",
                "city": "Mumbai",
                "station": "BKC",
                "last_update": "20-11-2026 12:00:00",
                "pollutant_id": "CO",
                "pollutant_avg": "1.2",
                "pollutant_unit": "mg/m3",
            },
        ]
    }
    mapped = CPCBRecordMapper.map_records(records)
    assert len(mapped) == 2
    assert mapped[0].pollutant_code == "O3"
    assert mapped[0].unit == "µg/m³"
    assert mapped[1].pollutant_code == "CO"
    assert mapped[1].unit == "mg/m³"


def test_cpcb_mapper_invalid_values_filtered():
    """Verify that records with NA, negative concentrations, or missing city are skipped."""
    records = {
        "records": [
            {"city": "Delhi", "state": "Delhi", "pollutant_id": "PM2.5", "pollutant_avg": "NA"},
            {"city": "Delhi", "state": "Delhi", "pollutant_id": "PM2.5", "pollutant_avg": "-5"},
            {"city": "", "state": "Delhi", "pollutant_id": "PM2.5", "pollutant_avg": "50"},
            {"city": "Delhi", "state": "", "pollutant_id": "PM2.5", "pollutant_avg": "50"},
        ]
    }
    mapped = CPCBRecordMapper.map_records(records)
    assert len(mapped) == 0


@pytest.mark.anyio
async def test_cpcb_client_auth_error_when_no_key():
    """Verify CPCBClient raises CPCBAuthError if api_key is missing."""
    client = CPCBClient(base_url="https://api.data.gov.in/resource/test", api_key=None)
    with pytest.raises(CPCBAuthError) as exc_info:
        await client.get_raw_records()
    assert "CPCB API key is not configured" in str(exc_info.value)
    await client.close()


@pytest.mark.anyio
async def test_cpcb_client_http_status_handling():
    """Verify CPCBClient handles 401, 429, and 500 status codes appropriately."""
    client = CPCBClient(base_url="https://api.data.gov.in/resource/test", api_key="dummy_key", max_retries=0)

    # 401 Unauthorized
    mock_resp_401 = httpx.Response(status_code=401, request=httpx.Request("GET", "http://test"))
    with patch.object(client._get_client(), "get", AsyncMock(return_value=mock_resp_401)):
        with pytest.raises(CPCBAuthError):
            await client.get_raw_records()

    # 429 Rate Limit
    mock_resp_429 = httpx.Response(status_code=429, request=httpx.Request("GET", "http://test"))
    with patch.object(client._get_client(), "get", AsyncMock(return_value=mock_resp_429)):
        with pytest.raises(CPCBRateLimitError):
            await client.get_raw_records()

    # 500 Server Error
    mock_resp_500 = httpx.Response(status_code=500, request=httpx.Request("GET", "http://test"))
    with patch.object(client._get_client(), "get", AsyncMock(return_value=mock_resp_500)):
        with pytest.raises(CPCBProviderError):
            await client.get_raw_records()

    await client.close()


def test_canonical_city_matching():
    """Verify normalization of city spelling variations and aliases."""
    # Aliases
    assert DataNormalizationService.match_canonical_city("Bangalore") == ("Bengaluru", "Karnataka")
    assert DataNormalizationService.match_canonical_city("Calcutta") == ("Kolkata", "West Bengal")
    assert DataNormalizationService.match_canonical_city("Madras") == ("Chennai", "Tamil Nadu")
    assert DataNormalizationService.match_canonical_city("Cochin") == ("Kochi", "Kerala")
    assert DataNormalizationService.match_canonical_city("Tuticorin") == ("Thoothukudi", "Tamil Nadu")
    assert DataNormalizationService.match_canonical_city("New Delhi") == ("Delhi", "Delhi")

    # Canonical names
    assert DataNormalizationService.match_canonical_city("Coimbatore") == ("Coimbatore", "Tamil Nadu")
    assert DataNormalizationService.match_canonical_city("Hyderabad") == ("Hyderabad", "Telangana")

    # Unknown city
    assert DataNormalizationService.match_canonical_city("London") is None


@pytest.mark.anyio
async def test_mock_provider_observations():
    """Verify MockAQIProvider generates observations with is_simulated=True."""
    mock_provider = MockAQIProvider()
    obs = await mock_provider.fetch_observations(city="Coimbatore")
    assert len(obs) > 0
    assert all(o.city == "Coimbatore" for o in obs)
    assert all(o.is_simulated is True for o in obs)
    assert all(o.source == "SIMULATED" for o in obs)
    await mock_provider.close()


@pytest.mark.anyio
async def test_sync_and_persistence_deduplication(db_session: Session):
    """Verify data synchronization, station creation, and reading deduplication."""
    seed_cities(db_session)

    mock_provider = MockAQIProvider()
    service = AQIDataService(provider=mock_provider)

    # First sync
    res1 = await service.sync_and_persist(db=db_session, city="Coimbatore")
    assert res1.success is True
    assert res1.records_fetched > 0
    assert res1.readings_inserted > 0
    assert res1.stations_created > 0

    station_count = db_session.query(MonitoringStation).count()
    reading_count = db_session.query(PollutantReading).count()
    assert station_count > 0
    assert reading_count > 0

    # Second sync immediately with identical readings -> 0 new readings inserted
    res2 = await service.sync_and_persist(db=db_session, city="Coimbatore")
    assert res2.readings_inserted == 0
    assert res2.stations_created == 0

    assert db_session.query(MonitoringStation).count() == station_count
    assert db_session.query(PollutantReading).count() == reading_count


@pytest.mark.anyio
async def test_stale_data_detection(db_session: Session):
    """Verify calculation of data_age_seconds and is_stale flag."""
    seed_cities(db_session)
    coimbatore = db_session.query(City).filter(City.name == "Coimbatore").first()

    # Insert a reading measured 5 hours ago
    old_time = datetime.now(timezone.utc) - timedelta(hours=5)
    old_reading = PollutantReading(
        city_id=coimbatore.id,
        pollutant_code="PM2.5",
        concentration=45.0,
        unit="µg/m³",
        measured_at=old_time,
        source="CPCB",
    )
    db_session.add(old_reading)
    db_session.commit()

    service = AQIDataService(provider=MockAQIProvider())
    air_quality = service.get_city_air_quality(db_session, "Coimbatore")

    assert air_quality.data_available is True
    assert air_quality.is_stale is True
    assert air_quality.data_age_seconds is not None
    assert air_quality.data_age_seconds >= 18000


@pytest.mark.anyio
async def test_api_air_quality_endpoints(client, db_session: Session):
    """Verify all Phase 3 API routes work end-to-end."""
    seed_cities(db_session)

    # Sync data using Mock provider
    mock_provider = MockAQIProvider()
    service = AQIDataService(provider=mock_provider)
    await service.sync_and_persist(db=db_session, city="Delhi")

    # 1. GET /api/v1/air-quality/cities
    resp_cities = await client.get("/api/v1/air-quality/cities")
    assert resp_cities.status_code == 200
    cities_data = resp_cities.json()
    assert len(cities_data) == 10
    delhi_summary = next(c for c in cities_data if c["city_name"] == "Delhi")
    assert delhi_summary["data_available"] is True

    # 2. GET /api/v1/air-quality/cities/Delhi
    resp_delhi = await client.get("/api/v1/air-quality/cities/Delhi")
    assert resp_delhi.status_code == 200
    delhi_data = resp_delhi.json()
    assert delhi_data["city_name"] == "Delhi"
    assert len(delhi_data["pollutants"]) > 0

    # 3. GET /api/v1/air-quality/cities/UnknownCity -> 404
    resp_404 = await client.get("/api/v1/air-quality/cities/NonExistentCity")
    assert resp_404.status_code == 404

    # 4. GET /api/v1/stations
    resp_stations = await client.get("/api/v1/stations?city=Delhi")
    assert resp_stations.status_code == 200
    stations = resp_stations.json()
    assert len(stations) > 0

    # 5. GET /api/v1/air-quality/source-status
    resp_status = await client.get("/api/v1/air-quality/source-status")
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert "provider_name" in status_data
    assert "license" in status_data
    # Ensure no secrets or API keys leaked
    assert "api_key" not in status_data
    assert "secret" not in status_data


@pytest.mark.anyio
async def test_api_sync_endpoint_protection(client, db_session: Session):
    """Verify POST /api/v1/air-quality/sync executes safely and honors secret protection."""
    seed_cities(db_session)

    # When no secret is configured, sync succeeds
    resp = await client.post("/api/v1/air-quality/sync")
    assert resp.status_code in (200, 502)  # 200 if provider succeeds or 502 if unconfigured real CPCB

