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

        # Sort readings chronologically
        sorted_readings = sorted(readings, key=lambda r: r.measured_at)

        # Bucket by window start
        buckets: dict[datetime, list[AQIReading]] = {}
        for r in sorted_readings:
            start_window, _ = cls.get_bucket_window(r.measured_at, interval)
            if start_window not in buckets:
                buckets[start_window] = []
            buckets[start_window].append(r)

        aggregated_records: list[AQIHistoryRecord] = []

        for window_start in sorted(buckets.keys()):
            bucket_items = buckets[window_start]
            _, window_end = cls.get_bucket_window(window_start, interval)

            # Filter valid AQI readings
            valid_items = [r for r in bucket_items if r.aqi_value is not None and r.data_quality != "invalid"]
            if not valid_items:
                continue

            values = [r.aqi_value for r in valid_items]
            avg_val = round(statistics.mean(values), 1)
            min_val = min(values)
            max_val = max(values)
            median_val = round(float(statistics.median(values)), 1)
            count = len(values)

            # Category distribution
            cat_counts: Counter[str] = Counter(r.aqi_category for r in valid_items if r.aqi_category)
            dominant_category = cat_counts.most_common(1)[0][0] if cat_counts else None

            # Dominant pollutant distribution
            pollutant_candidates = [r.dominant_pollutant for r in valid_items if r.dominant_pollutant]
            dominant_pollutant = Counter(pollutant_candidates).most_common(1)[0][0] if pollutant_candidates else None

            # Source & simulation metadata
            is_sim = any(r.is_simulated for r in valid_items)
            source = valid_items[0].source if valid_items else "CPCB"

            rec = AQIHistoryRecord(
                period_start=window_start,
                period_end=window_end,
                interval=interval,
                average_aqi=avg_val,
                min_aqi=min_val,
                max_aqi=max_val,
                median_aqi=median_val,
                record_count=count,
                dominant_category=dominant_category,
                category_distribution=dict(cat_counts),
                dominant_pollutant=dominant_pollutant,
                source=source,
                is_simulated=is_sim,
                data_quality="valid" if count > 0 else "insufficient_data",
                city_name=city_name or (valid_items[0].city.name if valid_items[0].city else None),
                station_id=station_id,
                station_name=station_name,
            )
            aggregated_records.append(rec)

        return aggregated_records

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

        # Bucket by window start
        buckets: dict[datetime, list[PollutantReading]] = {}
        for r in sorted_readings:
            start_window, _ = cls.get_bucket_window(r.measured_at, interval)
            if start_window not in buckets:
                buckets[start_window] = []
            buckets[start_window].append(r)

        aggregated_records: list[PollutantHistoryRecord] = []

        for window_start in sorted(buckets.keys()):
            bucket_items = buckets[window_start]
            _, window_end = cls.get_bucket_window(window_start, interval)

            valid_items = [r for r in bucket_items if r.concentration is not None and r.concentration >= 0]
            if not valid_items:
                continue

            values = [r.concentration for r in valid_items]
            avg_val = round(statistics.mean(values), 2)
            min_val = round(min(values), 2)
            max_val = round(max(values), 2)
            median_val = round(float(statistics.median(values)), 2)
            count = len(values)

            # Calculate reproducible sub-index for average concentration
            sub_index = AQICalculator.calculate_sub_index(pollutant_code, avg_val, unit)
            sub_cat = get_aqi_category(sub_index) if sub_index is not None else None

            is_sim = any(r.is_simulated for r in valid_items)
            source = valid_items[0].source if valid_items else "CPCB"

            rec = PollutantHistoryRecord(
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
                city_name=city_name or (valid_items[0].city.name if valid_items[0].city else None),
                station_id=station_id,
                station_name=station_name,
            )
            aggregated_records.append(rec)

        return aggregated_records

