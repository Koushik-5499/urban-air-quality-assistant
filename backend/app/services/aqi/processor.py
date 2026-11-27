"""AQI processing service executing database queries, batch processing, and history retrieval."""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
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
from app.services.aqi.breakpoints import POLLUTANT_INFO
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.categories import get_aqi_category
from app.services.data_normalization_service import DataNormalizationService

logger = get_logger("app.services.aqi.processor")


def _apply_history_filters(
    stmt: Any,
    city_name: str | None,
    station_id: int | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[Any, str | None]:
    """Apply city/station/date filters to an AQI history query. Returns (stmt, resolved_name)."""
    resolved_name: str | None = None
    if city_name:
        match = DataNormalizationService.match_canonical_city(city_name)
        resolved_name = match[0] if match else city_name.strip()
        stmt = stmt.where(func.lower(City.name) == resolved_name.lower())
    if station_id:
        stmt = stmt.where(AQIReading.station_id == station_id)
    if start_date:
        stmt = stmt.where(AQIReading.measured_at >= start_date)
    if end_date:
        stmt = stmt.where(AQIReading.measured_at <= end_date)
    return stmt, resolved_name


class AQIProcessingService:
    """Service handling NAQI calculations, station groupings, deduplication, and persistence."""

    @classmethod
    def _resolve_city_from_name(cls, db: Session, city_name: str) -> "City":
        """Look up a City entity by name, raising 404 if not found."""
        match = DataNormalizationService.match_canonical_city(city_name)
        canonical_name = match[0] if match else city_name.strip()
        city_entity = db.execute(
            select(City).where(func.lower(City.name) == canonical_name.lower())
        ).scalar_one_or_none()
        if not city_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City '{city_name}' is not in the list of supported cities.",
            )
        return city_entity

    @classmethod
    def _resolve_city_from_station(cls, db: Session, station_id: int) -> "City":
        """Look up a City entity via a monitoring station, raising 404 if not found."""
        station = db.get(MonitoringStation, station_id)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitoring station {station_id} not found.",
            )
        city_entity = db.get(City, station.city_id)
        if not city_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City for monitoring station {station_id} not found.",
            )
        return city_entity

    @classmethod
    def _build_latest_readings_query(
        cls, city_id: int, station_id: int | None
    ) -> Any:
        """Build a SQLAlchemy query for the latest reading per pollutant."""
        latest_sel = select(
            PollutantReading.pollutant_code,
            func.max(PollutantReading.measured_at).label("max_measured"),
        ).where(PollutantReading.city_id == city_id)
        if station_id:
            latest_sel = latest_sel.where(PollutantReading.station_id == station_id)
        latest_subquery = latest_sel.group_by(PollutantReading.pollutant_code).subquery()

        stmt = (
            select(PollutantReading)
            .join(
                latest_subquery,
                (PollutantReading.pollutant_code == latest_subquery.c.pollutant_code)
                & (PollutantReading.measured_at == latest_subquery.c.max_measured),
            )
            .where(PollutantReading.city_id == city_id)
        )
        if station_id:
            stmt = stmt.where(PollutantReading.station_id == station_id)
        return stmt

    @classmethod
    def _build_no_data_response(
        cls,
        city_entity: City,
        station_id: int | None,
        station_name: str | None,
        now_utc: datetime,
    ) -> AQICalculationResponse:
        """Return a typed empty AQI response when no readings are available."""
        return AQICalculationResponse(
            city_id=city_entity.id,
            city_name=city_entity.name,
            station_id=station_id,
            station_name=station_name,
            aqi=None,
            category=None,
            dominant_pollutant=None,
            pollutant_subindices={},
            measurement_timestamp=None,
            calculated_at=now_utc,
            source="CPCB",
            is_simulated=False,
            data_quality="no_data",
            averaging_period="1-hour (indicative)",
            available_pollutants=[],
            missing_pollutants=["All pollutants missing"],
            explanation=f"No pollutant measurements found for {city_entity.name}.",
        )

    @classmethod
    def _compute_sub_indices(
        cls, readings: list["PollutantReading"]
    ) -> tuple[dict[str, int], dict[str, PollutantSubIndexResult]]:
        """Compute NAQI sub-indices for each pollutant reading."""
        sub_indices_dict: dict[str, int] = {}
        sub_index_results: dict[str, PollutantSubIndexResult] = {}
        for r in readings:
            sub_index = AQICalculator.calculate_sub_index(r.pollutant_code, r.concentration, r.unit)
            info = POLLUTANT_INFO.get(r.pollutant_code)
            avg_period = info.averaging_period if info else "24-hour"
            cat = get_aqi_category(sub_index) if sub_index is not None else None
            sub_index_results[r.pollutant_code] = PollutantSubIndexResult(
                pollutant_code=r.pollutant_code,
                concentration=r.concentration,
                unit=r.unit,
                sub_index=sub_index,
                category=cat,
                averaging_period=f"{avg_period} (reported as 1-hr observation)",
                is_valid=sub_index is not None,
            )
            if sub_index is not None:
                sub_indices_dict[r.pollutant_code] = sub_index
        return sub_indices_dict, sub_index_results

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
        except (SQLAlchemyError, ValueError) as exc:
            logger.warning("Error calculating AQI for %s (station %s): %s", city.name, st_id, exc)
            return None
        except Exception as exc:
            # Station evaluation boundary preventing one faulty station from stopping batch
            logger.exception(
                "Unexpected error calculating AQI for %s (station %s): %s", city.name, st_id, exc
            )
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
        stmt = (
            select(
                AQIReading,
                City.name.label("city_name"),
                MonitoringStation.station_name.label("station_name"),
            )
            .join(City, AQIReading.city_id == City.id)
            .outerjoin(MonitoringStation, AQIReading.station_id == MonitoringStation.id)
        )

        if city_name:
            match = DataNormalizationService.match_canonical_city(city_name)
            name_to_query = match[0] if match else city_name.strip()
            stmt = stmt.where(func.lower(City.name) == name_to_query.lower())

        if station_id:
            stmt = stmt.where(AQIReading.station_id == station_id)

        stmt = stmt.order_by(desc(AQIReading.measured_at)).limit(1)
        row = db.execute(stmt).first()

        if not row:
            return None

        reading, c_name, st_name = row
        return AQIHistoryItem(
            id=reading.id,
            city_id=reading.city_id,
            city_name=c_name,
            station_id=reading.station_id,
            station_name=st_name,
            aqi_value=reading.aqi_value,
            aqi_category=reading.aqi_category,
            dominant_pollutant=reading.dominant_pollutant,
            measured_at=reading.measured_at,
            source=reading.source,
            is_simulated=reading.is_simulated,
            created_at=reading.created_at,
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
        base_stmt = (
            select(
                AQIReading,
                City.name.label("city_name"),
                MonitoringStation.station_name.label("station_name"),
            )
            .join(City, AQIReading.city_id == City.id)
            .outerjoin(MonitoringStation, AQIReading.station_id == MonitoringStation.id)
        )
        stmt, resolved_name = _apply_history_filters(
            base_stmt, city_name, station_id, start_date, end_date
        )

        # Count total (re-apply filters on separate count statement)
        count_stmt = select(func.count(AQIReading.id)).join(City, AQIReading.city_id == City.id)
        count_stmt, _ = _apply_history_filters(
            count_stmt, city_name, station_id, start_date, end_date
        )
        total = db.execute(count_stmt).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(AQIReading.measured_at)).offset(offset).limit(page_size)
        rows = db.execute(stmt).all()

        items = [
            AQIHistoryItem(
                id=reading.id,
                city_id=reading.city_id,
                city_name=c_name,
                station_id=reading.station_id,
                station_name=st_name,
                aqi_value=reading.aqi_value,
                aqi_category=reading.aqi_category,
                dominant_pollutant=reading.dominant_pollutant,
                measured_at=reading.measured_at,
                source=reading.source,
                is_simulated=reading.is_simulated,
                created_at=reading.created_at,
            )
            for reading, c_name, st_name in rows
        ]

        return AQIHistoryResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        )
