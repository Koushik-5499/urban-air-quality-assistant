"""Location comparison service for multi-city and multi-station historical analysis."""

from collections import Counter
from datetime import datetime
import statistics
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.schemas.history import HistoryCompareResponse, LocationComparisonItem


class ComparisonService:
    """Evaluates and compares air quality metrics across multiple cities and stations."""

    @classmethod
    def compare_locations(
        cls,
        db: Session,
        cities: List[str],
        stations: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_simulated: bool = True,
    ) -> HistoryCompareResponse:
        """Compare AQI metrics for 2 to 10 cities or stations over identical date ranges."""
        comparisons: List[LocationComparisonItem] = []

        # 1. Evaluate Cities
        for city_name in cities:
            stmt = select(City).where(City.name.ilike(city_name.strip()))
            city_entity = db.execute(stmt).scalar_one_or_none()
            if not city_entity:
                continue

            query = select(AQIReading).where(AQIReading.city_id == city_entity.id)
            if not include_simulated:
                query = query.where(AQIReading.is_simulated.is_(False))
            if start_date:
                query = query.where(AQIReading.measured_at >= start_date)
            if end_date:
                query = query.where(AQIReading.measured_at <= end_date)

            readings = list(db.execute(query).scalars().all())
            valid_readings = [r for r in readings if r.aqi_value is not None and r.data_quality != "invalid"]
            count = len(valid_readings)

            if count > 0:
                values = [r.aqi_value for r in valid_readings]
                avg_aqi = round(statistics.mean(values), 1)
                min_aqi = min(values)
                max_aqi = max(values)
                median_aqi = round(float(statistics.median(values)), 1)
                cat_counts = Counter(r.aqi_category for r in valid_readings)
                dominant_counts = Counter(r.dominant_pollutant for r in valid_readings if r.dominant_pollutant)
                quality = "sufficient" if count >= 3 else "insufficient_data"
            else:
                avg_aqi = None
                min_aqi = None
                max_aqi = None
                median_aqi = None
                cat_counts = Counter()
                dominant_counts = Counter()
                quality = "no_data"

            comparisons.append(
                LocationComparisonItem(
                    location_type="city",
                    city_name=city_entity.name,
                    station_id=None,
                    station_name=None,
                    average_aqi=avg_aqi,
                    min_aqi=min_aqi,
                    max_aqi=max_aqi,
                    median_aqi=median_aqi,
                    record_count=count,
                    category_distribution=dict(cat_counts),
                    dominant_pollutant_distribution=dict(dominant_counts),
                    data_quality=quality,
                )
            )

        # 2. Evaluate Stations
        for station_id in stations:
            st_entity = db.get(MonitoringStation, station_id)
            if not st_entity:
                continue

            query = select(AQIReading).where(AQIReading.station_id == station_id)
            if not include_simulated:
                query = query.where(AQIReading.is_simulated.is_(False))
            if start_date:
                query = query.where(AQIReading.measured_at >= start_date)
            if end_date:
                query = query.where(AQIReading.measured_at <= end_date)

            readings = list(db.execute(query).scalars().all())
            valid_readings = [r for r in readings if r.aqi_value is not None and r.data_quality != "invalid"]
            count = len(valid_readings)

            if count > 0:
                values = [r.aqi_value for r in valid_readings]
                avg_aqi = round(statistics.mean(values), 1)
                min_aqi = min(values)
                max_aqi = max(values)
                median_aqi = round(float(statistics.median(values)), 1)
                cat_counts = Counter(r.aqi_category for r in valid_readings)
                dominant_counts = Counter(r.dominant_pollutant for r in valid_readings if r.dominant_pollutant)
                quality = "sufficient" if count >= 3 else "insufficient_data"
            else:
                avg_aqi = None
                min_aqi = None
                max_aqi = None
                median_aqi = None
                cat_counts = Counter()
                dominant_counts = Counter()
                quality = "no_data"

            comparisons.append(
                LocationComparisonItem(
                    location_type="station",
                    city_name=st_entity.city.name if st_entity.city else "Unknown City",
                    station_id=st_entity.id,
                    station_name=st_entity.station_name,
                    average_aqi=avg_aqi,
                    min_aqi=min_aqi,
                    max_aqi=max_aqi,
                    median_aqi=median_aqi,
                    record_count=count,
                    category_distribution=dict(cat_counts),
                    dominant_pollutant_distribution=dict(dominant_counts),
                    data_quality=quality,
                )
            )

        return HistoryCompareResponse(
            period_start=start_date,
            period_end=end_date,
            location_count=len(comparisons),
            comparisons=comparisons,
        )

