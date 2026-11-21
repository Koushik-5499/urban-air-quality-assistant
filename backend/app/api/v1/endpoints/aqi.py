"""Air Quality Index calculation and processing endpoints following CPCB NAQI."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import verify_admin_access
from app.db.session import get_db
from app.schemas.aqi_processing import (
    AQICalculationResponse,
    AQIHistoryItem,
    AQIHistoryResponse,
    AQIProcessResponse,
    SubIndicesOnlyResponse,
)
from app.services.aqi.processor import AQIProcessingService

router = APIRouter()


@router.get(
    "/calculate",
    response_model=AQICalculationResponse,
    summary="Calculate NAQI for City or Station",
    description="Calculate Indian National Air Quality Index (NAQI) sub-indices and overall index using CPCB methodology.",
)
async def calculate_aqi(
    city: Optional[str] = Query(None, description="City name (e.g. Delhi, Coimbatore)"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID"),
    db: Session = Depends(get_db),
) -> AQICalculationResponse:
    """Compute CPCB sub-indices, data sufficiency, and overall AQI from stored observations."""
    return AQIProcessingService.calculate_for_city_or_station(
        db=db,
        city_name=city,
        station_id=station_id,
    )


@router.get(
    "/pollutant-subindices",
    response_model=SubIndicesOnlyResponse,
    summary="Get Pollutant Sub-Indices",
    description="Retrieve individual pollutant sub-indices (0-500) and dominant pollutant for a location.",
)
async def get_pollutant_subindices(
    city: Optional[str] = Query(None, description="City name filter"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID filter"),
    db: Session = Depends(get_db),
) -> SubIndicesOnlyResponse:
    """Retrieve isolated pollutant sub-indices and dominant driver pollutant."""
    return AQIProcessingService.get_pollutant_subindices(
        db=db,
        city_name=city,
        station_id=station_id,
    )


@router.get(
    "/latest",
    response_model=AQIHistoryItem,
    summary="Get Latest Stored AQI Reading",
    description="Retrieve the latest persisted AQI record for a specified city or monitoring station.",
)
async def get_latest_aqi(
    city: Optional[str] = Query(None, description="City name filter"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID filter"),
    db: Session = Depends(get_db),
) -> AQIHistoryItem:
    """Query the most recent stored AQI reading."""
    result = AQIProcessingService.get_latest_aqi_reading(
        db=db,
        city_name=city,
        station_id=station_id,
    )
    if not result:
        loc = city or f"station {station_id}" or "the database"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stored AQI reading found for {loc}. Run /api/v1/aqi/process or check /api/v1/aqi/calculate.",
        )
    return result


@router.get(
    "/history",
    response_model=AQIHistoryResponse,
    summary="Get Historical AQI Readings",
    description="Query historical calculated AQI readings with optional date-range and pagination filtering.",
)
async def get_aqi_history(
    city: Optional[str] = Query(None, description="Filter by city name"),
    station_id: Optional[int] = Query(None, description="Filter by monitoring station ID"),
    start_date: Optional[datetime] = Query(None, description="ISO datetime start filter"),
    end_date: Optional[datetime] = Query(None, description="ISO datetime end filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
) -> AQIHistoryResponse:
    """Retrieve paginated historical AQI index records."""
    return AQIProcessingService.get_history(
        db=db,
        city_name=city,
        station_id=station_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/process",
    response_model=AQIProcessResponse,
    summary="Batch Process Stored Observations into AQI Records",
    description="Evaluate stored pollutant readings against CPCB sufficiency rules and persist calculated AQI readings.",
)
async def process_aqi_readings(
    city_id: Optional[int] = Query(None, description="Optional city ID to scope processing"),
    _admin: None = Depends(verify_admin_access),
    db: Session = Depends(get_db),
) -> AQIProcessResponse:
    """Process current pollutant measurements and persist new AQI readings with deduplication."""
    return AQIProcessingService.process_and_persist_aqi(
        db=db,
        city_id=city_id,
    )

