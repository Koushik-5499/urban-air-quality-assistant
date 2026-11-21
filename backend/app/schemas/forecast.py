"""Pydantic schemas for Air Quality Forecasting requests, responses, models, and evaluations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AQIForecastItem(BaseModel):
    """Individual future AQI prediction point."""

    city: str = Field(..., description="Target city name")
    station_id: Optional[int] = Field(None, description="Optional monitoring station ID")
    station_name: Optional[str] = Field(None, description="Optional monitoring station name")
    forecast_timestamp: datetime = Field(..., description="Target future timestamp in UTC")
    generated_at: datetime = Field(..., description="Timestamp when forecast was computed")
    predicted_aqi: int = Field(..., ge=0, le=500, description="Predicted numerical AQI value (0-500)")
    predicted_category: str = Field(..., description="Predicted CPCB NAQI category")
    dominant_pollutant: Optional[str] = Field(None, description="Primary predicted pollutant driver")
    horizon_hours: int = Field(..., ge=1, le=72, description="Prediction horizon in hours")
    horizon_label: str = Field(..., description="Configurable horizon label (e.g. '1h', '6h', '24h')")
    lower_bound: Optional[int] = Field(None, ge=0, le=500, description="Lower prediction interval bound")
    upper_bound: Optional[int] = Field(None, ge=0, le=500, description="Upper prediction interval bound")
    uncertainty_status: str = Field(
        default="estimated",
        description="Uncertainty state: 'estimated', 'high_uncertainty', or 'unavailable'",
    )
    model_name: str = Field(..., description="Identifier of the forecasting model")
    model_version: str = Field(..., description="Model release version")
    training_data_start: Optional[datetime] = Field(None, description="Start time of historical training window")
    training_data_end: Optional[datetime] = Field(None, description="End time of historical training window")
    training_samples: int = Field(default=0, description="Number of historical observations used for training")
    data_quality: str = Field(default="verified_cpcb", description="Source data quality label")
    source: str = Field(default="CPCB Historical Observations", description="Origin data provider")
    is_simulated: bool = Field(default=False, description="Whether forecast is based on simulated data")
    is_forecast: bool = Field(default=True, description="Explicit indicator that this is a modeled prediction")
    forecast_status: str = Field(default="valid", description="Status: 'valid', 'insufficient_data', 'fallback'")

    model_config = ConfigDict(from_attributes=True)


class ForecastListResponse(BaseModel):
    """Collection of AQI predictions for a requested horizon or multi-horizon set."""

    city: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    generated_at: datetime
    model_name: str
    model_version: str
    forecasts: List[AQIForecastItem] = Field(default_factory=list)
    total_horizons: int = Field(default=0)
    data_quality: str = Field(default="verified_cpcb")
    weather_integrated: bool = Field(default=False)


class HourlyForecastResponse(BaseModel):
    """Hourly step-by-step predictions for up to 72 hours."""

    city: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    hours: int = Field(..., ge=1, le=72)
    generated_at: datetime
    forecasts: List[AQIForecastItem] = Field(default_factory=list)


class DailyForecastSummary(BaseModel):
    """Aggregated daily forecast summary for multi-day outlooks."""

    date: str = Field(..., description="Target date in YYYY-MM-DD format")
    min_predicted_aqi: int = Field(..., ge=0, le=500)
    max_predicted_aqi: int = Field(..., ge=0, le=500)
    average_predicted_aqi: float = Field(..., ge=0, le=500)
    predominant_category: str
    dominant_pollutant: Optional[str] = None
    forecast_points_count: int = Field(..., ge=1)
    lower_bound: Optional[int] = None
    upper_bound: Optional[int] = None


class DailyForecastResponse(BaseModel):
    """Collection of daily forecast summaries."""

    city: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    days: int = Field(..., ge=1, le=7)
    generated_at: datetime
    summaries: List[DailyForecastSummary] = Field(default_factory=list)


class ForecastRunSummary(BaseModel):
    """Summary of a past forecast run for auditing and historical evaluation."""

    id: int
    city_name: str
    station_name: Optional[str] = None
    model_name: str
    model_version: str
    generated_at: datetime
    training_samples: int
    evaluation_mae: Optional[float] = None
    evaluation_rmse: Optional[float] = None
    evaluation_mape: Optional[float] = None
    is_simulated: bool
    status: str
    forecast_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ForecastHistoryResponse(BaseModel):
    """History of previous forecast execution runs."""

    city: str
    station_id: Optional[int] = None
    total_runs: int
    runs: List[ForecastRunSummary] = Field(default_factory=list)


class ModelEvaluationMetric(BaseModel):
    """Evaluation metrics for a specific prediction horizon."""

    horizon_hours: int
    sample_count: int
    mae: float
    rmse: float
    mape: Optional[float] = None


class ModelStatusResponse(BaseModel):
    """Operational status, versioning, evaluation metrics, and readiness of the forecasting service."""

    model_name: str
    model_version: str
    is_ready: bool
    active_provider: str
    training_data_coverage_hours: Optional[float] = None
    training_sample_count: int = 0
    latest_training_timestamp: Optional[datetime] = None
    supported_horizons: List[str] = Field(default_factory=list)
    baseline_comparison: Dict[str, Any] = Field(default_factory=dict)
    evaluation_metrics: List[ModelEvaluationMetric] = Field(default_factory=list)
    weather_integration_status: Dict[str, Any] = Field(default_factory=dict)


class ForecastGenerateRequest(BaseModel):
    """Payload to trigger an on-demand forecast training and prediction run."""

    city: str = Field(..., min_length=1, max_length=100, description="Target city name")
    station_id: Optional[int] = Field(None, description="Optional monitoring station ID")
    horizons: Optional[List[str]] = Field(
        None,
        description="List of target horizons (e.g. ['1h', '6h', '12h', '24h', '48h']). Defaults to all supported.",
    )
    force_retrain: bool = Field(default=False, description="Whether to recompute model even if recent run exists")


class ForecastGenerateResponse(BaseModel):
    """Response returned upon completion of forecast generation."""

    success: bool
    city: str
    station_id: Optional[int] = None
    model_name: str
    model_version: str
    horizons_generated: List[str] = Field(default_factory=list)
    generated_forecasts_count: int
    training_samples: int
    evaluation_mae: Optional[float] = None
    evaluation_rmse: Optional[float] = None
    weather_integrated: bool
    is_simulated: bool
    generated_at: datetime
    message: str

