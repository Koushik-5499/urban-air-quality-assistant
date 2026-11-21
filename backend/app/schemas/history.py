"""Pydantic schemas for historical air quality data, aggregations, summaries, and trends."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AQIHistoryRecord(BaseModel):
    """Schema representing either a single point-in-time or aggregated historical AQI reading."""

    # Raw observation attributes (optional in aggregated mode)
    id: int | None = Field(None, description="Record ID (raw observations only)")
    measured_at: datetime | None = Field(None, description="Exact observation measurement timestamp in UTC")
    created_at: datetime | None = Field(None, description="Ingestion timestamp in UTC")
    aqi_value: int | None = Field(None, description="AQI numerical index (0-500)")
    aqi_category: str | None = Field(None, description="CPCB NAQI Category")

    # Aggregated bucket attributes (optional in raw mode)
    period_start: datetime | None = Field(None, description="Aggregation window start in UTC")
    period_end: datetime | None = Field(None, description="Aggregation window end in UTC")
    interval: str | None = Field(None, description="Aggregation interval (hourly, daily, weekly, monthly)")
    average_aqi: float | None = Field(None, description="Mean AQI over aggregation period")
    min_aqi: int | None = Field(None, description="Minimum AQI recorded in period")
    max_aqi: int | None = Field(None, description="Maximum AQI recorded in period")
    median_aqi: float | None = Field(None, description="Median AQI recorded in period")
    record_count: int | None = Field(None, description="Number of valid observations aggregated")
    dominant_category: str | None = Field(None, description="Most frequent NAQI category in bucket")
    category_distribution: dict[str, int] | None = Field(None, description="Frequency count of NAQI categories")

    # Common location and metadata attributes
    dominant_pollutant: str | None = Field(None, description="Primary pollutant driving the index")
    source: str = Field(default="CPCB", description="Data provider or source")
    is_simulated: bool = Field(default=False, description="Whether reading is simulated or observed")
    data_quality: str = Field(default="valid", description="Data quality or sufficiency status")
    city_name: str | None = Field(None, description="Associated city name")
    station_id: int | None = Field(None, description="Monitoring station ID")
    station_name: str | None = Field(None, description="Monitoring station name")

    model_config = ConfigDict(from_attributes=True)


class AQIHistoryResponse(BaseModel):
    """Paginated historical AQI query response."""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Page size limit")
    total_records: int = Field(..., ge=0, description="Total matching records count")
    total_pages: int = Field(..., ge=0, description="Total available pages")
    city: str | None = Field(None, description="Filtered city name")
    station_id: int | None = Field(None, description="Filtered station ID")
    station_name: str | None = Field(None, description="Filtered station name")
    interval: str | None = Field(None, description="Aggregation interval applied, or null for raw")
    period_start: datetime | None = Field(None, description="Requested start timestamp")
    period_end: datetime | None = Field(None, description="Requested end timestamp")
    records: list[AQIHistoryRecord] = Field(default_factory=list, description="Historical AQI records")


class PollutantHistoryRecord(BaseModel):
    """Schema representing either a raw pollutant observation or an aggregated bucket."""

    # Raw observation attributes
    id: int | None = Field(None, description="Record ID")
    pollutant_code: str = Field(..., description="Pollutant code (PM2.5, PM10, NO2, SO2, CO, O3, NH3, Pb)")
    concentration: float | None = Field(None, description="Measured concentration value")
    unit: str = Field(..., description="Measurement unit (e.g. µg/m³ or mg/m³)")
    sub_index: int | None = Field(None, description="Reproducibly calculated CPCB NAQI sub-index")
    sub_index_category: str | None = Field(None, description="CPCB category for sub-index")
    measured_at: datetime | None = Field(None, description="Observation timestamp in UTC")
    created_at: datetime | None = Field(None, description="Ingestion timestamp in UTC")

    # Aggregated bucket attributes
    period_start: datetime | None = Field(None, description="Aggregation window start in UTC")
    period_end: datetime | None = Field(None, description="Aggregation window end in UTC")
    interval: str | None = Field(None, description="Aggregation interval (hourly, daily, weekly, monthly)")
    average: float | None = Field(None, description="Average concentration over period")
    minimum: float | None = Field(None, description="Minimum concentration over period")
    maximum: float | None = Field(None, description="Maximum concentration over period")
    median: float | None = Field(None, description="Median concentration over period")
    record_count: int | None = Field(None, description="Number of valid measurements aggregated")

    # Common attributes
    source: str = Field(default="CPCB", description="Data source")
    is_simulated: bool = Field(default=False, description="Whether measurement is simulated")
    data_quality: str = Field(default="valid", description="Quality flag")
    city_name: str | None = Field(None, description="City name")
    station_id: int | None = Field(None, description="Station ID")
    station_name: str | None = Field(None, description="Station name")

    model_config = ConfigDict(from_attributes=True)


class PollutantHistoryResponse(BaseModel):
    """Paginated historical pollutant concentration response."""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Page size limit")
    total_records: int = Field(..., ge=0, description="Total matching records count")
    total_pages: int = Field(..., ge=0, description="Total available pages")
    city: str | None = Field(None, description="Filtered city name")
    station_id: int | None = Field(None, description="Filtered station ID")
    station_name: str | None = Field(None, description="Filtered station name")
    pollutant: str | None = Field(None, description="Filtered pollutant code")
    unit: str | None = Field(None, description="Standard pollutant unit")
    interval: str | None = Field(None, description="Aggregation interval applied")
    period_start: datetime | None = Field(None, description="Requested start timestamp")
    period_end: datetime | None = Field(None, description="Requested end timestamp")
    records: list[PollutantHistoryRecord] = Field(default_factory=list, description="Historical pollutant records")


class AQISummaryResponse(BaseModel):
    """Statistical summary of historical AQI records."""

    city: str | None = Field(None, description="City name")
    station_id: int | None = Field(None, description="Station ID")
    station_name: str | None = Field(None, description="Station name")
    period_start: datetime | None = Field(None, description="Effective start timestamp")
    period_end: datetime | None = Field(None, description="Effective end timestamp")
    min_aqi: int | None = Field(None, description="Lowest recorded valid AQI")
    max_aqi: int | None = Field(None, description="Highest recorded valid AQI")
    average_aqi: float | None = Field(None, description="Mean AQI rounded to 1 decimal place")
    median_aqi: float | None = Field(None, description="Median AQI value")
    record_count: int = Field(..., ge=0, description="Number of valid records evaluated")
    category_distribution: dict[str, int] = Field(default_factory=dict, description="Count of readings per NAQI category")
    dominant_pollutant_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of readings per dominant pollutant"
    )
    data_quality: str = Field(..., description="Overall data quality flag ('sufficient', 'insufficient_data', 'no_data')")


class HistoryTrendResponse(BaseModel):
    """Historical trend analysis comparing consecutive time horizons."""

    city: str | None = Field(None, description="City name")
    station_id: int | None = Field(None, description="Station ID")
    station_name: str | None = Field(None, description="Station name")
    pollutant: str | None = Field(None, description="Evaluated pollutant, or null for AQI")
    metric: str = Field(..., description="Target evaluated metric ('AQI' or 'Concentration')")
    unit: str = Field(..., description="Unit of measurement ('AQI Index', 'µg/m³', 'mg/m³')")
    interval: str = Field(..., description="Granularity interval used ('daily', 'weekly', 'monthly')")
    threshold: float = Field(..., description="Stability threshold value")
    earlier_period_start: datetime | None = Field(None, description="Earlier comparison period start")
    earlier_period_end: datetime | None = Field(None, description="Earlier comparison period end")
    later_period_start: datetime | None = Field(None, description="Later comparison period start")
    later_period_end: datetime | None = Field(None, description="Later comparison period end")
    earlier_average: float | None = Field(None, description="Average metric value in earlier period")
    later_average: float | None = Field(None, description="Average metric value in later period")
    absolute_change: float | None = Field(None, description="later_average - earlier_average")
    percentage_change: float | None = Field(None, description="Percentage change if mathematically valid")
    trend_direction: str = Field(
        ...,
        description="Trend classification: 'improving', 'worsening', 'stable', 'insufficient_data'",
    )
    earlier_record_count: int = Field(..., ge=0, description="Number of valid records in earlier period")
    later_record_count: int = Field(..., ge=0, description="Number of valid records in later period")
    total_records: int = Field(..., ge=0, description="Total valid records evaluated")
    methodology: str = Field(..., description="Explanation of trend classification algorithm")
    explanation: str = Field(..., description="Human-readable contextual summary of the trend outcome")


class LocationComparisonItem(BaseModel):
    """Comparable environmental metrics for an individual location."""

    location_type: str = Field(..., description="Location level: 'city' or 'station'")
    city_name: str = Field(..., description="City name")
    station_id: int | None = Field(None, description="Station ID if comparing stations")
    station_name: str | None = Field(None, description="Station name if comparing stations")
    average_aqi: float | None = Field(None, description="Mean AQI")
    min_aqi: int | None = Field(None, description="Minimum AQI")
    max_aqi: int | None = Field(None, description="Maximum AQI")
    median_aqi: float | None = Field(None, description="Median AQI")
    record_count: int = Field(..., ge=0, description="Number of valid records analyzed")
    category_distribution: dict[str, int] = Field(default_factory=dict, description="Category distribution breakdown")
    dominant_pollutant_distribution: dict[str, int] = Field(
        default_factory=dict, description="Dominant pollutant distribution breakdown"
    )
    data_quality: str = Field(..., description="Data quality status ('sufficient', 'insufficient_data', 'no_data')")


class HistoryCompareResponse(BaseModel):
    """Multi-location comparative evaluation across identical time horizons."""

    period_start: datetime | None = Field(None, description="Comparison window start in UTC")
    period_end: datetime | None = Field(None, description="Comparison window end in UTC")
    location_count: int = Field(..., ge=0, description="Number of compared locations")
    comparisons: list[LocationComparisonItem] = Field(default_factory=list, description="Metrics per location")

