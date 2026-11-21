"""Readings and alerts repository for environmental observations."""

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.alert import AlertCreate
from app.schemas.aqi import AQIReadingCreate
from app.schemas.pollutant import PollutantReadingCreate


class ReadingRepository:
    """Repository handling pollutant readings, composite AQI readings, and alerts."""

    def __init__(self, db: Session):
        self.db = db

    # Pollutant Readings
    def create_pollutant_reading(self, reading_in: PollutantReadingCreate) -> PollutantReading:
        """Persist an individual pollutant measurement."""
        reading = PollutantReading(
            city_id=reading_in.city_id,
            station_id=reading_in.station_id,
            pollutant_code=reading_in.pollutant_code,
            concentration=reading_in.concentration,
            unit=reading_in.unit,
            measured_at=reading_in.measured_at,
            source=reading_in.source,
            is_simulated=reading_in.is_simulated or (reading_in.source.upper() == "SIMULATED"),
            data_quality=reading_in.data_quality,
        )
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def list_pollutant_readings(
        self,
        city_id: int,
        pollutant_code: str | None = None,
        limit: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[PollutantReading]:
        """Query pollutant readings filtered by city, pollutant type, and time interval."""
        statement = select(PollutantReading).where(PollutantReading.city_id == city_id)
        if pollutant_code:
            statement = statement.where(PollutantReading.pollutant_code == pollutant_code)
        if start_time:
            statement = statement.where(PollutantReading.measured_at >= start_time)
        if end_time:
            statement = statement.where(PollutantReading.measured_at <= end_time)
        statement = statement.order_by(desc(PollutantReading.measured_at)).limit(limit)
        return list(self.db.execute(statement).scalars().all())

    def get_latest_pollutant_reading(self, city_id: int, pollutant_code: str) -> PollutantReading | None:
        """Fetch the most recent reading for a given city and pollutant."""
        statement = (
            select(PollutantReading)
            .where(PollutantReading.city_id == city_id, PollutantReading.pollutant_code == pollutant_code)
            .order_by(desc(PollutantReading.measured_at))
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()

    # AQI Readings
    def create_aqi_reading(self, aqi_in: AQIReadingCreate) -> AQIReading:
        """Persist a composite AQI measurement."""
        reading = AQIReading(
            city_id=aqi_in.city_id,
            station_id=aqi_in.station_id,
            aqi_value=aqi_in.aqi_value,
            aqi_category=aqi_in.aqi_category,
            dominant_pollutant=aqi_in.dominant_pollutant,
            measured_at=aqi_in.measured_at,
            source=aqi_in.source,
            is_simulated=aqi_in.is_simulated,
            data_quality=aqi_in.data_quality,
        )
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def get_latest_aqi_reading(self, city_id: int) -> AQIReading | None:
        """Fetch the latest AQI reading for a specific city."""
        statement = (
            select(AQIReading)
            .where(AQIReading.city_id == city_id)
            .order_by(desc(AQIReading.measured_at))
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list_aqi_readings(self, city_id: int, limit: int = 50) -> list[AQIReading]:
        """Retrieve recent chronological AQI readings for a city."""
        statement = (
            select(AQIReading)
            .where(AQIReading.city_id == city_id)
            .order_by(desc(AQIReading.measured_at))
            .limit(limit)
        )
        return list(self.db.execute(statement).scalars().all())

    # Alerts
    def create_alert(self, alert_in: AlertCreate) -> Alert:
        """Persist an air quality notification or threshold alert."""
        alert = Alert(
            city_id=alert_in.city_id,
            aqi_reading_id=alert_in.aqi_reading_id,
            title=alert_in.title,
            description=alert_in.description,
            severity=alert_in.severity,
            alert_type=alert_in.alert_type,
            is_read=alert_in.is_read,
            is_simulated=alert_in.is_simulated,
            expires_at=alert_in.expires_at,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_alerts(
        self,
        city_id: int | None = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Alert]:
        """Retrieve alerts optionally filtered by city and read status."""
        statement = select(Alert)
        if city_id:
            statement = statement.where(Alert.city_id == city_id)
        if unread_only:
            statement = statement.where(Alert.is_read.is_(False))
        statement = statement.order_by(desc(Alert.created_at)).limit(limit)
        return list(self.db.execute(statement).scalars().all())

    def mark_alert_read(self, alert_id: int, is_read: bool = True) -> Alert | None:
        """Update read status of an alert."""
        alert = self.db.get(Alert, alert_id)
        if alert:
            alert.is_read = is_read
            self.db.commit()
            self.db.refresh(alert)
        return alert

