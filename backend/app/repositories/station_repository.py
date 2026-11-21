"""Monitoring station repository for database access."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.monitoring_station import MonitoringStation
from app.schemas.monitoring_station import StationCreate


class StationRepository:
    """Repository handling database operations for MonitoringStation entities."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, station_id: int) -> Optional[MonitoringStation]:
        """Retrieve a station by its primary key."""
        return self.db.get(MonitoringStation, station_id)

    def list_by_city(self, city_id: int, active_only: bool = True) -> List[MonitoringStation]:
        """Retrieve all stations belonging to a specific city."""
        statement = select(MonitoringStation).where(MonitoringStation.city_id == city_id)
        if active_only:
            statement = statement.where(MonitoringStation.is_active.is_(True))
        statement = statement.order_by(MonitoringStation.station_name)
        return list(self.db.execute(statement).scalars().all())

    def list_all_active(self) -> List[MonitoringStation]:
        """Retrieve all currently active monitoring stations across all cities."""
        statement = select(MonitoringStation).where(MonitoringStation.is_active.is_(True)).order_by(MonitoringStation.station_name)
        return list(self.db.execute(statement).scalars().all())

    def create(self, station_in: StationCreate) -> MonitoringStation:
        """Persist a new monitoring station record."""
        station = MonitoringStation(
            station_name=station_in.station_name,
            external_station_id=station_in.external_station_id,
            city_id=station_in.city_id,
            latitude=station_in.latitude,
            longitude=station_in.longitude,
            provider=station_in.provider,
            is_active=station_in.is_active,
        )
        self.db.add(station)
        self.db.commit()
        self.db.refresh(station)
        return station

