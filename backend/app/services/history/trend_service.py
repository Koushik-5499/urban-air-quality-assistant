"""Trend calculation service for chronological air quality analysis."""

from datetime import datetime, timedelta, timezone
import statistics
from typing import List, Optional, Tuple

from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import HistoryTrendResponse


class TrendService:
    """Analyzes direction and magnitude of air quality metric movements over time."""

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        """Ensure datetime has UTC timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @classmethod
    def calculate_aqi_trend(
        cls,
        readings: List[AQIReading],
        threshold: float = 5.0,
        min_records_per_period: int = 3,
        interval: str = "daily",
        city_name: Optional[str] = None,
        station_id: Optional[int] = None,
        station_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> HistoryTrendResponse:
        """Calculate trend for AQI readings by comparing earlier and later temporal halves."""
        valid_readings = [r for r in readings if r.aqi_value is not None and r.data_quality != "invalid"]
        total_records = len(valid_readings)

        methodology_doc = (
            f"Dual-horizon comparative trend methodology: The selected time range is split into two equal chronological "
            f"halves (earlier vs later). Average AQI is computed for each period. A minimum of {min_records_per_period} "
            f"valid observations per period is required. Trend is classified using a stability threshold of {threshold:.1f} "
            f"AQI points: 'improving' (decrease > {threshold:.1f}), 'worsening' (increase > {threshold:.1f}), 'stable' "
            f"(movement within ±{threshold:.1f}), or 'insufficient_data'."
        )

        if total_records < (min_records_per_period * 2):
            return HistoryTrendResponse(
                city=city_name,
                station_id=station_id,
                station_name=station_name,
                pollutant=None,
                metric="AQI",
                unit="AQI Index",
                interval=interval,
                threshold=threshold,
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
                methodology=methodology_doc,
                explanation=f"Insufficient observations: {total_records} valid records found, but at least {min_records_per_period * 2} are required ({min_records_per_period} per half).",
            )

        # Sort chronologically
        sorted_readings = sorted(valid_readings, key=lambda r: r.measured_at)
        t_start = start_date or sorted_readings[0].measured_at
        t_end = end_date or sorted_readings[-1].measured_at

        if t_start.tzinfo is None:
            t_start = t_start.replace(tzinfo=timezone.utc)
        if t_end.tzinfo is None:
            t_end = t_end.replace(tzinfo=timezone.utc)

        midpoint = t_start + (t_end - t_start) / 2

        earlier_readings = [r for r in sorted_readings if cls._as_utc(r.measured_at) < midpoint]
        later_readings = [r for r in sorted_readings if cls._as_utc(r.measured_at) >= midpoint]

        earlier_count = len(earlier_readings)
        later_count = len(later_readings)

        if earlier_count < min_records_per_period or later_count < min_records_per_period:
            return HistoryTrendResponse(
                city=city_name,
                station_id=station_id,
                station_name=station_name,
                pollutant=None,
                metric="AQI",
                unit="AQI Index",
                interval=interval,
                threshold=threshold,
                earlier_period_start=t_start,
                earlier_period_end=midpoint,
                later_period_start=midpoint,
                later_period_end=t_end,
                earlier_average=round(statistics.mean([r.aqi_value for r in earlier_readings]), 1) if earlier_readings else None,
                later_average=round(statistics.mean([r.aqi_value for r in later_readings]), 1) if later_readings else None,
                absolute_change=None,
                percentage_change=None,
                trend_direction="insufficient_data",
                earlier_record_count=earlier_count,
                later_record_count=later_count,
                total_records=total_records,
                methodology=methodology_doc,
                explanation=f"Insufficient period balance: earlier period has {earlier_count} records, later period has {later_count} records (minimum required: {min_records_per_period} per period).",
            )

        earlier_avg = round(statistics.mean([r.aqi_value for r in earlier_readings]), 1)
        later_avg = round(statistics.mean([r.aqi_value for r in later_readings]), 1)
        abs_change = round(later_avg - earlier_avg, 1)

        pct_change: Optional[float] = None
        if earlier_avg > 0:
            pct_change = round(((later_avg - earlier_avg) / earlier_avg) * 100.0, 1)

        # Classification for AQI: lower is better!
        if abs_change < -threshold:
            direction = "improving"
            expl = f"Air quality improved by {abs(abs_change):.1f} AQI points ({abs(pct_change or 0.0):.1f}%), moving from {earlier_avg:.1f} to {later_avg:.1f}."
        elif abs_change > threshold:
            direction = "worsening"
            expl = f"Air quality degraded by {abs_change:.1f} AQI points (+{pct_change or 0.0:.1f}%), moving from {earlier_avg:.1f} to {later_avg:.1f}."
        else:
            direction = "stable"
            expl = f"Air quality remained stable within ±{threshold:.1f} threshold (net change: {abs_change:+.1f} points, from {earlier_avg:.1f} to {later_avg:.1f})."

        return HistoryTrendResponse(
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=None,
            metric="AQI",
            unit="AQI Index",
            interval=interval,
            threshold=threshold,
            earlier_period_start=t_start,
            earlier_period_end=midpoint,
            later_period_start=midpoint,
            later_period_end=t_end,
            earlier_average=earlier_avg,
            later_average=later_avg,
            absolute_change=abs_change,
            percentage_change=pct_change,
            trend_direction=direction,
            earlier_record_count=earlier_count,
            later_record_count=later_count,
            total_records=total_records,
            methodology=methodology_doc,
            explanation=expl,
        )

    @classmethod
    def calculate_pollutant_trend(
        cls,
        readings: List[PollutantReading],
        threshold: float = 2.0,
        min_records_per_period: int = 3,
        interval: str = "daily",
        city_name: Optional[str] = None,
        station_id: Optional[int] = None,
        station_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> HistoryTrendResponse:
        """Calculate trend for a specific pollutant concentration."""
        valid_readings = [r for r in readings if r.concentration is not None and r.concentration >= 0]
        total_records = len(valid_readings)

        pollutant_code = readings[0].pollutant_code if readings else "Pollutant"
        unit = readings[0].unit if readings else "µg/m³"

        methodology_doc = (
            f"Dual-horizon comparative trend methodology for {pollutant_code}: Time window is split into two equal halves. "
            f"Average concentration is evaluated across each period. A minimum of {min_records_per_period} valid observations "
            f"per period is required. Trend is classified using a stability threshold of {threshold:.2f} {unit}: "
            f"'improving' (decrease > {threshold:.2f}), 'worsening' (increase > {threshold:.2f}), 'stable' "
            f"(movement within ±{threshold:.2f}), or 'insufficient_data'. Lower concentration indicates improved ambient quality."
        )

        if total_records < (min_records_per_period * 2):
            return HistoryTrendResponse(
                city=city_name,
                station_id=station_id,
                station_name=station_name,
                pollutant=pollutant_code,
                metric="Concentration",
                unit=unit,
                interval=interval,
                threshold=threshold,
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
                methodology=methodology_doc,
                explanation=f"Insufficient observations: {total_records} valid measurements found for {pollutant_code}, at least {min_records_per_period * 2} required.",
            )

        sorted_readings = sorted(valid_readings, key=lambda r: r.measured_at)
        t_start = start_date or sorted_readings[0].measured_at
        t_end = end_date or sorted_readings[-1].measured_at

        if t_start.tzinfo is None:
            t_start = t_start.replace(tzinfo=timezone.utc)
        if t_end.tzinfo is None:
            t_end = t_end.replace(tzinfo=timezone.utc)

        midpoint = t_start + (t_end - t_start) / 2

        earlier_readings = [r for r in sorted_readings if cls._as_utc(r.measured_at) < midpoint]
        later_readings = [r for r in sorted_readings if cls._as_utc(r.measured_at) >= midpoint]

        earlier_count = len(earlier_readings)
        later_count = len(later_readings)

        if earlier_count < min_records_per_period or later_count < min_records_per_period:
            return HistoryTrendResponse(
                city=city_name,
                station_id=station_id,
                station_name=station_name,
                pollutant=pollutant_code,
                metric="Concentration",
                unit=unit,
                interval=interval,
                threshold=threshold,
                earlier_period_start=t_start,
                earlier_period_end=midpoint,
                later_period_start=midpoint,
                later_period_end=t_end,
                earlier_average=round(statistics.mean([r.concentration for r in earlier_readings]), 2) if earlier_readings else None,
                later_average=round(statistics.mean([r.concentration for r in later_readings]), 2) if later_readings else None,
                absolute_change=None,
                percentage_change=None,
                trend_direction="insufficient_data",
                earlier_record_count=earlier_count,
                later_record_count=later_count,
                total_records=total_records,
                methodology=methodology_doc,
                explanation=f"Insufficient period balance for {pollutant_code}: earlier period has {earlier_count} records, later has {later_count} records (minimum required: {min_records_per_period}).",
            )

        earlier_avg = round(statistics.mean([r.concentration for r in earlier_readings]), 2)
        later_avg = round(statistics.mean([r.concentration for r in later_readings]), 2)
        abs_change = round(later_avg - earlier_avg, 2)

        pct_change: Optional[float] = None
        if earlier_avg > 0:
            pct_change = round(((later_avg - earlier_avg) / earlier_avg) * 100.0, 1)

        # For pollutants, lower concentration is an improvement
        if abs_change < -threshold:
            direction = "improving"
            expl = f"{pollutant_code} concentration decreased by {abs(abs_change):.2f} {unit} ({abs(pct_change or 0.0):.1f}%), moving from {earlier_avg:.2f} to {later_avg:.2f} {unit}."
        elif abs_change > threshold:
            direction = "worsening"
            expl = f"{pollutant_code} concentration increased by {abs_change:.2f} {unit} (+{pct_change or 0.0:.1f}%), moving from {earlier_avg:.2f} to {later_avg:.2f} {unit}."
        else:
            direction = "stable"
            expl = f"{pollutant_code} concentration remained stable within ±{threshold:.2f} {unit} threshold (net change: {abs_change:+.2f} {unit})."

        return HistoryTrendResponse(
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=pollutant_code,
            metric="Concentration",
            unit=unit,
            interval=interval,
            threshold=threshold,
            earlier_period_start=t_start,
            earlier_period_end=midpoint,
            later_period_start=midpoint,
            later_period_end=t_end,
            earlier_average=earlier_avg,
            later_average=later_avg,
            absolute_change=abs_change,
            percentage_change=pct_change,
            trend_direction=direction,
            earlier_record_count=earlier_count,
            later_record_count=later_count,
            total_records=total_records,
            methodology=methodology_doc,
            explanation=expl,
        )
