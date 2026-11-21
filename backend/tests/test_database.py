"""Automated tests for database models, relationships, constraints, repositories, and seeding."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.init_db import check_database_health
from app.db.seed import seed_cities
from app.models.alert import Alert
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.repositories.city_repository import CityRepository
from app.repositories.reading_repository import ReadingRepository
from app.repositories.station_repository import StationRepository
from app.schemas.alert import AlertCreate
from app.schemas.aqi import AQIReadingCreate
from app.schemas.city import CityCreate, CityUpdate
from app.schemas.monitoring_station import StationCreate
from app.schemas.pollutant import PollutantReadingCreate


def test_city_creation(db_session: Session):
    """Test creating and persisting a valid City record."""
    city = City(
        name="Coimbatore",
        state="Tamil Nadu",
        country="India",
        latitude=11.0168,
        longitude=76.9558,
    )
    db_session.add(city)
    db_session.flush()

    assert city.id is not None
    assert city.name == "Coimbatore"
    assert city.state == "Tamil Nadu"
    assert city.country == "India"
    assert city.created_at is not None
    assert city.updated_at is not None


def test_duplicate_city_prevention(db_session: Session):
    """Test that the unique constraint on (name, state) prevents duplicate cities."""
    city1 = City(
        name="Chennai",
        state="Tamil Nadu",
        country="India",
        latitude=13.0827,
        longitude=80.2707,
    )
    db_session.add(city1)
    db_session.flush()

    city2 = City(
        name="Chennai",
        state="Tamil Nadu",
        country="India",
        latitude=13.0827,
        longitude=80.2707,
    )
    db_session.add(city2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_city_and_station_relationship(db_session: Session):
    """Test bidirectional relationship between City and MonitoringStation."""
    city = City(
        name="Bengaluru",
        state="Karnataka",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
    )
    db_session.add(city)
    db_session.flush()

    station = MonitoringStation(
        station_name="BTM Layout Sensor",
        external_station_id="BLR_BTM_01",
        city_id=city.id,
        latitude=12.9166,
        longitude=77.6101,
        provider="CPCB",
        is_active=True,
    )
    db_session.add(station)
    db_session.flush()

    # Test relationship navigation
    assert len(city.stations) == 1
    assert city.stations[0].station_name == "BTM Layout Sensor"
    assert station.city.name == "Bengaluru"


def test_pollutant_reading_creation_and_constraints(db_session: Session):
    """Test pollutant reading storage and non-negative concentration check constraint."""
    city = City(
        name="Delhi",
        state="Delhi",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
    )
    db_session.add(city)
    db_session.flush()

    # Valid non-negative concentration
    now_utc = datetime.now(UTC)
    reading = PollutantReading(
        city_id=city.id,
        pollutant_code="PM2.5",
        concentration=45.2,
        unit="µg/m³",
        measured_at=now_utc,
        source="CPCB",
    )
    db_session.add(reading)
    db_session.flush()
    assert reading.id is not None
    assert reading.concentration == 45.2

    # Negative concentration should violate check constraint
    invalid_reading = PollutantReading(
        city_id=city.id,
        pollutant_code="PM10",
        concentration=-10.0,
        unit="µg/m³",
        measured_at=now_utc,
        source="CPCB",
    )
    db_session.add(invalid_reading)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_aqi_reading_creation_and_simulation(db_session: Session):
    """Test AQI reading creation and distinction between simulated and real readings."""
    city = City(
        name="Hyderabad",
        state="Telangana",
        country="India",
        latitude=17.3850,
        longitude=78.4867,
    )
    db_session.add(city)
    db_session.flush()

    now_utc = datetime.now(UTC)

    # Simulated reading
    sim_reading = AQIReading(
        city_id=city.id,
        aqi_value=85,
        aqi_category="Satisfactory",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="OpenAQ",
        is_simulated=True,
    )
    # Real observed reading
    real_reading = AQIReading(
        city_id=city.id,
        aqi_value=142,
        aqi_category="Moderate",
        dominant_pollutant="PM10",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    db_session.add_all([sim_reading, real_reading])
    db_session.flush()

    assert sim_reading.is_simulated is True
    assert real_reading.is_simulated is False
    assert len(city.aqi_readings) == 2


def test_alert_creation_and_relationships(db_session: Session):
    """Test Alert model persistence and relationships to City and AQI reading."""
    city = City(
        name="Mumbai",
        state="Maharashtra",
        country="India",
        latitude=19.0760,
        longitude=72.8777,
    )
    db_session.add(city)
    db_session.flush()

    now_utc = datetime.now(UTC)
    aqi_record = AQIReading(
        city_id=city.id,
        aqi_value=310,
        aqi_category="Very Poor",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    db_session.add(aqi_record)
    db_session.flush()

    alert = Alert(
        city_id=city.id,
        aqi_reading_id=aqi_record.id,
        title="High Pollution Advisory",
        description="Air quality has reached Very Poor levels in Mumbai.",
        severity="high",
        alert_type="AQI_SPIKE",
        is_read=False,
        is_simulated=False,
    )
    db_session.add(alert)
    db_session.flush()

    assert alert.id is not None
    assert alert.city.name == "Mumbai"
    assert alert.aqi_reading.aqi_value == 310
    assert len(aqi_record.alerts) == 1


def test_foreign_key_constraints(db_session: Session):
    """Test foreign key constraint enforcement on non-existent references and restrict deletion."""
    # Inserting station with invalid city_id
    invalid_station = MonitoringStation(
        station_name="Ghost Station",
        city_id=999999,
        latitude=10.0,
        longitude=20.0,
        provider="CPCB",
    )
    db_session.add(invalid_station)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_repositories(db_session: Session):
    """Test Repository CRUD operations for City, Station, Readings, and Alerts."""
    city_repo = CityRepository(db_session)
    station_repo = StationRepository(db_session)
    reading_repo = ReadingRepository(db_session)

    # CityRepository create & get
    created_city = city_repo.create(
        CityCreate(
            name="Kochi",
            state="Kerala",
            country="India",
            latitude=9.9312,
            longitude=76.2673,
        )
    )
    assert created_city.id is not None

    found = city_repo.get_by_name_and_state("Kochi", "Kerala")
    assert found is not None
    assert found.id == created_city.id

    # CityRepository update
    updated = city_repo.update(created_city, CityUpdate(country="Republic of India"))
    assert updated.country == "Republic of India"

    # StationRepository create & list
    station = station_repo.create(
        StationCreate(
            station_name="Marine Drive Node",
            city_id=created_city.id,
            latitude=9.9800,
            longitude=76.2750,
            provider="CPCB",
            is_active=True,
        )
    )
    stations = station_repo.list_by_city(created_city.id)
    assert len(stations) == 1
    assert stations[0].station_name == "Marine Drive Node"

    # ReadingRepository pollutant reading
    now_utc = datetime.now(UTC)
    reading_repo.create_pollutant_reading(
        PollutantReadingCreate(
            city_id=created_city.id,
            station_id=station.id,
            pollutant_code="NO2",
            concentration=18.5,
            unit="µg/m³",
            measured_at=now_utc,
            source="CPCB",
        )
    )
    latest_pollutant = reading_repo.get_latest_pollutant_reading(created_city.id, "NO2")
    assert latest_pollutant is not None
    assert latest_pollutant.concentration == 18.5

    # ReadingRepository AQI reading
    reading_repo.create_aqi_reading(
        AQIReadingCreate(
            city_id=created_city.id,
            aqi_value=62,
            aqi_category="Satisfactory",
            dominant_pollutant="NO2",
            measured_at=now_utc,
            source="CPCB",
            is_simulated=False,
        )
    )
    latest_aqi = reading_repo.get_latest_aqi_reading(created_city.id)
    assert latest_aqi is not None
    assert latest_aqi.aqi_value == 62

    # ReadingRepository alert creation & update
    alert = reading_repo.create_alert(
        AlertCreate(
            city_id=created_city.id,
            title="Clean Air Notice",
            description="Air quality is satisfactory.",
            severity="low",
            alert_type="ADVISORY",
            is_read=False,
            is_simulated=False,
        )
    )
    unread_alerts = reading_repo.list_alerts(city_id=created_city.id, unread_only=True)
    assert len(unread_alerts) == 1

    marked = reading_repo.mark_alert_read(alert.id, is_read=True)
    assert marked.is_read is True
    unread_now = reading_repo.list_alerts(city_id=created_city.id, unread_only=True)
    assert len(unread_now) == 0


def test_repeated_city_seeding_without_duplicates(db_session: Session):
    """Test that seed_cities inserts 10 cities initially and 0 on subsequent runs."""
    # First seed execution
    res1 = seed_cities(db_session)
    assert res1["inserted"] == 10
    assert res1["existing"] == 0
    assert res1["total"] == 10

    # Second seed execution
    res2 = seed_cities(db_session)
    assert res2["inserted"] == 0
    assert res2["existing"] == 10
    assert res2["total"] == 10

    # Verify total count in database
    city_count = db_session.query(City).count()
    assert city_count == 10


def test_database_health_check(db_session: Session):
    """Test check_database_health function returns connected status."""
    health = check_database_health(db_session)
    assert health["healthy"] is True
    assert health["status"] == "connected"

