"""API v1 endpoints for air quality forecasting, hourly projections, daily summaries, and model status."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import verify_admin_access
from app.db.session import get_db
from app.schemas.forecast import (
    DailyForecastResponse,
    ForecastGenerateRequest,
    ForecastGenerateResponse,
    ForecastHistoryResponse,
    ForecastListResponse,
    HourlyForecastResponse,
    ModelStatusResponse,
)
from app.services.forecasting.forecast_service import ForecastService

router = APIRouter()


def get_forecast_service(
    settings: Settings = Depends(get_settings),
) -> ForecastService:
    """Dependency provider for ForecastService."""
    return ForecastService(settings=settings)


@router.get(
    "/aqi",
    response_model=ForecastListResponse,
    summary="Get AQI forecast predictions",
    description="Retrieve future air quality predictions for a specified city and optional horizon (e.g. '1h', '6h', '24h', 'all').",
)
async def get_aqi_forecast(
    city: str = Query(..., min_length=1, max_length=100, description="City name (e.g. 'Delhi', 'Bengaluru')"),
    station_id: int | None = Query(None, description="Optional monitoring station ID"),
    horizon: str | None = Query(None, description="Optional target horizon: '1h', '6h', '12h', '24h', '48h', '72h'"),
    include_uncertainty: bool = Query(True, description="Whether to include lower and upper prediction interval bounds"),
    db: Session = Depends(get_db),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> ForecastListResponse:
    """Return future AQI predictions."""
    return await forecast_service.get_forecasts(
        db=db,
        city_name=city,
        station_id=station_id,
        horizon=horizon,
        include_uncertainty=include_uncertainty,
    )


@router.get(
    "/hourly",
    response_model=HourlyForecastResponse,
    summary="Get hourly AQI forecast projections",
    description="Retrieve sequential hourly AQI projections for up to 72 hours.",
)
async def get_hourly_forecast(
    city: str = Query(..., min_length=1, max_length=100, description="City name"),
    station_id: int | None = Query(None, description="Optional monitoring station ID"),
    hours: int = Query(24, ge=1, le=72, description="Number of future hours to project (1 to 72)"),
    db: Session = Depends(get_db),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> HourlyForecastResponse:
    """Return hourly future predictions."""
    return await forecast_service.get_hourly_forecast(
        db=db,
        city_name=city,
        station_id=station_id,
        hours=hours,
    )


@router.get(
    "/daily",
    response_model=DailyForecastResponse,
    summary="Get daily AQI forecast outlook",
    description="Retrieve daily aggregated forecast summaries (min, max, average AQI, and predominant category) for up to 7 days.",
)
async def get_daily_forecast(
    city: str = Query(..., min_length=1, max_length=100, description="City name"),
    station_id: int | None = Query(None, description="Optional monitoring station ID"),
    days: int = Query(3, ge=1, le=7, description="Number of future days (1 to 7)"),
    db: Session = Depends(get_db),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> DailyForecastResponse:
    """Return daily aggregated summaries."""
    return await forecast_service.get_daily_forecast(
        db=db,
        city_name=city,
        station_id=station_id,
        days=days,
    )


@router.get(
    "/history",
    response_model=ForecastHistoryResponse,
    summary="Get historical forecast runs",
    description="Retrieve previous forecast generation runs with model metadata and out-of-sample evaluation metrics.",
)
def get_forecast_history(
    city: str = Query(..., min_length=1, max_length=100, description="City name"),
    station_id: int | None = Query(None, description="Optional monitoring station ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of historical runs to retrieve"),
    db: Session = Depends(get_db),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> ForecastHistoryResponse:
    """Return past forecast execution runs."""
    return forecast_service.get_forecast_history(
        db=db,
        city_name=city,
        station_id=station_id,
        limit=limit,
    )


@router.get(
    "/model-status",
    response_model=ModelStatusResponse,
    summary="Get forecasting model status and evaluation metrics",
    description="Inspect model architecture, version, evaluation metrics (MAE, RMSE, MAPE), supported horizons, and weather integration status.",
)
def get_model_status(
    city: str | None = Query(None, description="Optional city name to scope status and latest run metrics"),
    db: Session = Depends(get_db),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> ModelStatusResponse:
    """Return model status and evaluation metrics."""
    return forecast_service.get_model_status(
        db=db,
        city_name=city,
    )


@router.post(
    "/generate",
    response_model=ForecastGenerateResponse,
    summary="Trigger model training and forecast generation run",
    description="Train forecasting model on verified historical observations, compute out-of-sample evaluation metrics, and persist predictions. Protected by X-Admin-Secret.",
)
async def generate_forecast(
    request: ForecastGenerateRequest,
    _admin: None = Depends(verify_admin_access),
    db: Session = Depends(get_db),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> ForecastGenerateResponse:
    """Trigger bounded forecast generation run."""
    return await forecast_service.generate_forecast_run(
        db=db,
        city_name=request.city,
        station_id=request.station_id,
        requested_horizons=request.horizons,
        force_retrain=request.force_retrain,
    )

