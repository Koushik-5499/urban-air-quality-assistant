"""SQLAlchemy Declarative Base and model registration."""

from app.db.base_class import Base  # noqa: F401

# Import all models here so Alembic and Base.metadata recognize them
from app.models.city import City  # noqa: E402, F401
from app.models.monitoring_station import MonitoringStation  # noqa: E402, F401
from app.models.pollutant_reading import PollutantReading  # noqa: E402, F401
from app.models.aqi_reading import AQIReading  # noqa: E402, F401
from app.models.alert import Alert  # noqa: E402, F401
from app.models.alert_preference import AlertPreference  # noqa: E402, F401
from app.models.forecast import AQIForecast, ForecastEvaluation, ForecastRun  # noqa: E402, F401
from app.models.push_subscription import PushSubscription  # noqa: E402, F401
