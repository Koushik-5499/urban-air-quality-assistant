"""Master router aggregating all v1 endpoint sub-routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import air_quality, alerts, aqi, forecast, health, history, stations

api_router = APIRouter()

# Register health check endpoint under /health
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

# Register air quality endpoints under /air-quality
api_router.include_router(
    air_quality.router,
    prefix="/air-quality",
    tags=["Air Quality"],
)

# Register alerts and notifications endpoints under /alerts
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts & Notifications"],
)

# Register AQI processing engine endpoints under /aqi
api_router.include_router(
    aqi.router,
    prefix="/aqi",
    tags=["AQI Processing Engine"],
)

# Register historical data service endpoints under /history
api_router.include_router(
    history.router,
    prefix="/history",
    tags=["Historical Data Service"],
)

# Register air quality forecasting endpoints under /forecast
api_router.include_router(
    forecast.router,
    prefix="/forecast",
    tags=["Air Quality Forecasting"],
)

# Register monitoring stations endpoints under /stations
api_router.include_router(
    stations.router,
    prefix="/stations",
    tags=["Monitoring Stations"],
)
