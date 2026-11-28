"""AQI processing service executing database queries, batch processing, and history retrieval."""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.schemas.aqi_processing import (
    AQICalculationResponse,
    AQIHistoryItem,
    AQIHistoryResponse,
    AQIProcessResponse,
    PollutantSubIndexResult,
    SubIndicesOnlyResponse,
)
from app.services.aqi import processor_queries
from app.services.aqi.calculator import AQICalculator

logger = get_logger("app.services.aqi.processor")


def _apply_history_filters(
    stmt: Any,
    city_name: str | None,
    station_id: int | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[Any, str | None]:
    """Apply city/station/date filters to an AQI history query."""
    return processor_queries.apply_history_filters(
        stmt, city_name, station_id, start_date, end_date
    )


class AQIProcessingService:
    """Service handling NAQI calculations, station groupings, deduplication, and persistence."""

    @classmethod
    def _resolve_city_from_name(cls, db: Session, city_name: str) -> City:
        """Look up a City entity by name, raising 404 if not found."""
        return processor_queries.resolve_city_from_name(db, city_name)

    @classmethod
    def _resolve_city_from_station(cls, db: Session, station_id: int) -> City:
        """Look up a City entity via a monitoring station, raising 404 if not found."""
        return processor_queries.resolve_city_from_station(db, station_id)

    @classmethod
    def _build_latest_readings_query(cls, city_id: int, station_id: int | None) -> Any:
        """Build a SQLAlchemy query for the latest reading per pollutant."""
        return processor_queries.build_latest_readings_query(city_id, station_id)

    @classmethod
    def _build_no_data_response(
        cls,
        city_entity: City,
        station_id: int | None,
        station_name: str | None,
        now_utc: datetime,
    ) -> AQICalculationResponse:
        """Return a typed empty AQI response when no readings are available."""
        return processor_queries.build_no_data_response(
            city_entity, station_id, station_name, now_utc
        )

    @classmethod
    def _compute_sub_indices(
        cls, readings: list[PollutantReading]
    ) -> tuple[dict[str, int], dict[str, PollutantSubIndexResult]]:
        """Compute NAQI sub-indices for each pollutant reading."""
        return processor_queries.compute_sub_indices(readings)

    @classmethod
    def calculate_for_city_or_station(
        cls,
        db: Session,
        city_name: str | None = None,
        station_id: int | None = None,
    ) -> AQICalculationResponse:
        """Calculate CPCB NAQI on the fly from current database pollutant readings."""
        now_utc = datetime.now(UTC)

        if city_name:
            city_entity = cls._resolve_city_from_name(db, city_name)
        elif station_id:
            city_entity = cls._resolve_city_from_station(db, station_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either city or station_id must be provided.",
            )

        readings = list(
            db.execute(cls._build_latest_readings_query(city_entity.id, station_id)).scalars().all()
        )

        station_name = None
        if station_id:
            st = db.get(MonitoringStation, station_id)
            station_name = st.station_name if st else None

        if not readings:
            return cls._build_no_data_response(city_entity, station_id, station_name, now_utc)

        is_simulated = any(r.source.upper() == "SIMULATED" for r in readings)
        latest_measured_at = max(r.measured_at for r in readings)
        source = readings[0].source
        sub_indices_dict, sub_index_results = cls._compute_sub_indices(readings)

        overall_aqi, cat, dominant, is_suff, expl, missing = AQICalculator.calculate_overall_aqi(
            sub_indices_dict
        )

        return AQICalculationResponse(
            city_id=city_entity.id,
            city_name=city_entity.name,
            station_id=station_id,
            station_name=station_name,
            aqi=overall_aqi,
            category=cat,
            dominant_pollutant=dominant,
            pollutant_subindices=sub_index_results,
            measurement_timestamp=latest_measured_at,
            calculated_at=now_utc,
            source=source,
            is_simulated=is_simulated,
            data_quality="sufficient" if is_suff else "insufficient_data",
            averaging_period="1-hour (indicative)",
            available_pollutants=list(sub_indices_dict.keys()),
            missing_pollutants=missing,
            explanation=expl,
        )

    @classmethod
    def get_pollutant_subindices(
        cls,
        db: Session,
        city_name: str | None = None,
        station_id: int | None = None,
    ) -> SubIndicesOnlyResponse:
        """Return individual pollutant sub-indices and dominant pollutant."""
        calc = cls.calculate_for_city_or_station(db, city_name=city_name, station_id=station_id)
        return SubIndicesOnlyResponse(
            city_id=calc.city_id,
            city_name=calc.city_name,
            station_id=calc.station_id,
            station_name=calc.station_name,
            dominant_pollutant=calc.dominant_pollutant,
            sub_indices=calc.pollutant_subindices,
            calculated_at=calc.calculated_at,
        )

    @classmethod
    def _process_station(
        cls,
        db: Session,
        city: City,
        st_id: int | None,
    ) -> int | None:
        """Calculate AQI for one station and persist if new.

        Returns 1 if created, 0 if skipped (insufficient/duplicate), None if error.
        """
        try:
            calc = cls.calculate_for_city_or_station(db, city_name=city.name, station_id=st_id)
        except (
            SQLAlchemyError,
            ValueError,
            KeyError,
            TypeError,
            ArithmeticError,
            RuntimeError,
        ) as exc:
            logger.warning("Error calculating AQI for %s (station %s): %s", city.name, st_id, exc)
            return None

        if calc.aqi is None or not calc.measurement_timestamp:
            return 0  # insufficient data

        existing_stmt = select(AQIReading).where(
            AQIReading.city_id == city.id,
            AQIReading.station_id == st_id,
            AQIReading.measured_at == calc.measurement_timestamp,
        )
        if db.execute(existing_stmt).scalar_one_or_none():
            return 0  # duplicate

        db.add(AQIReading(
            city_id=city.id,
            station_id=st_id,
            aqi_value=calc.aqi,
            aqi_category=calc.category or "Unknown",
            dominant_pollutant=calc.dominant_pollutant,
            measured_at=calc.measurement_timestamp,
            source=calc.source,
            is_simulated=calc.is_simulated,
            data_quality=calc.data_quality or "valid",
        ))
        return 1  # created

    @classmethod
    def process_and_persist_aqi(
        cls,
        db: Session,
        city_id: int | None = None,
    ) -> AQIProcessResponse:
        """Batch-process stored pollutant readings into deduplicated AQIReading records."""
        now_utc = datetime.now(UTC)
        cities_query = select(City)
        if city_id:
            cities_query = cities_query.where(City.id == city_id)
        cities = list(db.execute(cities_query).scalars().all())

        records_created = 0
        stations_evaluated = 0
        skipped_insufficient = 0

        for city in cities:
            stations = list(
                db.execute(select(MonitoringStation).where(MonitoringStation.city_id == city.id))
                .scalars()
                .all()
            )
            for st in stations if stations else [None]:
                st_id = st.id if st else None
                stations_evaluated += 1
                result = cls._process_station(db, city, st_id)
                if result is None:
                    continue
                if result == 1:
                    records_created += 1
                else:
                    skipped_insufficient += 1

        db.commit()

        return AQIProcessResponse(
            success=True,
            stations_evaluated=stations_evaluated,
            aqi_records_created=records_created,
            skipped_insufficient_data=skipped_insufficient,
            processed_at=now_utc,
            message=(
                f"AQI processing finished. {records_created} new AQI records persisted. "
                f"{skipped_insufficient} evaluations had insufficient criteria data."
            ),
        )

    @classmethod
    def get_latest_aqi_reading(
        cls,
        db: Session,
        city_name: str | None = None,
        station_id: int | None = None,
    ) -> AQIHistoryItem | None:
        """Fetch the latest stored AQIReading record from the database."""
        return processor_queries.get_latest_aqi_reading(
            db, city_name=city_name, station_id=station_id
        )

    @classmethod
    def get_history(
        cls,
        db: Session,
        city_name: str | None = None,
        station_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AQIHistoryResponse:
        """Retrieve paginated historical calculated AQI readings."""
        return processor_queries.get_history(
            db,
            city_name=city_name,
            station_id=station_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
