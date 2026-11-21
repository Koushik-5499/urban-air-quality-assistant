"""Pydantic schemas for Air Quality Index (AQI) readings."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AQIReadingBase(BaseModel):
    """Base AQI reading schema."""

    city_id: int = Field(..., description="Foreign key to city")
    station_id: Optional[int] = Field(None, description="Optional foreign key to monitoring station")
    aqi_value: int = Field(..., ge=0, le=500, description="AQI numerical index (0-500)")
    aqi_category: str = Field(..., max_length=50, description="AQI category (e.g. Good, Moderate)")
    dominant_pollutant: Optional[str] = Field(None, max_length=20, description="Primary driver pollutant")
    measured_at: datetime = Field(..., description="Timestamp of measurement in UTC")
    source: str = Field(default="CPCB", max_length=100, description="Reading origin source")
    is_simulated: bool = Field(default=False, description="Whether reading is simulated or observed")
    data_quality: str = Field(default="valid", max_length=50, description="Data quality indicator")


class AQIReadingCreate(AQIReadingBase):
    """Schema for creating an AQI reading record."""

    pass


class AQIReadingResponse(AQIReadingBase):
    """Schema for AQI reading response."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

