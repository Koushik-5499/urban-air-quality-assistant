"""AQI processing service executing database queries, batch processing, and history retrieval."""

from datetime import UTC, datetime

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


class AQIProcessingService:
    """Service handling NAQI calculations, station groupings, deduplication, and persistence."""

    @classmethod
    def calculate_for_city_or_station(
        cls,
        db: Session,
        city_name: str | None = None,
        station_id: int | None = None,
    ) -> AQICalculationResponse:
        """Calculate CPCB NAQI on the fly from current database pollutant readings."""
        now_utc = datetime.now(UTC)

        # Resolve City
        city_entity = None
        if city_name:
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
        elif station_id:
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
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either city or station_id must be provided.",
            )

        assert city_entity is not None

        # Query latest readings for this city or station
        stmt = select(PollutantReading).where(PollutantReading.city_id == city_entity.id)
        if station_id:
            stmt = stmt.where(PollutantReading.station_id == station_id)

        # Get the latest readings per pollutant
        latest_sel = select(
            PollutantReading.pollutant_code,
            func.max(PollutantReading.measured_at).label("max_measured"),
        ).where(PollutantReading.city_id == city_entity.id)
        if station_id:
            latest_sel = latest_sel.where(PollutantReading.station_id == station_id)
        latest_subquery = latest_sel.group_by(PollutantReading.pollutant_code).subquery()

        readings_stmt = (
            select(PollutantReading)
            .join(
                latest_subquery,
                (PollutantReading.pollutant_code == latest_subquery.c.pollutant_code)
                & (PollutantReading.measured_at == latest_subquery.c.max_measured),
            )
            .where(PollutantReading.city_id == city_entity.id)
        )
        if station_id:
            readings_stmt = readings_stmt.where(PollutantReading.station_id == station_id)

        readings = list(db.execute(readings_stmt).scalars().all())

        station_name = None
        if station_id:
            st = db.get(MonitoringStation, station_id)
            station_name = st.station_name if st else None

        if not readings:
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

        # Calculate sub-indices
        sub_indices_dict: dict[str, int] = {}
        sub_index_results: dict[str, PollutantSubIndexResult] = {}
        is_simulated = any(r.source.upper() == "SIMULATED" for r in readings)
        latest_measured_at = max(r.measured_at for r in readings)
        source = readings[0].source

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

        # Calculate overall AQI
        overall_aqi, cat, dominant, is_suff, expl, missing = AQICalculator.calculate_overall_aqi(
            sub_indices_dict
        )

        data_quality = "sufficient" if is_suff else "insufficient_data"

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
            data_quality=data_quality,
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
            # Retrieve stations in this city
            stations = list(
                db.execute(select(MonitoringStation).where(MonitoringStation.city_id == city.id))
                .scalars()
                .all()
            )

            targets = stations if stations else [None]

            for st in targets:
                st_id = st.id if st else None
                stations_evaluated += 1

                try:
                    calc = cls.calculate_for_city_or_station(
                        db, city_name=city.name, station_id=st_id
                    )
                except (SQLAlchemyError, ValueError) as exc:
                    logger.warning(
                        "Error calculating AQI for %s (station %s): %s", city.name, st_id, exc
                    )
                    continue
                except Exception as exc:
                    # Station evaluation boundary preventing one faulty station from stopping batch
                    logger.exception(
                        "Unexpected error calculating AQI for %s (station %s): %s",
                        city.name,
                        st_id,
                        exc,
                    )
                    continue

                if calc.aqi is None or not calc.measurement_timestamp:
                    skipped_insufficient += 1
                    continue

                # Deduplicate: Check if AQIReading already exists for station & timestamp
                existing_stmt = select(AQIReading).where(
                    AQIReading.city_id == city.id,
                    AQIReading.station_id == st_id,
                    AQIReading.measured_at == calc.measurement_timestamp,
                )
                existing_record = db.execute(existing_stmt).scalar_one_or_none()

                if not existing_record:
                    new_aqi = AQIReading(
                        city_id=city.id,
                        station_id=st_id,
                        aqi_value=calc.aqi,
                        aqi_category=calc.category or "Unknown",
                        dominant_pollutant=calc.dominant_pollutant,
                        measured_at=calc.measurement_timestamp,
                        source=calc.source,
                        is_simulated=calc.is_simulated,
                        data_quality=calc.data_quality or "valid",
                    )
                    db.add(new_aqi)
                    records_created += 1

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

        if start_date:
            stmt = stmt.where(AQIReading.measured_at >= start_date)
        if end_date:
            stmt = stmt.where(AQIReading.measured_at <= end_date)

        # Count total
        count_stmt = select(func.count(AQIReading.id))
        if city_name:
            match = DataNormalizationService.match_canonical_city(city_name)
            name_to_query = match[0] if match else city_name.strip()
            count_stmt = count_stmt.join(City, AQIReading.city_id == City.id).where(
                func.lower(City.name) == name_to_query.lower()
            )
        if station_id:
            count_stmt = count_stmt.where(AQIReading.station_id == station_id)
        if start_date:
            count_stmt = count_stmt.where(AQIReading.measured_at >= start_date)
        if end_date:
            count_stmt = count_stmt.where(AQIReading.measured_at <= end_date)

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
