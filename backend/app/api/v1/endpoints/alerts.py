"""API v1 endpoints for air quality alerts, notifications, preferences, and web push."""

from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import validate_user_id, verify_admin_access
from app.db.session import get_db
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
from app.services.alerts.alert_service import AlertService

router = APIRouter()


def get_alert_service(
    settings: Settings = Depends(get_settings),
) -> AlertService:
    """Dependency provider for AlertService."""
    return AlertService(settings=settings)


@router.get(
    "",
    response_model=AlertPaginatedResponse,
    summary="List air quality alerts",
    description="Retrieve a paginated list of alerts with optional filtering by city, station, severity, read status, and date range.",
)
def get_alerts(
    city: Optional[str] = Query(None, description="Filter by city name"),
    station_id: Optional[int] = Query(None, description="Filter by monitoring station ID"),
    severity: Optional[str] = Query(None, description="Filter by severity: Low, Moderate, High, Critical"),
    is_read: Optional[bool] = Query(None, description="Filter by read status (true/false)"),
    start_date: Optional[datetime] = Query(None, description="Filter alerts created on or after this ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter alerts created on or before this ISO datetime"),
    is_simulated: Optional[bool] = Query(None, description="Filter by simulation status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db),
) -> AlertPaginatedResponse:
    """Return paginated list of alerts."""
    return AlertService.list_alerts(
        db=db,
        user_id=x_user_id,
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


@router.get(
    "/unread-count",
    response_model=AlertUnreadCountResponse,
    summary="Get unread alert count",
    description="Retrieve the total count of unread air quality alerts.",
)
def get_unread_count(
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db),
) -> AlertUnreadCountResponse:
    """Return unread count."""
    return AlertService.get_unread_count(db=db, user_id=x_user_id)


@router.patch(
    "/{alert_id}/read",
    response_model=AlertResponse,
    summary="Mark single alert as read",
    description="Mark a specific alert identified by ID as read.",
)
def mark_alert_read(
    alert_id: int = Path(..., ge=1, description="ID of the alert to mark as read"),
    db: Session = Depends(get_db),
) -> AlertResponse:
    """Mark an alert as read."""
    return AlertService.mark_alert_read(db=db, alert_id=alert_id)


@router.patch(
    "/read-all",
    response_model=AlertUnreadCountResponse,
    summary="Mark all alerts as read",
    description="Mark all unread alerts in the system as read.",
)
def mark_all_alerts_read(
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db),
) -> AlertUnreadCountResponse:
    """Mark all alerts as read."""
    return AlertService.mark_all_read(db=db, user_id=x_user_id)


@router.get(
    "/preferences",
    response_model=AlertPreferenceResponse,
    summary="Get user alert preferences",
    description="Retrieve notification and alert threshold preferences for the requesting user.",
)
def get_user_preferences(
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db),
) -> AlertPreferenceResponse:
    """Fetch user alert preferences or default configuration."""
    return AlertService.get_preferences(db=db, user_id=x_user_id)


@router.put(
    "/preferences",
    response_model=AlertPreferenceResponse,
    summary="Set or update alert preferences",
    description="Save or update notification channels, threshold, quiet hours, and target city/station preferences.",
)
def update_user_preferences(
    preference_in: AlertPreferenceCreate,
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db),
) -> AlertPreferenceResponse:
    """Create or update user alert preferences."""
    return AlertService.upsert_preferences(db=db, pref_in=preference_in, user_id=x_user_id)


@router.post(
    "/process",
    response_model=AlertProcessResponse,
    summary="Trigger alert evaluation and processing run",
    description="Evaluate recent AQI measurements across all locations, detect events, deduplicate, generate alerts, and dispatch notifications. Protected by X-Admin-Secret.",
)
async def process_alerts(
    _admin: None = Depends(verify_admin_access),
    db: Session = Depends(get_db),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertProcessResponse:
    """Trigger one bounded evaluation cycle for all cities and stations."""
    return await alert_service.process_all_alerts(db=db)


@router.get(
    "/status",
    response_model=AlertStatusResponse,
    summary="Get alert engine status",
    description="Check status of the alert engine, last evaluation time, active channels, and configured providers.",
)
def get_alert_status(
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertStatusResponse:
    """Return engine configuration and operational status."""
    return alert_service.get_status()


@router.post(
    "/test-notification",
    response_model=AlertTestNotificationResponse,
    summary="Test notification channel delivery",
    description="Send a test notification via email, web push, or in-app to verify provider credentials and configuration. Protected by X-Admin-Secret.",
)
async def test_notification(
    request: AlertTestNotificationRequest,
    _admin: None = Depends(verify_admin_access),
    db: Session = Depends(get_db),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertTestNotificationResponse:
    """Send a test notification to verify delivery channels."""
    return await alert_service.send_test_notification(db=db, request=request)


@router.post(
    "/push/subscribe",
    response_model=Dict[str, str],
    summary="Register Web Push subscription",
    description="Save or update a browser Web Push subscription (endpoint, p256dh, auth keys) for the requesting user.",
)
def subscribe_push(
    subscription_in: PushSubscriptionCreate,
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Register browser push subscription."""
    AlertService.register_push_subscription(db=db, sub_in=subscription_in, user_id=x_user_id)
    return {"status": "success", "message": "Push subscription registered successfully."}
