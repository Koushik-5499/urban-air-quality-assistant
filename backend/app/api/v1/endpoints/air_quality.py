"""Air Quality endpoints for real-time observations, city availability, and sync."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import verify_admin_access
from app.db.session import get_db
from app.repositories.reading_repository import ReadingRepository
from app.schemas.air_quality import (
    CityAirQualityResponse,
    CityAvailabilitySummary,
    SourceStatusResponse,
    SyncResponse,
)
from app.schemas.pollutant import PollutantReadingResponse
from app.services.aqi_data_service import AQIDataService, get_aqi_data_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=list[PollutantReadingResponse],
    summary="List Pollutant Observations",
    description=(
        "Retrieve historical and latest ambient pollutant measurements filtered by city, "
        "state, or pollutant code."
    ),
)
async def list_air_quality_readings(
    city: str | None = Query(None, description="City name filter"),
    pollutant: str | None = Query(None, description="Pollutant code filter (PM2.5, PM10, etc.)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
    aqi_service: AQIDataService = Depends(get_aqi_data_service),
) -> list[PollutantReadingResponse]:
    """Retrieve pollutant observations from the database repository."""
    repo = ReadingRepository(db)

    city_id = None
    if city:
        try:
            city_data = aqi_service.get_city_air_quality(db, city)
            city_id = city_data.city_id
        except KeyError:
            return []

    if city_id is not None:
        readings = repo.list_pollutant_readings(
            city_id=city_id, pollutant_code=pollutant, limit=limit
        )
        return [PollutantReadingResponse.model_validate(r) for r in readings]

    # If no specific city, return recent readings across all cities
    from sqlalchemy import desc, select

    from app.models.pollutant_reading import PollutantReading

    stmt = select(PollutantReading)
    if pollutant:
        stmt = stmt.where(PollutantReading.pollutant_code == pollutant)
    stmt = stmt.order_by(desc(PollutantReading.measured_at)).limit(limit)

    all_readings = db.execute(stmt).scalars().all()
    return [PollutantReadingResponse.model_validate(r) for r in all_readings]


@router.get(
    "/cities",
    response_model=list[CityAvailabilitySummary],
    summary="List Cities Data Availability",
    description=(
        "Retrieve data availability, active station counts, and freshness status for all 10 "
        "supported Indian cities."
    ),
)
async def list_cities_availability(
    db: Session = Depends(get_db),
    aqi_service: AQIDataService = Depends(get_aqi_data_service),
) -> list[CityAvailabilitySummary]:
    """Return overview of all supported cities and their live telemetry coverage."""
    return aqi_service.get_cities_summary(db)


@router.get(
    "/cities/{city_name}",
    response_model=CityAirQualityResponse,
    summary="Get City Air Quality",
    description=(
        "Retrieve the latest ambient observations, active pollutants, and data age for a "
        "specific city."
    ),
)
async def get_city_air_quality(
    city_name: str,
    db: Session = Depends(get_db),
    aqi_service: AQIDataService = Depends(get_aqi_data_service),
) -> CityAirQualityResponse:
    """Return latest pollutant readings and freshness metrics for a specified city."""
    try:
        return aqi_service.get_city_air_quality(db, city_name)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        )


@router.get(
    "/source-status",
    response_model=SourceStatusResponse,
    summary="Get Data Source Diagnostics",
    description=(
        "Check external CPCB provider status, licensing, and sync timestamps without exposing "
        "credentials."
    ),
)
async def get_source_status(
    aqi_service: AQIDataService = Depends(get_aqi_data_service),
) -> SourceStatusResponse:
    """Return diagnostic metadata and data freshness status."""
    return aqi_service.get_source_status()


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Trigger Provider Synchronization",
    description=(
        "Trigger an on-demand synchronization against the configured provider with "
        "deduplication and persistence."
    ),
)
async def trigger_sync(
    city: str | None = Query(None, description="Optional city filter for targeted synchronization"),
    _admin: None = Depends(verify_admin_access),
    db: Session = Depends(get_db),
    aqi_service: AQIDataService = Depends(get_aqi_data_service),
) -> SyncResponse:
    """Execute bounded on-demand data sync."""
    try:
        return await aqi_service.sync_and_persist(db=db, city=city)
    except Exception as exc:
        # Top-level HTTP endpoint boundary converting upstream provider or DB errors to 502
        logger.exception("Synchronization failed for city %s: %s", city, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Synchronization failed: {type(exc).__name__}",
        )
