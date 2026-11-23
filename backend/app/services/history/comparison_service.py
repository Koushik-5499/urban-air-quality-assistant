"""Location comparison service for multi-city and multi-station historical analysis."""

import statistics
from collections import Counter
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.schemas.history import HistoryCompareResponse, LocationComparisonItem


class ComparisonService:
    """Evaluates and compares air quality metrics across multiple cities and stations."""

    @classmethod
    def _compute_metrics(
        cls, valid_readings: list[AQIReading]
    ) -> tuple[
        float | None, int | None, int | None, float | None, dict[str, int], dict[str, int], str
    ]:
        """Compute statistical metrics and distributions for valid AQI readings."""
        count = len(valid_readings)
        if count == 0:
            return None, None, None, None, {}, {}, "no_data"

        values = [r.aqi_value for r in valid_readings if r.aqi_value is not None]
        avg_aqi = round(statistics.mean(values), 1)
        min_aqi = min(values)
        max_aqi = max(values)
        median_aqi = round(float(statistics.median(values)), 1)
        cat_counts = dict(Counter(r.aqi_category for r in valid_readings if r.aqi_category))
        dominant_counts = dict(
            Counter(r.dominant_pollutant for r in valid_readings if r.dominant_pollutant)
        )
        quality = "sufficient" if count >= 3 else "insufficient_data"
        return avg_aqi, min_aqi, max_aqi, median_aqi, cat_counts, dominant_counts, quality

    @classmethod
    def _evaluate_city(
        cls,
        db: Session,
        city_name: str,
        start_date: datetime | None,
        end_date: datetime | None,
        include_simulated: bool,
    ) -> LocationComparisonItem | None:
        """Fetch and evaluate comparison metrics for a single city."""
        stmt = select(City).where(City.name.ilike(city_name.strip()))
        city_entity = db.execute(stmt).scalar_one_or_none()
        if not city_entity:
            return None

        query = select(AQIReading).where(AQIReading.city_id == city_entity.id)
        if not include_simulated:
            query = query.where(AQIReading.is_simulated.is_(False))
        if start_date:
            query = query.where(AQIReading.measured_at >= start_date)
        if end_date:
            query = query.where(AQIReading.measured_at <= end_date)

        readings = list(db.execute(query).scalars().all())
        valid_readings = [
            r for r in readings if r.aqi_value is not None and r.data_quality != "invalid"
        ]
        avg_aqi, min_aqi, max_aqi, median_aqi, cat_dist, dom_dist, quality = cls._compute_metrics(
            valid_readings
        )

        return LocationComparisonItem(
            location_type="city",
            city_name=city_entity.name,
            station_id=None,
            station_name=None,
            average_aqi=avg_aqi,
            min_aqi=min_aqi,
            max_aqi=max_aqi,
            median_aqi=median_aqi,
            record_count=len(valid_readings),
            category_distribution=cat_dist,
            dominant_pollutant_distribution=dom_dist,
            data_quality=quality,
        )

    @classmethod
    def _evaluate_station(
        cls,
        db: Session,
        station_id: int,
        start_date: datetime | None,
        end_date: datetime | None,
        include_simulated: bool,
    ) -> LocationComparisonItem | None:
        """Fetch and evaluate comparison metrics for a single monitoring station."""
        st_entity = db.get(MonitoringStation, station_id)
        if not st_entity:
            return None

        query = select(AQIReading).where(AQIReading.station_id == station_id)
        if not include_simulated:
            query = query.where(AQIReading.is_simulated.is_(False))
        if start_date:
            query = query.where(AQIReading.measured_at >= start_date)
        if end_date:
            query = query.where(AQIReading.measured_at <= end_date)

        readings = list(db.execute(query).scalars().all())
        valid_readings = [
            r for r in readings if r.aqi_value is not None and r.data_quality != "invalid"
        ]
        avg_aqi, min_aqi, max_aqi, median_aqi, cat_dist, dom_dist, quality = cls._compute_metrics(
            valid_readings
        )

        return LocationComparisonItem(
            location_type="station",
            city_name=st_entity.city.name if st_entity.city else "Unknown City",
            station_id=st_entity.id,
            station_name=st_entity.station_name,
            average_aqi=avg_aqi,
            min_aqi=min_aqi,
            max_aqi=max_aqi,
            median_aqi=median_aqi,
            record_count=len(valid_readings),
            category_distribution=cat_dist,
            dominant_pollutant_distribution=dom_dist,
            data_quality=quality,
        )

    @classmethod
    def compare_locations(
        cls,
        db: Session,
        cities: list[str],
        stations: list[int],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        include_simulated: bool = True,
    ) -> HistoryCompareResponse:
        """Compare AQI metrics for 2 to 10 cities or stations over identical date ranges."""
        comparisons: list[LocationComparisonItem] = []

        for city_name in cities:
            city_item = cls._evaluate_city(db, city_name, start_date, end_date, include_simulated)
            if city_item:
                comparisons.append(city_item)

        for station_id in stations:
            station_item = cls._evaluate_station(
                db, station_id, start_date, end_date, include_simulated
            )
            if station_item:
                comparisons.append(station_item)

        return HistoryCompareResponse(
            period_start=start_date,
            period_end=end_date,
            location_count=len(comparisons),
            comparisons=comparisons,
        )
