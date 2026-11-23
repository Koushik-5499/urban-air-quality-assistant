"""Pydantic schemas for individual pollutant readings."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PollutantReadingBase(BaseModel):
    """Base pollutant reading schema."""

    city_id: int = Field(..., description="Foreign key to city")
    station_id: int | None = Field(None, description="Optional foreign key to monitoring station")
    pollutant_code: str = Field(
        ..., max_length=20, description="Code: PM2.5, PM10, CO, NO2, SO2, O3"
    )
    concentration: float = Field(..., ge=0.0, description="Non-negative concentration value")
    unit: str = Field(default="µg/m³", max_length=20, description="Unit of measurement")
    measured_at: datetime = Field(..., description="Timestamp of measurement in UTC")
    source: str = Field(default="CPCB", max_length=100, description="Reading source")
    is_simulated: bool = Field(
        default=False, description="Whether reading is simulated or observed"
    )
    data_quality: str = Field(
        default="valid", max_length=50, description="Quality indicator for measurement"
    )


class PollutantReadingCreate(PollutantReadingBase):
    """Schema for creating a pollutant reading."""

    pass


class PollutantReadingResponse(PollutantReadingBase):
    """Schema for returning pollutant reading data."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
