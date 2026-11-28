"""Asynchronous HTTP client for retrieving meteorological observations from Open-Meteo."""

import asyncio
import logging
from datetime import UTC, datetime

import httpx

from app.core.config import Settings, get_settings
from app.integrations.weather.schemas import WeatherObservation

logger = logging.getLogger(__name__)


class WeatherClient:
    """Client for fetching real-time meteorological data with caching and retry logic."""

    # Key: (round(lat, 2), round(lon, 2)), Value: (WeatherObservation, cache_time)
    _cache: dict[tuple[float, float], tuple[WeatherObservation, datetime]] = {}

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherObservation | None:
        """Fetch current weather observation for given coordinates.

        Returns None gracefully if weather integration is disabled or provider is unreachable.
        """
        if not self.settings.WEATHER_ENABLED:
            logger.debug("Weather integration is disabled via configuration.")
            return None

        # Check in-memory cache
        cache_key = (round(latitude, 2), round(longitude, 2))
        now_utc = datetime.now(UTC)

        if cache_key in self._cache:
            obs, cached_at = self._cache[cache_key]
            age_seconds = (now_utc - cached_at).total_seconds()
            if age_seconds < self.settings.WEATHER_CACHE_TTL_SECONDS:
                cached_copy = obs.model_copy()
                cached_copy.is_cached = True
                return cached_copy

        # Mock provider for testing/offline environments
        if self.settings.WEATHER_PROVIDER.lower() == "mock":
            mock_obs = WeatherObservation(
                latitude=latitude,
                longitude=longitude,
                temperature_celsius=28.5,
                relative_humidity_percent=55.0,
                wind_speed_kmh=12.4,
                wind_direction_degrees=180.0,
                precipitation_mm=0.0,
                surface_pressure_hpa=1012.0,
                observed_at=now_utc,
                provider="mock",
                is_cached=False,
            )
            self._cache[cache_key] = (mock_obs, now_utc)
            return mock_obs

        return await self._fetch_live_weather(latitude, longitude, cache_key, now_utc)

    @staticmethod
    def _parse_optional_float(data: dict[str, object], key: str) -> float | None:
        """Safely coerce an optional JSON field to float without suppressing type errors."""
        value = data.get(key)
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float, str)):
            try:
                return float(value)
            except ValueError:
                return None
        return None

    def _build_observation(
        self,
        current_data: dict[str, object],
        latitude: float,
        longitude: float,
        now_utc: datetime,
    ) -> WeatherObservation:
        """Construct a WeatherObservation from an Open-Meteo current-data dict."""
        time_str = current_data.get("time")
        obs_time = (
            datetime.fromisoformat(str(time_str)).replace(tzinfo=UTC)
            if time_str
            else now_utc
        )
        return WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=self._parse_optional_float(current_data, "temperature_2m"),
            relative_humidity_percent=self._parse_optional_float(
                current_data, "relative_humidity_2m"
            ),
            wind_speed_kmh=self._parse_optional_float(current_data, "wind_speed_10m"),
            wind_direction_degrees=self._parse_optional_float(current_data, "wind_direction_10m"),
            precipitation_mm=self._parse_optional_float(current_data, "precipitation"),
            surface_pressure_hpa=self._parse_optional_float(current_data, "surface_pressure"),
            observed_at=obs_time,
            provider=self.settings.WEATHER_PROVIDER,
            is_cached=False,
        )

    async def _fetch_live_weather(
        self,
        latitude: float,
        longitude: float,
        cache_key: tuple[float, float],
        now_utc: datetime,
    ) -> WeatherObservation | None:
        """Fetch and cache a live Open-Meteo observation with retry logic."""
        params: dict[str, str | float] = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "wind_speed_10m,wind_direction_10m,surface_pressure"
            ),
            "timezone": "UTC",
        }
        url = f"{self.settings.WEATHER_API_BASE_URL.rstrip('/')}/forecast"
        headers = {"User-Agent": "UrbanAirQualityAssistant/1.0"}
        if self.settings.WEATHER_API_KEY:
            params["apikey"] = self.settings.WEATHER_API_KEY

        for attempt in range(1, 3):
            try:
                async with httpx.AsyncClient(
                    timeout=self.settings.WEATHER_REQUEST_TIMEOUT
                ) as client:
                    resp = await client.get(url, params=params, headers=headers)
                    if resp.status_code == 200:
                        observation = self._build_observation(
                            resp.json().get("current", {}), latitude, longitude, now_utc
                        )
                        self._cache[cache_key] = (observation, now_utc)
                        return observation
                    logger.warning(
                        "Open-Meteo returned HTTP %d for coordinates (%s, %s)",
                        resp.status_code, latitude, longitude,
                    )
            except httpx.TimeoutException:
                logger.warning(
                    "Timeout contacting weather provider (attempt %d/2) for (%s, %s)",
                    attempt, latitude, longitude,
                )
            except httpx.HTTPError as exc:
                logger.warning(
                    "Error contacting weather provider (attempt %d/2): %s", attempt, exc,
                )
            if attempt < 2:
                await asyncio.sleep(0.5)

        logger.info(
            "Proceeding without weather telemetry for coordinates (%s, %s)", latitude, longitude,
        )
        return None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear weather observation in-memory cache."""
        cls._cache.clear()
