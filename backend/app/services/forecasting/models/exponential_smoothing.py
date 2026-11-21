"""Holt-Winters and Double Exponential Smoothing with damped trend and diurnal seasonality."""

import math
from datetime import datetime

from app.services.forecasting.models.base import BaseForecastModel


class ExponentialSmoothingModel(BaseForecastModel):
    """Adaptive Exponential Smoothing model incorporating level, damped trend, and 24h diurnal seasonality."""

    def __init__(
        self,
        alpha: float = 0.40,  # Level smoothing factor
        beta: float = 0.10,   # Trend smoothing factor
        gamma: float = 0.20,  # Seasonal smoothing factor
        phi: float = 0.92,    # Damped trend parameter
        seasonal_period: int = 24,
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.phi = phi
        self.seasonal_period = seasonal_period

        self._level: float = 0.0
        self._trend: float = 0.0
        self._seasonals: list[float] = [0.0] * seasonal_period
        self._last_hour: int = 0
        self._has_seasonality: bool = False
        self._fitted: bool = False

    @property
    def name(self) -> str:
        return "ExponentialSmoothingForecaster"

    @property
    def version(self) -> str:
        return "1.2.0"

    def fit(self, series: list[float], timestamps: list[datetime]) -> None:
        """Fit level, trend, and diurnal seasonal components to the time-series."""
        n = len(series)
        if n < 2:
            raise ValueError(f"ExponentialSmoothingModel requires at least 2 observations, got {n}.")

        m = self.seasonal_period
        self._has_seasonality = (n >= 2 * m)
        self._last_hour = timestamps[-1].hour if timestamps else 0

        # 1. Initialize level and trend
        level = series[0]
        trend = (series[min(n - 1, 12)] - series[0]) / float(min(n - 1, 12)) if n > 1 else 0.0

        # 2. Initialize seasonal factors if sufficient data exists
        seasonals = [0.0] * m
        if self._has_seasonality:
            # Estimate additive seasonal factors across full periods
            num_periods = n // m
            averages = [
                sum(series[i * m : (i + 1) * m]) / float(m)
                for i in range(num_periods)
            ]
            for i in range(m):
                sum_over_periods = 0.0
                for j in range(num_periods):
                    sum_over_periods += (series[j * m + i] - averages[j])
                seasonals[i] = sum_over_periods / float(num_periods)

            # Normalize seasonal factors to sum to zero
            mean_seasonal = sum(seasonals) / float(m)
            seasonals = [s - mean_seasonal for s in seasonals]

        # 3. Recursive Holt-Winters update equations over history
        for t in range(n):
            y_t = series[t]
            s_idx = t % m if self._has_seasonality else 0
            s_val = seasonals[s_idx] if self._has_seasonality else 0.0

            # Deseasonalized observation
            y_deseason = y_t - s_val

            prev_level = level
            level = self.alpha * y_deseason + (1.0 - self.alpha) * (prev_level + self.phi * trend)
            trend = self.beta * (level - prev_level) + (1.0 - self.beta) * self.phi * trend

            if self._has_seasonality:
                seasonals[s_idx] = self.gamma * (y_t - level) + (1.0 - self.gamma) * s_val

        self._level = level
        self._trend = trend
        self._seasonals = seasonals
        self._fitted = True

    def predict(self, steps: int) -> list[float]:
        """Project future values across `steps` hours with damped trend and diurnal cycle."""
        if not self._fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")
        if steps <= 0:
            return []

        predictions: list[float] = []
        cumulative_phi = 0.0
        m = self.seasonal_period

        for h in range(1, steps + 1):
            # Sum of damped trend factors: phi + phi^2 + ... + phi^h
            cumulative_phi += math.pow(self.phi, h)
            trend_component = cumulative_phi * self._trend

            # Diurnal seasonal component aligned with target future hour
            if self._has_seasonality:
                target_hour = (self._last_hour + h) % m
                seasonal_component = self._seasonals[target_hour]
            else:
                seasonal_component = 0.0

            predicted_val = self._level + trend_component + seasonal_component

            # Clamp predictions to valid physical NAQI range [0, 500]
            clamped = max(0.0, min(500.0, round(predicted_val, 1)))
            predictions.append(clamped)

        return predictions

