"""Monitoring stations API endpoints."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.schemas.monitoring_station import StationResponse

router = APIRouter()


@router.get(
    "",
    response_model=list[StationResponse],
    summary="List Monitoring Stations",
    description="Retrieve registered environmental monitoring stations filtered by city, state, or provider.",
)
async def list_monitoring_stations(
    city: str | None = Query(None, description="Filter by city name"),
    state: str | None = Query(None, description="Filter by state name"),
    provider: str | None = Query(None, description="Filter by provider (e.g. CPCB)"),
    db: Session = Depends(get_db),
) -> list[StationResponse]:
    """Query known monitoring stations."""
    stmt = select(MonitoringStation).join(City, MonitoringStation.city_id == City.id)

    if city:
        stmt = stmt.where(City.name.ilike(f"%{city.strip()}%"))
    if state:
        stmt = stmt.where(City.state.ilike(f"%{state.strip()}%"))
    if provider:
        stmt = stmt.where(MonitoringStation.provider.ilike(f"%{provider.strip()}%"))

    stmt = stmt.order_by(MonitoringStation.station_name)
    stations = db.execute(stmt).scalars().all()
    return [StationResponse.model_validate(st) for st in stations]

