"""Evaluates quiet hours, recipient timezones, and delivery status tracking."""

from datetime import datetime, time, timezone
import logging
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class DeliveryTracker:
    """Manages quiet hours policy and dispatch status resolution."""

    @classmethod
    def is_in_quiet_hours(
        cls,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        tz_name: str = "Asia/Kolkata",
        current_time_utc: Optional[datetime] = None,
        quiet_start: Optional[str] = None,
        quiet_end: Optional[str] = None,
        user_tz: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> bool:
        """Check if current timestamp falls within the user's local quiet hours window."""
        start_str = quiet_hours_start or quiet_start
        end_str = quiet_hours_end or quiet_end
        zone_str = user_tz or tz_name
        ref_time = current_time_utc or now_utc

        if not start_str or not end_str:
            return False

        try:
            user_zone = ZoneInfo(zone_str)
        except Exception:
            user_zone = ZoneInfo("Asia/Kolkata")

        now = ref_time or datetime.now(timezone.utc)
        user_now = now.astimezone(user_zone)
        current_t = user_now.time()

        try:
            start_parts = [int(p) for p in start_str.split(":")]
            end_parts = [int(p) for p in end_str.split(":")]
            start_t = time(hour=start_parts[0], minute=start_parts[1])
            end_t = time(hour=end_parts[0], minute=end_parts[1])
        except Exception as exc:
            logger.warning("Failed parsing quiet hours '%s'-'%s': %s", start_str, end_str, exc)
            return False

        # Range does not cross midnight (e.g. 13:00 to 15:00)
        if start_t <= end_t:
            return start_t <= current_t <= end_t
        # Range crosses midnight (e.g. 22:00 to 07:00)
        else:
            return current_t >= start_t or current_t <= end_t

    is_quiet_hours = is_in_quiet_hours

    @classmethod
    def should_deliver(
        cls,
        severity: str,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        tz_name: str = "Asia/Kolkata",
        current_time_utc: Optional[datetime] = None,
        quiet_start: Optional[str] = None,
        quiet_end: Optional[str] = None,
        user_tz: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> Tuple[bool, str]:
        """Determine whether an alert should be dispatched immediately or suppressed for quiet hours."""
        start_str = quiet_hours_start or quiet_start
        end_str = quiet_hours_end or quiet_end
        zone_str = user_tz or tz_name
        ref_time = current_time_utc or now_utc

        if not start_str or not end_str:
            return True, "delivered"

        in_quiet = cls.is_in_quiet_hours(
            quiet_hours_start=start_str,
            quiet_hours_end=end_str,
            tz_name=zone_str,
            current_time_utc=ref_time,
        )
        if in_quiet:
            # Critical alerts (Severe AQI) bypass quiet hours for life-safety warnings
            if severity.lower() == "critical":
                return True, "delivered_critical_override"
            return False, "skipped_quiet_hours"

        return True, "delivered"

    @classmethod
    def can_deliver_now(
        cls,
        severity: str,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        tz_name: str = "Asia/Kolkata",
        current_time_utc: Optional[datetime] = None,
        quiet_start: Optional[str] = None,
        quiet_end: Optional[str] = None,
        user_tz: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> bool:
        """Helper returning boolean indicating whether delivery is permitted right now."""
        deliver, _ = cls.should_deliver(
            severity=severity,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            tz_name=tz_name,
            current_time_utc=current_time_utc,
            quiet_start=quiet_start,
            quiet_end=quiet_end,
            user_tz=user_tz,
            now_utc=now_utc,
        )
        return deliver
