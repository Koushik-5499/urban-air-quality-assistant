"""Generates persistent Alert database entities grounded in knowledge-base health precautions."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.services.alerts.deduplication import AlertDeduplicator
from app.services.alerts.threshold_engine import AlertCondition
from app.services.health.knowledge_base import HealthKnowledgeBase


class AlertGenerator:
    """Creates structured Alert records with health precautions and expiration timestamps."""

    @classmethod
    def create_alert_from_condition(
        cls,
        db: Session,
        city_id: int,
        condition: AlertCondition,
        station_id: int | None = None,
        aqi_reading_id: int | None = None,
        expiration_hours: int = 24,
    ) -> Alert:
        """Create and populate a new Alert model instance."""
        now_utc = datetime.now(UTC)
        expires_at = now_utc + timedelta(hours=expiration_hours)

        # Generate deterministic deduplication key
        dedup_key = AlertDeduplicator.generate_dedup_key(
            city_id=city_id,
            station_id=station_id,
            alert_type=condition.alert_type,
            current_aqi=condition.current_aqi,
            measurement_timestamp=condition.measurement_timestamp,
        )

        # Retrieve protective precautions from health knowledge base
        guideline = HealthKnowledgeBase.get_category_guideline(condition.aqi_category)
        precautions_text = ""
        if guideline.precautions:
            precautions_text = f" Recommended precautions: {guideline.precautions[0]}"

        full_description = f"{condition.description}{precautions_text}"

        alert = Alert(
            city_id=city_id,
            station_id=station_id,
            aqi_reading_id=aqi_reading_id,
            title=condition.title,
            description=full_description,
            severity=condition.severity,
            alert_type=condition.alert_type,
            current_aqi=condition.current_aqi,
            previous_aqi=condition.previous_aqi,
            threshold_value=condition.threshold_value,
            aqi_category=condition.aqi_category,
            dominant_pollutant=condition.dominant_pollutant,
            source=condition.source,
            dedup_key=dedup_key,
            delivery_status="delivered",
            is_read=False,
            is_simulated=condition.is_simulated,
            created_at=now_utc,
            expires_at=expires_at,
        )

        db.add(alert)
        return alert
