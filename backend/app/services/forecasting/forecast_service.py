"""Master orchestrator for model training, forecast generation, evaluation, and retrieval."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings, get_settings
from app.integrations.weather.client import WeatherClient
from app.models.city import City
from app.models.forecast import AQIForecast, ForecastEvaluation, ForecastRun
from app.schemas.forecast import (
    AQIForecastItem,
    DailyForecastResponse,
    DailyForecastSummary,
    ForecastGenerateResponse,
    ForecastHistoryResponse,
    ForecastListResponse,
    ForecastRunSummary,
    HourlyForecastResponse,
    ModelEvaluationMetric,
    ModelStatusResponse,
)
from app.services.forecasting.confidence import UncertaintyEstimator
from app.services.forecasting.data_preparation import DataPreparationService
from app.services.forecasting.evaluation import ForecastEvaluator
from app.services.forecasting.models.factory import ModelFactory
from app.services.forecasting.validators import SUPPORTED_HORIZONS, ForecastValidator

logger = logging.getLogger(__name__)


class ForecastService:
    """Manages end-to-end AQI forecasting lifecycle, data preparation, evaluation, and persistence."""

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
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Satisfactory"
        elif aqi <= 200:
            return "Moderate"
        elif aqi <= 300:
            return "Poor"
        elif aqi <= 400:
            return "Very Poor"
        else:
            return "Severe"

    async def generate_forecast_run(
        self,
        db: Session,
        city_name: str,
        station_id: int | None = None,
        requested_horizons: list[str] | None = None,
        force_retrain: bool = False,
    ) -> ForecastGenerateResponse:
        """Execute a controlled model training and forecast generation task with concurrency protection."""
        async with self._generation_lock:
            now_utc = datetime.now(UTC)
            city, station = ForecastValidator.resolve_city_and_station(db, city_name, station_id)
            target_horizons = ForecastValidator.validate_horizons_list(requested_horizons)

            # 1. Check if a very recent run already exists (< 1 hour old) unless force_retrain is requested
            if not force_retrain:
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
                if existing_run:
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

            # 2. Extract and prepare historical observations
            dataset = DataPreparationService.load_and_prepare_dataset(
                db=db,
                city_id=city.id,
                station_id=station.id if station else None,
                min_required_samples=self.settings.FORECAST_MIN_TRAINING_SAMPLES,
            )

            if not dataset.is_sufficient:
                # Record failed or insufficient run
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

            # 3. Partition data chronologically for out-of-sample evaluation
            splits = DataPreparationService.split_chronological(dataset)

            # 4. Instantiate model and evaluate
            model = ModelFactory.get_model(self.settings.FORECAST_MODEL)
            eval_report = ForecastEvaluator.evaluate_model(model, splits, horizons=target_horizons)

            # 5. Fit model on complete dataset up to the latest observation
            model.fit(dataset.aqi_values, dataset.timestamps)

            # 6. Fetch optional meteorological data
            weather_obs = None
            if self.settings.WEATHER_ENABLED and city.latitude and city.longitude:
                try:
                    weather_obs = await self.weather_client.get_current_weather(
                        latitude=city.latitude,
                        longitude=city.longitude,
                    )
                except Exception as exc:
                    logger.warning("Weather fetch failed for %s: %s", city.name, exc)

            # 7. Compute empirical residual standard deviation for prediction intervals
            val_actuals = splits.val_values + splits.test_values
            val_model = ModelFactory.get_model(self.settings.FORECAST_MODEL)
            val_model.fit(splits.train_values, splits.train_timestamps)
            val_preds = val_model.predict(len(val_actuals))

            residual_std = UncertaintyEstimator.calculate_residual_standard_deviation(
                actuals=val_actuals,
                predictions=val_preds,
            )

            # 8. Project forecasts across max horizon
            max_horizon = max(target_horizons)
            raw_predictions = model.predict(max_horizon)

            # 9. Create ForecastRun record
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

            # 10. Save per-horizon evaluation metrics
            for h_eval in eval_report.horizon_metrics:
                eval_entry = ForecastEvaluation(
                    forecast_run_id=forecast_run.id,
                    horizon_hours=h_eval.horizon_hours,
                    sample_count=h_eval.sample_count,
                    mae=h_eval.mae,
                    rmse=h_eval.rmse,
                    mape=h_eval.mape,
                    evaluated_at=now_utc,
                )
                db.add(eval_entry)

            # 11. Generate step-by-step forecast records
            latest_time = dataset.timestamps[-1]
            latest_dom = dataset.dominant_pollutants[-1] if dataset.dominant_pollutants else "PM2.5"

            forecast_records: list[AQIForecast] = []
            for step_h in range(1, max_horizon + 1):
                pred_aqi = int(round(raw_predictions[step_h - 1]))
                target_timestamp = latest_time + timedelta(hours=step_h)
                pred_cat = self.get_category_for_aqi(pred_aqi)

                uncertainty = UncertaintyEstimator.estimate_interval(
                    predicted_aqi=pred_aqi,
                    horizon_hours=step_h,
                    residual_std=residual_std,
                    sample_count=len(val_actuals),
                )

                f_point = AQIForecast(
                    forecast_run_id=forecast_run.id,
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
                forecast_records.append(f_point)

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

        # Retrieve the latest completed run
        run_stmt = (
            select(ForecastRun)
            .where(
                ForecastRun.city_id == city.id,
                ForecastRun.station_id == (station.id if station else None),
                ForecastRun.status == "completed",
            )
            .order_by(desc(ForecastRun.generated_at))
            .limit(1)
        )
        run = db.execute(run_stmt).scalar_one_or_none()

        # If no completed run exists, trigger an automatic run
        if not run:
            await self.generate_forecast_run(
                db=db,
                city_name=city.name,
                station_id=station.id if station else None,
            )
            run = db.execute(run_stmt).scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No forecast records found for {city.name}.",
            )

        # Query forecast points
        query = select(AQIForecast).where(AQIForecast.forecast_run_id == run.id)
        if parsed_horizon is not None:
            query = query.where(AQIForecast.horizon_hours == parsed_horizon)
        else:
            # By default return the standard supported horizons: 1, 6, 12, 24, 48, 72
            query = query.where(AQIForecast.horizon_hours.in_(SUPPORTED_HORIZONS))

        query = query.order_by(AQIForecast.horizon_hours.asc())
        points = list(db.execute(query).scalars().all())

        items = [
            AQIForecastItem(
                city=city.name,
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
        hours: int = 24,
    ) -> HourlyForecastResponse:
        """Return step-by-step hourly forecasts up to `hours` (1 to 72)."""
        hours = max(1, min(72, hours))
        city, station = ForecastValidator.resolve_city_and_station(db, city_name, station_id)

        # Retrieve the latest completed run
        run_stmt = (
            select(ForecastRun)
            .where(
                ForecastRun.city_id == city.id,
                ForecastRun.station_id == (station.id if station else None),
                ForecastRun.status == "completed",
            )
            .order_by(desc(ForecastRun.generated_at))
            .limit(1)
        )
        run = db.execute(run_stmt).scalar_one_or_none()

        if not run:
            await self.generate_forecast_run(
                db=db,
                city_name=city.name,
                station_id=station.id if station else None,
            )
            run = db.execute(run_stmt).scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No hourly forecast records available for {city.name}.",
            )

        query = (
            select(AQIForecast)
            .where(
                AQIForecast.forecast_run_id == run.id,
                AQIForecast.horizon_hours <= hours,
            )
            .order_by(AQIForecast.horizon_hours.asc())
        )
        points = list(db.execute(query).scalars().all())

        items = [
            AQIForecastItem(
                city=city.name,
                station_id=p.station_id,
                station_name=station.station_name if station else None,
                forecast_timestamp=p.forecast_timestamp,
                generated_at=run.generated_at,
                predicted_aqi=p.predicted_aqi,
                predicted_category=p.predicted_category,
                dominant_pollutant=p.dominant_pollutant,
                horizon_hours=p.horizon_hours,
                horizon_label=f"{p.horizon_hours}h",
                lower_bound=p.lower_bound,
                upper_bound=p.upper_bound,
                uncertainty_status=p.uncertainty_status,
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
            for p in points
        ]

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
        days = max(1, min(7, days))
        max_hours = days * 24

        hourly_resp = await self.get_hourly_forecast(
            db=db,
            city_name=city_name,
            station_id=station_id,
            hours=max_hours,
        )

        # Group hourly forecasts by UTC calendar date
        grouped: dict[str, list[AQIForecastItem]] = {}
        for item in hourly_resp.forecasts:
            date_key = item.forecast_timestamp.strftime("%Y-%m-%d")
            grouped.setdefault(date_key, []).append(item)

        summaries: list[DailyForecastSummary] = []
        for d_key in sorted(grouped.keys())[:days]:
            day_items = grouped[d_key]
            aqis = [it.predicted_aqi for it in day_items]
            min_aqi = min(aqis)
            max_aqi = max(aqis)
            avg_aqi = round(sum(aqis) / float(len(aqis)), 1)
            predom_cat = self.get_category_for_aqi(int(round(avg_aqi)))

            lowers = [it.lower_bound for it in day_items if it.lower_bound is not None]
            uppers = [it.upper_bound for it in day_items if it.upper_bound is not None]

            summaries.append(
                DailyForecastSummary(
                    date=d_key,
                    min_predicted_aqi=min_aqi,
                    max_predicted_aqi=max_aqi,
                    average_predicted_aqi=avg_aqi,
                    predominant_category=predom_cat,
                    dominant_pollutant=day_items[0].dominant_pollutant,
                    forecast_points_count=len(day_items),
                    lower_bound=min(lowers) if lowers else None,
                    upper_bound=max(uppers) if uppers else None,
                )
            )

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
        for r in runs:
            f_count_stmt = select(func.count(AQIForecast.id)).where(AQIForecast.forecast_run_id == r.id)
            f_count = db.execute(f_count_stmt).scalar() or 0

            summaries.append(
                ForecastRunSummary(
                    id=r.id,
                    city_name=r.city.name if r.city else city.name,
                    station_name=r.station.station_name if r.station else None,
                    model_name=r.model_name,
                    model_version=r.model_version,
                    generated_at=r.generated_at,
                    training_samples=r.training_samples,
                    evaluation_mae=r.evaluation_mae,
                    evaluation_rmse=r.evaluation_rmse,
                    evaluation_mape=r.evaluation_mape,
                    is_simulated=r.is_simulated,
                    status=r.status,
                    forecast_count=f_count,
                )
            )

        return ForecastHistoryResponse(
            city=city.name,
            station_id=station.id if station else None,
            total_runs=len(summaries),
            runs=summaries,
        )

    def get_model_status(
        self,
        db: Session,
        city_name: str | None = None,
    ) -> ModelStatusResponse:
        """Report operational status, versioning, evaluation metrics, and readiness of the forecasting service."""
        city_entity = None
        if city_name:
            city_stmt = select(City).where(City.name.ilike(city_name.strip()))
            city_entity = db.execute(city_stmt).scalar_one_or_none()

        filters = [ForecastRun.status == "completed"]
        if city_entity:
            filters.append(ForecastRun.city_id == city_entity.id)

        latest_run_stmt = select(ForecastRun).where(*filters).order_by(desc(ForecastRun.generated_at)).limit(1)
        latest_run = db.execute(latest_run_stmt).scalar_one_or_none()

        eval_metrics: list[ModelEvaluationMetric] = []
        if latest_run:
            evals_stmt = (
                select(ForecastEvaluation)
                .where(ForecastEvaluation.forecast_run_id == latest_run.id)
                .order_by(ForecastEvaluation.horizon_hours.asc())
            )
            eval_records = list(db.execute(evals_stmt).scalars().all())
            eval_metrics = [
                ModelEvaluationMetric(
                    horizon_hours=er.horizon_hours,
                    sample_count=er.sample_count,
                    mae=er.mae,
                    rmse=er.rmse,
                    mape=er.mape,
                )
                for er in eval_records
            ]

        # Calculate coverage hours
        coverage = None
        if latest_run and latest_run.training_data_start and latest_run.training_data_end:
            coverage = round(
                (latest_run.training_data_end - latest_run.training_data_start).total_seconds() / 3600.0,
                1,
            )

        return ModelStatusResponse(
            model_name="ExponentialSmoothingForecaster",
            model_version="1.2.0",
            is_ready=latest_run is not None,
            active_provider="statistical_exponential_smoothing",
            training_data_coverage_hours=coverage,
            training_sample_count=latest_run.training_samples if latest_run else 0,
            latest_training_timestamp=latest_run.generated_at if latest_run else None,
            supported_horizons=["1h", "6h", "12h", "24h", "48h", "72h"],
            baseline_comparison={
                "baseline_model": "PersistenceBaseline",
                "evaluation_metric": "Mean Absolute Error (MAE)",
                "latest_run_mae": latest_run.evaluation_mae if latest_run else None,
                "latest_run_rmse": latest_run.evaluation_rmse if latest_run else None,
            },
            evaluation_metrics=eval_metrics,
            weather_integration_status={
                "enabled": self.settings.WEATHER_ENABLED,
                "provider": self.settings.WEATHER_PROVIDER,
                "base_url": self.settings.WEATHER_API_BASE_URL,
            },
        )

