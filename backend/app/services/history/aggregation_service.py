"""Temporal aggregation service for historical AQI and pollutant records."""

import statistics
from collections import Counter
from datetime import UTC, datetime, timedelta

from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import AQIHistoryRecord, PollutantHistoryRecord
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.categories import get_aqi_category


class AggregationService:
    """Provides safe, timezone-consistent chronological bucketing and aggregation."""

    @staticmethod
    def get_bucket_window(dt: datetime, interval: str) -> tuple[datetime, datetime]:
        """Compute the [start, end) UTC window for a given timestamp and interval.

        - Hourly: Floor to UTC hour.
        - Daily: Floor to UTC day (00:00:00 UTC).
        - Weekly: Floor to ISO week start (Monday 00:00:00 UTC).
        - Monthly: Floor to calendar month (1st of month 00:00:00 UTC).
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)

        if interval == "hourly":
            start = dt.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif interval == "daily":
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif interval == "weekly":
            # ISO week starts on Monday (weekday() == 0)
            monday_offset = timedelta(days=dt.weekday())
            start = (dt - monday_offset).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif interval == "monthly":
            start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:
            # Fallback to daily
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)

        return start, end

    @classmethod
    def _group_by_bucket(cls, readings: list, interval: str) -> dict[datetime, list]:
        """Sort chronologically and group readings into bucket windows."""
        sorted_readings = sorted(readings, key=lambda r: r.measured_at)
        buckets: dict[datetime, list] = {}
        for r in sorted_readings:
            start_window, _ = cls.get_bucket_window(r.measured_at, interval)
            if start_window not in buckets:
                buckets[start_window] = []
            buckets[start_window].append(r)
        return buckets

    @staticmethod
    def _extract_dominant_meta(valid_items: list[AQIReading]) -> tuple[str | None, dict[str, int], str | None]:
        """Extract dominant category, category distribution, and dominant pollutant."""
        cat_counts: Counter[str] = Counter(r.aqi_category for r in valid_items if r.aqi_category)
        dominant_category = cat_counts.most_common(1)[0][0] if cat_counts else None

        pollutant_candidates = [r.dominant_pollutant for r in valid_items if r.dominant_pollutant]
        dominant_pollutant = Counter(pollutant_candidates).most_common(1)[0][0] if pollutant_candidates else None
        return dominant_category, dict(cat_counts), dominant_pollutant

    @staticmethod
    def _resolve_source_and_city(
        valid_items: list,
        city_name: str | None,
    ) -> tuple[str, bool, str | None]:
        """Resolve reporting source, simulation flag, and fallback city name."""
        is_sim = any(r.is_simulated for r in valid_items)
        first_item = valid_items[0] if valid_items else None
        source = first_item.source if first_item else "CPCB"
        resolved_city = city_name
        if not resolved_city and first_item and getattr(first_item, "city", None):
            resolved_city = first_item.city.name
        return source, is_sim, resolved_city

    @classmethod
    def _aggregate_single_aqi_bucket(
        cls,
        window_start: datetime,
        bucket_items: list[AQIReading],
        interval: str,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
    ) -> AQIHistoryRecord | None:
        """Compute statistics and categorical summary for a single AQI time bucket."""
        valid_items = [r for r in bucket_items if r.aqi_value is not None and r.data_quality != "invalid"]
        if not valid_items:
            return None

        values = [r.aqi_value for r in valid_items if r.aqi_value is not None]
        avg_val = round(statistics.mean(values), 1)
        min_val = min(values)
        max_val = max(values)
        median_val = round(float(statistics.median(values)), 1)
        count = len(values)

        dominant_cat, cat_dist, dominant_pol = cls._extract_dominant_meta(valid_items)
        source, is_sim, resolved_city = cls._resolve_source_and_city(valid_items, city_name)
        _, window_end = cls.get_bucket_window(window_start, interval)

        return AQIHistoryRecord(
            period_start=window_start,
            period_end=window_end,
            interval=interval,
            average_aqi=avg_val,
            min_aqi=min_val,
            max_aqi=max_val,
            median_aqi=median_val,
            record_count=count,
            dominant_category=dominant_cat,
            category_distribution=cat_dist,
            dominant_pollutant=dominant_pol,
            source=source,
            is_simulated=is_sim,
            data_quality="valid" if count > 0 else "insufficient_data",
            city_name=resolved_city,
            station_id=station_id,
            station_name=station_name,
        )

    @classmethod
    def aggregate_aqi_readings(
        cls,
        readings: list[AQIReading],
        interval: str,
        city_name: str | None = None,
        station_id: int | None = None,
        station_name: str | None = None,
    ) -> list[AQIHistoryRecord]:
        """Group and aggregate AQI readings into chronological buckets without fabricating missing data."""
        if not readings:
            return []

        buckets = cls._group_by_bucket(readings, interval)
        aggregated_records: list[AQIHistoryRecord] = []

        for window_start in sorted(buckets.keys()):
            rec = cls._aggregate_single_aqi_bucket(
                window_start, buckets[window_start], interval, city_name, station_id, station_name
            )
            if rec:
                aggregated_records.append(rec)

        return aggregated_records

    @classmethod
    def _aggregate_single_pollutant_bucket(
        cls,
        window_start: datetime,
        bucket_items: list[PollutantReading],
        interval: str,
        pollutant_code: str,
        unit: str,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
    ) -> PollutantHistoryRecord | None:
        """Compute statistics and sub-index for a single pollutant time bucket."""
        valid_items = [r for r in bucket_items if r.concentration is not None and r.concentration >= 0]
        if not valid_items:
            return None

        values = [r.concentration for r in valid_items if r.concentration is not None]
        avg_val = round(statistics.mean(values), 2)
        min_val = round(min(values), 2)
        max_val = round(max(values), 2)
        median_val = round(float(statistics.median(values)), 2)
        count = len(values)

        sub_index = AQICalculator.calculate_sub_index(pollutant_code, avg_val, unit)
        sub_cat = get_aqi_category(sub_index) if sub_index is not None else None

        source, is_sim, resolved_city = cls._resolve_source_and_city(valid_items, city_name)
        _, window_end = cls.get_bucket_window(window_start, interval)

        return PollutantHistoryRecord(
            period_start=window_start,
            period_end=window_end,
            interval=interval,
            pollutant_code=pollutant_code,
            unit=unit,
            average=avg_val,
            minimum=min_val,
            maximum=max_val,
            median=median_val,
            sub_index=sub_index,
            sub_index_category=sub_cat,
            record_count=count,
            source=source,
            is_simulated=is_sim,
            data_quality="valid" if count > 0 else "insufficient_data",
            city_name=resolved_city,
            station_id=station_id,
            station_name=station_name,
        )

    @classmethod
    def aggregate_pollutant_readings(
        cls,
        readings: list[PollutantReading],
        interval: str,
        city_name: str | None = None,
        station_id: int | None = None,
        station_name: str | None = None,
    ) -> list[PollutantHistoryRecord]:
        """Group and aggregate pollutant readings into chronological buckets, computing sub-indices."""
        if not readings:
            return []

        sorted_readings = sorted(readings, key=lambda r: r.measured_at)
        pollutant_code = sorted_readings[0].pollutant_code
        unit = sorted_readings[0].unit

        buckets = cls._group_by_bucket(readings, interval)
        aggregated_records: list[PollutantHistoryRecord] = []

        for window_start in sorted(buckets.keys()):
            rec = cls._aggregate_single_pollutant_bucket(
                window_start, buckets[window_start], interval, pollutant_code, unit,
                city_name, station_id, station_name
            )
            if rec:
                aggregated_records.append(rec)

        return aggregated_records

