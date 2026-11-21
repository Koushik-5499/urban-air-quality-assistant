"""Abstract base interface for air quality time-series forecasting models."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class BaseForecastModel(ABC):
    """Abstract interface defining the contract for statistical and ML forecasting models."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier of the model."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Model release or architecture version string."""
        pass

    @property
    def supported_horizons(self) -> List[int]:
        """List of forecast horizons (in hours) supported by this model."""
        return [1, 6, 12, 24, 48, 72]

    @abstractmethod
    def fit(self, series: List[float], timestamps: List[datetime]) -> None:
        """Fit or initialize model parameters on historical time-series observations."""
        pass

    @abstractmethod
    def predict(self, steps: int) -> List[float]:
        """Generate forecasts for the specified number of future hourly steps."""
        pass

