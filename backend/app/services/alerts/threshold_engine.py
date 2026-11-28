"""AQI condition detection and threshold evaluation engine."""

from datetime import UTC, datetime

from app.models.aqi_reading import AQIReading
from app.services.alerts.threshold_rules import (
    AlertCondition,
    ReadingContext,
    evaluate_reading_pair,
)

SECONDS_PER_HOUR = 3600
AQI_LOW_SEVERITY_MAX = 100
AQI_MODERATE_SEVERITY_MAX = 200
AQI_HIGH_SEVERITY_MAX = 400

# CPCB NAQI Categories and severity mappings
CATEGORY_SEVERITY_MAP = {
    "Good": "Low",
    "Satisfactory": "Low",
    "Moderate": "Moderate",
    "Moderately Polluted": "Moderate",
    "Poor": "High",
    "Very Poor": "High",
    "Severe": "Critical",
}


class ThresholdEngine:
    """
    Evaluates chronological AQI readings to detect meaningful threshold and category
    transitions.
    """

    @staticmethod
    def get_severity_for_category(category: str | None) -> str:
        """Map CPCB NAQI category to alert severity."""
        if not category:
            return "Moderate"
        for key, sev in CATEGORY_SEVERITY_MAP.items():
            if key.lower() in category.lower():
                return sev
        return "Moderate"

    @staticmethod
    def get_severity_for_aqi(aqi: int) -> str:
        """Map AQI numerical value to alert severity according to NAQI breakpoints."""
        if aqi <= AQI_LOW_SEVERITY_MAX:
            return "Low"
        if aqi <= AQI_MODERATE_SEVERITY_MAX:
            return "Moderate"
        if aqi <= AQI_HIGH_SEVERITY_MAX:
            return "High"
        return "Critical"

    @classmethod
    def check_stale_data(
        cls,
        city_id: int,
        city_name: str,
        last_recorded_at: datetime,
        station_id: int | None = None,
        station_name: str | None = None,
        max_age_hours: int = 24,
    ) -> AlertCondition | None:
        """Detect when station/city monitoring data is older than threshold."""
        now_utc = datetime.now(UTC)
        if last_recorded_at.tzinfo is None:
            last_recorded_at = last_recorded_at.replace(tzinfo=UTC)

        age_seconds = (now_utc - last_recorded_at).total_seconds()
        if age_seconds > max_age_hours * SECONDS_PER_HOUR:
            location_label = f"{city_name} ({station_name})" if station_name else city_name
            return AlertCondition(
                alert_type="STALE_DATA",
                severity="Low",
                title=f"Data Outdated: No recent updates for {location_label}",
                description=(
                    f"The latest air quality observation for {location_label} is more than "
                    f"{max_age_hours} hours old ({int(age_seconds // SECONDS_PER_HOUR)}h elapsed). "
                    "Sensor may be offline or reporting delayed."
                ),
                current_aqi=0,
                previous_aqi=None,
                threshold_value=max_age_hours,
                aqi_category="Unknown",
                dominant_pollutant=None,
                measurement_timestamp=last_recorded_at,
                source="Monitoring Heartbeat",
                is_simulated=False,
            )
        return None

    @classmethod
    def _build_reading_context(
        cls,
        current_reading: AQIReading,
        previous_reading: AQIReading | None,
        city_name: str,
        station_name: str | None,
        min_threshold: int,
        deterioration_threshold: int,
        improvement_threshold: int,
    ) -> ReadingContext:
        """Normalize raw AQIReading ORM rows into an immutable ReadingContext."""
        location_label = f"{city_name} ({station_name})" if station_name else city_name
        curr_time = current_reading.measured_at
        if curr_time.tzinfo is None:
            curr_time = curr_time.replace(tzinfo=UTC)

        is_sim = current_reading.is_simulated
        prev_aqi = previous_reading.aqi_value if previous_reading else None
        prev_cat = previous_reading.aqi_category if previous_reading else None
        prev_dom = previous_reading.dominant_pollutant if previous_reading else None
        cls.get_severity_for_category(prev_cat)

        return ReadingContext(
            curr_aqi=current_reading.aqi_value,
            curr_cat=current_reading.aqi_category,
            curr_dom=current_reading.dominant_pollutant or "particulates",
            curr_time=curr_time,
            curr_severity=cls.get_severity_for_category(current_reading.aqi_category),
            source=current_reading.source,
            is_sim=is_sim,
            sim_prefix="[SIMULATED DATA] " if is_sim else "",
            location_label=location_label,
            min_threshold=min_threshold,
            deterioration_threshold=deterioration_threshold,
            improvement_threshold=improvement_threshold,
            prev_aqi=prev_aqi,
            prev_cat=prev_cat,
            prev_dom=prev_dom,
            aqi_delta=(current_reading.aqi_value - prev_aqi) if prev_aqi is not None else 0,
        )

    @classmethod
    def evaluate_readings(
        cls,
        current_reading: AQIReading,
        previous_reading: AQIReading | None,
        city_name: str,
        station_name: str | None = None,
        min_threshold: int = 100,
        deterioration_threshold: int = 30,
        improvement_threshold: int = 40,
    ) -> list[AlertCondition]:
        """Detect alert events between current and previous AQI observations."""
        ctx = cls._build_reading_context(
            current_reading=current_reading,
            previous_reading=previous_reading,
            city_name=city_name,
            station_name=station_name,
            min_threshold=min_threshold,
            deterioration_threshold=deterioration_threshold,
            improvement_threshold=improvement_threshold,
        )
        return evaluate_reading_pair(ctx, has_previous=previous_reading is not None)
