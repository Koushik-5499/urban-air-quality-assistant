"""Pydantic schemas for meteorological observations and weather features."""

from datetime import datetime

from pydantic import BaseModel, Field


class WeatherObservation(BaseModel):
    """Normalized weather metrics for a geographical location."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    temperature_celsius: float | None = Field(None, description="Ambient air temperature in degrees Celsius")
    relative_humidity_percent: float | None = Field(None, description="Relative humidity percentage (0-100)")
    wind_speed_kmh: float | None = Field(None, description="Wind speed in km/h")
    wind_direction_degrees: float | None = Field(None, description="Wind direction in degrees (0-360)")
    precipitation_mm: float | None = Field(None, description="Precipitation rate in millimeters")
    surface_pressure_hpa: float | None = Field(None, description="Atmospheric pressure at surface in hPa")
    observed_at: datetime = Field(..., description="UTC timestamp of the weather observation")
    provider: str = Field(default="open-meteo", description="Meteorological provider name")
    is_cached: bool = Field(default=False, description="Whether the record was retrieved from cache")


class WeatherStatusResponse(BaseModel):
    """Status of the weather integration service."""

    enabled: bool
    provider: str
    base_url: str
    available: bool

