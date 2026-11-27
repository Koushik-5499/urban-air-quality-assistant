"""Evaluates quiet hours, recipient timezones, and delivery status tracking."""

import logging
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _resolve_quiet_params(
    quiet_hours_start: str | None,
    quiet_hours_end: str | None,
    tz_name: str,
    current_time_utc: datetime | None,
    quiet_start: str | None,
    quiet_end: str | None,
    user_tz: str | None,
    now_utc: datetime | None,
) -> tuple[str | None, str | None, str, datetime | None]:
    """Merge aliased parameter pairs into canonical quiet-hours arguments."""
    return (
        quiet_hours_start or quiet_start,
        quiet_hours_end or quiet_end,
        user_tz or tz_name,
        current_time_utc or now_utc,
    )


def _parse_time_str(time_str: str) -> time:
    """Parse 'HH:MM' string into a datetime.time object."""
    parts = [int(p) for p in time_str.split(":")]
    return time(hour=parts[0], minute=parts[1])


def _is_time_in_window(current_t: time, start_t: time, end_t: time) -> bool:
    """Return True if current_t falls within [start_t, end_t], handling midnight crossing."""
    if start_t <= end_t:
        return start_t <= current_t <= end_t
    # Range crosses midnight (e.g. 22:00 to 07:00)
    return current_t >= start_t or current_t <= end_t


class DeliveryTracker:
    """Manages quiet hours policy and dispatch status resolution."""

    @classmethod
    def is_in_quiet_hours(
        cls,
        quiet_hours_start: str | None = None,
        quiet_hours_end: str | None = None,
        tz_name: str = "Asia/Kolkata",
        current_time_utc: datetime | None = None,
        quiet_start: str | None = None,
        quiet_end: str | None = None,
        user_tz: str | None = None,
        now_utc: datetime | None = None,
    ) -> bool:
        """Check if current timestamp falls within the user's local quiet hours window."""
        start_str, end_str, zone_str, ref_time = _resolve_quiet_params(
            quiet_hours_start, quiet_hours_end, tz_name,
            current_time_utc, quiet_start, quiet_end, user_tz, now_utc,
        )

        if not start_str or not end_str:
            return False

        try:
            user_zone = ZoneInfo(zone_str)
        except (KeyError, ValueError, TypeError):
            user_zone = ZoneInfo("Asia/Kolkata")

        user_now = (ref_time or datetime.now(UTC)).astimezone(user_zone)
        current_t = user_now.time()

        try:
            start_t = _parse_time_str(start_str)
            end_t = _parse_time_str(end_str)
        except (ValueError, IndexError) as exc:
            logger.warning("Failed parsing quiet hours '%s'-'%s': %s", start_str, end_str, exc)
            return False

        return _is_time_in_window(current_t, start_t, end_t)

    is_quiet_hours = is_in_quiet_hours

    @classmethod
    def should_deliver(
        cls,
        severity: str,
        quiet_hours_start: str | None = None,
        quiet_hours_end: str | None = None,
        tz_name: str = "Asia/Kolkata",
        current_time_utc: datetime | None = None,
        quiet_start: str | None = None,
        quiet_end: str | None = None,
        user_tz: str | None = None,
        now_utc: datetime | None = None,
    ) -> tuple[bool, str]:
        """Determine whether an alert should be dispatched or suppressed for quiet hours."""
        start_str, end_str, zone_str, ref_time = _resolve_quiet_params(
            quiet_hours_start, quiet_hours_end, tz_name,
            current_time_utc, quiet_start, quiet_end, user_tz, now_utc,
        )

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
        quiet_hours_start: str | None = None,
        quiet_hours_end: str | None = None,
        tz_name: str = "Asia/Kolkata",
        current_time_utc: datetime | None = None,
        quiet_start: str | None = None,
        quiet_end: str | None = None,
        user_tz: str | None = None,
        now_utc: datetime | None = None,
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
