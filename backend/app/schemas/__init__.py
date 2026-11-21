"""Pydantic data validation schemas."""

from app.schemas.air_quality import (
    CityAirQualityResponse,
    CityAvailabilitySummary,
    PollutantDetail,
    SourceStatusResponse,
    SyncResponse,
)
from app.schemas.alert import AlertBase, AlertCreate, AlertResponse, AlertUpdate
from app.schemas.aqi import AQIReadingBase, AQIReadingCreate, AQIReadingResponse
from app.schemas.city import CityBase, CityCreate, CityResponse, CitySummary, CityUpdate
from app.schemas.common import BaseResponse, ErrorResponse
from app.schemas.forecast import (
    AQIForecastItem,
    DailyForecastResponse,
    DailyForecastSummary,
    ForecastGenerateRequest,
    ForecastGenerateResponse,
    ForecastHistoryResponse,
    ForecastListResponse,
    ForecastRunSummary,
    HourlyForecastResponse,
    ModelEvaluationMetric,
    ModelStatusResponse,
)
from app.schemas.health import HealthResponse, RootResponse
from app.schemas.monitoring_station import StationBase, StationCreate, StationResponse
from app.schemas.pollutant import (
    PollutantReadingBase,
    PollutantReadingCreate,
    PollutantReadingResponse,
)

__all__ = [
    "AlertBase",
    "AlertCreate",
    "AlertResponse",
    "AlertUpdate",
    "AQIForecastItem",
    "AQIReadingBase",
    "AQIReadingCreate",
    "AQIReadingResponse",
    "BaseResponse",
    "CityAirQualityResponse",
    "CityAvailabilitySummary",
    "CityBase",
    "CityCreate",
    "CityResponse",
    "CitySummary",
    "CityUpdate",
    "DailyForecastResponse",
    "DailyForecastSummary",
    "ErrorResponse",
    "ForecastGenerateRequest",
    "ForecastGenerateResponse",
    "ForecastHistoryResponse",
    "ForecastListResponse",
    "ForecastRunSummary",
    "HealthResponse",
    "HourlyForecastResponse",
    "ModelEvaluationMetric",
    "ModelStatusResponse",
    "PollutantDetail",
    "PollutantReadingBase",
    "PollutantReadingCreate",
    "PollutantReadingResponse",
    "RootResponse",
    "SourceStatusResponse",
    "StationBase",
    "StationCreate",
    "StationResponse",
    "SyncResponse",
]
