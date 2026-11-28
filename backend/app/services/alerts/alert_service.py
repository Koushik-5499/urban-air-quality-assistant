"""Alert and Notification service orchestrating rules, deduplication, and dispatch."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.alert import Alert
from app.models.alert_preference import AlertPreference
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.schemas.alert import (
    AlertPaginatedResponse,
    AlertPreferenceCreate,
    AlertPreferenceResponse,
    AlertProcessResponse,
    AlertResponse,
    AlertStatusResponse,
    AlertTestNotificationRequest,
    AlertTestNotificationResponse,
    AlertUnreadCountResponse,
    PushSubscriptionCreate,
)
from app.services.alerts import alert_preference_service, alert_query_service
from app.services.alerts.alert_generator import AlertGenerator
from app.services.alerts.deduplication import AlertDeduplicator
from app.services.alerts.delivery_tracker import DeliveryTracker
from app.services.alerts.notification_service import NotificationService
from app.services.alerts.threshold_engine import AlertCondition, ThresholdEngine

logger = logging.getLogger(__name__)


class AlertService:
    """Manages environmental condition detection, alert generation, and notifications."""

    _process_lock = asyncio.Lock()
    _last_processed_at: datetime | None = None
    _last_processing_result: str | None = None

    def __init__(
        self,
        notification_service: NotificationService | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.notification_service = notification_service or NotificationService(
            settings=self.settings
        )

    @classmethod
    def _build_alert_filters(
        cls,
        city_entity: City | None,
        station_entity: MonitoringStation | None,
        severity: str | None,
        is_read: bool | None,
        is_simulated: bool | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list:
        """Build SQLAlchemy filter expressions for alert queries."""
        return alert_query_service.build_alert_filters(
            city_entity, station_entity, severity, is_read, is_simulated, start_utc, end_utc
        )

    @staticmethod
    def _map_alert_to_response(a: Alert) -> AlertResponse:
        """Map a single Alert ORM entity to its API response schema."""
        return alert_query_service.map_alert_to_response(a)

    @classmethod
    def list_alerts(
        cls,
        db: Session,
        city: str | None = None,
        station_id: int | None = None,
        severity: str | None = None,
        is_read: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        is_simulated: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> AlertPaginatedResponse:
        """Query paginated alerts with flexible filtering."""
        del user_id  # Platform alerts are public across all monitoring locations
        return alert_query_service.list_alerts(
            db=db,
            city=city,
            station_id=station_id,
            severity=severity,
            is_read=is_read,
            start_date=start_date,
            end_date=end_date,
            is_simulated=is_simulated,
            page=page,
            page_size=page_size,
        )

    @classmethod
    def get_unread_count(
        cls, db: Session, user_id: str = "default_user"
    ) -> AlertUnreadCountResponse:
        """Count all unread active alerts in database."""
        del user_id
        return alert_query_service.get_unread_count(db)

    @classmethod
    def mark_alert_read(cls, db: Session, alert_id: int) -> AlertResponse:
        """Mark a specific alert as read."""
        return alert_query_service.mark_alert_read(db, alert_id)

    @classmethod
    def mark_all_read(cls, db: Session, user_id: str = "default_user") -> AlertUnreadCountResponse:
        """Mark all unread alerts as read."""
        del user_id
        return alert_query_service.mark_all_read(db)

    @classmethod
    def get_preferences(cls, db: Session, user_id: str = "default_user") -> AlertPreferenceResponse:
        """Fetch alert preferences for user or return default preferences."""
        return alert_preference_service.get_preferences(db, user_id=user_id)

    @staticmethod
    def _validate_quiet_hours(start: str | None, end: str | None) -> None:
        """Raise HTTPException if quiet hours format is invalid."""
        alert_preference_service.validate_quiet_hours(start, end)

    @staticmethod
    def _validate_channels(channels: list[str]) -> None:
        """Raise HTTPException if any channel name is unsupported."""
        alert_preference_service.validate_channels(channels)

    @classmethod
    def upsert_preferences(
        cls,
        db: Session,
        pref_in: AlertPreferenceCreate,
        user_id: str = "default_user",
    ) -> AlertPreferenceResponse:
        """Create or update user's alert configuration."""
        return alert_preference_service.upsert_preferences(db, pref_in, user_id=user_id)

    async def _process_condition(
        self,
        db: Session,
        city_id: int,
        station_id: int | None,
        current_reading: AQIReading,
        cond: AlertCondition,
        user_pref: AlertPreference | None,
    ) -> Alert | None:
        """Deduplicate, check quiet hours, and persist a single alert condition."""
        dedup_key = AlertDeduplicator.generate_dedup_key(
            city_id=city_id,
            station_id=station_id,
            alert_type=cond.alert_type,
            current_aqi=cond.current_aqi,
            measurement_timestamp=cond.measurement_timestamp,
        )
        if AlertDeduplicator.is_duplicate(
            db=db, dedup_key=dedup_key, city_id=city_id,
            alert_type=cond.alert_type, station_id=station_id,
        ):
            return None

        _, delivery_status = DeliveryTracker.should_deliver(
            severity=cond.severity,
            quiet_hours_start=user_pref.quiet_hours_start if user_pref else None,
            quiet_hours_end=user_pref.quiet_hours_end if user_pref else None,
            tz_name=user_pref.timezone if user_pref else "Asia/Kolkata",
        )
        alert = AlertGenerator.create_alert_from_condition(
            db=db,
            city_id=city_id,
            condition=cond,
            station_id=station_id,
            aqi_reading_id=current_reading.id,
            expiration_hours=self.settings.ALERT_EXPIRATION_HOURS,
        )
        alert.delivery_status = delivery_status
        db.commit()
        db.refresh(alert)
        return alert

    async def evaluate_and_generate_alerts(
        self,
        db: Session,
        city_id: int,
        station_id: int | None = None,
        user_pref: AlertPreference | None = None,
    ) -> list[Alert]:
        """Evaluate chronological readings for a location and generate deduplicated alerts."""
        query = select(AQIReading).where(AQIReading.city_id == city_id)
        if station_id:
            query = query.where(AQIReading.station_id == station_id)
        query = query.order_by(desc(AQIReading.measured_at)).limit(2)

        readings = list(db.execute(query).scalars().all())
        if not readings:
            return []

        current_reading = readings[0]
        previous_reading = readings[1] if len(readings) > 1 else None

        city_entity = db.get(City, city_id)
        city_name = city_entity.name if city_entity else "Unknown City"
        station_entity = db.get(MonitoringStation, station_id) if station_id else None
        station_name = station_entity.station_name if station_entity else None

        conditions = ThresholdEngine.evaluate_readings(
            current_reading=current_reading,
            previous_reading=previous_reading,
            city_name=city_name,
            station_name=station_name,
            min_threshold=user_pref.min_aqi_threshold if user_pref else 100,
            deterioration_threshold=self.settings.ALERT_DETERIORATION_THRESHOLD,
            improvement_threshold=self.settings.ALERT_IMPROVEMENT_THRESHOLD,
        )

        generated_alerts: list[Alert] = []
        for cond in conditions:
            alert = await self._process_condition(
                db, city_id, station_id, current_reading, cond, user_pref
            )
            if alert:
                generated_alerts.append(alert)

        return generated_alerts

    async def process_all_alerts(self, db: Session) -> AlertProcessResponse:
        """Execute one bounded background alert detection and dispatch cycle across all cities."""
        if self._process_lock.locked():
            return AlertProcessResponse(
                success=False,
                locations_evaluated=0,
                alerts_generated=0,
                notifications_dispatched=0,
                deduplicated_count=0,
                errors=["A processing cycle is already actively executing."],
                processed_at=datetime.now(UTC),
            )

        async with self._process_lock:
            now_utc = datetime.now(UTC)
            cities = list(db.execute(select(City)).scalars().all())

            locations_evaluated = 0
            alerts_generated = 0
            notifications_dispatched = 0
            errors: list[str] = []

            for city in cities:
                locations_evaluated += 1
                try:
                    pref_stmt = (
                        select(AlertPreference).where(AlertPreference.city_id == city.id).limit(1)
                    )
                    user_pref = db.execute(pref_stmt).scalar_one_or_none()

                    alerts = await self.evaluate_and_generate_alerts(
                        db=db,
                        city_id=city.id,
                        user_pref=user_pref,
                    )
                    alerts_generated += len(alerts)
                    notifications_dispatched += sum(
                        1 for a in alerts if "delivered" in a.delivery_status
                    )
                except (SQLAlchemyError, ValueError, RuntimeError, TypeError) as exc:
                    err_msg = f"Error processing alerts for {city.name}: {exc}"
                    logger.error(err_msg)
                    errors.append(err_msg)

            AlertService._last_processed_at = now_utc
            AlertService._last_processing_result = (
                f"Generated {alerts_generated} alerts across {locations_evaluated} locations."
            )

            return AlertProcessResponse(
                success=len(errors) == 0,
                locations_evaluated=locations_evaluated,
                alerts_generated=alerts_generated,
                notifications_dispatched=notifications_dispatched,
                deduplicated_count=0,
                errors=errors,
                processed_at=now_utc,
            )

    def get_status(self) -> AlertStatusResponse:
        """Report engine status, enabled channels, and provider configuration."""
        push_ready = bool(self.settings.WEB_PUSH_ENABLED and self.settings.VAPID_PRIVATE_KEY)

        enabled_channels = ["in_app"]
        if self.settings.WEB_PUSH_ENABLED:
            enabled_channels.append("push")

        return AlertStatusResponse(
            alerts_enabled=self.settings.ALERTS_ENABLED,
            last_processed_at=AlertService._last_processed_at,
            last_processing_result=AlertService._last_processing_result,
            enabled_channels=enabled_channels,
            providers={
                "in_app": True,
                "web_push": push_ready,
            },
        )

    async def send_test_notification(
        self,
        db: Session,
        request: AlertTestNotificationRequest,
    ) -> AlertTestNotificationResponse:
        """Send a test notification via specified channel in development mode."""
        now_utc = datetime.now(UTC)

        if request.channel == "push":
            success_count = await self.notification_service.dispatch_web_push(
                db=db,
                user_id=request.destination or "default_user",
                title=f"Test Alert: {request.city}",
                body=f"Air quality test notification (AQI: {request.aqi}).",
            )
            success = success_count > 0
            msg = f"Dispatched push notification to {success_count} subscriptions."
        else:
            success = True
            msg = f"In-app notification test validated for {request.city}."

        return AlertTestNotificationResponse(
            success=success,
            channel=request.channel,
            destination=request.destination,
            message=msg,
            dispatched_at=now_utc,
        )

    @classmethod
    def register_push_subscription(
        cls,
        db: Session,
        sub_in: PushSubscriptionCreate,
        user_id: str = "default_user",
    ) -> bool:
        """Register or update a browser Web Push subscription."""
        return alert_preference_service.register_push_subscription(db, sub_in, user_id=user_id)
