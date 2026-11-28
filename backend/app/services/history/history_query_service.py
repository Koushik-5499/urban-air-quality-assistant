"""Historical AQI and pollutant paginated/aggregated query helpers."""

import math
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import (
    AQIHistoryRecord,
    AQIHistoryResponse,
    PollutantHistoryRecord,
    PollutantHistoryResponse,
)
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.categories import get_aqi_category
from app.services.history.aggregation_service import AggregationService


@dataclass(frozen=True, slots=True)
class HistoryQueryParams:
    """Common query context passed to historical AQI/pollutant helpers."""

    filters: list
    city_name: str | None
    station_id: int | None
    station_name: str | None
    start_utc: datetime | None
    end_utc: datetime | None
    page: int
    page_size: int
    interval_norm: str | None = None
    pollutant_norm: str | None = None


def get_aggregated_aqi_history(
    db: Session,
    params: HistoryQueryParams,
) -> AQIHistoryResponse:
    """Fetch and aggregate AQI history across specified time intervals."""
    stmt = select(AQIReading).options(
        joinedload(AQIReading.city),
        joinedload(AQIReading.station),
    )
    if params.filters:
        stmt = stmt.where(*params.filters)
    stmt = stmt.order_by(AQIReading.measured_at)

    all_readings = list(db.execute(stmt).scalars().all())
    interval_norm = params.interval_norm or "daily"

    aggregated = AggregationService.aggregate_aqi_readings(
        readings=all_readings,
        interval=interval_norm,
        city_name=params.city_name,
        station_id=params.station_id,
        station_name=params.station_name,
    )

    total_records = len(aggregated)
    total_pages = math.ceil(total_records / params.page_size) if total_records > 0 else 0
    start_idx = (params.page - 1) * params.page_size
    end_idx = start_idx + params.page_size
    paginated_records = aggregated[start_idx:end_idx]

    return AQIHistoryResponse(
        page=params.page,
        page_size=params.page_size,
        total_records=total_records,
        total_pages=total_pages,
        city=params.city_name,
        station_id=params.station_id,
        station_name=params.station_name,
        interval=interval_norm,
        period_start=params.start_utc,
        period_end=params.end_utc,
        records=paginated_records,
    )


def get_raw_aqi_history(
    db: Session,
    params: HistoryQueryParams,
) -> AQIHistoryResponse:
    """Fetch raw, unaggregated AQI readings using SQL offset pagination."""
    count_stmt = select(func.count(AQIReading.id))
    if params.filters:
        count_stmt = count_stmt.where(*params.filters)
    total_records = db.execute(count_stmt).scalar() or 0
    total_pages = math.ceil(total_records / params.page_size) if total_records > 0 else 0

    data_stmt = select(AQIReading).options(
        joinedload(AQIReading.city), joinedload(AQIReading.station)
    )
    if params.filters:
        data_stmt = data_stmt.where(*params.filters)
    data_stmt = (
        data_stmt.order_by(desc(AQIReading.measured_at))
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )

    raw_readings = list(db.execute(data_stmt).scalars().all())

    records = [
        AQIHistoryRecord(
            id=r.id,
            measured_at=r.measured_at,
            created_at=r.created_at,
            aqi_value=r.aqi_value,
            aqi_category=r.aqi_category,
            dominant_pollutant=r.dominant_pollutant,
            source=r.source,
            is_simulated=r.is_simulated,
            data_quality=r.data_quality,
            city_name=r.city.name if r.city else None,
            station_id=r.station_id,
            station_name=r.station.station_name if r.station else None,
        )
        for r in raw_readings
    ]

    return AQIHistoryResponse(
        page=params.page,
        page_size=params.page_size,
        total_records=total_records,
        total_pages=total_pages,
        city=params.city_name,
        station_id=params.station_id,
        station_name=params.station_name,
        interval=None,
        period_start=params.start_utc,
        period_end=params.end_utc,
        records=records,
    )


def get_aggregated_pollutant_history(
    db: Session,
    params: HistoryQueryParams,
) -> PollutantHistoryResponse:
    """Fetch and aggregate pollutant history across specified intervals."""
    stmt = select(PollutantReading).options(
        joinedload(PollutantReading.city),
        joinedload(PollutantReading.station),
    )
    if params.filters:
        stmt = stmt.where(*params.filters)
    stmt = stmt.order_by(PollutantReading.measured_at)

    all_readings = list(db.execute(stmt).scalars().all())
    interval_norm = params.interval_norm or "daily"

    aggregated = AggregationService.aggregate_pollutant_readings(
        readings=all_readings,
        interval=interval_norm,
        city_name=params.city_name,
        station_id=params.station_id,
        station_name=params.station_name,
    )

    total_records = len(aggregated)
    total_pages = math.ceil(total_records / params.page_size) if total_records > 0 else 0
    start_idx = (params.page - 1) * params.page_size
    end_idx = start_idx + params.page_size
    paginated_records = aggregated[start_idx:end_idx]
    default_unit = paginated_records[0].unit if paginated_records else None

    return PollutantHistoryResponse(
        page=params.page,
        page_size=params.page_size,
        total_records=total_records,
        total_pages=total_pages,
        city=params.city_name,
        station_id=params.station_id,
        station_name=params.station_name,
        pollutant=params.pollutant_norm,
        unit=default_unit,
        interval=interval_norm,
        period_start=params.start_utc,
        period_end=params.end_utc,
        records=paginated_records,
    )


def get_raw_pollutant_history(
    db: Session,
    params: HistoryQueryParams,
) -> PollutantHistoryResponse:
    """Fetch raw pollutant readings using SQL pagination."""
    count_stmt = select(func.count(PollutantReading.id))
    if params.filters:
        count_stmt = count_stmt.where(*params.filters)
    total_records = db.execute(count_stmt).scalar() or 0
    total_pages = math.ceil(total_records / params.page_size) if total_records > 0 else 0

    data_stmt = select(PollutantReading).options(
        joinedload(PollutantReading.city), joinedload(PollutantReading.station)
    )
    if params.filters:
        data_stmt = data_stmt.where(*params.filters)
    data_stmt = (
        data_stmt.order_by(desc(PollutantReading.measured_at))
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )

    raw_readings = list(db.execute(data_stmt).scalars().all())

    records: list[PollutantHistoryRecord] = []
    for r in raw_readings:
        sub_idx = AQICalculator.calculate_sub_index(r.pollutant_code, r.concentration, r.unit)
        sub_cat = get_aqi_category(sub_idx) if sub_idx is not None else None
        records.append(
            PollutantHistoryRecord(
                id=r.id,
                pollutant_code=r.pollutant_code,
                concentration=r.concentration,
                unit=r.unit,
                sub_index=sub_idx,
                sub_index_category=sub_cat,
                measured_at=r.measured_at,
                created_at=r.created_at,
                source=r.source,
                is_simulated=r.is_simulated,
                data_quality=r.data_quality,
                city_name=r.city.name if r.city else None,
                station_id=r.station_id,
                station_name=r.station.station_name if r.station else None,
            )
        )

    default_unit = records[0].unit if records else None

    return PollutantHistoryResponse(
        page=params.page,
        page_size=params.page_size,
        total_records=total_records,
        total_pages=total_pages,
        city=params.city_name,
        station_id=params.station_id,
        station_name=params.station_name,
        pollutant=params.pollutant_norm,
        unit=default_unit,
        interval=None,
        period_start=params.start_utc,
        period_end=params.end_utc,
        records=records,
    )
