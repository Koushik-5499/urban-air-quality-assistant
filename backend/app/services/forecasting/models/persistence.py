"""Persistence baseline model (Last-Value Forecaster: y_hat_{t+h} = y_t)."""

from datetime import datetime

from app.services.forecasting.models.base import BaseForecastModel


class PersistenceModel(BaseForecastModel):
    """Standard time-series baseline forecasting that future values equal the latest observation."""

    def __init__(self):
        self._last_value: float = 0.0
        self._fitted: bool = False

    @property
    def name(self) -> str:
        """Return persistence model identifier."""
        return "PersistenceBaseline"

    @property
    def version(self) -> str:
        """Return baseline model version."""
        return "1.0.0"

    def fit(self, series: list[float], timestamps: list[datetime]) -> None:
        """Store the most recent observation as the persistent forecast baseline."""
        if not series:
            raise ValueError("Cannot fit PersistenceModel with empty observation series.")
        self._last_value = float(series[-1])
        self._fitted = True

    def predict(self, steps: int) -> list[float]:
        """Generate static forecast equal to the last observed value for all steps."""
        if not self._fitted:
            raise RuntimeError("PersistenceModel must be fitted before predict() is called.")
        if steps <= 0:
            return []
        # Clamp to valid AQI range
        clamped = max(0.0, min(500.0, self._last_value))
        return [clamped] * steps
