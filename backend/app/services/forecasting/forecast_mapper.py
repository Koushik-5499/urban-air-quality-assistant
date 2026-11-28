"""Mapping and response-building helpers for ForecastService."""

from datetime import datetime
from typing import Any

from app.core.config import Settings
from app.models.forecast import AQIForecast, ForecastRun
from app.models.monitoring_station import MonitoringStation
from app.schemas.forecast import (
    AQIForecastItem,
    DailyForecastSummary,
    ForecastRunSummary,
    ModelEvaluationMetric,
    ModelStatusResponse,
)

SECONDS_PER_HOUR = 3600.0
AQI_GOOD_MAX = 50
AQI_SATISFACTORY_MAX = 100
AQI_MODERATE_MAX = 200
AQI_POOR_MAX = 300
AQI_VERY_POOR_MAX = 400


def get_category_for_aqi(aqi: int) -> str:
    """Map numerical AQI to CPCB National Air Quality Index (NAQI) category."""
    if aqi <= AQI_GOOD_MAX:
        return "Good"
    if aqi <= AQI_SATISFACTORY_MAX:
        return "Satisfactory"
    if aqi <= AQI_MODERATE_MAX:
        return "Moderate"
    if aqi <= AQI_POOR_MAX:
        return "Poor"
    if aqi <= AQI_VERY_POOR_MAX:
        return "Very Poor"
    return "Severe"


def build_forecast_item(
    p: AQIForecast,
    run: ForecastRun,
    city_name: str,
    station: MonitoringStation | None,
    include_uncertainty: bool = True,
) -> AQIForecastItem:
    """Map an AQIForecast ORM row and run metadata into an AQIForecastItem schema."""
    return AQIForecastItem(
        city=city_name,
        station_id=p.station_id,
        station_name=station.station_name if station else None,
        forecast_timestamp=p.forecast_timestamp,
        generated_at=run.generated_at,
        predicted_aqi=p.predicted_aqi,
        predicted_category=p.predicted_category,
        dominant_pollutant=p.dominant_pollutant,
        horizon_hours=p.horizon_hours,
        horizon_label=f"{p.horizon_hours}h",
        lower_bound=p.lower_bound if include_uncertainty else None,
        upper_bound=p.upper_bound if include_uncertainty else None,
        uncertainty_status=p.uncertainty_status if include_uncertainty else "unavailable",
        model_name=p.model_name,
        model_version=p.model_version,
        training_data_start=run.training_data_start,
        training_data_end=run.training_data_end,
        training_samples=run.training_samples,
        data_quality="simulated" if p.is_simulated else "verified_cpcb",
        source="Simulated Engine" if p.is_simulated else "CPCB Historical Observations",
        is_simulated=p.is_simulated,
        is_forecast=True,
        forecast_status="valid",
    )


def aggregate_daily_summaries(
    hourly_items: list[AQIForecastItem], days: int
) -> list[DailyForecastSummary]:
    """Group hourly forecast points by UTC date into daily summary buckets."""
    grouped: dict[str, list[AQIForecastItem]] = {}
    for item in hourly_items:
        date_key = item.forecast_timestamp.strftime("%Y-%m-%d")
        grouped.setdefault(date_key, []).append(item)

    summaries: list[DailyForecastSummary] = []
    for d_key in sorted(grouped.keys())[:days]:
        day_items = grouped[d_key]
        aqis = [it.predicted_aqi for it in day_items]
        avg_aqi = round(sum(aqis) / float(len(aqis)), 1)
        lowers = [it.lower_bound for it in day_items if it.lower_bound is not None]
        uppers = [it.upper_bound for it in day_items if it.upper_bound is not None]
        summaries.append(
            DailyForecastSummary(
                date=d_key,
                min_predicted_aqi=min(aqis),
                max_predicted_aqi=max(aqis),
                average_predicted_aqi=avg_aqi,
                predominant_category=get_category_for_aqi(int(round(avg_aqi))),
                dominant_pollutant=day_items[0].dominant_pollutant,
                forecast_points_count=len(day_items),
                lower_bound=min(lowers) if lowers else None,
                upper_bound=max(uppers) if uppers else None,
            )
        )
    return summaries


def build_forecast_run_summary(
    run: ForecastRun, city_fallback: str, forecast_count: int
) -> ForecastRunSummary:
    """Build a ForecastRunSummary schema object from a ForecastRun row."""
    return ForecastRunSummary(
        id=run.id,
        city_name=run.city.name if run.city else city_fallback,
        station_name=run.station.station_name if run.station else None,
        model_name=run.model_name,
        model_version=run.model_version,
        generated_at=run.generated_at,
        training_samples=run.training_samples,
        evaluation_mae=run.evaluation_mae,
        evaluation_rmse=run.evaluation_rmse,
        evaluation_mape=run.evaluation_mape,
        is_simulated=run.is_simulated,
        status=run.status,
        forecast_count=forecast_count,
    )


def compute_coverage_hours(run: ForecastRun) -> float | None:
    """Return training data coverage in hours, or None if timestamps unavailable."""
    if run.training_data_start and run.training_data_end:
        return round(
            (run.training_data_end - run.training_data_start).total_seconds() / SECONDS_PER_HOUR,
            1,
        )
    return None


def build_model_status_response(
    latest_run: ForecastRun | None,
    eval_metrics: list[ModelEvaluationMetric],
    coverage: float | None,
    settings: Settings,
) -> ModelStatusResponse:
    """Build ModelStatusResponse from latest run metadata and settings."""
    baseline: dict[str, Any] = {
        "baseline_model": "PersistenceBaseline",
        "evaluation_metric": "Mean Absolute Error (MAE)",
        "latest_run_mae": latest_run.evaluation_mae if latest_run else None,
        "latest_run_rmse": latest_run.evaluation_rmse if latest_run else None,
    }
    return ModelStatusResponse(
        model_name="ExponentialSmoothingForecaster",
        model_version="1.2.0",
        is_ready=latest_run is not None,
        active_provider="statistical_exponential_smoothing",
        training_data_coverage_hours=coverage,
        training_sample_count=latest_run.training_samples if latest_run else 0,
        latest_training_timestamp=latest_run.generated_at if latest_run else None,
        supported_horizons=["1h", "6h", "12h", "24h", "48h", "72h"],
        baseline_comparison=baseline,
        evaluation_metrics=eval_metrics,
        weather_integration_status={
            "enabled": settings.WEATHER_ENABLED,
            "provider": settings.WEATHER_PROVIDER,
            "base_url": settings.WEATHER_API_BASE_URL,
        },
    )


def forecast_generated_at(run: ForecastRun) -> datetime:
    """Return forecast generation timestamp helper."""
    return run.generated_at
