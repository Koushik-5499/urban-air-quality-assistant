"""High-level Historical Data Service orchestrating queries, pagination, and service delegation."""

import math
import statistics
from collections import Counter
from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.aqi_reading import AQIReading
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import (
    AQIHistoryRecord,
    AQIHistoryResponse,
    AQISummaryResponse,
    HistoryCompareResponse,
    HistoryTrendResponse,
    PollutantHistoryRecord,
    PollutantHistoryResponse,
)
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.categories import get_aqi_category
from app.services.history.aggregation_service import AggregationService
from app.services.history.comparison_service import ComparisonService
from app.services.history.trend_service import TrendService
from app.services.history.validators import HistoryValidator


class HistoryService:
    """Orchestrates database queries, pagination, statistical aggregations, and trends."""

    @classmethod
    def get_aqi_history(
        cls,
        db: Session,
        city: str | None = None,
        station_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        interval: str | None = None,
        page: int = 1,
        page_size: int = 20,
        include_simulated: bool = True,
    ) -> AQIHistoryResponse:
        """Query historical AQI records with optional temporal aggregation and pagination."""
        page, page_size = HistoryValidator.validate_pagination(page, page_size)
        interval_norm = HistoryValidator.validate_interval(interval)
        start_utc, end_utc = HistoryValidator.validate_date_range(start_date, end_date, is_aggregated=bool(interval_norm))

        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)

        # Base query filters
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

        # If aggregated, retrieve matching records and bucket
        if interval_norm:
            stmt = select(AQIReading).options(
                joinedload(AQIReading.city),
                joinedload(AQIReading.station),
            )
            if filters:
                stmt = stmt.where(*filters)
            stmt = stmt.order_by(AQIReading.measured_at)

            all_readings = list(db.execute(stmt).scalars().all())

            aggregated = AggregationService.aggregate_aqi_readings(
                readings=all_readings,
                interval=interval_norm,
                city_name=city_entity.name if city_entity else None,
                station_id=station_entity.id if station_entity else None,
                station_name=station_entity.station_name if station_entity else None,
            )

            total_records = len(aggregated)
            total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_records = aggregated[start_idx:end_idx]

            return AQIHistoryResponse(
                page=page,
                page_size=page_size,
                total_records=total_records,
                total_pages=total_pages,
                city=city_entity.name if city_entity else city,
                station_id=station_id,
                station_name=station_entity.station_name if station_entity else None,
                interval=interval_norm,
                period_start=start_utc,
                period_end=end_utc,
                records=paginated_records,
            )

        # Raw observations: database-level pagination
        count_stmt = select(func.count(AQIReading.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_records = db.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

        data_stmt = (
            select(AQIReading)
            .options(joinedload(AQIReading.city), joinedload(AQIReading.station))
        )
        if filters:
            data_stmt = data_stmt.where(*filters)
        data_stmt = data_stmt.order_by(desc(AQIReading.measured_at)).offset((page - 1) * page_size).limit(page_size)

        raw_readings = list(db.execute(data_stmt).scalars().all())

        records = [
            AQIHistoryRecord(
                id=r.id,
                measured_at=r.measured_at,
                created_at=r.created_at,
                aqi_value=r.aqi_value,
                aqi_category=r.aqi_category,
                dominant_pollutant=r.dominant_pollutant,
                source=r.source,
                is_simulated=r.is_simulated,
                data_quality=r.data_quality,
                city_name=r.city.name if r.city else None,
                station_id=r.station_id,
                station_name=r.station.station_name if r.station else None,
            )
            for r in raw_readings
        ]

        return AQIHistoryResponse(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            city=city_entity.name if city_entity else city,
            station_id=station_id,
            station_name=station_entity.station_name if station_entity else None,
            interval=None,
            period_start=start_utc,
            period_end=end_utc,
            records=records,
        )

    @classmethod
    def get_pollutant_history(
        cls,
        db: Session,
        city: str | None = None,
        station_id: int | None = None,
        pollutant: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        interval: str | None = None,
        page: int = 1,
        page_size: int = 20,
        include_simulated: bool = True,
    ) -> PollutantHistoryResponse:
        """Query historical pollutant concentrations with sub-indices and optional aggregation."""
        page, page_size = HistoryValidator.validate_pagination(page, page_size)
        interval_norm = HistoryValidator.validate_interval(interval)
        pollutant_norm = HistoryValidator.validate_pollutant_code(pollutant)
        start_utc, end_utc = HistoryValidator.validate_date_range(start_date, end_date, is_aggregated=bool(interval_norm))

        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)

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

        if interval_norm:
            stmt = select(PollutantReading).options(
                joinedload(PollutantReading.city),
                joinedload(PollutantReading.station),
            )
            if filters:
                stmt = stmt.where(*filters)
            stmt = stmt.order_by(PollutantReading.measured_at)

            all_readings = list(db.execute(stmt).scalars().all())

            aggregated = AggregationService.aggregate_pollutant_readings(
                readings=all_readings,
                interval=interval_norm,
                city_name=city_entity.name if city_entity else None,
                station_id=station_entity.id if station_entity else None,
                station_name=station_entity.station_name if station_entity else None,
            )

            total_records = len(aggregated)
            total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_records = aggregated[start_idx:end_idx]

            default_unit = paginated_records[0].unit if paginated_records else None

            return PollutantHistoryResponse(
                page=page,
                page_size=page_size,
                total_records=total_records,
                total_pages=total_pages,
                city=city_entity.name if city_entity else city,
                station_id=station_id,
                station_name=station_entity.station_name if station_entity else None,
                pollutant=pollutant_norm,
                unit=default_unit,
                interval=interval_norm,
                period_start=start_utc,
                period_end=end_utc,
                records=paginated_records,
            )

        # Raw observations: database-level pagination
        count_stmt = select(func.count(PollutantReading.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_records = db.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

        data_stmt = (
            select(PollutantReading)
            .options(joinedload(PollutantReading.city), joinedload(PollutantReading.station))
        )
        if filters:
            data_stmt = data_stmt.where(*filters)
        data_stmt = data_stmt.order_by(desc(PollutantReading.measured_at)).offset((page - 1) * page_size).limit(page_size)

        raw_readings = list(db.execute(data_stmt).scalars().all())

        records: list[PollutantHistoryRecord] = []
        for r in raw_readings:
            sub_idx = AQICalculator.calculate_sub_index(r.pollutant_code, r.concentration, r.unit)
            sub_cat = get_aqi_category(sub_idx) if sub_idx is not None else None

            records.append(
                PollutantHistoryRecord(
                    id=r.id,
                    pollutant_code=r.pollutant_code,
                    concentration=r.concentration,
                    unit=r.unit,
                    sub_index=sub_idx,
                    sub_index_category=sub_cat,
                    measured_at=r.measured_at,
                    created_at=r.created_at,
                    source=r.source,
                    is_simulated=r.is_simulated,
                    data_quality=r.data_quality,
                    city_name=r.city.name if r.city else None,
                    station_id=r.station_id,
                    station_name=r.station.station_name if r.station else None,
                )
            )

        default_unit = records[0].unit if records else None

        return PollutantHistoryResponse(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            city=city_entity.name if city_entity else city,
            station_id=station_id,
            station_name=station_entity.station_name if station_entity else None,
            pollutant=pollutant_norm,
            unit=default_unit,
            interval=None,
            period_start=start_utc,
            period_end=end_utc,
            records=records,
        )

    @classmethod
    def get_summary(
        cls,
        db: Session,
        city: str | None = None,
        station_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        include_simulated: bool = True,
    ) -> AQISummaryResponse:
        """Calculate statistical summaries (min, max, mean, median, distributions) for valid AQI readings."""
        start_utc, end_utc = HistoryValidator.validate_date_range(start_date, end_date, is_aggregated=True)
        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)

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

        stmt = select(AQIReading)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(AQIReading.measured_at)

        all_readings = list(db.execute(stmt).scalars().all())
        valid_readings = [r for r in all_readings if r.aqi_value is not None and r.data_quality != "invalid"]
        count = len(valid_readings)

        if count == 0:
            return AQISummaryResponse(
                city=city_entity.name if city_entity else city,
                station_id=station_id,
                station_name=station_entity.station_name if station_entity else None,
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

        values = [r.aqi_value for r in valid_readings]
        avg_aqi = round(statistics.mean(values), 1)
        min_aqi = min(values)
        max_aqi = max(values)
        median_aqi = round(float(statistics.median(values)), 1)

        cat_counts = Counter(r.aqi_category for r in valid_readings)
        dominant_counts = Counter(r.dominant_pollutant for r in valid_readings if r.dominant_pollutant)
        data_quality = "sufficient" if count >= 3 else "insufficient_data"

        effective_start = start_utc or valid_readings[0].measured_at
        effective_end = end_utc or valid_readings[-1].measured_at

        return AQISummaryResponse(
            city=city_entity.name if city_entity else city,
            station_id=station_id,
            station_name=station_entity.station_name if station_entity else None,
            period_start=effective_start,
            period_end=effective_end,
            min_aqi=min_aqi,
            max_aqi=max_aqi,
            average_aqi=avg_aqi,
            median_aqi=median_aqi,
            record_count=count,
            category_distribution=dict(cat_counts),
            dominant_pollutant_distribution=dict(dominant_counts),
            data_quality=data_quality,
        )

    @classmethod
    def get_trends(
        cls,
        db: Session,
        city: str | None = None,
        station_id: int | None = None,
        pollutant: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        interval: str = "daily",
        threshold: float | None = None,
        min_records_per_period: int = 3,
        include_simulated: bool = True,
    ) -> HistoryTrendResponse:
        """Compute chronological trend comparing earlier and later periods."""
        interval_norm = HistoryValidator.validate_interval(interval) or "daily"
        pollutant_norm = HistoryValidator.validate_pollutant_code(pollutant) if pollutant else None
        start_utc, end_utc = HistoryValidator.validate_date_range(start_date, end_date, is_aggregated=True)

        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)

        city_name = city_entity.name if city_entity else city
        station_name = station_entity.station_name if station_entity else None

        if pollutant_norm:
            # Pollutant concentration trend
            p_threshold = threshold if threshold is not None else 2.0
            filters = [PollutantReading.pollutant_code == pollutant_norm]
            if city_entity:
                filters.append(PollutantReading.city_id == city_entity.id)
            if station_entity:
                filters.append(PollutantReading.station_id == station_entity.id)
            if not include_simulated:
                filters.append(PollutantReading.is_simulated.is_(False))
            if start_utc:
                filters.append(PollutantReading.measured_at >= start_utc)
            if end_utc:
                filters.append(PollutantReading.measured_at <= end_utc)

            stmt = select(PollutantReading).where(*filters).order_by(PollutantReading.measured_at)
            readings = list(db.execute(stmt).scalars().all())

            return TrendService.calculate_pollutant_trend(
                readings=readings,
                threshold=p_threshold,
                min_records_per_period=min_records_per_period,
                interval=interval_norm,
                city_name=city_name,
                station_id=station_id,
                station_name=station_name,
                start_date=start_utc,
                end_date=end_utc,
            )

        # AQI Trend
        aqi_threshold = threshold if threshold is not None else 5.0
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

        aqi_stmt = select(AQIReading).where(*filters).order_by(AQIReading.measured_at)
        aqi_readings = list(db.execute(aqi_stmt).scalars().all())

        return TrendService.calculate_aqi_trend(
            readings=aqi_readings,
            threshold=aqi_threshold,
            min_records_per_period=min_records_per_period,
            interval=interval_norm,
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
            start_date=start_utc,
            end_date=end_utc,
        )

    @classmethod
    def compare_locations(
        cls,
        db: Session,
        cities: list[str] | None = None,
        stations: list[int] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        include_simulated: bool = True,
    ) -> HistoryCompareResponse:
        """Compare AQI metrics for 2 to 10 cities or stations over identical date ranges."""
        parsed_cities, parsed_stations = HistoryValidator.validate_comparison_targets(cities, stations)
        start_utc, end_utc = HistoryValidator.validate_date_range(start_date, end_date, is_aggregated=True)

        return ComparisonService.compare_locations(
            db=db,
            cities=parsed_cities,
            stations=parsed_stations,
            start_date=start_utc,
            end_date=end_utc,
            include_simulated=include_simulated,
        )

