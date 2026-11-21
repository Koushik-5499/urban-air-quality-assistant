"""Builds verified environmental and AQI context snapshots for health guidance."""

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.integrations.ai.schemas import AQIContextSnapshot
from app.models.aqi_reading import AQIReading
from app.services.history.history_service import HistoryService
from app.services.history.validators import HistoryValidator

STALE_THRESHOLD_SECONDS = 18000  # 5 hours


class ContextBuilder:
    """Extracts, verifies, and packages live environmental data into structured context."""

    @classmethod
    def build_snapshot(
        cls,
        db: Session,
        city_name: str,
        station_id: int | None = None,
    ) -> AQIContextSnapshot:
        """Construct verified AQI context snapshot from the database."""
        now_utc = datetime.now(UTC)
        city_entity = HistoryValidator.resolve_city(db, city_name)
        station_entity = HistoryValidator.resolve_station(db, station_id) if station_id else None

        if not city_entity:
            return AQIContextSnapshot(
                city_name=city_name,
                station_id=None,
                station_name=None,
                aqi=None,
                category=None,
                dominant_pollutant=None,
                measurement_timestamp=None,
                data_age_seconds=None,
                is_stale=False,
                is_simulated=False,
                data_source="None",
                trend_direction="insufficient_data",
            )

        # Query latest AQI reading
        query = (
            select(AQIReading)
            .options(joinedload(AQIReading.station))
            .where(AQIReading.city_id == city_entity.id)
        )
        if station_entity:
            query = query.where(AQIReading.station_id == station_entity.id)
        query = query.order_by(desc(AQIReading.measured_at)).limit(1)

        latest_aqi = db.execute(query).scalar_one_or_none()

        # Query recent trend
        trend_resp = HistoryService.get_trends(
            db=db,
            city=city_entity.name,
            station_id=station_entity.id if station_entity else None,
            interval="daily",
            min_records_per_period=2,
        )
        trend_dir = trend_resp.trend_direction

        if not latest_aqi:
            return AQIContextSnapshot(
                city_name=city_entity.name,
                station_id=station_entity.id if station_entity else None,
                station_name=station_entity.station_name if station_entity else None,
                aqi=None,
                category=None,
                dominant_pollutant=None,
                measurement_timestamp=None,
                data_age_seconds=None,
                is_stale=False,
                is_simulated=False,
                data_source="CPCB",
                trend_direction=trend_dir,
            )

        measured_time = latest_aqi.measured_at
        if measured_time.tzinfo is None:
            measured_time = measured_time.replace(tzinfo=UTC)

        data_age = int((now_utc - measured_time).total_seconds())
        is_stale = data_age > STALE_THRESHOLD_SECONDS

        return AQIContextSnapshot(
            city_name=city_entity.name,
            station_id=latest_aqi.station_id,
            station_name=latest_aqi.station.station_name if latest_aqi.station else None,
            aqi=latest_aqi.aqi_value,
            category=latest_aqi.aqi_category,
            dominant_pollutant=latest_aqi.dominant_pollutant,
            measurement_timestamp=measured_time,
            data_age_seconds=data_age,
            is_stale=is_stale,
            is_simulated=latest_aqi.is_simulated,
            data_source=latest_aqi.source,
            trend_direction=trend_dir,
        )

    @classmethod
    def format_context_for_prompt(cls, snapshot: AQIContextSnapshot) -> str:
        """Format verified context into an isolated, factual markdown block."""
        measured_str = (
            snapshot.measurement_timestamp.strftime("%Y-%m-%d %H:%M UTC")
            if snapshot.measurement_timestamp
            else "Unavailable"
        )
        stale_indicator = "STALE (measured over 5 hours ago - exercise caution)" if snapshot.is_stale else "Fresh observation"
        sim_indicator = "Simulated demonstration telemetry" if snapshot.is_simulated else "Official provider observation"

        return (
            f"--- VERIFIED AIR QUALITY OBSERVATION DATA ---\n"
            f"City: {snapshot.city_name}\n"
            f"Monitoring Station: {snapshot.station_name or 'City-wide aggregate'}\n"
            f"Current Composite NAQI: {snapshot.aqi if snapshot.aqi is not None else 'No reading available'}\n"
            f"NAQI Category: {snapshot.category or 'Unknown'}\n"
            f"Dominant Pollutant: {snapshot.dominant_pollutant or 'Unspecified'}\n"
            f"Measurement Timestamp: {measured_str}\n"
            f"Data Freshness Status: {stale_indicator}\n"
            f"Measurement Nature: {sim_indicator}\n"
            f"Recent Trend: {snapshot.trend_direction or 'insufficient_data'}\n"
            f"Source Authority: {snapshot.data_source}\n"
            f"--- END VERIFIED DATA ---"
        )

