"""Historical Air Quality and Pollutant data endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.history import (
    AQIHistoryResponse,
    AQISummaryResponse,
    HistoryCompareResponse,
    HistoryTrendResponse,
    PollutantHistoryResponse,
)
from app.services.history.history_service import HistoryService

router = APIRouter()


@router.get(
    "/aqi",
    response_model=AQIHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Historical AQI Readings",
    description="Retrieve paginated historical AQI records with optional daily/weekly/monthly temporal aggregation.",
)
def get_aqi_history(
    city: Optional[str] = Query(None, description="City name (e.g. 'Delhi', 'Bengaluru')"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID"),
    start_date: Optional[datetime] = Query(None, description="Start date in ISO-8601 UTC"),
    end_date: Optional[datetime] = Query(None, description="End date in ISO-8601 UTC"),
    interval: Optional[str] = Query(
        None,
        description="Temporal aggregation interval: 'hourly', 'daily', 'weekly', 'monthly'. Omit for raw observations.",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    include_simulated: bool = Query(True, description="Whether to include simulated measurements"),
    db: Session = Depends(get_db),
) -> AQIHistoryResponse:
    """Retrieve historical AQI records with optional aggregation and pagination."""
    return HistoryService.get_aqi_history(
        db=db,
        city=city,
        station_id=station_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        page=page,
        page_size=page_size,
        include_simulated=include_simulated,
    )


@router.get(
    "/pollutants",
    response_model=PollutantHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Historical Pollutant Concentrations",
    description="Retrieve paginated historical pollutant measurements with sub-indices and optional aggregation.",
)
def get_pollutant_history(
    city: Optional[str] = Query(None, description="City name (e.g. 'Delhi')"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID"),
    pollutant: Optional[str] = Query(
        None,
        description="Criteria pollutant code ('PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3', 'NH3', 'Pb')",
    ),
    start_date: Optional[datetime] = Query(None, description="Start date in ISO-8601 UTC"),
    end_date: Optional[datetime] = Query(None, description="End date in ISO-8601 UTC"),
    interval: Optional[str] = Query(
        None,
        description="Aggregation interval: 'hourly', 'daily', 'weekly', 'monthly'. Omit for raw measurements.",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_simulated: bool = Query(True, description="Whether to include simulated measurements"),
    db: Session = Depends(get_db),
) -> PollutantHistoryResponse:
    """Retrieve historical pollutant concentrations."""
    return HistoryService.get_pollutant_history(
        db=db,
        city=city,
        station_id=station_id,
        pollutant=pollutant,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        page=page,
        page_size=page_size,
        include_simulated=include_simulated,
    )


@router.get(
    "/summary",
    response_model=AQISummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Historical AQI Summary",
    description="Retrieve statistical summaries (min, max, mean, median, category and dominant pollutant distributions).",
)
def get_historical_summary(
    city: Optional[str] = Query(None, description="City name"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID"),
    start_date: Optional[datetime] = Query(None, description="Start date in ISO-8601 UTC"),
    end_date: Optional[datetime] = Query(None, description="End date in ISO-8601 UTC"),
    include_simulated: bool = Query(True, description="Whether to include simulated readings"),
    db: Session = Depends(get_db),
) -> AQISummaryResponse:
    """Retrieve statistical summary for AQI observations."""
    return HistoryService.get_summary(
        db=db,
        city=city,
        station_id=station_id,
        start_date=start_date,
        end_date=end_date,
        include_simulated=include_simulated,
    )


@router.get(
    "/trends",
    response_model=HistoryTrendResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Historical Trends",
    description="Evaluate direction and magnitude of air quality trends comparing earlier and later periods.",
)
def get_historical_trends(
    city: Optional[str] = Query(None, description="City name"),
    station_id: Optional[int] = Query(None, description="Monitoring station ID"),
    pollutant: Optional[str] = Query(
        None,
        description="Optional pollutant code to evaluate concentration trend instead of composite AQI",
    ),
    start_date: Optional[datetime] = Query(None, description="Start date in ISO-8601 UTC"),
    end_date: Optional[datetime] = Query(None, description="End date in ISO-8601 UTC"),
    interval: str = Query("daily", description="Trend interval granularity ('daily', 'weekly', 'monthly')"),
    threshold: Optional[float] = Query(
        None,
        description="Stability threshold value (default 5.0 for AQI, 2.0 for pollutants)",
    ),
    min_records_per_period: int = Query(
        3,
        ge=1,
        description="Minimum valid records required in both earlier and later periods",
    ),
    include_simulated: bool = Query(True, description="Whether to include simulated readings"),
    db: Session = Depends(get_db),
) -> HistoryTrendResponse:
    """Calculate historical trend metrics."""
    return HistoryService.get_trends(
        db=db,
        city=city,
        station_id=station_id,
        pollutant=pollutant,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        threshold=threshold,
        min_records_per_period=min_records_per_period,
        include_simulated=include_simulated,
    )


@router.get(
    "/compare",
    response_model=HistoryCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Historical Data Across Locations",
    description="Compare historical AQI metrics across 2 to 10 cities or stations over identical date ranges.",
)
def compare_historical_data(
    cities: Optional[List[str]] = Query(
        None,
        description="List of city names to compare (supports repeated parameters or comma-separated names)",
    ),
    stations: Optional[List[int]] = Query(
        None,
        description="List of station IDs to compare",
    ),
    start_date: Optional[datetime] = Query(None, description="Start date in ISO-8601 UTC"),
    end_date: Optional[datetime] = Query(None, description="End date in ISO-8601 UTC"),
    include_simulated: bool = Query(True, description="Whether to include simulated readings"),
    db: Session = Depends(get_db),
) -> HistoryCompareResponse:
    """Compare air quality metrics across multiple cities and stations."""
    return HistoryService.compare_locations(
        db=db,
        cities=cities,
        stations=stations,
        start_date=start_date,
        end_date=end_date,
        include_simulated=include_simulated,
    )

