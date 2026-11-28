"""Query and response helpers for ForecastService."""

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.models.city import City
from app.models.forecast import AQIForecast, ForecastEvaluation, ForecastRun
from app.models.monitoring_station import MonitoringStation
from app.schemas.forecast import (
    ForecastHistoryResponse,
    ModelEvaluationMetric,
    ModelStatusResponse,
)
from app.services.forecasting import forecast_mapper
from app.services.forecasting.validators import SUPPORTED_HORIZONS, ForecastValidator


def apply_horizon_filter(query: Any, parsed_horizon: int | None) -> Any:
    """Apply horizon filtering: specific or all standard horizons."""
    if parsed_horizon is not None:
        return query.where(AQIForecast.horizon_hours == parsed_horizon)
    return query.where(AQIForecast.horizon_hours.in_(SUPPORTED_HORIZONS))


def latest_completed_run_stmt(city_id: int, station_id: int | None) -> Any:
    """Build a SQLAlchemy select for the latest completed ForecastRun for a city/station."""
    return (
        select(ForecastRun)
        .where(
            ForecastRun.city_id == city_id,
            ForecastRun.station_id == station_id,
            ForecastRun.status == "completed",
        )
        .order_by(desc(ForecastRun.generated_at))
        .limit(1)
    )


def query_eval_metrics(db: Session, run: ForecastRun) -> list[ModelEvaluationMetric]:
    """Query ForecastEvaluation rows for a completed run and map to response schema."""
    evals_stmt = (
        select(ForecastEvaluation)
        .where(ForecastEvaluation.forecast_run_id == run.id)
        .order_by(ForecastEvaluation.horizon_hours.asc())
    )
    return [
        ModelEvaluationMetric(
            horizon_hours=er.horizon_hours,
            sample_count=er.sample_count,
            mae=er.mae,
            rmse=er.rmse,
            mape=er.mape,
        )
        for er in db.execute(evals_stmt).scalars().all()
    ]


def build_hourly_forecast_items(
    points: list[AQIForecast],
    run: ForecastRun,
    city: City,
    station: MonitoringStation | None,
) -> list:
    """Map AQIForecast database points into hourly AQIForecastItem response objects."""
    return [
        forecast_mapper.build_forecast_item(
            p=p,
            run=run,
            city_name=city.name,
            station=station,
            include_uncertainty=True,
        )
        for p in points
    ]


def get_forecast_history(
    db: Session,
    city_name: str,
    station_id: int | None = None,
    limit: int = 10,
) -> ForecastHistoryResponse:
    """Query previous forecast execution runs and their performance evaluations."""
    limit = max(1, min(100, limit))
    city, station = ForecastValidator.resolve_city_and_station(db, city_name, station_id)

    filters = [ForecastRun.city_id == city.id]
    if station is not None:
        filters.append(ForecastRun.station_id == station.id)

    stmt = (
        select(ForecastRun)
        .options(joinedload(ForecastRun.city), joinedload(ForecastRun.station))
        .where(*filters)
        .order_by(desc(ForecastRun.generated_at))
        .limit(limit)
    )
    runs = list(db.execute(stmt).scalars().all())

    summaries = []
    for run in runs:
        f_count_stmt = select(func.count(AQIForecast.id)).where(
            AQIForecast.forecast_run_id == run.id
        )
        f_count = db.execute(f_count_stmt).scalar() or 0
        summaries.append(forecast_mapper.build_forecast_run_summary(run, city.name, f_count))

    return ForecastHistoryResponse(
        city=city.name,
        station_id=station.id if station else None,
        total_runs=len(summaries),
        runs=summaries,
    )


def get_model_status(
    db: Session,
    settings: Settings,
    city_name: str | None = None,
) -> ModelStatusResponse:
    """Report operational status, versioning, evaluation metrics, and readiness."""
    city_entity = None
    if city_name:
        city_stmt = select(City).where(City.name.ilike(city_name.strip()))
        city_entity = db.execute(city_stmt).scalar_one_or_none()

    filters = [ForecastRun.status == "completed"]
    if city_entity:
        filters.append(ForecastRun.city_id == city_entity.id)

    latest_run_stmt = (
        select(ForecastRun).where(*filters).order_by(desc(ForecastRun.generated_at)).limit(1)
    )
    latest_run = db.execute(latest_run_stmt).scalar_one_or_none()

    eval_metrics = query_eval_metrics(db, latest_run) if latest_run else []
    coverage = forecast_mapper.compute_coverage_hours(latest_run) if latest_run else None

    return forecast_mapper.build_model_status_response(
        latest_run=latest_run,
        eval_metrics=eval_metrics,
        coverage=coverage,
        settings=settings,
    )

