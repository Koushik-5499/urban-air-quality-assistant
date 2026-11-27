"""Alert and Notification service orchestrating rules, deduplication, and dispatch."""

import asyncio
import logging
import math
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings, get_settings
from app.models.alert import Alert
from app.models.alert_preference import AlertPreference
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.push_subscription import PushSubscription
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
from app.services.alerts.alert_generator import AlertGenerator
from app.services.alerts.deduplication import AlertDeduplicator
from app.services.alerts.delivery_tracker import DeliveryTracker
from app.services.alerts.notification_service import NotificationService
from app.services.alerts.threshold_engine import AlertCondition, ThresholdEngine
from app.services.history.validators import HistoryValidator

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

    # -----------------------------------------------------------------------
    # In-App Alerts Listing & Management
    # -----------------------------------------------------------------------

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
        filters = []
        if city_entity:
            filters.append(Alert.city_id == city_entity.id)
        if station_entity:
            filters.append(Alert.station_id == station_entity.id)
        if severity:
            filters.append(Alert.severity.ilike(severity.strip()))
        if is_read is not None:
            filters.append(Alert.is_read.is_(is_read))
        if is_simulated is not None:
            filters.append(Alert.is_simulated.is_(is_simulated))
        if start_utc:
            filters.append(Alert.created_at >= start_utc)
        if end_utc:
            filters.append(Alert.created_at <= end_utc)
        return filters

    @staticmethod
    def _map_alert_to_response(a: Alert) -> AlertResponse:
        """Map a single Alert ORM entity to its API response schema."""
        return AlertResponse(
            id=a.id,
            city_id=a.city_id,
            city_name=a.city.name if a.city else None,
            station_id=a.station_id,
            station_name=a.station.station_name if a.station else None,
            aqi_reading_id=a.aqi_reading_id,
            title=a.title,
            description=a.description,
            severity=a.severity,
            alert_type=a.alert_type,
            current_aqi=a.current_aqi,
            previous_aqi=a.previous_aqi,
            threshold_value=a.threshold_value,
            aqi_category=a.aqi_category,
            dominant_pollutant=a.dominant_pollutant,
            source=a.source,
            dedup_key=a.dedup_key,
            delivery_status=a.delivery_status,
            is_read=a.is_read,
            is_simulated=a.is_simulated,
            created_at=a.created_at,
            expires_at=a.expires_at,
        )

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
        page, page_size = HistoryValidator.validate_pagination(page, page_size)
        start_utc, end_utc = HistoryValidator.validate_date_range(
            start_date, end_date, is_aggregated=True
        )

        city_entity = HistoryValidator.resolve_city(db, city) if city else None
        station_entity = HistoryValidator.resolve_station(db, station_id) if station_id else None

        filters = cls._build_alert_filters(
            city_entity, station_entity, severity, is_read, is_simulated, start_utc, end_utc
        )

        # Count total matching alerts
        count_stmt = select(func.count(Alert.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_records = db.execute(count_stmt).scalar() or 0
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

        # Count unread alerts in this query scope
        unread_filters = list(filters)
        if is_read is None:
            unread_filters.append(Alert.is_read.is_(False))
        unread_stmt = select(func.count(Alert.id)).where(*unread_filters)
        unread_count = db.execute(unread_stmt).scalar() or 0

        # Query paginated rows
        data_stmt = select(Alert).options(joinedload(Alert.city), joinedload(Alert.station))
        if filters:
            data_stmt = data_stmt.where(*filters)
        data_stmt = (
            data_stmt.order_by(desc(Alert.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        alert_entities = list(db.execute(data_stmt).scalars().all())
        alert_responses = [cls._map_alert_to_response(a) for a in alert_entities]

        return AlertPaginatedResponse(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            unread_count=unread_count,
            alerts=alert_responses,
        )

    @classmethod
    def get_unread_count(
        cls, db: Session, user_id: str = "default_user"
    ) -> AlertUnreadCountResponse:
        """Count all unread active alerts in database."""
        stmt = select(func.count(Alert.id)).where(Alert.is_read.is_(False))
        count = db.execute(stmt).scalar() or 0
        return AlertUnreadCountResponse(unread_count=count)

    @classmethod
    def mark_alert_read(cls, db: Session, alert_id: int) -> AlertResponse:
        """Mark a specific alert as read."""
        stmt = (
            select(Alert)
            .options(joinedload(Alert.city), joinedload(Alert.station))
            .where(Alert.id == alert_id)
        )
        alert = db.execute(stmt).scalar_one_or_none()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found.",
            )
        alert.is_read = True
        db.commit()
        db.refresh(alert)

        return AlertResponse(
            id=alert.id,
            city_id=alert.city_id,
            city_name=alert.city.name if alert.city else None,
            station_id=alert.station_id,
            station_name=alert.station.station_name if alert.station else None,
            aqi_reading_id=alert.aqi_reading_id,
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            alert_type=alert.alert_type,
            current_aqi=alert.current_aqi,
            previous_aqi=alert.previous_aqi,
            threshold_value=alert.threshold_value,
            aqi_category=alert.aqi_category,
            dominant_pollutant=alert.dominant_pollutant,
            source=alert.source,
            dedup_key=alert.dedup_key,
            delivery_status=alert.delivery_status,
            is_read=alert.is_read,
            is_simulated=alert.is_simulated,
            created_at=alert.created_at,
            expires_at=alert.expires_at,
        )

    @classmethod
    def mark_all_read(cls, db: Session, user_id: str = "default_user") -> AlertUnreadCountResponse:
        """Mark all unread alerts as read."""
        stmt = update(Alert).where(Alert.is_read.is_(False)).values(is_read=True)
        db.execute(stmt)
        db.commit()
        return AlertUnreadCountResponse(unread_count=0)

    # -----------------------------------------------------------------------
    # User Preferences
    # -----------------------------------------------------------------------

    @classmethod
    def get_preferences(cls, db: Session, user_id: str = "default_user") -> AlertPreferenceResponse:
        """Fetch alert preferences for user or return default preferences."""
        stmt = (
            select(AlertPreference)
            .options(joinedload(AlertPreference.city), joinedload(AlertPreference.station))
            .where(AlertPreference.user_id == user_id)
            .limit(1)
        )
        pref = db.execute(stmt).scalar_one_or_none()

        if not pref:
            # Create default preferences for Delhi
            delhi = db.execute(select(City).where(City.name == "Delhi")).scalar_one_or_none()
            if not delhi:
                delhi = db.execute(select(City)).scalars().first()

            city_id = delhi.id if delhi else 1
            city_name = delhi.name if delhi else "Delhi"

            pref = AlertPreference(
                user_id=user_id,
                city_id=city_id,
                station_id=None,
                min_aqi_threshold=100,
                min_severity="Moderate",
                is_enabled=True,
                channels="in_app",
                quiet_hours_start="22:00",
                quiet_hours_end="07:00",
                timezone="Asia/Kolkata",
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
            return AlertPreferenceResponse(
                id=pref.id,
                user_id=pref.user_id,
                city_id=pref.city_id,
                city_name=city_name,
                station_id=pref.station_id,
                station_name=None,
                min_aqi_threshold=pref.min_aqi_threshold,
                min_severity=pref.min_severity,
                is_enabled=pref.is_enabled,
                channels=["in_app"],
                quiet_hours_start=pref.quiet_hours_start,
                quiet_hours_end=pref.quiet_hours_end,
                timezone=pref.timezone,
                created_at=pref.created_at,
                updated_at=pref.updated_at,
            )

        channel_list = [c.strip() for c in pref.channels.split(",") if c.strip()]

        return AlertPreferenceResponse(
            id=pref.id,
            user_id=pref.user_id,
            city_id=pref.city_id,
            city_name=pref.city.name if pref.city else "Delhi",
            station_id=pref.station_id,
            station_name=pref.station.station_name if pref.station else None,
            min_aqi_threshold=pref.min_aqi_threshold,
            min_severity=pref.min_severity,
            is_enabled=pref.is_enabled,
            channels=channel_list,
            quiet_hours_start=pref.quiet_hours_start,
            quiet_hours_end=pref.quiet_hours_end,
            timezone=pref.timezone,
            created_at=pref.created_at,
            updated_at=pref.updated_at,
        )

    @staticmethod
    def _validate_quiet_hours(start: str | None, end: str | None) -> None:
        """Raise HTTPException if quiet hours format is invalid."""
        if not start or not end:
            return
        for val in [start, end]:
            parts = val.split(":")
            try:
                h, m = int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                h, m = -1, -1
            if len(parts) != 2 or not (0 <= h <= 23 and 0 <= m <= 59):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quiet hours must be in valid HH:MM format (00:00 to 23:59).",
                )

    @staticmethod
    def _validate_channels(channels: list[str]) -> None:
        """Raise HTTPException if any channel name is unsupported."""
        valid_channels = {"in_app", "push"}
        for ch in channels:
            if ch not in valid_channels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid channel '{ch}'. Supported: {sorted(list(valid_channels))}.",
                )

    @classmethod
    def upsert_preferences(
        cls,
        db: Session,
        pref_in: AlertPreferenceCreate,
        user_id: str = "default_user",
    ) -> AlertPreferenceResponse:
        """Create or update user's alert configuration."""
        city_entity = HistoryValidator.resolve_city(db, pref_in.city)
        if not city_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City '{pref_in.city}' not found.",
            )

        station_entity = (
            HistoryValidator.resolve_station(db, pref_in.station_id) if pref_in.station_id else None
        )

        cls._validate_quiet_hours(pref_in.quiet_hours_start, pref_in.quiet_hours_end)
        cls._validate_channels(pref_in.channels)

        channels_str = ",".join(pref_in.channels)

        stmt = select(AlertPreference).where(
            AlertPreference.user_id == user_id, AlertPreference.city_id == city_entity.id
        )
        existing = db.execute(stmt).scalar_one_or_none()

        if existing:
            existing.station_id = station_entity.id if station_entity else None
            existing.min_aqi_threshold = pref_in.min_aqi_threshold
            existing.min_severity = pref_in.min_severity
            existing.is_enabled = pref_in.is_enabled
            existing.channels = channels_str
            existing.quiet_hours_start = pref_in.quiet_hours_start
            existing.quiet_hours_end = pref_in.quiet_hours_end
            existing.timezone = pref_in.timezone
            pref = existing
        else:
            pref = AlertPreference(
                user_id=user_id,
                city_id=city_entity.id,
                station_id=station_entity.id if station_entity else None,
                min_aqi_threshold=pref_in.min_aqi_threshold,
                min_severity=pref_in.min_severity,
                is_enabled=pref_in.is_enabled,
                channels=channels_str,
                quiet_hours_start=pref_in.quiet_hours_start,
                quiet_hours_end=pref_in.quiet_hours_end,
                timezone=pref_in.timezone,
            )
            db.add(pref)

        db.commit()
        db.refresh(pref)

        return AlertPreferenceResponse(
            id=pref.id,
            user_id=pref.user_id,
            city_id=pref.city_id,
            city_name=city_entity.name,
            station_id=pref.station_id,
            station_name=station_entity.station_name if station_entity else None,
            min_aqi_threshold=pref.min_aqi_threshold,
            min_severity=pref.min_severity,
            is_enabled=pref.is_enabled,
            channels=pref_in.channels,
            quiet_hours_start=pref.quiet_hours_start,
            quiet_hours_end=pref.quiet_hours_end,
            timezone=pref.timezone,
            created_at=pref.created_at,
            updated_at=pref.updated_at,
        )

    # -----------------------------------------------------------------------
    # Alert Evaluation & Processing
    # -----------------------------------------------------------------------

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
            # In public-only architecture, personal email/push dispatches are disabled.

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
                    # Retrieve user preference if configured for this city
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
                except (SQLAlchemyError, ValueError) as exc:
                    err_msg = f"Error processing alerts for {city.name}: {exc}"
                    logger.error(err_msg)
                    errors.append(err_msg)
                except Exception as exc:
                    # Alert evaluation boundary preventing one failure from halting all cities
                    err_msg = f"Unexpected error processing alerts for {city.name}: {exc}"
                    logger.exception(err_msg)
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
        stmt = select(PushSubscription).where(PushSubscription.endpoint == sub_in.endpoint)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.user_id = user_id
            existing.p256dh = sub_in.p256dh
            existing.auth = sub_in.auth
        else:
            sub = PushSubscription(
                user_id=user_id,
                endpoint=sub_in.endpoint,
                p256dh=sub_in.p256dh,
                auth=sub_in.auth,
            )
            db.add(sub)
        db.commit()
        return True
