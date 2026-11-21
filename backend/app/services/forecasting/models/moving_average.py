"""Simple and exponentially weighted moving average forecasting baseline."""

from datetime import datetime

from app.services.forecasting.models.base import BaseForecastModel


class MovingAverageModel(BaseForecastModel):
    """Moving Average baseline using a rolling window of recent historical values."""

    def __init__(self, window_size: int = 6):
        self.window_size = window_size
        self._mean_value: float = 0.0
        self._fitted: bool = False

    @property
    def name(self) -> str:
        return f"MovingAverageBaseline(window={self.window_size})"

    @property
    def version(self) -> str:
        return "1.0.0"

    def fit(self, series: list[float], timestamps: list[datetime]) -> None:
        """Compute the arithmetic mean of the most recent window."""
        if not series:
            raise ValueError("Cannot fit MovingAverageModel with empty observation series.")
        window = series[-self.window_size:] if len(series) >= self.window_size else series
        self._mean_value = sum(window) / float(len(window))
        self._fitted = True

    def predict(self, steps: int) -> list[float]:
        """Project the moving average into the future."""
        if not self._fitted:
            raise RuntimeError("MovingAverageModel must be fitted before predict() is called.")
        if steps <= 0:
            return []
        clamped = max(0.0, min(500.0, round(self._mean_value, 2)))
        return [clamped] * steps

