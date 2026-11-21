"""Pydantic schemas for NAQI calculation results, sub-indices, history, and processing."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PollutantSubIndexResult(BaseModel):
    """Calculated sub-index result for an individual pollutant."""

    pollutant_code: str
    concentration: float
    unit: str
    sub_index: Optional[int] = Field(None, description="Calculated CPCB sub-index (0-500)")
    category: Optional[str] = Field(None, description="Category for this pollutant sub-index")
    averaging_period: str = Field(..., description="Required averaging duration (e.g. 24-hour, 8-hour)")
    is_valid: bool = Field(True, description="Whether concentration and unit passed CPCB validation")
    validation_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AQICalculationResponse(BaseModel):
    """Complete CPCB NAQI calculation response."""

    city_id: int
    city_name: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    aqi: Optional[int] = Field(None, description="Composite NAQI index value (0-500); None if data is insufficient")
    category: Optional[str] = Field(None, description="Official CPCB NAQI category")
    dominant_pollutant: Optional[str] = Field(None, description="Pollutant with highest sub-index")
    pollutant_subindices: Dict[str, PollutantSubIndexResult] = Field(
        default_factory=dict,
        description="Dictionary of individual pollutant sub-indices",
    )
    measurement_timestamp: Optional[datetime] = Field(None, description="Observation timestamp in UTC")
    calculated_at: datetime = Field(..., description="Calculation timestamp in UTC")
    source: str = Field(default="CPCB", description="Source provider identifier")
    is_simulated: bool = Field(default=False, description="Whether calculation used simulated measurements")
    data_quality: str = Field(..., description="'sufficient', 'insufficient_data', or 'invalid_input'")
    averaging_period: str = Field(
        default="1-hour (indicative)",
        description="Averaging cadence (e.g. '24-hour' or '1-hour (indicative)')",
    )
    available_pollutants: List[str] = Field(default_factory=list)
    missing_pollutants: List[str] = Field(default_factory=list)
    explanation: str = Field(..., description="Data sufficiency explanation or health advisory")


class SubIndicesOnlyResponse(BaseModel):
    """Response containing individual pollutant sub-indices and dominant pollutant."""

    city_id: int
    city_name: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    dominant_pollutant: Optional[str] = None
    sub_indices: Dict[str, PollutantSubIndexResult]
    calculated_at: datetime


class AQIHistoryItem(BaseModel):
    """Historical AQI entry."""

    id: int
    city_id: int
    city_name: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    aqi_value: int
    aqi_category: str
    dominant_pollutant: Optional[str] = None
    measured_at: datetime
    source: str
    is_simulated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AQIHistoryResponse(BaseModel):
    """Paginated historical AQI list response."""

    total: int
    page: int
    page_size: int
    items: List[AQIHistoryItem]


class AQIProcessResponse(BaseModel):
    """Summary of batch AQI processing execution."""

    success: bool
    stations_evaluated: int
    aqi_records_created: int
    skipped_insufficient_data: int
    processed_at: datetime
    message: str

