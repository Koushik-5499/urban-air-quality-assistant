"""Base abstractions and domain schemas for external air quality integrations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NormalizedObservation(BaseModel):
    """Normalized observation schema produced by provider mappers."""

    country: str = Field(default="India", description="Country name")
    state: str = Field(..., description="Indian State name")
    city: str = Field(..., description="City name")
    station_name: str = Field(..., description="Full monitoring station name")
    external_station_id: Optional[str] = Field(None, description="Official provider station identifier")
    latitude: Optional[float] = Field(None, description="Geographic latitude")
    longitude: Optional[float] = Field(None, description="Geographic longitude")
    pollutant_code: str = Field(..., description="Standardized pollutant code: PM2.5, PM10, NO2, SO2, CO, O3")
    concentration: float = Field(..., ge=0.0, description="Measured concentration value")
    unit: str = Field(default="µg/m³", description="Preserved measurement unit")
    measured_at: datetime = Field(..., description="Timestamp of observation normalized to UTC")
    source: str = Field(default="CPCB", description="Source provider attribution")
    is_simulated: bool = Field(default=False, description="Whether reading is simulated")
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw payload")


class ProviderMetadata(BaseModel):
    """Provider descriptive metadata and operational configuration."""

    provider_name: str
    dataset_title: str
    publisher: str
    license: str
    base_url: str
    resource_id: Optional[str] = None
    is_configured: bool
    supports_filtering: bool = True


class BaseAQIProvider(ABC):
    """Abstract interface defining required provider integration capabilities."""

    @abstractmethod
    async def fetch_observations(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> List[NormalizedObservation]:
        """Fetch and return standardized pollutant observations."""
        pass

    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Return provider configuration metadata and licensing."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Gracefully release HTTP clients and connections."""
        pass

