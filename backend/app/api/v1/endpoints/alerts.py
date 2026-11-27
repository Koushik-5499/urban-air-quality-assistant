"""API v1 endpoints for air quality alerts, notifications, and public advisories."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_admin_scope
from app.db.session import get_db
from app.schemas.alert import (
    AlertPaginatedResponse,
    AlertProcessResponse,
    AlertStatusResponse,
    AlertTestNotificationRequest,
    AlertTestNotificationResponse,
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
    description=(
        "Retrieve a paginated list of public ambient alerts with optional filtering by city, "
        "station, severity, and date range."
    ),
)
def get_alerts(
    city: str | None = Query(None, description="Filter by city name"),
    station_id: int | None = Query(None, description="Filter by monitoring station ID"),
    severity: str | None = Query(
        None, description="Filter by severity: Low, Moderate, High, Critical"
    ),
    is_read: bool | None = Query(None, description="Filter by read status (true/false)"),
    start_date: datetime | None = Query(
        None, description="Filter alerts created on or after this ISO datetime"
    ),
    end_date: datetime | None = Query(
        None, description="Filter alerts created on or before this ISO datetime"
    ),
    is_simulated: bool | None = Query(None, description="Filter by simulation status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    db: Session = Depends(get_db),
) -> AlertPaginatedResponse:
    """Return paginated list of public ambient alerts."""
    return AlertService.list_alerts(
        db=db,
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
    status_code=status.HTTP_410_GONE,
    summary="[Retired] Get unread alert count",
    description=(
        "Retired: The platform operates as a public environmental monitoring service without "
        "personal accounts."
    ),
)
def get_unread_count() -> dict[str, str]:
    """Retired personal endpoint returning HTTP 410 Gone."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "User-specific notification tracking has been retired. All ambient alerts are public."
        ),
    )


@router.patch(
    "/{alert_id}/read",
    status_code=status.HTTP_410_GONE,
    summary="[Retired] Mark single alert as read",
    description=(
        "Retired: The platform operates as a public environmental monitoring service without "
        "personal accounts."
    ),
)
def mark_alert_read(
    alert_id: int = Path(..., ge=1, description="ID of the alert"),
) -> dict[str, str]:
    """Retired personal endpoint returning HTTP 410 Gone."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "User-specific notification management has been retired. All ambient alerts are public."
        ),
    )


@router.patch(
    "/read-all",
    status_code=status.HTTP_410_GONE,
    summary="[Retired] Mark all alerts as read",
    description=(
        "Retired: The platform operates as a public environmental monitoring service without "
        "personal accounts."
    ),
)
def mark_all_alerts_read() -> dict[str, str]:
    """Retired personal endpoint returning HTTP 410 Gone."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "User-specific notification tracking has been retired. All ambient alerts are public."
        ),
    )


@router.get(
    "/preferences",
    status_code=status.HTTP_410_GONE,
    summary="[Retired] Get user alert preferences",
    description=(
        "Retired: The platform operates as a public environmental monitoring service without "
        "personal accounts."
    ),
)
def get_user_preferences() -> dict[str, str]:
    """Retired personal endpoint returning HTTP 410 Gone."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Personal alert preferences have been retired. The platform operates exclusively "
            "as a public environmental monitoring service."
        ),
    )


@router.put(
    "/preferences",
    status_code=status.HTTP_410_GONE,
    summary="[Retired] Set or update alert preferences",
    description=(
        "Retired: The platform operates as a public environmental monitoring service without "
        "personal accounts."
    ),
)
def update_user_preferences() -> dict[str, str]:
    """Retired personal endpoint returning HTTP 410 Gone."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Personal alert preferences have been retired. The platform operates exclusively "
            "as a public environmental monitoring service."
        ),
    )


@router.post(
    "/process",
    response_model=AlertProcessResponse,
    summary="Trigger alert evaluation and processing run",
    description=(
        "Evaluate recent AQI measurements across all locations, detect events, deduplicate, "
        "generate alerts, and dispatch notifications. Protected by X-Admin-Secret."
    ),
)
async def process_alerts(
    _admin: None = Depends(require_admin_scope("alert")),
    db: Session = Depends(get_db),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertProcessResponse:
    """Trigger one bounded evaluation cycle for all cities and stations."""
    return await alert_service.process_all_alerts(db=db)


@router.get(
    "/status",
    response_model=AlertStatusResponse,
    summary="Get alert engine status",
    description=(
        "Check status of the alert engine, last evaluation time, active channels, and "
        "configured providers."
    ),
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
    description=(
        "Send a test notification via web push or in-app to verify provider credentials and "
        "configuration. Protected by X-Admin-Secret."
    ),
)
async def test_notification(
    request: AlertTestNotificationRequest,
    _admin: None = Depends(require_admin_scope("alert")),
    db: Session = Depends(get_db),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertTestNotificationResponse:
    """Send a test notification to verify delivery channels."""
    return await alert_service.send_test_notification(db=db, request=request)


@router.post(
    "/push/subscribe",
    status_code=status.HTTP_410_GONE,
    summary="[Retired] Register Web Push subscription",
    description=(
        "Retired: The platform operates as a public environmental monitoring service without "
        "personal accounts."
    ),
)
def subscribe_push() -> dict[str, str]:
    """Retired personal endpoint returning HTTP 410 Gone."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Personal push subscriptions have been retired. The platform operates exclusively "
            "as a public environmental monitoring service."
        ),
    )
