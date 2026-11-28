"""Trend calculation service for chronological air quality analysis."""

import statistics
from datetime import datetime

from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import HistoryTrendResponse
from app.services.history.trend_helpers import (
    TrendMetadata,
    as_utc,
    build_insufficient_halves_response,
    build_insufficient_total_response,
    classify_aqi_trend,
    classify_pollutant_trend,
    compute_delta,
    compute_time_halves,
)


class TrendService:
    """Analyzes direction and magnitude of air quality metric movements over time."""

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        """Ensure datetime has UTC timezone."""
        return as_utc(dt)

    @staticmethod
    def _pollutant_meta(readings: list[PollutantReading]) -> tuple[str, str]:
        """Extract pollutant code and measurement unit safely."""
        if not readings:
            return "Pollutant", "µg/m³"
        return readings[0].pollutant_code, readings[0].unit

    @staticmethod
    def _extract_aqi_values(readings: list[AQIReading]) -> list[float]:
        """Extract valid numerical AQI values."""
        return [
            float(r.aqi_value)
            for r in readings
            if r.aqi_value is not None and r.data_quality != "invalid"
        ]

    @staticmethod
    def _extract_pollutant_values(readings: list[PollutantReading]) -> list[float]:
        """Extract valid numerical pollutant concentrations."""
        return [
            float(r.concentration)
            for r in readings
            if r.concentration is not None and r.concentration >= 0
        ]

    @classmethod
    def calculate_aqi_trend(
        cls,
        readings: list[AQIReading],
        threshold: float = 5.0,
        min_records_per_period: int = 3,
        interval: str = "daily",
        city_name: str | None = None,
        station_id: int | None = None,
        station_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> HistoryTrendResponse:
        """Calculate trend for AQI readings by comparing earlier and later temporal halves."""
        valid_readings = [
            r for r in readings if r.aqi_value is not None and r.data_quality != "invalid"
        ]
        total_records = len(valid_readings)
        methodology_doc = (
            f"Dual-horizon comparative trend methodology: The selected time range is split "
            f"into two equal chronological halves (earlier vs later). Average AQI is computed "
            f"for each period. A minimum of {min_records_per_period} valid observations "
            f"per period is required. Trend is classified using a stability threshold "
            f"of {threshold:.1f} AQI points: 'improving' (decrease > {threshold:.1f}), "
            f"'worsening' (increase > {threshold:.1f}), "
            f"'stable' (movement within ±{threshold:.1f}), or 'insufficient_data'."
        )
        meta = TrendMetadata(
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=None,
            metric="AQI",
            unit="AQI Index",
            interval=interval,
            threshold=threshold,
            methodology_doc=methodology_doc,
        )

        if total_records < (min_records_per_period * 2):
            return build_insufficient_total_response(meta, total_records, min_records_per_period)

        sorted_readings = sorted(valid_readings, key=lambda r: r.measured_at)
        t_start, t_end, midpoint, earlier_readings, later_readings = compute_time_halves(
            sorted_readings, start_date, end_date
        )
        earlier_vals = cls._extract_aqi_values(earlier_readings)
        later_vals = cls._extract_aqi_values(later_readings)
        earlier_count, later_count = len(earlier_vals), len(later_vals)

        if earlier_count < min_records_per_period or later_count < min_records_per_period:
            return build_insufficient_halves_response(
                meta, earlier_count, later_count, min_records_per_period,
                total_records, t_start, t_end, midpoint, earlier_vals, later_vals, precision=1,
            )

        earlier_avg = round(statistics.mean(earlier_vals), 1)
        later_avg = round(statistics.mean(later_vals), 1)
        abs_change, pct_change = compute_delta(earlier_avg, later_avg, precision=1)
        direction, expl = classify_aqi_trend(
            abs_change, pct_change, threshold, earlier_avg, later_avg
        )

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
        readings: list[PollutantReading],
        threshold: float = 2.0,
        min_records_per_period: int = 3,
        interval: str = "daily",
        city_name: str | None = None,
        station_id: int | None = None,
        station_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> HistoryTrendResponse:
        """Calculate trend for a specific pollutant concentration."""
        valid_readings = [
            r for r in readings if r.concentration is not None and r.concentration >= 0
        ]
        total_records = len(valid_readings)
        pollutant_code, unit = cls._pollutant_meta(readings)

        methodology_doc = (
            f"Dual-horizon comparative trend methodology for {pollutant_code}: Time window is "
            f"split into two equal halves. Average concentration is evaluated across each period. "
            f"A minimum of {min_records_per_period} valid observations per period is required. "
            f"Trend is classified using a stability threshold of {threshold:.2f} {unit}: "
            f"'improving' (decrease > {threshold:.2f}), 'worsening' (increase > {threshold:.2f}), "
            f"'stable' (movement within ±{threshold:.2f}), or 'insufficient_data'. "
            f"Lower concentration indicates improved ambient quality."
        )
        meta = TrendMetadata(
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=pollutant_code,
            metric="Concentration",
            unit=unit,
            interval=interval,
            threshold=threshold,
            methodology_doc=methodology_doc,
        )

        if total_records < (min_records_per_period * 2):
            return build_insufficient_total_response(meta, total_records, min_records_per_period)

        sorted_readings = sorted(valid_readings, key=lambda r: r.measured_at)
        t_start, t_end, midpoint, earlier_readings, later_readings = compute_time_halves(
            sorted_readings, start_date, end_date
        )
        earlier_vals = cls._extract_pollutant_values(earlier_readings)
        later_vals = cls._extract_pollutant_values(later_readings)
        earlier_count, later_count = len(earlier_vals), len(later_vals)

        if earlier_count < min_records_per_period or later_count < min_records_per_period:
            return build_insufficient_halves_response(
                meta, earlier_count, later_count, min_records_per_period,
                total_records, t_start, t_end, midpoint, earlier_vals, later_vals, precision=2,
            )

        earlier_avg = round(statistics.mean(earlier_vals), 2)
        later_avg = round(statistics.mean(later_vals), 2)
        abs_change, pct_change = compute_delta(earlier_avg, later_avg, precision=2)
        direction, expl = classify_pollutant_trend(
            abs_change, pct_change, threshold, earlier_avg, later_avg, pollutant_code, unit
        )

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
