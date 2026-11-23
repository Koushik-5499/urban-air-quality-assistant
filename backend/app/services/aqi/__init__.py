"""AQI Processing Engine package."""

from app.services.aqi.breakpoints import CPCB_BREAKPOINTS, POLLUTANT_INFO
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.categories import get_aqi_category, get_category_info
from app.services.aqi.dominant_pollutant import DominantPollutantResolver
from app.services.aqi.processor import AQIProcessingService
from app.services.aqi.validators import AQIValidator

__all__ = [
    "AQICalculator",
    "AQIProcessingService",
    "AQIValidator",
    "CPCB_BREAKPOINTS",
    "DominantPollutantResolver",
    "get_aqi_category",
    "get_category_info",
    "POLLUTANT_INFO",
]
