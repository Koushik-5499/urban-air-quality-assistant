"""Forecast run persistence, cache lookup, and hourly forecast-point construction helpers."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.city import City
from app.models.forecast import AQIForecast, ForecastEvaluation, ForecastRun
from app.models.monitoring_station import MonitoringStation
from app.schemas.forecast import ForecastGenerateResponse
from app.services.forecasting import forecast_mapper
from app.services.forecasting.confidence import UncertaintyEstimator
from app.services.forecasting.data_preparation import PreparedDataset


def check_recent_forecast_run(
    db: Session,
    city: City,
    station: MonitoringStation | None,
    now_utc: datetime,
    target_horizons: list[int],
) -> ForecastGenerateResponse | None:
    """Return cached response if a recent run exists within the last hour."""
    recent_stmt = (
        select(ForecastRun)
        .where(
            ForecastRun.city_id == city.id,
            ForecastRun.station_id == (station.id if station else None),
            ForecastRun.status == "completed",
            ForecastRun.generated_at >= now_utc - timedelta(hours=1),
        )
        .order_by(desc(ForecastRun.generated_at))
        .limit(1)
    )
    existing_run = db.execute(recent_stmt).scalar_one_or_none()
    if not existing_run:
        return None

    forecast_count_stmt = select(func.count(AQIForecast.id)).where(
        AQIForecast.forecast_run_id == existing_run.id
    )
    f_count = db.execute(forecast_count_stmt).scalar() or 0

    return ForecastGenerateResponse(
        success=True,
        city=city.name,
        station_id=station.id if station else None,
        model_name=existing_run.model_name,
        model_version=existing_run.model_version,
        horizons_generated=[f"{h}h" for h in target_horizons],
        generated_forecasts_count=f_count,
        training_samples=existing_run.training_samples,
        evaluation_mae=existing_run.evaluation_mae,
        evaluation_rmse=existing_run.evaluation_rmse,
        weather_integrated=False,
        is_simulated=existing_run.is_simulated,
        generated_at=existing_run.generated_at,
        message="Reused recent valid forecast run from database cache.",
    )


def handle_insufficient_dataset(
    db: Session,
    city: City,
    station: MonitoringStation | None,
    dataset: PreparedDataset,
    now_utc: datetime,
) -> None:
    """Persist failed run record and raise HTTP 422 for insufficient training data."""
    run_rec = ForecastRun(
        city_id=city.id,
        station_id=station.id if station else None,
        model_name="ExponentialSmoothingForecaster",
        model_version="1.2.0",
        generated_at=now_utc,
        training_data_start=dataset.start_time,
        training_data_end=dataset.end_time,
        training_samples=dataset.sample_count,
        status="insufficient_data",
        error_message=dataset.insufficiency_reason,
        is_simulated=dataset.is_simulated,
    )
    db.add(run_rec)
    db.commit()

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=dataset.insufficiency_reason or "Insufficient historical data for forecasting.",
    )


def persist_forecast_run(
    db: Session,
    city: City,
    station: MonitoringStation | None,
    model: Any,
    dataset: PreparedDataset,
    eval_report: Any,
    now_utc: datetime,
) -> ForecastRun:
    """Save ForecastRun and associated horizon evaluation records."""
    forecast_run = ForecastRun(
        city_id=city.id,
        station_id=station.id if station else None,
        model_name=model.name,
        model_version=model.version,
        generated_at=now_utc,
        training_data_start=dataset.start_time,
        training_data_end=dataset.end_time,
        training_samples=dataset.sample_count,
        evaluation_mae=eval_report.overall_mae,
        evaluation_rmse=eval_report.overall_rmse,
        evaluation_mape=eval_report.overall_mape,
        is_simulated=dataset.is_simulated,
        status="completed",
        error_message=None,
    )
    db.add(forecast_run)
    db.flush()

    for h_eval in eval_report.horizon_metrics:
        db.add(
            ForecastEvaluation(
                forecast_run_id=forecast_run.id,
                horizon_hours=h_eval.horizon_hours,
                sample_count=h_eval.sample_count,
                mae=h_eval.mae,
                rmse=h_eval.rmse,
                mape=h_eval.mape,
                evaluated_at=now_utc,
            )
        )
    return forecast_run


def build_step_forecasts(
    forecast_run_id: int,
    city: City,
    station: MonitoringStation | None,
    model: Any,
    dataset: PreparedDataset,
    raw_predictions: list[float],
    max_horizon: int,
    residual_std: float | None,
    val_count: int,
    now_utc: datetime,
) -> list[AQIForecast]:
    """Generate hourly step forecast models with uncertainty intervals."""
    latest_time = dataset.timestamps[-1]
    latest_dom = dataset.dominant_pollutants[-1] if dataset.dominant_pollutants else "PM2.5"

    forecast_records: list[AQIForecast] = []
    for step_h in range(1, max_horizon + 1):
        pred_aqi = int(round(raw_predictions[step_h - 1]))
        target_timestamp = latest_time + timedelta(hours=step_h)
        pred_cat = forecast_mapper.get_category_for_aqi(pred_aqi)

        uncertainty = UncertaintyEstimator.estimate_interval(
            predicted_aqi=pred_aqi,
            horizon_hours=step_h,
            residual_std=residual_std,
            sample_count=val_count,
        )

        forecast_records.append(
            AQIForecast(
                forecast_run_id=forecast_run_id,
                city_id=city.id,
                station_id=station.id if station else None,
                forecast_timestamp=target_timestamp,
                horizon_hours=step_h,
                predicted_aqi=pred_aqi,
                predicted_category=pred_cat,
                dominant_pollutant=latest_dom,
                lower_bound=uncertainty.lower_bound,
                upper_bound=uncertainty.upper_bound,
                uncertainty_status=uncertainty.uncertainty_status,
                model_name=model.name,
                model_version=model.version,
                is_simulated=dataset.is_simulated,
                created_at=now_utc,
            )
        )
    return forecast_records
