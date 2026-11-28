"""Helper functions and parameter objects for chronological air quality trend analysis."""

import statistics
from dataclasses import dataclass
from datetime import UTC, datetime

from app.schemas.history import HistoryTrendResponse


@dataclass(frozen=True, slots=True)
class TrendMetadata:
    """Shared contextual metadata describing a trend analysis query."""

    city_name: str | None
    station_id: int | None
    station_name: str | None
    pollutant: str | None
    metric: str
    unit: str
    interval: str
    threshold: float
    methodology_doc: str


def as_utc(dt: datetime) -> datetime:
    """Ensure datetime carries UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def compute_time_halves(
    sorted_readings: list,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime, datetime, list, list]:
    """Determine time bounds, midpoint, and partition readings into chronological halves."""
    t_start = as_utc(start_date or sorted_readings[0].measured_at)
    t_end = as_utc(end_date or sorted_readings[-1].measured_at)
    midpoint = t_start + (t_end - t_start) / 2
    earlier = [r for r in sorted_readings if as_utc(r.measured_at) < midpoint]
    later = [r for r in sorted_readings if as_utc(r.measured_at) >= midpoint]
    return t_start, t_end, midpoint, earlier, later


def compute_delta(
    earlier_avg: float, later_avg: float, precision: int = 1
) -> tuple[float, float | None]:
    """Compute absolute and percentage differences between period averages."""
    abs_change = round(later_avg - earlier_avg, precision)
    pct_change = (
        round(((later_avg - earlier_avg) / earlier_avg) * 100.0, 1) if earlier_avg > 0 else None
    )
    return abs_change, pct_change


def classify_aqi_trend(
    abs_change: float,
    pct_change: float | None,
    threshold: float,
    earlier_avg: float,
    later_avg: float,
) -> tuple[str, str]:
    """Classify AQI movement direction and build explanatory narrative."""
    if abs_change < -threshold:
        return (
            "improving",
            f"Air quality improved by {abs(abs_change):.1f} AQI points "
            f"({abs(pct_change or 0.0):.1f}%), "
            f"moving from {earlier_avg:.1f} to {later_avg:.1f}.",
        )
    if abs_change > threshold:
        return (
            "worsening",
            f"Air quality degraded by {abs_change:.1f} AQI points (+{pct_change or 0.0:.1f}%), "
            f"moving from {earlier_avg:.1f} to {later_avg:.1f}.",
        )
    return (
        "stable",
        f"Air quality remained stable within ±{threshold:.1f} threshold "
        f"(net change: {abs_change:+.1f} points, "
        f"from {earlier_avg:.1f} to {later_avg:.1f}).",
    )


def classify_pollutant_trend(
    abs_change: float,
    pct_change: float | None,
    threshold: float,
    earlier_avg: float,
    later_avg: float,
    pollutant_code: str,
    unit: str,
) -> tuple[str, str]:
    """Classify pollutant concentration movement direction and build explanatory narrative."""
    if abs_change < -threshold:
        return (
            "improving",
            f"{pollutant_code} concentration decreased by {abs(abs_change):.2f} "
            f"{unit} ({abs(pct_change or 0.0):.1f}%), "
            f"moving from {earlier_avg:.2f} to {later_avg:.2f} {unit}.",
        )
    if abs_change > threshold:
        return (
            "worsening",
            f"{pollutant_code} concentration increased by {abs_change:.2f} "
            f"{unit} (+{pct_change or 0.0:.1f}%), "
            f"moving from {earlier_avg:.2f} to {later_avg:.2f} {unit}.",
        )
    return (
        "stable",
        f"{pollutant_code} concentration remained stable within "
        f"±{threshold:.2f} {unit} threshold "
        f"(net change: {abs_change:+.2f} {unit}).",
    )


def build_insufficient_total_response(
    meta: TrendMetadata,
    total_records: int,
    min_records_per_period: int,
) -> HistoryTrendResponse:
    """Construct response when overall record count is below minimum threshold."""
    target_name = f" for {meta.pollutant}" if meta.pollutant else ""
    return HistoryTrendResponse(
        city=meta.city_name,
        station_id=meta.station_id,
        station_name=meta.station_name,
        pollutant=meta.pollutant,
        metric=meta.metric,
        unit=meta.unit,
        interval=meta.interval,
        threshold=meta.threshold,
        earlier_period_start=None,
        earlier_period_end=None,
        later_period_start=None,
        later_period_end=None,
        earlier_average=None,
        later_average=None,
        absolute_change=None,
        percentage_change=None,
        trend_direction="insufficient_data",
        earlier_record_count=0,
        later_record_count=0,
        total_records=total_records,
        methodology=meta.methodology_doc,
        explanation=(
            f"Insufficient observations: {total_records} valid measurements "
            f"found{target_name}, "
            f"at least {min_records_per_period * 2} required."
        ),
    )


def build_insufficient_halves_response(
    meta: TrendMetadata,
    earlier_count: int,
    later_count: int,
    min_records_per_period: int,
    total_records: int,
    t_start: datetime,
    t_end: datetime,
    midpoint: datetime,
    earlier_values: list[float],
    later_values: list[float],
    precision: int = 1,
) -> HistoryTrendResponse:
    """Construct response when one or both chronological halves lack enough records."""
    earlier_avg = round(statistics.mean(earlier_values), precision) if earlier_values else None
    later_avg = round(statistics.mean(later_values), precision) if later_values else None
    target_name = f" for {meta.pollutant}" if meta.pollutant else ""
    return HistoryTrendResponse(
        city=meta.city_name,
        station_id=meta.station_id,
        station_name=meta.station_name,
        pollutant=meta.pollutant,
        metric=meta.metric,
        unit=meta.unit,
        interval=meta.interval,
        threshold=meta.threshold,
        earlier_period_start=t_start,
        earlier_period_end=midpoint,
        later_period_start=midpoint,
        later_period_end=t_end,
        earlier_average=earlier_avg,
        later_average=later_avg,
        absolute_change=None,
        percentage_change=None,
        trend_direction="insufficient_data",
        earlier_record_count=earlier_count,
        later_record_count=later_count,
        total_records=total_records,
        methodology=meta.methodology_doc,
        explanation=(
            f"Insufficient period balance{target_name}: earlier period has "
            f"{earlier_count} records, "
            f"later has {later_count} records (minimum required: {min_records_per_period})."
        ),
    )

