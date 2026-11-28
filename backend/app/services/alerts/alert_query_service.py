"""Query and read-state management helpers for AlertService."""

import math
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.alert import Alert
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.schemas.alert import (
    AlertPaginatedResponse,
    AlertResponse,
    AlertUnreadCountResponse,
)
from app.services.history.validators import HistoryValidator


def build_alert_filters(
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


def map_alert_to_response(alert: Alert) -> AlertResponse:
    """Map a single Alert ORM entity to its API response schema."""
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


def list_alerts(
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
) -> AlertPaginatedResponse:
    """Query paginated alerts with flexible filtering."""
    page, page_size = HistoryValidator.validate_pagination(page, page_size)
    start_utc, end_utc = HistoryValidator.validate_date_range(
        start_date, end_date, is_aggregated=True
    )

    city_entity = HistoryValidator.resolve_city(db, city) if city else None
    station_entity = HistoryValidator.resolve_station(db, station_id) if station_id else None

    filters = build_alert_filters(
        city_entity, station_entity, severity, is_read, is_simulated, start_utc, end_utc
    )

    count_stmt = select(func.count(Alert.id))
    if filters:
        count_stmt = count_stmt.where(*filters)
    total_records = db.execute(count_stmt).scalar() or 0
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

    unread_filters = list(filters)
    if is_read is None:
        unread_filters.append(Alert.is_read.is_(False))
    unread_stmt = select(func.count(Alert.id)).where(*unread_filters)
    unread_count = db.execute(unread_stmt).scalar() or 0

    data_stmt = select(Alert).options(joinedload(Alert.city), joinedload(Alert.station))
    if filters:
        data_stmt = data_stmt.where(*filters)
    data_stmt = (
        data_stmt.order_by(desc(Alert.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    alert_entities = list(db.execute(data_stmt).scalars().all())
    alert_responses = [map_alert_to_response(a) for a in alert_entities]

    return AlertPaginatedResponse(
        page=page,
        page_size=page_size,
        total_records=total_records,
        total_pages=total_pages,
        unread_count=unread_count,
        alerts=alert_responses,
    )


def get_unread_count(db: Session) -> AlertUnreadCountResponse:
    """Count all unread active alerts in database."""
    stmt = select(func.count(Alert.id)).where(Alert.is_read.is_(False))
    count = db.execute(stmt).scalar() or 0
    return AlertUnreadCountResponse(unread_count=count)


def mark_alert_read(db: Session, alert_id: int) -> AlertResponse:
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
    return map_alert_to_response(alert)


def mark_all_read(db: Session) -> AlertUnreadCountResponse:
    """Mark all unread alerts as read."""
    stmt = update(Alert).where(Alert.is_read.is_(False)).values(is_read=True)
    db.execute(stmt)
    db.commit()
    return AlertUnreadCountResponse(unread_count=0)

