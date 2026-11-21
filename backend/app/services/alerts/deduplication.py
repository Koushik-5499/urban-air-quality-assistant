"""Deduplication service ensuring alerts are not duplicated across polling runs."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert


class AlertDeduplicator:
    """Manages deterministic alert key generation and active alert deduplication."""

    @staticmethod
    def generate_dedup_key(
        city_id: int,
        station_id: Optional[int],
        alert_type: str,
        current_aqi: int,
        measurement_timestamp: Optional[datetime] = None,
        timestamp: Optional[datetime] = None,
        aqi_value: Optional[int] = None,
    ) -> str:
        """Create a deterministic deduplication string based on observation time and event."""
        ts = measurement_timestamp or timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        aqi = aqi_value if aqi_value is not None else current_aqi

        # Floor measurement timestamp to hour to prevent duplicate alerts within same observation hour
        hour_str = ts.strftime("%Y%m%d%H")
        st_part = str(station_id) if station_id is not None else "city"
        return f"{city_id}:{st_part}:{alert_type}:{aqi}:{hour_str}"

    generate_key = generate_dedup_key

    @classmethod
    def is_duplicate(
        cls,
        db: Session,
        dedup_key: str,
        city_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        station_id: Optional[int] = None,
        dedup_window_hours: int = 2,
        window_hours: Optional[int] = None,
        now_utc: Optional[datetime] = None,
    ) -> bool:
        """Check whether a duplicate alert was already generated within the active deduplication window."""
        ref_time = now_utc or datetime.now(timezone.utc)
        eff_window = window_hours if window_hours is not None else dedup_window_hours
        window_start = ref_time - timedelta(hours=eff_window)

        # 1. Exact dedup_key match
        exact_stmt = (
            select(Alert.id)
            .where(
                Alert.dedup_key == dedup_key,
                Alert.created_at >= window_start,
            )
            .limit(1)
        )
        if db.execute(exact_stmt).scalar_one_or_none() is not None:
            return True

        # 2. Similar active alert for same location and alert_type within recent window
        if city_id is not None and alert_type is not None:
            active_stmt = (
                select(Alert.id)
                .where(
                    Alert.city_id == city_id,
                    Alert.station_id == station_id,
                    Alert.alert_type == alert_type,
                    Alert.created_at >= window_start,
                )
                .limit(1)
            )
            if db.execute(active_stmt).scalar_one_or_none() is not None:
                return True

        return False
