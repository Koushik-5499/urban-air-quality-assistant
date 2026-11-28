"""High-level Historical Data Service orchestrating queries, pagination, and service delegation."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.schemas.history import (
    AQIHistoryResponse,
    AQISummaryResponse,
    HistoryCompareResponse,
    HistoryTrendResponse,
    PollutantHistoryResponse,
)
from app.services.history import history_query_service, summary_service
from app.services.history.comparison_service import ComparisonService
from app.services.history.history_query_service import HistoryQueryParams
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
        return summary_service.build_aqi_filters(
            city_entity, station_entity, include_simulated, start_utc, end_utc
        )

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
        return summary_service.build_pollutant_filters(
            city_entity,
            station_entity,
            pollutant_norm,
            include_simulated,
            start_utc,
            end_utc,
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
        params = HistoryQueryParams(
            filters=filters,
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
            start_utc=start_utc,
            end_utc=end_utc,
            page=page,
            page_size=page_size,
            interval_norm=interval_norm,
        )

        if interval_norm:
            return history_query_service.get_aggregated_aqi_history(db, params)
        return history_query_service.get_raw_aqi_history(db, params)

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
        params = HistoryQueryParams(
            filters=filters,
            city_name=city_name,
            station_id=station_id,
            station_name=station_name,
            start_utc=start_utc,
            end_utc=end_utc,
            page=page,
            page_size=page_size,
            interval_norm=interval_norm,
            pollutant_norm=pollutant_norm,
        )

        if interval_norm:
            return history_query_service.get_aggregated_pollutant_history(db, params)
        return history_query_service.get_raw_pollutant_history(db, params)

    @staticmethod
    def _empty_summary_response(
        city_name: str | None,
        station_id: int | None,
        station_name: str | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> AQISummaryResponse:
        """Return zero-record default summary response."""
        return summary_service.empty_summary_response(
            city_name, station_id, station_name, start_utc, end_utc
        )

    @staticmethod
    def _calc_summary_distributions(
        valid_readings: list[AQIReading],
    ) -> tuple[dict[str, int], dict[str, int]]:
        """Calculate categorical and dominant pollutant distributions."""
        return summary_service.calc_summary_distributions(valid_readings)

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
        return summary_service.compute_summary_stats(
            valid_readings, city_name, station_id, station_name, start_utc, end_utc
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
        """Calculate statistical summaries for valid AQI readings."""
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
