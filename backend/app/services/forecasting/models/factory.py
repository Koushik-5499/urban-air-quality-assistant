"""Factory for instantiating forecasting models."""


from app.services.forecasting.models.base import BaseForecastModel
from app.services.forecasting.models.exponential_smoothing import ExponentialSmoothingModel
from app.services.forecasting.models.moving_average import MovingAverageModel
from app.services.forecasting.models.persistence import PersistenceModel


class ModelFactory:
    """Instantiates configured or requested forecasting models."""

    @staticmethod
    def get_model(model_name: str | None = "exponential_smoothing") -> BaseForecastModel:
        """Return forecasting model instance matching identifier."""
        name = (model_name or "exponential_smoothing").lower().strip()

        if name in ("persistence", "persistence_baseline", "last_value"):
            return PersistenceModel()
        elif name in ("moving_average", "ma", "rolling_mean"):
            return MovingAverageModel(window_size=6)
        elif name in ("exponential_smoothing", "holt_winters", "ets", "default"):
            return ExponentialSmoothingModel()
        else:
            return ExponentialSmoothingModel()

