"""AQI condition detection and threshold evaluation engine."""

from datetime import UTC, datetime

from pydantic import BaseModel

from app.models.aqi_reading import AQIReading

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


class AlertCondition(BaseModel):
    """Detected alert condition metadata."""

    alert_type: str
    severity: str
    title: str
    description: str
    current_aqi: int
    previous_aqi: int | None
    threshold_value: int | None
    aqi_category: str
    dominant_pollutant: str | None
    measurement_timestamp: datetime
    source: str
    is_simulated: bool


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
        if aqi <= 100:
            return "Low"
        if aqi <= 200:
            return "Moderate"
        if aqi <= 400:
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
        if age_seconds > max_age_hours * 3600:
            location_label = f"{city_name} ({station_name})" if station_name else city_name
            return AlertCondition(
                alert_type="STALE_DATA",
                severity="Low",
                title=f"Data Outdated: No recent updates for {location_label}",
                description=(
                    f"The latest air quality observation for {location_label} is more than "
                    f"{max_age_hours} hours old ({int(age_seconds // 3600)}h elapsed). "
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
        conditions: list[AlertCondition] = []
        location_label = f"{city_name} ({station_name})" if station_name else city_name

        curr_aqi = current_reading.aqi_value
        curr_cat = current_reading.aqi_category
        curr_dom = current_reading.dominant_pollutant or "particulates"
        curr_time = current_reading.measured_at
        if curr_time.tzinfo is None:
            curr_time = curr_time.replace(tzinfo=UTC)

        curr_severity = cls.get_severity_for_category(curr_cat)
        source = current_reading.source
        is_sim = current_reading.is_simulated
        sim_prefix = "[SIMULATED DATA] " if is_sim else ""

        # Scenario 1: Initial observation crossing minimum threshold (no previous reading)
        if not previous_reading:
            if curr_aqi >= min_threshold:
                conditions.append(
                    AlertCondition(
                        alert_type="THRESHOLD_CROSSING",
                        severity=curr_severity,
                        title=f"{sim_prefix}Air Quality Alert: {curr_cat} in {location_label}",
                        description=(
                            f"Current AQI is {curr_aqi} ({curr_cat}), "
                            f"driven primarily by {curr_dom}. "
                            f"Air quality has reached elevated pollution levels."
                        ),
                        current_aqi=curr_aqi,
                        previous_aqi=None,
                        threshold_value=min_threshold,
                        aqi_category=curr_cat,
                        dominant_pollutant=curr_dom,
                        measurement_timestamp=curr_time,
                        source=source,
                        is_simulated=is_sim,
                    )
                )
            return conditions

        prev_aqi = previous_reading.aqi_value
        prev_cat = previous_reading.aqi_category
        prev_dom = previous_reading.dominant_pollutant
        cls.get_severity_for_category(prev_cat)  # side-effect: validates category enum

        aqi_delta = curr_aqi - prev_aqi

        # Scenario 2: Category Transition (e.g. Moderate -> Poor, or Poor -> Very Poor)
        if curr_cat != prev_cat:
            # Worsening category change
            if curr_aqi > prev_aqi and curr_aqi >= min_threshold:
                conditions.append(
                    AlertCondition(
                        alert_type="CATEGORY_CHANGE",
                        severity=curr_severity,
                        title=f"{sim_prefix}Air Quality Worsened to {curr_cat} in {location_label}",
                        description=(
                            f"AQI transitioned from {prev_aqi} ({prev_cat}) "
                            f"to {curr_aqi} ({curr_cat}). "
                            f"Dominant pollutant is {curr_dom}. "
                            f"Increased health precautions are advised."
                        ),
                        current_aqi=curr_aqi,
                        previous_aqi=prev_aqi,
                        threshold_value=min_threshold,
                        aqi_category=curr_cat,
                        dominant_pollutant=curr_dom,
                        measurement_timestamp=curr_time,
                        source=source,
                        is_simulated=is_sim,
                    )
                )
            # Significant improvement category change
            elif curr_aqi < prev_aqi and abs(aqi_delta) >= improvement_threshold:
                conditions.append(
                    AlertCondition(
                        alert_type="IMPROVEMENT",
                        severity="Low",
                        title=f"{sim_prefix}Air Quality Improved to {curr_cat} in {location_label}",
                        description=(
                            f"AQI improved significantly by {abs(aqi_delta)} points, "
                            f"dropping from {prev_aqi} ({prev_cat}) "
                            f"to {curr_aqi} ({curr_cat})."
                        ),
                        current_aqi=curr_aqi,
                        previous_aqi=prev_aqi,
                        threshold_value=min_threshold,
                        aqi_category=curr_cat,
                        dominant_pollutant=curr_dom,
                        measurement_timestamp=curr_time,
                        source=source,
                        is_simulated=is_sim,
                    )
                )

        # Scenario 3: Sudden Deterioration Spike (even if within same category)
        elif aqi_delta >= deterioration_threshold and curr_aqi >= min_threshold:
            conditions.append(
                AlertCondition(
                    alert_type="DETERIORATION",
                    severity=curr_severity,
                    title=f"{sim_prefix}Sudden Pollution Spike in {location_label}",
                    description=(
                        f"AQI spiked by +{aqi_delta} points (from {prev_aqi} to {curr_aqi}) "
                        f"within the recent monitoring period. "
                        f"Category remains {curr_cat} with {curr_dom} as dominant pollutant."
                    ),
                    current_aqi=curr_aqi,
                    previous_aqi=prev_aqi,
                    threshold_value=deterioration_threshold,
                    aqi_category=curr_cat,
                    dominant_pollutant=curr_dom,
                    measurement_timestamp=curr_time,
                    source=source,
                    is_simulated=is_sim,
                )
            )

        # Scenario 4: User-defined threshold crossing (prev was below, current is above)
        elif prev_aqi < min_threshold <= curr_aqi:
            conditions.append(
                AlertCondition(
                    alert_type="THRESHOLD_CROSSING",
                    severity=curr_severity,
                    title=(
                        f"{sim_prefix}AQI Crossed Threshold ({min_threshold}) in {location_label}"
                    ),
                    description=(
                        f"AQI has crossed your alert threshold of {min_threshold}. "
                        f"Current AQI is {curr_aqi} ({curr_cat}), "
                        f"up from {prev_aqi}."
                    ),
                    current_aqi=curr_aqi,
                    previous_aqi=prev_aqi,
                    threshold_value=min_threshold,
                    aqi_category=curr_cat,
                    dominant_pollutant=curr_dom,
                    measurement_timestamp=curr_time,
                    source=source,
                    is_simulated=is_sim,
                )
            )

        # Scenario 5: Dominant Pollutant Change (at elevated AQI levels)
        if prev_dom and curr_dom != prev_dom and curr_aqi >= 150:
            conditions.append(
                AlertCondition(
                    alert_type="POLLUTANT_CHANGE",
                    severity=curr_severity,
                    title=f"{sim_prefix}Dominant Pollutant Shift in {location_label}",
                    description=(
                        f"Primary pollution driver shifted from {prev_dom} to {curr_dom}. "
                        f"Current AQI is {curr_aqi} ({curr_cat})."
                    ),
                    current_aqi=curr_aqi,
                    previous_aqi=prev_aqi,
                    threshold_value=None,
                    aqi_category=curr_cat,
                    dominant_pollutant=curr_dom,
                    measurement_timestamp=curr_time,
                    source=source,
                    is_simulated=is_sim,
                )
            )

        return conditions
