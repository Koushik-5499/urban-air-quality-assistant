"""AQI data fetching, caching, deduplication, and database persistence."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations.base import BaseAQIProvider, NormalizedObservation
from app.integrations.cpcb.provider import CPCBProvider
from app.integrations.mock.provider import MockAQIProvider
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.pollutant_reading import PollutantReading
from app.schemas.air_quality import (
    CityAirQualityResponse,
    CityAvailabilitySummary,
    PollutantDetail,
    SourceStatusResponse,
    SyncResponse,
)
from app.services.data_normalization_service import DataNormalizationService

logger = get_logger("app.services.aqi_data_service")

# Threshold in seconds after which observation is considered stale (4 hours)
STALE_THRESHOLD_SECONDS = 14400


class AQIDataService:
    """Central business service for air quality ingestion, freshness, and retrieval."""

    def __init__(self, provider: BaseAQIProvider | None = None, settings: Settings | None = None):
        self.settings = settings or get_settings()

        if provider:
            self.provider = provider
        elif self.settings.AQI_PROVIDER.lower() == "mock":
            self.provider = MockAQIProvider()
        else:
            self.provider = CPCBProvider()

        self._sync_lock = asyncio.Lock()
        self._cache: dict[str, Any] = {}
        self._last_successful_fetch: datetime | None = None
        self._last_successful_sync: datetime | None = None
        self._last_error: str | None = None
        self._last_error_category: str | None = None

    async def fetch_provider_observations(
        self,
        city: str | None = None,
        state: str | None = None,
        limit: int = 100,
        bypass_cache: bool = False,
    ) -> list[NormalizedObservation]:
        """Fetch observations from the configured provider with in-memory caching."""
        cache_key = f"{city or 'all'}_{state or 'all'}_{limit}"
        now = datetime.now(UTC)

        # Check cache freshness
        if not bypass_cache and cache_key in self._cache:
            entry = self._cache[cache_key]
            if (now - entry["timestamp"]).total_seconds() < self.settings.AQI_CACHE_TTL_SECONDS:
                return entry["data"]

        try:
            observations = await self.provider.fetch_observations(
                city=city, state=state, limit=limit
            )
            self._cache[cache_key] = {"timestamp": now, "data": observations}
            self._last_successful_fetch = now
            self._last_error = None
            self._last_error_category = None
            return observations
        except Exception as exc:
            # Diagnostics boundary recording upstream provider fetch failures before re-raising
            self._last_error = str(exc)
            self._last_error_category = type(exc).__name__
            logger.error("Failed to fetch provider observations: %s", exc)
            raise

    async def sync_and_persist(
        self,
        db: Session,
        city: str | None = None,
    ) -> SyncResponse:
        """Fetch external observations, normalize, deduplicate, and persist to SQLite."""
        async with self._sync_lock:
            now_utc = datetime.now(UTC)
            observations = await self.fetch_provider_observations(
                city=city, limit=200, bypass_cache=True
            )

            readings_inserted = 0
            stations_created = 0

            # Pre-load all supported cities from the DB for fast lookup
            cities_db = {c.name.lower(): c for c in db.execute(select(City)).scalars().all()}

            for obs in observations:
                # Canonical city match
                match = DataNormalizationService.match_canonical_city(obs.city, obs.state)
                if not match:
                    # Ignore or skip unknown/unsupported cities without crashing
                    continue

                canonical_name, canonical_state = match
                city_entity = cities_db.get(canonical_name.lower())
                if not city_entity:
                    continue

                # Deduplicate or find MonitoringStation
                station_query = select(MonitoringStation).where(
                    MonitoringStation.city_id == city_entity.id,
                    MonitoringStation.station_name == obs.station_name,
                )
                station_entity = db.execute(station_query).scalar_one_or_none()

                if not station_entity:
                    station_entity = MonitoringStation(
                        station_name=obs.station_name,
                        external_station_id=obs.external_station_id,
                        city_id=city_entity.id,
                        latitude=obs.latitude or city_entity.latitude,
                        longitude=obs.longitude or city_entity.longitude,
                        provider=obs.source,
                        is_active=True,
                    )
                    db.add(station_entity)
                    db.flush()
                    stations_created += 1

                # Deduplicate PollutantReading by (city_id, pollutant_code, measured_at, station_id)
                reading_query = select(PollutantReading).where(
                    PollutantReading.city_id == city_entity.id,
                    PollutantReading.pollutant_code == obs.pollutant_code,
                    PollutantReading.measured_at == obs.measured_at,
                    PollutantReading.station_id == station_entity.id,
                )
                existing_reading = db.execute(reading_query).scalar_one_or_none()

                if not existing_reading:
                    new_reading = PollutantReading(
                        city_id=city_entity.id,
                        station_id=station_entity.id,
                        pollutant_code=obs.pollutant_code,
                        concentration=obs.concentration,
                        unit=obs.unit,
                        measured_at=obs.measured_at,
                        source=obs.source,
                        is_simulated=obs.source.upper() == "SIMULATED",
                        data_quality="valid",
                    )
                    db.add(new_reading)
                    readings_inserted += 1

            db.commit()
            self._last_successful_sync = now_utc

            return SyncResponse(
                success=True,
                message=(
                    f"Sync completed successfully. {readings_inserted} new readings "
                    f"recorded across {stations_created} new stations."
                ),
                records_fetched=len(observations),
                readings_inserted=readings_inserted,
                stations_created=stations_created,
                synced_at=now_utc,
            )

    def get_city_air_quality(self, db: Session, city_name: str) -> CityAirQualityResponse:
        """Retrieve real-time observations and freshness metrics for a city."""
        match = DataNormalizationService.match_canonical_city(city_name)
        if not match:
            # Query directly from DB
            statement = select(City).where(func.lower(City.name) == city_name.strip().lower())
            city_entity = db.execute(statement).scalar_one_or_none()
        else:
            canonical_name, _ = match
            statement = select(City).where(City.name == canonical_name)
            city_entity = db.execute(statement).scalar_one_or_none()

        if not city_entity:
            raise KeyError(f"City '{city_name}' is not in the list of supported cities.")

        now_utc = datetime.now(UTC)

        # Retrieve active stations count
        station_count_stmt = select(func.count(MonitoringStation.id)).where(
            MonitoringStation.city_id == city_entity.id,
            MonitoringStation.is_active.is_(True),
        )
        active_stations = db.execute(station_count_stmt).scalar() or 0

        # Query latest readings for each pollutant for this city
        latest_readings_subquery = (
            select(
                PollutantReading.pollutant_code,
                func.max(PollutantReading.measured_at).label("max_measured"),
            )
            .where(PollutantReading.city_id == city_entity.id)
            .group_by(PollutantReading.pollutant_code)
            .subquery()
        )

        pollutant_stmt = (
            select(PollutantReading)
            .join(
                latest_readings_subquery,
                (PollutantReading.pollutant_code == latest_readings_subquery.c.pollutant_code)
                & (PollutantReading.measured_at == latest_readings_subquery.c.max_measured),
            )
            .where(PollutantReading.city_id == city_entity.id)
            .order_by(PollutantReading.pollutant_code)
        )
        readings = list(db.execute(pollutant_stmt).scalars().all())

        if not readings:
            return CityAirQualityResponse(
                city_id=city_entity.id,
                city_name=city_entity.name,
                state=city_entity.state,
                country=city_entity.country,
                data_available=False,
                source=self.provider.get_metadata().provider_name,
                is_simulated=False,
                is_stale=False,
                data_age_seconds=None,
                measured_at=None,
                fetched_at=now_utc,
                pollutants=[],
                active_stations_count=active_stations,
                message=f"No telemetry readings currently recorded for {city_entity.name}.",
            )

        # Find newest timestamp among returned pollutants
        latest_time = max(r.measured_at for r in readings)
        if latest_time.tzinfo is None:
            latest_time = latest_time.replace(tzinfo=UTC)
        data_age = int((now_utc - latest_time).total_seconds())
        is_stale = data_age > STALE_THRESHOLD_SECONDS
        source = readings[0].source

        pollutant_details = [
            PollutantDetail(
                code=r.pollutant_code,
                concentration=r.concentration,
                unit=r.unit,
                measured_at=r.measured_at,
                source=r.source,
            )
            for r in readings
        ]

        return CityAirQualityResponse(
            city_id=city_entity.id,
            city_name=city_entity.name,
            state=city_entity.state,
            country=city_entity.country,
            data_available=True,
            source=source,
            is_simulated=source.upper() == "SIMULATED",
            is_stale=is_stale,
            data_age_seconds=data_age,
            measured_at=latest_time,
            fetched_at=now_utc,
            pollutants=pollutant_details,
            active_stations_count=active_stations,
            message="Fresh ambient observations available"
            if not is_stale
            else "Readings exceed freshness threshold",
        )

    def get_cities_summary(self, db: Session) -> list[CityAvailabilitySummary]:
        """Return data availability and freshness summary for all registered cities."""
        now_utc = datetime.now(UTC)
        cities = list(db.execute(select(City).order_by(City.name)).scalars().all())
        results: list[CityAvailabilitySummary] = []

        for city in cities:
            # Query station count
            station_count = (
                db.execute(
                    select(func.count(MonitoringStation.id)).where(
                        MonitoringStation.city_id == city.id
                    )
                ).scalar()
                or 0
            )

            # Query newest measured_at
            latest_time = db.execute(
                select(func.max(PollutantReading.measured_at)).where(
                    PollutantReading.city_id == city.id
                )
            ).scalar()

            if latest_time is not None:
                if latest_time.tzinfo is None:
                    latest_time = latest_time.replace(tzinfo=UTC)
                data_age = int((now_utc - latest_time).total_seconds())
                is_stale = data_age > STALE_THRESHOLD_SECONDS
                results.append(
                    CityAvailabilitySummary(
                        city_id=city.id,
                        city_name=city.name,
                        state=city.state,
                        country=city.country,
                        data_available=True,
                        last_measured_at=latest_time,
                        is_stale=is_stale,
                        station_count=station_count,
                        source="CPCB",
                    )
                )
            else:
                results.append(
                    CityAvailabilitySummary(
                        city_id=city.id,
                        city_name=city.name,
                        state=city.state,
                        country=city.country,
                        data_available=False,
                        last_measured_at=None,
                        is_stale=False,
                        station_count=station_count,
                        source="CPCB",
                    )
                )

        return results

    def get_source_status(self) -> SourceStatusResponse:
        """Return operational diagnostics for the current active provider."""
        meta = self.provider.get_metadata()

        if not meta.is_configured and self.settings.AQI_PROVIDER == "cpcb":
            freshness_status = "unconfigured"
        elif self._last_successful_fetch is None:
            freshness_status = "no_data"
        else:
            age = (datetime.now(UTC) - self._last_successful_fetch).total_seconds()
            freshness_status = (
                "fresh" if age <= self.settings.AQI_CACHE_TTL_SECONDS * 2 else "stale"
            )

        return SourceStatusResponse(
            provider_name=meta.provider_name,
            dataset_title=meta.dataset_title,
            publisher=meta.publisher,
            license=meta.license,
            base_url=meta.base_url,
            resource_id=meta.resource_id,
            is_configured=meta.is_configured,
            last_successful_fetch=self._last_successful_fetch,
            last_successful_sync=self._last_successful_sync,
            data_freshness_status=freshness_status,
            last_error_category=self._last_error_category,
        )


# Global singleton instance for service state reuse
_aqi_service_instance: AQIDataService | None = None


def get_aqi_data_service() -> AQIDataService:
    """Retrieve or initialize the AQIDataService singleton."""
    global _aqi_service_instance
    if _aqi_service_instance is None:
        _aqi_service_instance = AQIDataService()
    return _aqi_service_instance
