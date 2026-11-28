"""Master orchestrator for model training, forecast generation, evaluation, and retrieval."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.weather.client import WeatherClient
from app.models.city import City
from app.models.forecast import AQIForecast, ForecastRun
from app.models.monitoring_station import MonitoringStation
from app.schemas.forecast import (
    AQIForecastItem,
    DailyForecastResponse,
    ForecastGenerateResponse,
    ForecastHistoryResponse,
    ForecastListResponse,
    HourlyForecastResponse,
    ModelEvaluationMetric,
    ModelStatusResponse,
)
from app.services.forecasting import (
    forecast_mapper,
    forecast_query_service,
    forecast_run_helper,
)
from app.services.forecasting.confidence import UncertaintyEstimator
from app.services.forecasting.data_preparation import DataPreparationService, PreparedDataset
from app.services.forecasting.evaluation import ForecastEvaluator
from app.services.forecasting.models.factory import ModelFactory
from app.services.forecasting.validators import ForecastValidator

logger = logging.getLogger(__name__)

MAX_HOURLY_FORECAST_HOURS = 72
HOURS_PER_DAY = 24
MAX_DAILY_FORECAST_DAYS = 7


class ForecastService:
    """Manages AQI forecasting lifecycle, data preparation, evaluation, and persistence."""

    _generation_lock = asyncio.Lock()

    def __init__(
        self,
        weather_client: WeatherClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.weather_client = weather_client or WeatherClient(settings=self.settings)

    @staticmethod
    def get_category_for_aqi(aqi: int) -> str:
        """Map numerical AQI to CPCB National Air Quality Index (NAQI) category."""
        return forecast_mapper.get_category_for_aqi(aqi)

    @staticmethod
    def _check_recent_forecast_run(
        db: Session,
        city: City,
        station: MonitoringStation | None,
        now_utc: datetime,
        target_horizons: list[int],
    ) -> ForecastGenerateResponse | None:
        """Return cached response if a recent run exists within the last hour."""
        return forecast_run_helper.check_recent_forecast_run(
            db, city, station, now_utc, target_horizons
        )

    @staticmethod
    def _handle_insufficient_dataset(
        db: Session,
        city: City,
        station: MonitoringStation | None,
        dataset: PreparedDataset,
        now_utc: datetime,
    ) -> None:
        """Persist failed run record and raise HTTP 422 for insufficient training data."""
        forecast_run_helper.handle_insufficient_dataset(db, city, station, dataset, now_utc)

    async def _fetch_optional_weather(self, city: City) -> Any:
        """Fetch meteorological readings if weather service is enabled."""
        if not (self.settings.WEATHER_ENABLED and city.latitude and city.longitude):
            return None
        try:
            return await self.weather_client.get_current_weather(
                latitude=city.latitude,
                longitude=city.longitude,
            )
        except (httpx.HTTPError, OSError, ValueError, RuntimeError) as exc:
            logger.warning("Weather fetch failed for %s: %s", city.name, exc)
            return None

    @staticmethod
    def _persist_forecast_run(
        db: Session,
        city: City,
        station: MonitoringStation | None,
        model: Any,
        dataset: PreparedDataset,
        eval_report: Any,
        now_utc: datetime,
    ) -> ForecastRun:
        """Save ForecastRun and associated horizon evaluation records."""
        return forecast_run_helper.persist_forecast_run(
            db, city, station, model, dataset, eval_report, now_utc
        )

    def _build_step_forecasts(
        self,
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
        return forecast_run_helper.build_step_forecasts(
            forecast_run_id, city, station, model, dataset,
            raw_predictions, max_horizon, residual_std, val_count, now_utc,
        )

    async def generate_forecast_run(
        self,
        db: Session,
        city_name: str,
        station_id: int | None = None,
        requested_horizons: list[str] | None = None,
        force_retrain: bool = False,
    ) -> ForecastGenerateResponse:
        """Execute a model training and forecast generation task with concurrency protection."""
        async with self._generation_lock:
            now_utc = datetime.now(UTC)
            city, station = ForecastValidator.resolve_city_and_station(db, city_name, station_id)
            target_horizons = ForecastValidator.validate_horizons_list(requested_horizons)

            if not force_retrain:
                cached_res = self._check_recent_forecast_run(
                    db, city, station, now_utc, target_horizons
                )
                if cached_res:
                    return cached_res

            dataset = DataPreparationService.load_and_prepare_dataset(
                db=db,
                city_id=city.id,
                station_id=station.id if station else None,
                min_required_samples=self.settings.FORECAST_MIN_TRAINING_SAMPLES,
            )
            if not dataset.is_sufficient:
                self._handle_insufficient_dataset(db, city, station, dataset, now_utc)

            splits = DataPreparationService.split_chronological(dataset)
            model = ModelFactory.get_model(self.settings.FORECAST_MODEL)
            eval_report = ForecastEvaluator.evaluate_model(model, splits, horizons=target_horizons)
            model.fit(dataset.aqi_values, dataset.timestamps)

            weather_obs = await self._fetch_optional_weather(city)

            val_actuals = splits.val_values + splits.test_values
            val_model = ModelFactory.get_model(self.settings.FORECAST_MODEL)
            val_model.fit(splits.train_values, splits.train_timestamps)
            val_preds = val_model.predict(len(val_actuals))

            residual_std = UncertaintyEstimator.calculate_residual_standard_deviation(
                actuals=val_actuals,
                predictions=val_preds,
            )

            max_horizon = max(target_horizons)
            raw_predictions = model.predict(max_horizon)
            forecast_run = self._persist_forecast_run(
                db, city, station, model, dataset, eval_report, now_utc
            )
            forecast_records = self._build_step_forecasts(
                forecast_run.id, city, station, model, dataset,
                raw_predictions, max_horizon, residual_std, len(val_actuals), now_utc,
            )

            db.add_all(forecast_records)
            db.commit()

            return ForecastGenerateResponse(
                success=True,
                city=city.name,
                station_id=station.id if station else None,
                model_name=model.name,
                model_version=model.version,
                horizons_generated=[f"{h}h" for h in target_horizons],
                generated_forecasts_count=len(forecast_records),
                training_samples=dataset.sample_count,
                evaluation_mae=eval_report.overall_mae,
                evaluation_rmse=eval_report.overall_rmse,
                weather_integrated=(weather_obs is not None),
                is_simulated=dataset.is_simulated,
                generated_at=now_utc,
                message=f"Forecast generation completed successfully using {model.name}.",
            )

    def _apply_horizon_filter(self, query: Any, parsed_horizon: int | None) -> Any:
        """Apply horizon filtering: specific or all standard horizons."""
        return forecast_query_service.apply_horizon_filter(query, parsed_horizon)

    async def _get_or_generate_run(
        self,
        db: Session,
        city: Any,
        station: Any,
        run_stmt: Any,
    ) -> Any:
        """Fetch latest completed run, triggering a new one if none exists."""
        run = db.execute(run_stmt).scalar_one_or_none()
        if not run:
            await self.generate_forecast_run(
                db=db,
                city_name=city.name,
                station_id=station.id if station else None,
            )
            run = db.execute(run_stmt).scalar_one_or_none()
        return run

    def _build_forecast_item(
        self,
        p: AQIForecast,
        run: ForecastRun,
        city_name: str,
        station: MonitoringStation | None,
        include_uncertainty: bool,
    ) -> AQIForecastItem:
        """Map a single AQIForecast DB row + run metadata to the response schema."""
        return forecast_mapper.build_forecast_item(
            p=p, run=run, city_name=city_name, station=station,
            include_uncertainty=include_uncertainty,
        )

    def _latest_completed_run_stmt(self, city_id: int, station_id: int | None) -> Any:
        """Build a SQLAlchemy select for the latest completed ForecastRun for a city/station."""
        return forecast_query_service.latest_completed_run_stmt(city_id, station_id)

    async def get_forecasts(
        self,
        db: Session,
        city_name: str,
        station_id: int | None = None,
        horizon: str | None = None,
        include_uncertainty: bool = True,
    ) -> ForecastListResponse:
        """Retrieve latest generated forecasts for a city, optionally filtered by horizon."""
        city, station = ForecastValidator.resolve_city_and_station(db, city_name, station_id)
        parsed_horizon = ForecastValidator.parse_horizon(horizon)

        run_stmt = self._latest_completed_run_stmt(city.id, station.id if station else None)
        run = await self._get_or_generate_run(db, city, station, run_stmt)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No forecast records found for {city.name}.",
            )

        query = self._apply_horizon_filter(
            select(AQIForecast).where(AQIForecast.forecast_run_id == run.id),
            parsed_horizon,
        ).order_by(AQIForecast.horizon_hours.asc())
        points = list(db.execute(query).scalars().all())
        items = [
            self._build_forecast_item(p, run, city.name, station, include_uncertainty)
            for p in points
        ]

        return ForecastListResponse(
            city=city.name,
            station_id=station.id if station else None,
            station_name=station.station_name if station else None,
            generated_at=run.generated_at,
            model_name=run.model_name,
            model_version=run.model_version,
            forecasts=items,
            total_horizons=len(items),
            data_quality="simulated" if run.is_simulated else "verified_cpcb",
            weather_integrated=self.settings.WEATHER_ENABLED,
        )

    async def get_hourly_forecast(
        self,
        db: Session,
        city_name: str,
        station_id: int | None = None,
        hours: int = HOURS_PER_DAY,
    ) -> HourlyForecastResponse:
        """Return step-by-step hourly forecasts up to `hours` (1 to 72)."""
        hours = max(1, min(MAX_HOURLY_FORECAST_HOURS, hours))
        city, station = ForecastValidator.resolve_city_and_station(db, city_name, station_id)

        run_stmt = self._latest_completed_run_stmt(city.id, station.id if station else None)
        run = await self._get_or_generate_run(db, city, station, run_stmt)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No hourly forecast records available for {city.name}.",
            )

        query = (
            select(AQIForecast)
            .where(AQIForecast.forecast_run_id == run.id, AQIForecast.horizon_hours <= hours)
            .order_by(AQIForecast.horizon_hours.asc())
        )
        points = list(db.execute(query).scalars().all())
        items = forecast_query_service.build_hourly_forecast_items(points, run, city, station)

        return HourlyForecastResponse(
            city=city.name,
            station_id=station.id if station else None,
            station_name=station.station_name if station else None,
            hours=hours,
            generated_at=run.generated_at,
            forecasts=items,
        )

    async def get_daily_forecast(
        self,
        db: Session,
        city_name: str,
        station_id: int | None = None,
        days: int = 3,
    ) -> DailyForecastResponse:
        """Return daily forecast summaries aggregating hourly predictions."""
        days = max(1, min(MAX_DAILY_FORECAST_DAYS, days))
        hourly_resp = await self.get_hourly_forecast(
            db=db, city_name=city_name, station_id=station_id, hours=days * HOURS_PER_DAY
        )
        summaries = forecast_mapper.aggregate_daily_summaries(hourly_resp.forecasts, days)
        return DailyForecastResponse(
            city=hourly_resp.city,
            station_id=hourly_resp.station_id,
            station_name=hourly_resp.station_name,
            days=len(summaries),
            generated_at=hourly_resp.generated_at,
            summaries=summaries,
        )

    def get_forecast_history(
        self,
        db: Session,
        city_name: str,
        station_id: int | None = None,
        limit: int = 10,
    ) -> ForecastHistoryResponse:
        """Query previous forecast execution runs and their performance evaluations."""
        return forecast_query_service.get_forecast_history(db, city_name, station_id, limit)

    def _query_eval_metrics(self, db: Session, run: ForecastRun) -> list[ModelEvaluationMetric]:
        """Query ForecastEvaluation rows for a completed run and map to response schema."""
        return forecast_query_service.query_eval_metrics(db, run)

    def _coverage_hours(self, run: ForecastRun) -> float | None:
        """Return training data coverage in hours, or None if timestamps unavailable."""
        return forecast_mapper.compute_coverage_hours(run)

    def get_model_status(
        self,
        db: Session,
        city_name: str | None = None,
    ) -> ModelStatusResponse:
        """Report operational status, versioning, evaluation metrics, and readiness."""
        return forecast_query_service.get_model_status(db, self.settings, city_name)
