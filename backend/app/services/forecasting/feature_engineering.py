"""Feature engineering for time-series forecasting: lags, rolling windows, and cyclical diurnal patterns."""

import math
from datetime import datetime

from app.integrations.weather.schemas import WeatherObservation


class FeatureEngineeringService:
    """Extracts autoregressive lag, rolling window statistics, and diurnal cyclical features."""

    @staticmethod
    def extract_time_features(dt: datetime) -> dict[str, float]:
        """Compute sinusoidal cyclical encodings for hour of day and day of week."""
        hour = dt.hour + (dt.minute / 60.0)
        day_of_week = dt.weekday()

        return {
            "hour_sin": round(math.sin(2.0 * math.pi * hour / 24.0), 4),
            "hour_cos": round(math.cos(2.0 * math.pi * hour / 24.0), 4),
            "dow_sin": round(math.sin(2.0 * math.pi * day_of_week / 7.0), 4),
            "dow_cos": round(math.cos(2.0 * math.pi * day_of_week / 7.0), 4),
        }

    @staticmethod
    def calculate_rolling_mean(series: list[float], window_size: int) -> float | None:
        """Calculate mean of the last `window_size` elements."""
        if len(series) < window_size or window_size <= 0:
            return None
        window = series[-window_size:]
        return round(sum(window) / float(len(window)), 2)

    @classmethod
    def build_feature_vector(
        cls,
        history_values: list[float],
        target_timestamp: datetime,
        weather: WeatherObservation | None = None,
    ) -> dict[str, float]:
        """Construct full feature dictionary for a single prediction step."""
        features: dict[str, float] = {}

        # 1. Cyclical time encodings
        time_feats = cls.extract_time_features(target_timestamp)
        features.update(time_feats)

        # 2. Lag features (t-1, t-2, t-3, t-6, t-12, t-24)
        n = len(history_values)
        for lag in [1, 2, 3, 6, 12, 24]:
            if n >= lag:
                features[f"lag_{lag}"] = round(history_values[-lag], 2)
            else:
                features[f"lag_{lag}"] = round(history_values[-1], 2) if n > 0 else 0.0

        # 3. Rolling window means (3h, 6h, 24h)
        for window in [3, 6, 24]:
            rm = cls.calculate_rolling_mean(history_values, window)
            features[f"rolling_mean_{window}h"] = rm if rm is not None else features.get("lag_1", 0.0)

        # 4. Optional meteorological feature integration
        if weather:
            if weather.temperature_celsius is not None:
                features["weather_temp_c"] = weather.temperature_celsius
            if weather.relative_humidity_percent is not None:
                features["weather_humidity_pct"] = weather.relative_humidity_percent
            if weather.wind_speed_kmh is not None:
                features["weather_wind_speed_kmh"] = weather.wind_speed_kmh
            if weather.surface_pressure_hpa is not None:
                features["weather_pressure_hpa"] = weather.surface_pressure_hpa

        return features

