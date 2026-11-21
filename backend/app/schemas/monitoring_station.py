"""Pydantic schemas for environmental monitoring stations."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StationBase(BaseModel):
    """Base monitoring station schema."""

    station_name: str = Field(..., max_length=200, description="Human-readable station name")
    external_station_id: Optional[str] = Field(None, max_length=100, description="Provider station ID")
    city_id: int = Field(..., description="Foreign key to cities table")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    provider: str = Field(default="CPCB", max_length=100, description="Data source provider")
    is_active: bool = Field(default=True, description="Whether the station is actively recording")


class StationCreate(StationBase):
    """Schema for registering a new monitoring station."""

    pass


class StationResponse(StationBase):
    """Schema for monitoring station responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

