"""Database query and persistence helpers for AQIProcessingService."""

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.schemas.aqi_processing import (
    AQICalculationResponse,
    AQIHistoryItem,
    AQIHistoryResponse,
    PollutantSubIndexResult,
)
from app.services.aqi.breakpoints import POLLUTANT_INFO
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.categories import get_aqi_category
from app.services.data_normalization_service import DataNormalizationService


def apply_history_filters(
    stmt: Any,
    city_name: str | None,
    station_id: int | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[Any, str | None]:
    """Apply city/station/date filters to an AQI history query. Returns (stmt, resolved_name)."""
    resolved_name: str | None = None
    if city_name:
        match = DataNormalizationService.match_canonical_city(city_name)
        resolved_name = match[0] if match else city_name.strip()
        stmt = stmt.where(func.lower(City.name) == resolved_name.lower())
    if station_id:
        stmt = stmt.where(AQIReading.station_id == station_id)
    if start_date:
        stmt = stmt.where(AQIReading.measured_at >= start_date)
    if end_date:
        stmt = stmt.where(AQIReading.measured_at <= end_date)
    return stmt, resolved_name


def resolve_city_from_name(db: Session, city_name: str) -> City:
    """Look up a City entity by name, raising 404 if not found."""
    match = DataNormalizationService.match_canonical_city(city_name)
    canonical_name = match[0] if match else city_name.strip()
    city_entity = db.execute(
        select(City).where(func.lower(City.name) == canonical_name.lower())
    ).scalar_one_or_none()
    if not city_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{city_name}' is not in the list of supported cities.",
        )
    return city_entity


def resolve_city_from_station(db: Session, station_id: int) -> City:
    """Look up a City entity via a monitoring station, raising 404 if not found."""
    station = db.get(MonitoringStation, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitoring station {station_id} not found.",
        )
    city_entity = db.get(City, station.city_id)
    if not city_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City for monitoring station {station_id} not found.",
        )
    return city_entity


def build_latest_readings_query(city_id: int, station_id: int | None) -> Any:
    """Build a SQLAlchemy query for the latest reading per pollutant."""
    latest_sel = select(
        PollutantReading.pollutant_code,
        func.max(PollutantReading.measured_at).label("max_measured"),
    ).where(PollutantReading.city_id == city_id)
    if station_id:
        latest_sel = latest_sel.where(PollutantReading.station_id == station_id)
    latest_subquery = latest_sel.group_by(PollutantReading.pollutant_code).subquery()

    stmt = (
        select(PollutantReading)
        .join(
            latest_subquery,
            (PollutantReading.pollutant_code == latest_subquery.c.pollutant_code)
            & (PollutantReading.measured_at == latest_subquery.c.max_measured),
        )
        .where(PollutantReading.city_id == city_id)
    )
    if station_id:
        stmt = stmt.where(PollutantReading.station_id == station_id)
    return stmt


def build_no_data_response(
    city_entity: City,
    station_id: int | None,
    station_name: str | None,
    now_utc: datetime,
) -> AQICalculationResponse:
    """Return a typed empty AQI response when no readings are available."""
    return AQICalculationResponse(
        city_id=city_entity.id,
        city_name=city_entity.name,
        station_id=station_id,
        station_name=station_name,
        aqi=None,
        category=None,
        dominant_pollutant=None,
        pollutant_subindices={},
        measurement_timestamp=None,
        calculated_at=now_utc,
        source="CPCB",
        is_simulated=False,
        data_quality="no_data",
        averaging_period="1-hour (indicative)",
        available_pollutants=[],
        missing_pollutants=["All pollutants missing"],
        explanation=f"No pollutant measurements found for {city_entity.name}.",
    )


def compute_sub_indices(
    readings: list[PollutantReading],
) -> tuple[dict[str, int], dict[str, PollutantSubIndexResult]]:
    """Compute NAQI sub-indices for each pollutant reading."""
    sub_indices_dict: dict[str, int] = {}
    sub_index_results: dict[str, PollutantSubIndexResult] = {}
    for reading in readings:
        sub_index = AQICalculator.calculate_sub_index(
            reading.pollutant_code, reading.concentration, reading.unit
        )
        info = POLLUTANT_INFO.get(reading.pollutant_code)
        avg_period = info.averaging_period if info else "24-hour"
        cat = get_aqi_category(sub_index) if sub_index is not None else None
        sub_index_results[reading.pollutant_code] = PollutantSubIndexResult(
            pollutant_code=reading.pollutant_code,
            concentration=reading.concentration,
            unit=reading.unit,
            sub_index=sub_index,
            category=cat,
            averaging_period=f"{avg_period} (reported as 1-hr observation)",
            is_valid=sub_index is not None,
        )
        if sub_index is not None:
            sub_indices_dict[reading.pollutant_code] = sub_index
    return sub_indices_dict, sub_index_results


def get_latest_aqi_reading(
    db: Session,
    city_name: str | None = None,
    station_id: int | None = None,
) -> AQIHistoryItem | None:
    """Fetch the latest stored AQIReading record from the database."""
    stmt = (
        select(
            AQIReading,
            City.name.label("city_name"),
            MonitoringStation.station_name.label("station_name"),
        )
        .join(City, AQIReading.city_id == City.id)
        .outerjoin(MonitoringStation, AQIReading.station_id == MonitoringStation.id)
    )

    if city_name:
        match = DataNormalizationService.match_canonical_city(city_name)
        name_to_query = match[0] if match else city_name.strip()
        stmt = stmt.where(func.lower(City.name) == name_to_query.lower())

    if station_id:
        stmt = stmt.where(AQIReading.station_id == station_id)

    stmt = stmt.order_by(desc(AQIReading.measured_at)).limit(1)
    row = db.execute(stmt).first()
    if not row:
        return None

    reading, c_name, st_name = row
    return AQIHistoryItem(
        id=reading.id,
        city_id=reading.city_id,
        city_name=c_name,
        station_id=reading.station_id,
        station_name=st_name,
        aqi_value=reading.aqi_value,
        aqi_category=reading.aqi_category,
        dominant_pollutant=reading.dominant_pollutant,
        measured_at=reading.measured_at,
        source=reading.source,
        is_simulated=reading.is_simulated,
        created_at=reading.created_at,
    )


def get_history(
    db: Session,
    city_name: str | None = None,
    station_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> AQIHistoryResponse:
    """Retrieve paginated historical calculated AQI readings."""
    base_stmt = (
        select(
            AQIReading,
            City.name.label("city_name"),
            MonitoringStation.station_name.label("station_name"),
        )
        .join(City, AQIReading.city_id == City.id)
        .outerjoin(MonitoringStation, AQIReading.station_id == MonitoringStation.id)
    )
    stmt, _ = apply_history_filters(base_stmt, city_name, station_id, start_date, end_date)

    count_stmt = select(func.count(AQIReading.id)).join(City, AQIReading.city_id == City.id)
    count_stmt, _ = apply_history_filters(count_stmt, city_name, station_id, start_date, end_date)
    total = db.execute(count_stmt).scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(desc(AQIReading.measured_at)).offset(offset).limit(page_size)
    rows = db.execute(stmt).all()

    items = [
        AQIHistoryItem(
            id=reading.id,
            city_id=reading.city_id,
            city_name=c_name,
            station_id=reading.station_id,
            station_name=st_name,
            aqi_value=reading.aqi_value,
            aqi_category=reading.aqi_category,
            dominant_pollutant=reading.dominant_pollutant,
            measured_at=reading.measured_at,
            source=reading.source,
            is_simulated=reading.is_simulated,
            created_at=reading.created_at,
        )
        for reading, c_name, st_name in rows
    ]

    return AQIHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
