"""High-level Historical Data Service orchestrating queries, pagination, and service delegation."""

import math
import statistics
from collections import Counter
from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
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

    @staticmethod
    def _build_aqi_filters(
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

    @staticmethod
    def _build_pollutant_filters(
        city_entity: City | None,
        station_entity: MonitoringStation | None,
        pollutant_norm: str | None,
        include_simulated: bool,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list:
        """Construct SQL filter clauses for pollutant readings."""
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

    @classmethod
    def _get_aggregated_aqi_history(
        cls,
        db: Session,
        filters: list,
        interval_norm: str,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
        page: int,
        page_size: int,
    ) -> AQIHistoryResponse:
        """Fetch and aggregate AQI history across specified time intervals."""
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
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
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
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            interval=interval_norm,
            period_start=start_utc,
            period_end=end_utc,
            records=paginated_records,
        )

    @classmethod
    def _get_raw_aqi_history(
        cls,
        db: Session,
        filters: list,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
        page: int,
        page_size: int,
    ) -> AQIHistoryResponse:
        """Fetch raw, unaggregated AQI readings using SQL offset pagination."""
        count_stmt = select(func.count(AQIReading.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_records = db.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

        data_stmt = select(AQIReading).options(
            joinedload(AQIReading.city), joinedload(AQIReading.station)
        )
        if filters:
            data_stmt = data_stmt.where(*filters)
        data_stmt = (
            data_stmt.order_by(desc(AQIReading.measured_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

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
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            interval=None,
            period_start=start_utc,
            period_end=end_utc,
            records=records,
        )

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
        start_utc, end_utc = HistoryValidator.validate_date_range(
            start_date, end_date, is_aggregated=bool(interval_norm)
        )

        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)
        city_name = city_entity.name if city_entity else city
        station_name = station_entity.station_name if station_entity else None

        filters = cls._build_aqi_filters(
            city_entity, station_entity, include_simulated, start_utc, end_utc
        )

        if interval_norm:
            return cls._get_aggregated_aqi_history(
                db,
                filters,
                interval_norm,
                city_name,
                station_id,
                station_name,
                start_utc,
                end_utc,
                page,
                page_size,
            )

        return cls._get_raw_aqi_history(
            db, filters, city_name, station_id, station_name, start_utc, end_utc, page, page_size
        )

    @classmethod
    def _get_aggregated_pollutant_history(
        cls,
        db: Session,
        filters: list,
        interval_norm: str,
        pollutant_norm: str | None,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
        page: int,
        page_size: int,
    ) -> PollutantHistoryResponse:
        """Fetch and aggregate pollutant history across specified intervals."""
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
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
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
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=pollutant_norm,
            unit=default_unit,
            interval=interval_norm,
            period_start=start_utc,
            period_end=end_utc,
            records=paginated_records,
        )

    @classmethod
    def _get_raw_pollutant_history(
        cls,
        db: Session,
        filters: list,
        pollutant_norm: str | None,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
        page: int,
        page_size: int,
    ) -> PollutantHistoryResponse:
        """Fetch raw pollutant readings using SQL pagination."""
        count_stmt = select(func.count(PollutantReading.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_records = db.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

        data_stmt = select(PollutantReading).options(
            joinedload(PollutantReading.city), joinedload(PollutantReading.station)
        )
        if filters:
            data_stmt = data_stmt.where(*filters)
        data_stmt = (
            data_stmt.order_by(desc(PollutantReading.measured_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

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
            city=city_name,
            station_id=station_id,
            station_name=station_name,
            pollutant=pollutant_norm,
            unit=default_unit,
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
        start_utc, end_utc = HistoryValidator.validate_date_range(
            start_date, end_date, is_aggregated=bool(interval_norm)
        )

        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)
        city_name = city_entity.name if city_entity else city
        station_name = station_entity.station_name if station_entity else None

        filters = cls._build_pollutant_filters(
            city_entity, station_entity, pollutant_norm, include_simulated, start_utc, end_utc
        )

        if interval_norm:
            return cls._get_aggregated_pollutant_history(
                db,
                filters,
                interval_norm,
                pollutant_norm,
                city_name,
                station_id,
                station_name,
                start_utc,
                end_utc,
                page,
                page_size,
            )

        return cls._get_raw_pollutant_history(
            db,
            filters,
            pollutant_norm,
            city_name,
            station_id,
            station_name,
            start_utc,
            end_utc,
            page,
            page_size,
        )

    @staticmethod
    def _empty_summary_response(
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

    @staticmethod
    def _calc_summary_distributions(
        valid_readings: list[AQIReading],
    ) -> tuple[dict[str, int], dict[str, int]]:
        """Calculate categorical and dominant pollutant distributions."""
        cat_counts = Counter(r.aqi_category for r in valid_readings if r.aqi_category)
        dominant_counts = Counter(
            r.dominant_pollutant for r in valid_readings if r.dominant_pollutant
        )
        return dict(cat_counts), dict(dominant_counts)

    @classmethod
    def _compute_summary_stats(
        cls,
        valid_readings: list[AQIReading],
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> AQISummaryResponse:
        """Calculate statistical summaries for non-empty set of valid AQI readings."""
        count = len(valid_readings)
        if count == 0:
            return cls._empty_summary_response(
                city_name, station_id, station_name, start_utc, end_utc
            )

        values = [r.aqi_value for r in valid_readings if r.aqi_value is not None]
        avg_aqi = round(statistics.mean(values), 1)
        min_aqi = min(values)
        max_aqi = max(values)
        median_aqi = round(float(statistics.median(values)), 1)

        cat_dist, dom_dist = cls._calc_summary_distributions(valid_readings)
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
        """
        Calculate statistical summaries (min, max, mean, median, distributions) for valid AQI
        readings.
        """
        start_utc, end_utc = HistoryValidator.validate_date_range(
            start_date, end_date, is_aggregated=True
        )
        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)
        city_name = city_entity.name if city_entity else city
        station_name = station_entity.station_name if station_entity else None

        filters = cls._build_aqi_filters(
            city_entity, station_entity, include_simulated, start_utc, end_utc
        )

        stmt = select(AQIReading)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(AQIReading.measured_at)

        all_readings = list(db.execute(stmt).scalars().all())
        valid_readings = [
            r for r in all_readings if r.aqi_value is not None and r.data_quality != "invalid"
        ]

        return cls._compute_summary_stats(
            valid_readings, city_name, station_id, station_name, start_utc, end_utc
        )

    @classmethod
    def _get_pollutant_trend_result(
        cls,
        db: Session,
        city_entity: City | None,
        station_entity: MonitoringStation | None,
        pollutant_norm: str,
        threshold: float | None,
        min_records_per_period: int,
        include_simulated: bool,
        interval_norm: str,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> HistoryTrendResponse:
        """Execute query and compute trend for pollutant concentration."""
        p_threshold = threshold if threshold is not None else 2.0
        filters = cls._build_pollutant_filters(
            city_entity, station_entity, pollutant_norm, include_simulated, start_utc, end_utc
        )
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

    @classmethod
    def _get_aqi_trend_result(
        cls,
        db: Session,
        city_entity: City | None,
        station_entity: MonitoringStation | None,
        threshold: float | None,
        min_records_per_period: int,
        include_simulated: bool,
        interval_norm: str,
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> HistoryTrendResponse:
        """Execute query and compute trend for AQI index values."""
        aqi_threshold = threshold if threshold is not None else 5.0
        filters = cls._build_aqi_filters(
            city_entity, station_entity, include_simulated, start_utc, end_utc
        )
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
        start_utc, end_utc = HistoryValidator.validate_date_range(
            start_date, end_date, is_aggregated=True
        )

        city_entity = HistoryValidator.resolve_city(db, city)
        station_entity = HistoryValidator.resolve_station(db, station_id)

        city_name = city_entity.name if city_entity else city
        station_name = station_entity.station_name if station_entity else None

        if pollutant_norm:
            return cls._get_pollutant_trend_result(
                db,
                city_entity,
                station_entity,
                pollutant_norm,
                threshold,
                min_records_per_period,
                include_simulated,
                interval_norm,
                city_name,
                station_id,
                station_name,
                start_utc,
                end_utc,
            )

        return cls._get_aqi_trend_result(
            db,
            city_entity,
            station_entity,
            threshold,
            min_records_per_period,
            include_simulated,
            interval_norm,
            city_name,
            station_id,
            station_name,
            start_utc,
            end_utc,
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
        parsed_cities, parsed_stations = HistoryValidator.validate_comparison_targets(
            cities, stations
        )
        start_utc, end_utc = HistoryValidator.validate_date_range(
            start_date, end_date, is_aggregated=True
        )

        return ComparisonService.compare_locations(
            db=db,
            cities=parsed_cities,
            stations=parsed_stations,
            start_date=start_utc,
            end_date=end_utc,
            include_simulated=include_simulated,
        )
