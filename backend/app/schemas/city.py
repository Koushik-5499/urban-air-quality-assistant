"""Pydantic schemas for City entity."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CityBase(BaseModel):
    """Base city schema."""

    name: str = Field(..., max_length=100, description="City name")
    state: str = Field(..., max_length=100, description="Indian state name")
    country: str = Field(default="India", max_length=100, description="Country")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")


class CityCreate(CityBase):
    """Schema for creating a new city."""

    pass


class CityUpdate(BaseModel):
    """Schema for updating an existing city."""

    name: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class CityResponse(CityBase):
    """Schema for city response with database identifiers."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CitySummary(BaseModel):
    """Lightweight summary of city for listings and references."""

    id: int
    name: str
    state: str
    country: str

    model_config = ConfigDict(from_attributes=True)

