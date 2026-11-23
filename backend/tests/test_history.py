"""Comprehensive test suite for Phase 5: Historical Data Service."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading


@pytest.fixture
def history_seed_data(db_session: Session):
    """Seed test database with multi-city historical measurements."""
    # Create Cities
    delhi = City(
        name="Delhi",
        state="Delhi",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
    )
    bengaluru = City(
        name="Bengaluru",
        state="Karnataka",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
    )
    mumbai = City(
        name="Mumbai",
        state="Maharashtra",
        country="India",
        latitude=19.0760,
        longitude=72.8777,
    )
    db_session.add_all([delhi, bengaluru, mumbai])
    db_session.flush()

    # Create Stations
    st_delhi = MonitoringStation(
        station_name="Anand Vihar CAAQMS",
        external_station_id="DEL_AV_01",
        city_id=delhi.id,
        latitude=28.6469,
        longitude=77.3160,
        provider="CPCB",
        is_active=True,
    )
    st_blr = MonitoringStation(
        station_name="BTM Layout Station",
        external_station_id="BLR_BTM_01",
        city_id=bengaluru.id,
        latitude=12.9166,
        longitude=77.6101,
        provider="CPCB",
        is_active=True,
    )
    db_session.add_all([st_delhi, st_blr])
    db_session.flush()

    # Base reference date: 2026-11-01 10:00:00 UTC (a Sunday)
    base_time = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)

    # Populate 10 consecutive daily AQI readings for Delhi
    # Values: 150, 160, 155, 145, 140 (earlier period), then 110, 105, 100, 95, 90 (later
    # period: improving!)
    delhi_aqi_values = [150, 160, 155, 145, 140, 110, 105, 100, 95, 90]
    for i, val in enumerate(delhi_aqi_values):
        measured_time = base_time + timedelta(days=i)
        cat = "Moderate" if val > 100 else "Satisfactory"
        aqi_rec = AQIReading(
            city_id=delhi.id,
            station_id=st_delhi.id,
            aqi_value=val,
            aqi_category=cat,
            dominant_pollutant="PM2.5",
            measured_at=measured_time,
            source="CPCB",
            is_simulated=(i % 2 == 1),  # Alternating real and simulated
            data_quality="valid",
        )
        db_session.add(aqi_rec)

    # Populate Bengaluru AQI readings: steady Good/Satisfactory [45, 50, 48, 52, 49]
    blr_aqi_values = [45, 50, 48, 52, 49]
    for i, val in enumerate(blr_aqi_values):
        measured_time = base_time + timedelta(days=i)
        aqi_rec = AQIReading(
            city_id=bengaluru.id,
            station_id=st_blr.id,
            aqi_value=val,
            aqi_category="Good" if val <= 50 else "Satisfactory",
            dominant_pollutant="PM10",
            measured_at=measured_time,
            source="CPCB",
            is_simulated=False,
            data_quality="valid",
        )
        db_session.add(aqi_rec)

    # Populate Pollutant Readings for Delhi: PM2.5 concentrations corresponding to the days
    pm25_concentrations = [65.0, 72.0, 68.0, 60.0, 58.0, 42.0, 39.0, 36.0, 34.0, 30.0]
    for i, conc in enumerate(pm25_concentrations):
        measured_time = base_time + timedelta(days=i)
        p_rec = PollutantReading(
            city_id=delhi.id,
            station_id=st_delhi.id,
            pollutant_code="PM2.5",
            concentration=conc,
            unit="µg/m³",
            measured_at=measured_time,
            source="CPCB",
            is_simulated=(i % 2 == 1),
            data_quality="valid",
        )
        db_session.add(p_rec)

    db_session.commit()
    return {
        "delhi": delhi,
        "bengaluru": bengaluru,
        "mumbai": mumbai,
        "st_delhi": st_delhi,
        "st_blr": st_blr,
        "base_time": base_time,
    }


@pytest.mark.anyio
async def test_get_aqi_history_raw_pagination(client: AsyncClient, history_seed_data):
    """Test retrieving raw AQI historical records with pagination."""
    response = await client.get("/api/v1/history/aqi?city=Delhi&page=1&page_size=4")
    assert response.status_code == 200
    data = response.json()

    assert data["city"] == "Delhi"
    assert data["total_records"] == 10
    assert data["page"] == 1
    assert data["page_size"] == 4
    assert data["total_pages"] == 3
    assert len(data["records"]) == 4

    # Verify descending chronological order
    first_record = data["records"][0]
    second_record = data["records"][1]
    assert first_record["measured_at"] > second_record["measured_at"]
    assert first_record["aqi_value"] is not None
    assert first_record["source"] == "CPCB"


@pytest.mark.anyio
async def test_get_aqi_history_filter_simulated(client: AsyncClient, history_seed_data):
    """Test filtering real vs simulated historical AQI records."""
    # When include_simulated=false, only 5 real records should be returned
    response = await client.get("/api/v1/history/aqi?city=Delhi&include_simulated=false")
    assert response.status_code == 200
    data = response.json()

    assert data["total_records"] == 5
    for r in data["records"]:
        assert r["is_simulated"] is False


@pytest.mark.anyio
async def test_get_aqi_history_date_filtering(client: AsyncClient, history_seed_data):
    """Test date filtering on historical AQI records."""
    base = history_seed_data["base_time"]
    start = (base + timedelta(days=2)).isoformat()
    end = (base + timedelta(days=5)).isoformat()

    response = await client.get(
        "/api/v1/history/aqi", params={"city": "Delhi", "start_date": start, "end_date": end}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 4


@pytest.mark.anyio
async def test_get_aqi_history_station_filter(client: AsyncClient, history_seed_data):
    """Test filtering by station ID."""
    st_id = history_seed_data["st_blr"].id
    response = await client.get(f"/api/v1/history/aqi?station_id={st_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["total_records"] == 5
    assert data["station_id"] == st_id
    assert data["station_name"] == "BTM Layout Station"


@pytest.mark.anyio
async def test_get_aqi_history_daily_aggregation(client: AsyncClient, history_seed_data):
    """Test daily temporal aggregation of AQI records."""
    response = await client.get("/api/v1/history/aqi?city=Delhi&interval=daily")
    assert response.status_code == 200
    data = response.json()

    assert data["interval"] == "daily"
    assert data["total_records"] == 10  # 10 days
    rec = data["records"][0]
    assert rec["period_start"] is not None
    assert rec["period_end"] is not None
    assert rec["average_aqi"] is not None
    assert rec["min_aqi"] is not None
    assert rec["max_aqi"] is not None
    assert rec["median_aqi"] is not None
    assert rec["record_count"] == 1


@pytest.mark.anyio
async def test_get_aqi_history_weekly_aggregation(client: AsyncClient, history_seed_data):
    """Test weekly aggregation using ISO week (Monday start) convention."""
    response = await client.get("/api/v1/history/aqi?city=Delhi&interval=weekly")
    assert response.status_code == 200
    data = response.json()

    assert data["interval"] == "weekly"
    # Nov 1 2026 is Sunday (week 1), Nov 2-8 is Monday-Sunday (week 2), Nov 9-10 (week 3) => 3 weeks
    assert data["total_records"] == 3
    for rec in data["records"]:
        # Verify period_start falls on Monday 00:00:00 UTC
        dt = datetime.fromisoformat(rec["period_start"])
        assert dt.weekday() == 0  # Monday


@pytest.mark.anyio
async def test_get_pollutant_history_raw_and_subindex(client: AsyncClient, history_seed_data):
    """
    Test raw pollutant concentration retrieval and reproducible CPCB NAQI sub-index
    calculation.
    """
    response = await client.get("/api/v1/history/pollutants?city=Delhi&pollutant=PM2.5")
    assert response.status_code == 200
    data = response.json()

    assert data["pollutant"] == "PM2.5"
    assert data["total_records"] == 10
    rec = data["records"][0]
    assert rec["pollutant_code"] == "PM2.5"
    assert rec["unit"] == "µg/m³"
    # Reproducible sub-index
    assert rec["sub_index"] is not None
    assert rec["sub_index_category"] in [
        "Good",
        "Satisfactory",
        "Moderate",
        "Poor",
        "Very Poor",
        "Severe",
    ]


@pytest.mark.anyio
async def test_get_pollutant_history_aggregation(client: AsyncClient, history_seed_data):
    """Test daily aggregation of pollutant concentrations."""
    response = await client.get(
        "/api/v1/history/pollutants?city=Delhi&pollutant=PM2.5&interval=daily"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["interval"] == "daily"
    assert data["total_records"] == 10
    rec = data["records"][0]
    assert rec["average"] is not None
    assert rec["sub_index"] is not None


@pytest.mark.anyio
async def test_get_summary_statistics(client: AsyncClient, history_seed_data):
    """Test statistical summary calculation for valid AQI observations."""
    response = await client.get("/api/v1/history/summary?city=Delhi")
    assert response.status_code == 200
    data = response.json()

    assert data["city"] == "Delhi"
    assert data["record_count"] == 10
    assert data["min_aqi"] == 90
    assert data["max_aqi"] == 160
    # Mean of [150, 160, 155, 145, 140, 110, 105, 100, 95, 90] = 1250 / 10 = 125.0
    assert data["average_aqi"] == 125.0
    assert data["median_aqi"] == 125.0
    assert "Moderate" in data["category_distribution"]
    assert "Satisfactory" in data["category_distribution"]
    assert data["dominant_pollutant_distribution"]["PM2.5"] == 10
    assert data["data_quality"] == "sufficient"


@pytest.mark.anyio
async def test_get_summary_empty_city(client: AsyncClient, history_seed_data):
    """Test statistical summary for a city with no historical measurements."""
    response = await client.get("/api/v1/history/summary?city=Mumbai")
    assert response.status_code == 200
    data = response.json()

    assert data["city"] == "Mumbai"
    assert data["record_count"] == 0
    assert data["average_aqi"] is None
    assert data["data_quality"] == "no_data"


@pytest.mark.anyio
async def test_get_trends_aqi_improving(client: AsyncClient, history_seed_data):
    """Test trend analysis detection of improving air quality (AQI decreases)."""
    response = await client.get("/api/v1/history/trends?city=Delhi&threshold=5.0")
    assert response.status_code == 200
    data = response.json()

    # Earlier values: [150, 160, 155, 145, 140] -> avg = 150.0
    # Later values: [110, 105, 100, 95, 90] -> avg = 100.0
    # Absolute change = -50.0 points => 'improving'
    assert data["trend_direction"] == "improving"
    assert data["absolute_change"] == -50.0
    assert data["percentage_change"] == -33.3
    assert data["earlier_record_count"] == 5
    assert data["later_record_count"] == 5
    assert "methodology" in data


@pytest.mark.anyio
async def test_get_trends_aqi_stable(client: AsyncClient, history_seed_data):
    """Test trend analysis detection of stable air quality."""
    # Bengaluru readings: [45, 50, 48, 52, 49] (5 records, split into 2 vs 3 or 3 vs 2)
    response = await client.get(
        "/api/v1/history/trends?city=Bengaluru&threshold=10.0&min_records_per_period=2"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["trend_direction"] == "stable"
    assert abs(data["absolute_change"]) <= 10.0


@pytest.mark.anyio
async def test_get_trends_insufficient_data(client: AsyncClient, history_seed_data):
    """Test trend classification with insufficient observations."""
    response = await client.get("/api/v1/history/trends?city=Bengaluru&min_records_per_period=10")
    assert response.status_code == 200
    data = response.json()

    assert data["trend_direction"] == "insufficient_data"
    assert data["absolute_change"] is None


@pytest.mark.anyio
async def test_get_trends_pollutant(client: AsyncClient, history_seed_data):
    """Test trend calculation on individual pollutant concentration."""
    response = await client.get("/api/v1/history/trends?city=Delhi&pollutant=PM2.5&threshold=2.0")
    assert response.status_code == 200
    data = response.json()

    assert data["pollutant"] == "PM2.5"
    assert data["metric"] == "Concentration"
    assert data["trend_direction"] == "improving"
    assert data["unit"] == "µg/m³"


@pytest.mark.anyio
async def test_compare_locations_multiple_cities(client: AsyncClient, history_seed_data):
    """Test multi-city historical comparison over identical date horizons."""
    response = await client.get("/api/v1/history/compare?cities=Delhi&cities=Bengaluru")
    assert response.status_code == 200
    data = response.json()

    assert data["location_count"] == 2
    delhi_comp = next(c for c in data["comparisons"] if c["city_name"] == "Delhi")
    blr_comp = next(c for c in data["comparisons"] if c["city_name"] == "Bengaluru")

    assert delhi_comp["average_aqi"] == 125.0
    assert blr_comp["average_aqi"] < delhi_comp["average_aqi"]
    assert delhi_comp["record_count"] == 10
    assert blr_comp["record_count"] == 5


@pytest.mark.anyio
async def test_compare_locations_comma_separated(client: AsyncClient, history_seed_data):
    """Test multi-city comparison with comma-separated query parameter."""
    response = await client.get("/api/v1/history/compare?cities=Delhi,Bengaluru")
    assert response.status_code == 200
    data = response.json()
    assert data["location_count"] == 2


@pytest.mark.anyio
async def test_compare_locations_validation_boundaries(client: AsyncClient):
    """Test validation errors for comparison targets (< 2 or > 10)."""
    # Less than 2 targets
    res1 = await client.get("/api/v1/history/compare?cities=Delhi")
    assert res1.status_code == 400
    assert "at least 2" in res1.json()["detail"]

    # More than 10 targets
    over_limit = ",".join([f"City{i}" for i in range(11)])
    res2 = await client.get(f"/api/v1/history/compare?cities={over_limit}")
    assert res2.status_code == 400
    assert "maximum of 10" in res2.json()["detail"]


@pytest.mark.anyio
async def test_validation_invalid_date_order(client: AsyncClient):
    """Test rejection when start_date is later than end_date."""
    response = await client.get(
        "/api/v1/history/aqi?start_date=2026-11-10T00:00:00Z&end_date=2026-11-01T00:00:00Z"
    )
    assert response.status_code == 400
    assert "start_date" in response.json()["detail"]


@pytest.mark.anyio
async def test_validation_unsupported_interval(client: AsyncClient):
    """Test rejection of unsupported aggregation intervals."""
    response = await client.get("/api/v1/history/aqi?interval=biweekly")
    assert response.status_code == 400
    assert "Unsupported interval" in response.json()["detail"]


@pytest.mark.anyio
async def test_validation_invalid_pollutant_code(client: AsyncClient):
    """Test rejection of invalid pollutant codes."""
    response = await client.get("/api/v1/history/pollutants?pollutant=CH4")
    assert response.status_code == 400
    assert "Invalid pollutant code" in response.json()["detail"]


@pytest.mark.anyio
async def test_validation_unknown_city_and_station(client: AsyncClient):
    """Test 404 response for non-existent city or station."""
    res_city = await client.get("/api/v1/history/aqi?city=Atlantis")
    assert res_city.status_code == 404

    res_st = await client.get("/api/v1/history/aqi?station_id=999999")
    assert res_st.status_code == 404
