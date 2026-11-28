"""SQLAlchemy Declarative Base and model registration."""

from app.db.base_class import Base
from app.models.alert import Alert
from app.models.alert_preference import AlertPreference
from app.models.aqi_reading import AQIReading

# Import all models here so Alembic and Base.metadata recognize them
from app.models.city import City
from app.models.forecast import AQIForecast, ForecastEvaluation, ForecastRun
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.models.push_subscription import PushSubscription

__all__ = [
    "AQIForecast",
    "AQIReading",
    "Alert",
    "AlertPreference",
    "Base",
    "City",
    "ForecastEvaluation",
    "ForecastRun",
    "MonitoringStation",
    "PollutantReading",
    "PushSubscription",
]
