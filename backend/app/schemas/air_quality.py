"""Pydantic schemas for Air Quality API endpoints and synchronization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PollutantDetail(BaseModel):
    """Detailed observation of a single pollutant."""

    code: str = Field(..., description="Standard pollutant code (e.g. PM2.5, PM10, NO2)")
    concentration: float = Field(..., ge=0.0, description="Measured concentration")
    unit: str = Field(default="µg/m³", description="Preserved unit of measurement")
    measured_at: datetime = Field(..., description="Observation timestamp in UTC")
    source: str = Field(..., description="Provider source identifier")

    model_config = ConfigDict(from_attributes=True)


class CityAirQualityResponse(BaseModel):
    """Real-time air quality observation response for a city."""

    city_id: int
    city_name: str
    state: str
    country: str
    data_available: bool = Field(..., description="Whether live or recent observations exist")
    source: str = Field(default="CPCB", description="Data provider")
    is_simulated: bool = Field(
        default=False, description="Flag indicating simulated vs observed data"
    )
    is_stale: bool = Field(
        default=False, description="True if latest reading exceeds freshness threshold"
    )
    data_age_seconds: int | None = Field(None, description="Age of latest measurement in seconds")
    measured_at: datetime | None = Field(None, description="Timestamp of latest observation")
    fetched_at: datetime = Field(..., description="Timestamp of API retrieval")
    pollutants: list[PollutantDetail] = Field(
        default_factory=list, description="Array of pollutant readings"
    )
    active_stations_count: int = Field(
        default=0, description="Number of active reporting stations in this city"
    )
    message: str | None = Field(None, description="Explanatory notes on coverage or availability")


class CityAvailabilitySummary(BaseModel):
    """City live monitoring status and coverage overview."""

    city_id: int
    city_name: str
    state: str
    country: str = "India"
    data_available: bool
    last_measured_at: datetime | None = None
    is_stale: bool = False
    station_count: int = 0
    source: str = "CPCB"


class SourceStatusResponse(BaseModel):
    """External provider status, licensing, and operational diagnostics."""

    provider_name: str
    dataset_title: str
    publisher: str
    license: str
    base_url: str
    resource_id: str | None = None
    is_configured: bool
    last_successful_fetch: datetime | None = None
    last_successful_sync: datetime | None = None
    data_freshness_status: str = Field(
        ...,
        description="Freshness assessment: 'fresh', 'stale', 'no_data', or 'unconfigured'",
    )
    last_error_category: str | None = None


class SyncResponse(BaseModel):
    """Response returned upon completion of an on-demand data sync."""

    success: bool
    message: str
    records_fetched: int
    readings_inserted: int
    stations_created: int
    synced_at: datetime
