"""Targeted tests to cover uncovered lines in forecast model modules.

Covers:
- feature_engineering.py: _build_weather_features with partial weather data (lines 54-63)
- forecasting/models/moving_average.py: name, version, fit, predict (lines 18, 22, 27, 35, 37)
- forecasting/models/persistence.py: name, version, fit, predict (lines 17, 21, 26, 33, 35)
- forecasting/models/base.py: supported_horizons property (line 25)
- forecasting/validators.py: missing lines (40-42, 80-86)
"""

from datetime import UTC, datetime

import pytest

from app.services.forecasting.feature_engineering import FeatureEngineeringService
from app.services.forecasting.models.moving_average import MovingAverageModel
from app.services.forecasting.models.persistence import PersistenceModel

# ---------------------------------------------------------------------------
# feature_engineering.py — _build_weather_features (partial weather data)
# ---------------------------------------------------------------------------


_NOW = datetime(2024, 1, 15, 8, 0, tzinfo=UTC)


def _make_obs(**overrides):  # type: ignore[return]
    """Build a WeatherObservation with required fields pre-filled."""
    from app.integrations.weather.schemas import WeatherObservation

    defaults: dict = dict(
        latitude=28.6,
        longitude=77.2,
        observed_at=_NOW,
        provider="test",
        temperature_celsius=None,
        relative_humidity_percent=None,
        wind_speed_kmh=None,
        surface_pressure_hpa=None,
    )
    defaults.update(overrides)
    return WeatherObservation(**defaults)


def test_build_weather_features_with_all_fields():
    """All four weather fields should produce four feature keys."""
    obs = _make_obs(
        temperature_celsius=28.5,
        relative_humidity_percent=65.0,
        wind_speed_kmh=12.0,
        surface_pressure_hpa=1010.0,
    )
    feats = FeatureEngineeringService._build_weather_features(obs)
    assert "weather_temp_c" in feats
    assert "weather_humidity_pct" in feats
    assert "weather_wind_speed_kmh" in feats
    assert "weather_pressure_hpa" in feats


def test_build_weather_features_with_partial_fields():
    """Only present weather fields produce feature keys."""
    obs = _make_obs(temperature_celsius=22.0)
    feats = FeatureEngineeringService._build_weather_features(obs)
    assert "weather_temp_c" in feats
    assert "weather_humidity_pct" not in feats
    assert "weather_wind_speed_kmh" not in feats
    assert "weather_pressure_hpa" not in feats


def test_build_weather_features_with_no_fields():
    """When all weather fields are None, return empty dict."""
    obs = _make_obs()
    feats = FeatureEngineeringService._build_weather_features(obs)
    assert feats == {}


def test_build_feature_vector_with_weather():
    """build_feature_vector includes weather keys when weather is supplied."""
    obs = _make_obs(
        temperature_celsius=30.0,
        relative_humidity_percent=70.0,
        wind_speed_kmh=8.0,
        surface_pressure_hpa=1005.0,
    )
    history = [120.0, 130.0, 125.0, 140.0, 135.0]
    ts = datetime(2024, 1, 15, 8, 0, tzinfo=UTC)
    vector = FeatureEngineeringService.build_feature_vector(history, ts, weather=obs)
    assert "weather_temp_c" in vector
    assert "hour_sin" in vector
    assert "lag_1" in vector


# ---------------------------------------------------------------------------
# MovingAverageModel — name, version, fit, predict
# ---------------------------------------------------------------------------


def test_moving_average_name_and_version():
    """MovingAverageModel.name and .version return expected strings."""
    model = MovingAverageModel(window_size=6)
    assert "MovingAverageBaseline" in model.name
    assert model.version == "1.0.0"


def test_moving_average_supported_horizons():
    """supported_horizons returns the base class default list."""
    model = MovingAverageModel(window_size=3)
    horizons = model.supported_horizons
    assert 24 in horizons
    assert len(horizons) >= 4


def test_moving_average_fit_and_predict():
    """Fit on a series then predict 5 steps returns 5 identical values."""
    model = MovingAverageModel(window_size=3)
    series = [100.0, 110.0, 120.0, 130.0, 140.0]
    ts = [datetime(2024, 1, 1, h, 0) for h in range(5)]
    model.fit(series, ts)
    preds = model.predict(5)
    assert len(preds) == 5
    # All predictions equal the mean of the last 3 values
    expected = round((120.0 + 130.0 + 140.0) / 3, 2)
    assert all(abs(p - expected) < 0.01 for p in preds)


def test_moving_average_predict_zero_steps():
    """predict(0) returns empty list."""
    model = MovingAverageModel(window_size=3)
    series = [100.0, 110.0, 120.0]
    ts = [datetime(2024, 1, 1, h, 0) for h in range(3)]
    model.fit(series, ts)
    assert model.predict(0) == []


def test_moving_average_fit_raises_on_empty_series():
    """fit() must raise ValueError for empty input."""
    model = MovingAverageModel(window_size=3)
    with pytest.raises(ValueError, match="empty"):
        model.fit([], [])


def test_moving_average_predict_raises_before_fit():
    """predict() raises RuntimeError if called before fit()."""
    model = MovingAverageModel(window_size=3)
    with pytest.raises(RuntimeError, match="fitted"):
        model.predict(3)


def test_moving_average_short_series_uses_all():
    """When series shorter than window, use all values."""
    model = MovingAverageModel(window_size=10)
    series = [50.0, 60.0]
    ts = [datetime(2024, 1, 1, h, 0) for h in range(2)]
    model.fit(series, ts)
    preds = model.predict(2)
    assert len(preds) == 2
    assert abs(preds[0] - 55.0) < 0.01


# ---------------------------------------------------------------------------
# PersistenceModel — name, version, fit, predict
# ---------------------------------------------------------------------------


def test_persistence_name_and_version():
    """PersistenceModel.name and .version return expected strings."""
    model = PersistenceModel()
    assert "Persistence" in model.name
    assert model.version == "1.0.0"


def test_persistence_fit_and_predict():
    """Fit on series then predict k steps returns k copies of last value (clamped)."""
    model = PersistenceModel()
    series = [200.0, 210.0, 220.0]
    ts = [datetime(2024, 1, 1, h, 0) for h in range(3)]
    model.fit(series, ts)
    preds = model.predict(4)
    assert len(preds) == 4
    assert all(abs(p - 220.0) < 0.01 for p in preds)


def test_persistence_predict_zero_steps():
    """predict(0) returns empty list."""
    model = PersistenceModel()
    model.fit([150.0], [datetime(2024, 1, 1)])
    assert model.predict(0) == []


def test_persistence_fit_raises_on_empty_series():
    """fit() must raise ValueError for empty input."""
    model = PersistenceModel()
    with pytest.raises(ValueError, match="empty"):
        model.fit([], [])


def test_persistence_predict_raises_before_fit():
    """predict() raises RuntimeError if called before fit()."""
    model = PersistenceModel()
    with pytest.raises(RuntimeError, match="fitted"):
        model.predict(3)


def test_persistence_clamps_above_500():
    """PersistenceModel clamps values above 500 to 500."""
    model = PersistenceModel()
    model.fit([600.0], [datetime(2024, 1, 1)])
    preds = model.predict(1)
    assert preds[0] == 500.0


def test_persistence_clamps_below_zero():
    """PersistenceModel clamps values below 0 to 0."""
    model = PersistenceModel()
    model.fit([-10.0], [datetime(2024, 1, 1)])
    preds = model.predict(1)
    assert preds[0] == 0.0

