"""Trend calculation service for chronological air quality analysis."""

import statistics
from datetime import UTC, datetime

from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import HistoryTrendResponse


class TrendService:
    """Analyzes direction and magnitude of air quality metric movements over time."""

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        """Ensure datetime has UTC timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @classmethod
    def _compute_time_halves(
        cls,
        sorted_readings: list,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> tuple[datetime, datetime, datetime, list, list]:
        """Determine time bounds, midpoint, and partition readings into chronological halves."""
        t_start = start_date or sorted_readings[0].measured_at
        t_end = end_date or sorted_readings[-1].measured_at
        if t_start.tzinfo is None:
            t_start = t_start.replace(tzinfo=UTC)
        if t_end.tzinfo is None:
            t_end = t_end.replace(tzinfo=UTC)
        midpoint = t_start + (t_end - t_start) / 2
        earlier = [r for r in sorted_readings if cls._as_utc(r.measured_at) < midpoint]
        later = [r for r in sorted_readings if cls._as_utc(r.measured_at) >= midpoint]
        return t_start, t_end, midpoint, earlier, later

    @staticmethod
    def _compute_delta(earlier_avg: float, later_avg: float, precision: int = 1) -> tuple[float, float | None]:
        """Compute absolute and percentage differences between period averages."""
        abs_change = round(later_avg - earlier_avg, precision)
        pct_change = round(((later_avg - earlier_avg) / earlier_avg) * 100.0, 1) if earlier_avg > 0 else None
        return abs_change, pct_change

    @staticmethod
    def _classify_aqi_trend(
        abs_change: float,
        pct_change: float | None,
        threshold: float,
        earlier_avg: float,
        later_avg: float,
    ) -> tuple[str, str]:
        """Classify AQI movement direction and build explanatory narrative."""
        if abs_change < -threshold:
            direction = "improving"
            expl = (
                f"Air quality improved by {abs(abs_change):.1f} AQI points ({abs(pct_change or 0.0):.1f}%), "
                f"moving from {earlier_avg:.1f} to {later_avg:.1f}."
            )
        elif abs_change > threshold:
            direction = "worsening"
            expl = (
                f"Air quality degraded by {abs_change:.1f} AQI points (+{pct_change or 0.0:.1f}%), "
                f"moving from {earlier_avg:.1f} to {later_avg:.1f}."
            )
        else:
            direction = "stable"
            expl = (
                f"Air quality remained stable within ±{threshold:.1f} threshold (net change: {abs_change:+.1f} points, "
                f"from {earlier_avg:.1f} to {later_avg:.1f})."
            )
        return direction, expl

    @staticmethod
    def _classify_pollutant_trend(
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
            direction = "improving"
            expl = (
                f"{pollutant_code} concentration decreased by {abs(abs_change):.2f} {unit} ({abs(pct_change or 0.0):.1f}%), "
                f"moving from {earlier_avg:.2f} to {later_avg:.2f} {unit}."
            )
        elif abs_change > threshold:
            direction = "worsening"
            expl = (
                f"{pollutant_code} concentration increased by {abs_change:.2f} {unit} (+{pct_change or 0.0:.1f}%), "
                f"moving from {earlier_avg:.2f} to {later_avg:.2f} {unit}."
            )
        else:
            direction = "stable"
            expl = (
                f"{pollutant_code} concentration remained stable within ±{threshold:.2f} {unit} threshold "
                f"(net change: {abs_change:+.2f} {unit})."
            )
        return direction, expl

    @staticmethod
    def _insufficient_total_response(
        total_records: int,
        min_records_per_period: int,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        pollutant: str | None,
        metric: str,
        unit: str,
        interval: str,
        threshold: float,
        methodology_doc: str,
    ) -> HistoryTrendResponse:
        """Construct response when overall record count is below threshold."""
        target_name = f" for {pollutant}" if pollutant else ""
        return HistoryTrendResponse(
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=pollutant,
            metric=metric,
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
            explanation=(
                f"Insufficient observations: {total_records} valid measurements found{target_name}, "
                f"at least {min_records_per_period * 2} required."
            ),
        )

    @staticmethod
    def _insufficient_halves_response(
        earlier_count: int,
        later_count: int,
        min_records_per_period: int,
        total_records: int,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        pollutant: str | None,
        metric: str,
        unit: str,
        interval: str,
        threshold: float,
        t_start: datetime,
        t_end: datetime,
        midpoint: datetime,
        earlier_values: list[float],
        later_values: list[float],
        methodology_doc: str,
        precision: int = 1,
    ) -> HistoryTrendResponse:
        """Construct response when one or both chronological halves have insufficient data."""
        earlier_avg = round(statistics.mean(earlier_values), precision) if earlier_values else None
        later_avg = round(statistics.mean(later_values), precision) if later_values else None
        target_name = f" for {pollutant}" if pollutant else ""
        return HistoryTrendResponse(
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=pollutant,
            metric=metric,
            unit=unit,
            interval=interval,
            threshold=threshold,
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
            methodology=methodology_doc,
            explanation=(
                f"Insufficient period balance{target_name}: earlier period has {earlier_count} records, "
                f"later has {later_count} records (minimum required: {min_records_per_period})."
            ),
        )

    @staticmethod
    def _pollutant_meta(readings: list[PollutantReading]) -> tuple[str, str]:
        """Extract pollutant code and measurement unit safely."""
        if not readings:
            return "Pollutant", "µg/m³"
        return readings[0].pollutant_code, readings[0].unit

    @staticmethod
    def _extract_aqi_values(readings: list[AQIReading]) -> list[float]:
        """Extract valid numerical AQI values."""
        vals: list[float] = []
        for r in readings:
            if r.aqi_value is not None and r.data_quality != "invalid":
                vals.append(r.aqi_value)
        return vals

    @staticmethod
    def _extract_pollutant_values(readings: list[PollutantReading]) -> list[float]:
        """Extract valid numerical pollutant concentrations."""
        vals: list[float] = []
        for r in readings:
            if r.concentration is not None and r.concentration >= 0:
                vals.append(r.concentration)
        return vals

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
            return cls._insufficient_total_response(
                total_records, min_records_per_period, city_name, station_id, station_name,
                None, "AQI", "AQI Index", interval, threshold, methodology_doc
            )

        sorted_readings = sorted(valid_readings, key=lambda r: r.measured_at)
        t_start, t_end, midpoint, earlier_readings, later_readings = cls._compute_time_halves(
            sorted_readings, start_date, end_date
        )
        earlier_vals = cls._extract_aqi_values(earlier_readings)
        later_vals = cls._extract_aqi_values(later_readings)
        earlier_count, later_count = len(earlier_vals), len(later_vals)

        if earlier_count < min_records_per_period or later_count < min_records_per_period:
            return cls._insufficient_halves_response(
                earlier_count, later_count, min_records_per_period, total_records,
                city_name, station_id, station_name, None, "AQI", "AQI Index", interval,
                threshold, t_start, t_end, midpoint, earlier_vals, later_vals, methodology_doc, precision=1
            )

        earlier_avg = round(statistics.mean(earlier_vals), 1)
        later_avg = round(statistics.mean(later_vals), 1)
        abs_change, pct_change = cls._compute_delta(earlier_avg, later_avg, precision=1)
        direction, expl = cls._classify_aqi_trend(abs_change, pct_change, threshold, earlier_avg, later_avg)

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
        valid_readings = [r for r in readings if r.concentration is not None and r.concentration >= 0]
        total_records = len(valid_readings)

        pollutant_code, unit = cls._pollutant_meta(readings)

        methodology_doc = (
            f"Dual-horizon comparative trend methodology for {pollutant_code}: Time window is split into two equal halves. "
            f"Average concentration is evaluated across each period. A minimum of {min_records_per_period} valid observations "
            f"per period is required. Trend is classified using a stability threshold of {threshold:.2f} {unit}: "
            f"'improving' (decrease > {threshold:.2f}), 'worsening' (increase > {threshold:.2f}), 'stable' "
            f"(movement within ±{threshold:.2f}), or 'insufficient_data'. Lower concentration indicates improved ambient quality."
        )

        if total_records < (min_records_per_period * 2):
            return cls._insufficient_total_response(
                total_records, min_records_per_period, city_name, station_id, station_name,
                pollutant_code, "Concentration", unit, interval, threshold, methodology_doc
            )

        sorted_readings = sorted(valid_readings, key=lambda r: r.measured_at)
        t_start, t_end, midpoint, earlier_readings, later_readings = cls._compute_time_halves(
            sorted_readings, start_date, end_date
        )
        earlier_vals = cls._extract_pollutant_values(earlier_readings)
        later_vals = cls._extract_pollutant_values(later_readings)
        earlier_count, later_count = len(earlier_vals), len(later_vals)

        if earlier_count < min_records_per_period or later_count < min_records_per_period:
            return cls._insufficient_halves_response(
                earlier_count, later_count, min_records_per_period, total_records,
                city_name, station_id, station_name, pollutant_code, "Concentration", unit, interval,
                threshold, t_start, t_end, midpoint, earlier_vals, later_vals, methodology_doc, precision=2
            )

        earlier_avg = round(statistics.mean(earlier_vals), 2)
        later_avg = round(statistics.mean(later_vals), 2)
        abs_change, pct_change = cls._compute_delta(earlier_avg, later_avg, precision=2)
        direction, expl = cls._classify_pollutant_trend(
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
