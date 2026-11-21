"""Comprehensive test suite for Phase 8: Air Quality Forecasting Service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from httpx import AsyncClient, Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.weather.client import WeatherClient
from app.integrations.weather.schemas import WeatherObservation
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.forecast import AQIForecast, ForecastEvaluation, ForecastRun
from app.models.monitoring_station import MonitoringStation
from app.services.forecasting.confidence import UncertaintyEstimator
from app.services.forecasting.data_preparation import DataPreparationService, PreparedDataset
from app.services.forecasting.evaluation import ForecastEvaluator
from app.services.forecasting.feature_engineering import FeatureEngineeringService
from app.services.forecasting.forecast_service import ForecastService
from app.services.forecasting.models import (
    BaseForecastModel,
    ExponentialSmoothingModel,
    ModelFactory,
    MovingAverageModel,
    PersistenceModel,
)
from app.services.forecasting.validators import ForecastValidator


@pytest.fixture
def forecast_seed_data(db_session: Session):
    """Seed test database with cities, stations, and rich chronological AQI readings."""
    now_utc = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Cities
    delhi = City(
        name="Delhi",
        state="Delhi",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
    )
    bengaluru = City(
        name="Bengaluru",
        state="Karnataka",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
    )
    db_session.add_all([delhi, bengaluru])
    db_session.flush()

    # 2. Station
    delhi_station = MonitoringStation(
        station_name="Anand Vihar CAAQMS",
        external_station_id="DEL_AV_01",
        city_id=delhi.id,
        latitude=28.6469,
        longitude=77.3160,
        provider="CPCB",
        is_active=True,
    )
    db_session.add(delhi_station)
    db_session.flush()

    # 3. Populate 72 consecutive hourly readings for Delhi (3 full diurnal days)
    # Diurnal pattern: baseline ~180, morning rush peak at 09:00 (+40), afternoon dispersion at 15:00 (-30)
    readings = []
    start_time = now_utc - timedelta(hours=72)
    for i in range(72):
        t = start_time + timedelta(hours=i)
        hour = t.hour
        # Diurnal fluctuation
        diurnal = 35.0 * (1.0 if (8 <= hour <= 11 or 19 <= hour <= 22) else (-0.8 if 13 <= hour <= 16 else 0.0))
        val = int(round(180.0 + diurnal + (i * 0.2)))
        cat = ForecastService.get_category_for_aqi(val)

        reading = AQIReading(
            city_id=delhi.id,
            station_id=delhi_station.id,
            aqi_value=val,
            aqi_category=cat,
            dominant_pollutant="PM2.5",
            source="CPCB",
            is_simulated=False,
            measured_at=t,
            data_quality="valid",
        )
        readings.append(reading)

    # Add 5 sparse readings for Bengaluru (insufficient for modeling)
    for i in range(5):
        t = start_time + timedelta(hours=i * 6)
        readings.append(
            AQIReading(
                city_id=bengaluru.id,
                station_id=None,
                aqi_value=55,
                aqi_category="Satisfactory",
                dominant_pollutant="PM10",
                source="CPCB",
                is_simulated=False,
                measured_at=t,
                data_quality="valid",
            )
        )

    db_session.add_all(readings)
    db_session.flush()

    return {
        "delhi": delhi,
        "bengaluru": bengaluru,
        "delhi_station": delhi_station,
        "readings_count": len(readings),
    }


# ===========================================================================
# 1. Data Preparation & Chronological Splitting Tests
# ===========================================================================


def test_data_preparation_sufficient_cpcb_data(db_session: Session, forecast_seed_data):
    """Verify loading, deduplication, sorting, and quality labeling of verified CPCB data."""
    delhi = forecast_seed_data["delhi"]
    dataset = DataPreparationService.load_and_prepare_dataset(
        db=db_session,
        city_id=delhi.id,
        min_required_samples=24,
    )
    assert dataset.is_sufficient is True
    assert dataset.sample_count == 72
    assert dataset.data_quality == "verified_cpcb"
    assert dataset.is_simulated is False
    assert dataset.coverage_hours >= 70.0
    # Strict chronological order check
    for i in range(len(dataset.timestamps) - 1):
        assert dataset.timestamps[i] < dataset.timestamps[i + 1]


def test_data_preparation_insufficient_data(db_session: Session, forecast_seed_data):
    """Verify detection and explicit reporting when historical data is sparse (< 24 samples)."""
    bengaluru = forecast_seed_data["bengaluru"]
    dataset = DataPreparationService.load_and_prepare_dataset(
        db=db_session,
        city_id=bengaluru.id,
        min_required_samples=24,
    )
    assert dataset.is_sufficient is False
    assert dataset.sample_count == 5
    assert "Insufficient historical data" in (dataset.insufficiency_reason or "")


def test_chronological_splitting_no_leakage():
    """Verify chronological split guarantees zero data leakage and preserved order."""
    now = datetime(2026, 11, 20, 0, 0, tzinfo=timezone.utc)
    ts = [now + timedelta(hours=i) for i in range(50)]
    vals = [100.0 + i for i in range(50)]
    dataset = PreparedDataset(
        timestamps=ts,
        aqi_values=vals,
        sample_count=50,
        is_sufficient=True,
    )
    splits = DataPreparationService.split_chronological(dataset, train_ratio=0.70, val_ratio=0.15)

    assert len(splits.train_values) == 35
    assert len(splits.val_values) == 7
    assert len(splits.test_values) == 8

    # Ensure train timestamps strictly precede val, and val strictly precede test
    assert max(splits.train_timestamps) < min(splits.val_timestamps)
    assert max(splits.val_timestamps) < min(splits.test_timestamps)


def test_feature_engineering_cyclical_and_lags():
    """Verify extraction of sine/cosine diurnal features and autoregressive lags."""
    test_time = datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc)
    time_feats = FeatureEngineeringService.extract_time_features(test_time)
    assert "hour_sin" in time_feats
    assert "hour_cos" in time_feats

    history = [120.0, 125.0, 130.0, 135.0, 140.0, 150.0]
    vector = FeatureEngineeringService.build_feature_vector(history, test_time)
    assert vector["lag_1"] == 150.0
    assert vector["lag_2"] == 140.0
    assert vector["rolling_mean_3h"] == round((135.0 + 140.0 + 150.0) / 3.0, 2)


# ===========================================================================
# 2. Forecasting Models Unit Tests
# ===========================================================================


def test_persistence_model():
    """Verify persistence baseline projects latest observed value across all steps."""
    model = PersistenceModel()
    now = datetime.now(timezone.utc)
    model.fit([185.0, 190.0, 195.0], [now - timedelta(hours=2), now - timedelta(hours=1), now])
    preds = model.predict(steps=5)
    assert len(preds) == 5
    assert all(p == 195.0 for p in preds)


def test_moving_average_model():
    """Verify moving average baseline projects rolling window mean."""
    model = MovingAverageModel(window_size=3)
    now = datetime.now(timezone.utc)
    model.fit([100.0, 110.0, 120.0, 130.0], [now] * 4)
    preds = model.predict(steps=3)
    # Average of last 3: (110 + 120 + 130) / 3 = 120.0
    assert len(preds) == 3
    assert all(p == 120.0 for p in preds)


def test_exponential_smoothing_model_fit_and_predict():
    """Verify Exponential Smoothing model projects damped trend and stays in [0, 500]."""
    model = ExponentialSmoothingModel()
    now = datetime.now(timezone.utc)
    ts = [now + timedelta(hours=i) for i in range(48)]
    # Trending series: 150 -> 200
    vals = [150.0 + (i * 1.0) for i in range(48)]

    model.fit(vals, ts)
    preds = model.predict(steps=24)
    assert len(preds) == 24
    assert all(0.0 <= p <= 500.0 for p in preds)
    # First prediction should be reasonably close to latest value (~197)
    assert 175.0 <= preds[0] <= 220.0


def test_model_factory():
    """Verify ModelFactory creates requested model types and handles aliases."""
    assert isinstance(ModelFactory.get_model("persistence"), PersistenceModel)
    assert isinstance(ModelFactory.get_model("moving_average"), MovingAverageModel)
    assert isinstance(ModelFactory.get_model("exponential_smoothing"), ExponentialSmoothingModel)
    assert isinstance(ModelFactory.get_model("unknown_alias"), ExponentialSmoothingModel)


# ===========================================================================
# 3. Model Evaluation & Baseline Comparison Tests
# ===========================================================================


def test_forecast_evaluator_metrics():
    """Verify MAE, RMSE, and MAPE calculations against deterministic actuals and predictions."""
    actuals = [100.0, 110.0, 120.0, 130.0]
    preds = [102.0, 108.0, 125.0, 128.0]

    # Errors: |2|, |2|, |5|, |2| -> MAE = 11 / 4 = 2.75
    mae = ForecastEvaluator.calculate_mae(actuals, preds)
    assert mae == 2.75

    # Squared errors: 4, 4, 25, 4 = 37 -> RMSE = sqrt(37 / 4) = sqrt(9.25) ~ 3.04
    rmse = ForecastEvaluator.calculate_rmse(actuals, preds)
    assert rmse == 3.04

    mape = ForecastEvaluator.calculate_mape(actuals, preds)
    assert mape is not None
    assert 2.0 <= mape <= 3.5


def test_evaluation_against_baseline(forecast_seed_data, db_session: Session):
    """Verify out-of-sample evaluation compares candidate model against persistence baseline."""
    delhi = forecast_seed_data["delhi"]
    dataset = DataPreparationService.load_and_prepare_dataset(db=db_session, city_id=delhi.id)
    splits = DataPreparationService.split_chronological(dataset)

    model = ExponentialSmoothingModel()
    report = ForecastEvaluator.evaluate_model(model, splits, horizons=[1, 6, 12])

    assert report.model_name == "ExponentialSmoothingForecaster"
    assert report.sample_count > 0
    assert report.overall_mae >= 0.0
    assert report.overall_rmse >= 0.0
    assert report.baseline_mae >= 0.0
    assert len(report.horizon_metrics) > 0


# ===========================================================================
# 4. Uncertainty & Prediction Interval Tests
# ===========================================================================


def test_uncertainty_interval_expansion():
    """Verify prediction intervals expand monotonically as horizon increases."""
    residual_std = 12.5
    est_1h = UncertaintyEstimator.estimate_interval(
        predicted_aqi=200,
        horizon_hours=1,
        residual_std=residual_std,
        sample_count=20,
    )
    est_24h = UncertaintyEstimator.estimate_interval(
        predicted_aqi=200,
        horizon_hours=24,
        residual_std=residual_std,
        sample_count=20,
    )
    est_72h = UncertaintyEstimator.estimate_interval(
        predicted_aqi=200,
        horizon_hours=72,
        residual_std=residual_std,
        sample_count=20,
    )

    width_1h = est_1h.upper_bound - est_1h.lower_bound
    width_24h = est_24h.upper_bound - est_24h.lower_bound
    width_72h = est_72h.upper_bound - est_72h.lower_bound

    assert width_1h < width_24h < width_72h
    assert est_1h.uncertainty_status == "estimated"
    assert est_72h.uncertainty_status == "high_uncertainty"


def test_uncertainty_unavailable_when_sample_sparse():
    """Verify intervals are marked 'unavailable' without arbitrary hallucination when sample count is low."""
    est = UncertaintyEstimator.estimate_interval(
        predicted_aqi=200,
        horizon_hours=6,
        residual_std=10.0,
        sample_count=3,  # < 6 samples
    )
    assert est.uncertainty_status == "unavailable"
    assert est.lower_bound is None
    assert est.upper_bound is None


# ===========================================================================
# 5. Weather Integration Client Tests
# ===========================================================================


@pytest.mark.anyio
async def test_weather_client_mock_provider():
    """Verify WeatherClient returns structured observation when provider is 'mock'."""
    settings = Settings(WEATHER_PROVIDER="mock", WEATHER_ENABLED=True)
    client = WeatherClient(settings=settings)
    WeatherClient.clear_cache()

    obs = await client.get_current_weather(28.61, 77.20)
    assert obs is not None
    assert obs.provider == "mock"
    assert obs.temperature_celsius == 28.5
    assert obs.relative_humidity_percent == 55.0


@pytest.mark.anyio
async def test_weather_client_timeout_handling():
    """Verify WeatherClient returns None gracefully on timeout without raising unhandled errors."""
    settings = Settings(WEATHER_PROVIDER="open-meteo", WEATHER_ENABLED=True)
    client = WeatherClient(settings=settings)
    WeatherClient.clear_cache()

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Mocked timeout")):
        obs = await client.get_current_weather(28.61, 77.20)
        assert obs is None


# ===========================================================================
# 6. Forecasting End-to-End Service Tests
# ===========================================================================


@pytest.mark.anyio
async def test_forecast_service_generate_run(db_session: Session, forecast_seed_data):
    """Verify complete forecast generation lifecycle, database persistence, and evaluation."""
    delhi = forecast_seed_data["delhi"]
    service = ForecastService(settings=Settings(WEATHER_PROVIDER="mock"))

    resp = await service.generate_forecast_run(
        db=db_session,
        city_name=delhi.name,
        requested_horizons=["1h", "6h", "24h"],
        force_retrain=True,
    )
    assert resp.success is True
    assert resp.city == "Delhi"
    assert resp.generated_forecasts_count >= 24
    assert resp.training_samples == 72

    # Verify ForecastRun was persisted
    runs = db_session.query(ForecastRun).filter(ForecastRun.city_id == delhi.id).all()
    assert len(runs) >= 1
    run = runs[0]
    assert run.status == "completed"
    assert run.evaluation_mae is not None

    # Verify AQIForecast points were persisted
    points = db_session.query(AQIForecast).filter(AQIForecast.forecast_run_id == run.id).all()
    assert len(points) >= 24


# ===========================================================================
# 7. REST API Endpoints Tests
# ===========================================================================


@pytest.mark.anyio
async def test_api_get_aqi_forecast(client: AsyncClient, forecast_seed_data):
    """Test GET /api/v1/forecast/aqi returns predictions, categories, and bounds."""
    resp = await client.get("/api/v1/forecast/aqi?city=Delhi")
    assert resp.status_code == 200
    data = resp.json()

    assert data["city"] == "Delhi"
    assert "model_name" in data
    assert "forecasts" in data
    assert len(data["forecasts"]) > 0

    first_item = data["forecasts"][0]
    assert "predicted_aqi" in first_item
    assert "predicted_category" in first_item
    assert first_item["is_forecast"] is True
    assert first_item["horizon_hours"] in [1, 6, 12, 24, 48, 72]


@pytest.mark.anyio
async def test_api_get_aqi_forecast_specific_horizon(client: AsyncClient, forecast_seed_data):
    """Test GET /api/v1/forecast/aqi?city=Delhi&horizon=24h returns only 24h prediction."""
    resp = await client.get("/api/v1/forecast/aqi?city=Delhi&horizon=24h")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["forecasts"]) == 1
    assert data["forecasts"][0]["horizon_hours"] == 24


@pytest.mark.anyio
async def test_api_get_hourly_forecast(client: AsyncClient, forecast_seed_data):
    """Test GET /api/v1/forecast/hourly returns step-by-step future hours."""
    resp = await client.get("/api/v1/forecast/hourly?city=Delhi&hours=12")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Delhi"
    assert data["hours"] == 12
    assert len(data["forecasts"]) == 12
    # Verify sequential horizons 1 to 12
    for idx, item in enumerate(data["forecasts"], start=1):
        assert item["horizon_hours"] == idx


@pytest.mark.anyio
async def test_api_get_daily_forecast(client: AsyncClient, forecast_seed_data):
    """Test GET /api/v1/forecast/daily returns aggregated calendar-day outlooks."""
    resp = await client.get("/api/v1/forecast/daily?city=Delhi&days=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Delhi"
    assert len(data["summaries"]) >= 2
    day_summary = data["summaries"][0]
    assert "date" in day_summary
    assert "min_predicted_aqi" in day_summary
    assert "max_predicted_aqi" in day_summary
    assert "average_predicted_aqi" in day_summary
    assert "predominant_category" in day_summary


@pytest.mark.anyio
async def test_api_get_forecast_history(client: AsyncClient, forecast_seed_data):
    """Test GET /api/v1/forecast/history returns past execution runs."""
    # First generate a run
    await client.get("/api/v1/forecast/aqi?city=Delhi")

    resp = await client.get("/api/v1/forecast/history?city=Delhi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Delhi"
    assert data["total_runs"] >= 1
    run = data["runs"][0]
    assert run["city_name"] == "Delhi"
    assert run["status"] == "completed"


@pytest.mark.anyio
async def test_api_get_model_status(client: AsyncClient, forecast_seed_data):
    """Test GET /api/v1/forecast/model-status reports architecture and readiness."""
    resp = await client.get("/api/v1/forecast/model-status?city=Delhi")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_name" in data
    assert "model_version" in data
    assert "is_ready" in data
    assert "supported_horizons" in data
    assert "baseline_comparison" in data
    assert "weather_integration_status" in data


@pytest.mark.anyio
async def test_api_generate_forecast_admin_protection(client: AsyncClient, monkeypatch, forecast_seed_data):
    """Test POST /api/v1/forecast/generate enforces admin secret check."""
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "FORECAST_ADMIN_SECRET", "super_forecast_secret_123")

    payload = {"city": "Delhi", "force_retrain": True}

    # 1. No secret -> 403
    resp_no_auth = await client.post("/api/v1/forecast/generate", json=payload)
    assert resp_no_auth.status_code == 403

    # 2. Bad secret -> 403
    resp_bad = await client.post(
        "/api/v1/forecast/generate",
        json=payload,
        headers={"X-Admin-Secret": "wrong_key"},
    )
    assert resp_bad.status_code == 403

    # 3. Valid secret -> 200
    resp_ok = await client.post(
        "/api/v1/forecast/generate",
        json=payload,
        headers={"X-Admin-Secret": "super_forecast_secret_123"},
    )
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["success"] is True
    assert data["city"] == "Delhi"


@pytest.mark.anyio
async def test_api_validation_errors(client: AsyncClient, forecast_seed_data):
    """Test API input validation: unsupported horizon and non-existent city."""
    # Unsupported horizon
    resp_h = await client.get("/api/v1/forecast/aqi?city=Delhi&horizon=999h")
    assert resp_h.status_code == 400
    assert "Unsupported horizon" in resp_h.json()["detail"]

    # Unknown city
    resp_city = await client.get("/api/v1/forecast/aqi?city=AtlantisCity")
    assert resp_city.status_code == 404
    assert "not found" in resp_city.json()["detail"]

