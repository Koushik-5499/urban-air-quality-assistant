"""Alert preference validation, CRUD, and Web Push subscription management."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.alert_preference import AlertPreference
from app.models.city import City
from app.models.push_subscription import PushSubscription
from app.schemas.alert import (
    AlertPreferenceCreate,
    AlertPreferenceResponse,
    PushSubscriptionCreate,
)
from app.services.history.validators import HistoryValidator

MAX_HOUR = 23
MAX_MINUTE = 59
DEFAULT_AQI_THRESHOLD = 100


def validate_quiet_hours(start: str | None, end: str | None) -> None:
    """Raise HTTPException if quiet hours format is invalid."""
    if not start or not end:
        return
    for val in [start, end]:
        parts = val.split(":")
        try:
            hour, minute = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            hour, minute = -1, -1
        if len(parts) != 2 or not (0 <= hour <= MAX_HOUR and 0 <= minute <= MAX_MINUTE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiet hours must be in valid HH:MM format (00:00 to 23:59).",
            )


def validate_channels(channels: list[str]) -> None:
    """Raise HTTPException if any channel name is unsupported."""
    valid_channels = {"in_app", "push"}
    for ch in channels:
        if ch not in valid_channels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid channel '{ch}'. Supported: {sorted(list(valid_channels))}.",
            )


def _map_preference_to_response(
    pref: AlertPreference,
    city_name: str,
    station_name: str | None,
    channels: list[str],
) -> AlertPreferenceResponse:
    """Map AlertPreference ORM instance to response schema."""
    return AlertPreferenceResponse(
        id=pref.id,
        user_id=pref.user_id,
        city_id=pref.city_id,
        city_name=city_name,
        station_id=pref.station_id,
        station_name=station_name,
        min_aqi_threshold=pref.min_aqi_threshold,
        min_severity=pref.min_severity,
        is_enabled=pref.is_enabled,
        channels=channels,
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
        timezone=pref.timezone,
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )


def get_preferences(db: Session, user_id: str = "default_user") -> AlertPreferenceResponse:
    """Fetch alert preferences for user or create default preferences."""
    stmt = (
        select(AlertPreference)
        .options(joinedload(AlertPreference.city), joinedload(AlertPreference.station))
        .where(AlertPreference.user_id == user_id)
        .limit(1)
    )
    pref = db.execute(stmt).scalar_one_or_none()

    if not pref:
        delhi = db.execute(select(City).where(City.name == "Delhi")).scalar_one_or_none()
        if not delhi:
            delhi = db.execute(select(City)).scalars().first()

        city_id = delhi.id if delhi else 1
        city_name = delhi.name if delhi else "Delhi"

        pref = AlertPreference(
            user_id=user_id,
            city_id=city_id,
            station_id=None,
            min_aqi_threshold=DEFAULT_AQI_THRESHOLD,
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
        return _map_preference_to_response(pref, city_name, None, ["in_app"])

    channel_list = [c.strip() for c in pref.channels.split(",") if c.strip()]
    return _map_preference_to_response(
        pref,
        pref.city.name if pref.city else "Delhi",
        pref.station.station_name if pref.station else None,
        channel_list,
    )


def upsert_preferences(
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

    validate_quiet_hours(pref_in.quiet_hours_start, pref_in.quiet_hours_end)
    validate_channels(pref_in.channels)
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

    return _map_preference_to_response(
        pref,
        city_entity.name,
        station_entity.station_name if station_entity else None,
        pref_in.channels,
    )


def register_push_subscription(
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

