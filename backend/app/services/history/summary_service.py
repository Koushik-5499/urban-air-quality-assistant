"""Statistical summary and query filter helpers for HistoryService."""

import statistics
from collections import Counter
from datetime import datetime

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import AQISummaryResponse


def build_aqi_filters(
    city_entity: City | None,
    station_entity: MonitoringStation | None,
    include_simulated: bool,
    start_utc: datetime | None,
    end_utc: datetime | None,
) -> list:
    """Construct SQL filter clauses for AQI readings."""
    filters = []
    if city_entity:
        filters.append(AQIReading.city_id == city_entity.id)
    if station_entity:
        filters.append(AQIReading.station_id == station_entity.id)
    if not include_simulated:
        filters.append(AQIReading.is_simulated.is_(False))
    if start_utc:
        filters.append(AQIReading.measured_at >= start_utc)
    if end_utc:
        filters.append(AQIReading.measured_at <= end_utc)
    return filters


def build_pollutant_filters(
    city_entity: City | None,
    station_entity: MonitoringStation | None,
    pollutant_norm: str | None,
    include_simulated: bool,
    start_utc: datetime | None,
    end_utc: datetime | None,
) -> list:
    """Construct SQL filter clauses for pollutant concentration readings."""
    filters = []
    if city_entity:
        filters.append(PollutantReading.city_id == city_entity.id)
    if station_entity:
        filters.append(PollutantReading.station_id == station_entity.id)
    if pollutant_norm:
        filters.append(PollutantReading.pollutant_code == pollutant_norm)
    if not include_simulated:
        filters.append(PollutantReading.is_simulated.is_(False))
    if start_utc:
        filters.append(PollutantReading.measured_at >= start_utc)
    if end_utc:
        filters.append(PollutantReading.measured_at <= end_utc)
    return filters


def empty_summary_response(
    city_name: str | None,
    station_id: int | None,
    station_name: str | None,
    start_utc: datetime | None,
    end_utc: datetime | None,
) -> AQISummaryResponse:
    """Return zero-record default summary response."""
    return AQISummaryResponse(
        city=city_name,
        station_id=station_id,
        station_name=station_name,
        period_start=start_utc,
        period_end=end_utc,
        min_aqi=None,
        max_aqi=None,
        average_aqi=None,
        median_aqi=None,
        record_count=0,
        category_distribution={},
        dominant_pollutant_distribution={},
        data_quality="no_data",
    )


def calc_summary_distributions(
    valid_readings: list[AQIReading],
) -> tuple[dict[str, int], dict[str, int]]:
    """Calculate categorical and dominant pollutant distributions."""
    cat_counts = Counter(r.aqi_category for r in valid_readings if r.aqi_category)
    dominant_counts = Counter(
        r.dominant_pollutant for r in valid_readings if r.dominant_pollutant
    )
    return dict(cat_counts), dict(dominant_counts)


def compute_summary_stats(
    valid_readings: list[AQIReading],
    city_name: str | None,
    station_id: int | None,
    station_name: str | None,
    start_utc: datetime | None,
    end_utc: datetime | None,
) -> AQISummaryResponse:
    """Calculate statistical summaries for a non-empty set of valid AQI readings."""
    count = len(valid_readings)
    if count == 0:
        return empty_summary_response(
            city_name, station_id, station_name, start_utc, end_utc
        )

    values = [r.aqi_value for r in valid_readings if r.aqi_value is not None]
    avg_aqi = round(statistics.mean(values), 1)
    min_aqi = min(values)
    max_aqi = max(values)
    median_aqi = round(float(statistics.median(values)), 1)

    cat_dist, dom_dist = calc_summary_distributions(valid_readings)
    quality = "sufficient" if count >= 3 else "insufficient_data"

    return AQISummaryResponse(
        city=city_name,
        station_id=station_id,
        station_name=station_name,
        period_start=start_utc or valid_readings[0].measured_at,
        period_end=end_utc or valid_readings[-1].measured_at,
        min_aqi=min_aqi,
        max_aqi=max_aqi,
        average_aqi=avg_aqi,
        median_aqi=median_aqi,
        record_count=count,
        category_distribution=cat_dist,
        dominant_pollutant_distribution=dom_dist,
        data_quality=quality,
    )

