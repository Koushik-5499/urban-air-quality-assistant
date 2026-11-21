"""Pydantic schemas for air quality alerts, notifications, preferences, and subscriptions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertBase(BaseModel):
    """Base alert attributes."""

    city_id: int = Field(..., description="Foreign key to city")
    station_id: int | None = Field(None, description="Optional foreign key to monitoring station")
    aqi_reading_id: int | None = Field(None, description="Associated AQI reading if triggered by index")
    title: str = Field(..., max_length=200, description="Alert title")
    description: str = Field(..., description="Detailed alert explanation and guidance")
    severity: str = Field(..., max_length=50, description="Severity: Low, Moderate, High, Critical")
    alert_type: str = Field(..., max_length=100, description="Type: CATEGORY_CHANGE, THRESHOLD_CROSSING, DETERIORATION, IMPROVEMENT, STALE_DATA")
    current_aqi: int | None = Field(None, description="Current AQI value triggering the alert")
    previous_aqi: int | None = Field(None, description="Previous AQI value for transition tracking")
    threshold_value: int | None = Field(None, description="Threshold level crossed")
    aqi_category: str | None = Field(None, description="Current NAQI category")
    dominant_pollutant: str | None = Field(None, description="Primary pollutant driver")
    source: str = Field(default="CPCB", max_length=100, description="Data source")
    dedup_key: str | None = Field(None, max_length=200, description="Deterministic deduplication key")
    delivery_status: str = Field(default="delivered", max_length=50, description="Notification delivery status")
    is_read: bool = Field(default=False, description="Whether alert was acknowledged by user")
    is_simulated: bool = Field(default=False, description="Whether alert is from simulated data")
    expires_at: datetime | None = Field(None, description="Expiration time in UTC")


class AlertCreate(AlertBase):
    """Payload for creating a new alert."""

    pass


class AlertUpdate(BaseModel):
    """Payload for updating an existing alert."""

    title: str | None = Field(None, max_length=200)
    description: str | None = None
    severity: str | None = Field(None, max_length=50)
    is_read: bool | None = None
    expires_at: datetime | None = None


class AlertResponse(AlertBase):
    """Full alert response representation."""

    id: int
    city_name: str | None = Field(None, description="Associated city name")
    station_name: str | None = Field(None, description="Associated station name")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertPaginatedResponse(BaseModel):
    """Paginated response containing list of alerts."""

    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Page size")
    total_records: int = Field(..., ge=0, description="Total matching alerts")
    total_pages: int = Field(..., ge=0, description="Total pages")
    unread_count: int = Field(default=0, description="Total unread alerts in this query scope")
    alerts: list[AlertResponse] = Field(default_factory=list, description="List of alert records")


class AlertUnreadCountResponse(BaseModel):
    """Response containing unread count."""

    unread_count: int = Field(..., ge=0, description="Number of unread alerts")


class AlertPreferenceBase(BaseModel):
    """Base user alert preference schema."""

    city: str = Field(..., min_length=1, max_length=100, description="City name for notifications")
    station_id: int | None = Field(None, description="Optional specific station ID")
    min_aqi_threshold: int = Field(default=100, ge=0, le=500, description="Minimum AQI triggering alert")
    min_severity: str = Field(default="Moderate", description="Minimum severity to receive notifications for")
    is_enabled: bool = Field(default=True, description="Whether notifications are active")
    channels: list[str] = Field(default_factory=lambda: ["in_app"], description="Preferred channels: 'in_app', 'push'")
    quiet_hours_start: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="HH:MM start of quiet hours")
    quiet_hours_end: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="HH:MM end of quiet hours")
    timezone: str = Field(default="Asia/Kolkata", max_length=50, description="User timezone (IANA format)")


class AlertPreferenceCreate(AlertPreferenceBase):
    """Payload for setting or updating preferences."""

    pass


class AlertPreferenceResponse(BaseModel):
    """Representation of saved user preferences."""

    id: int
    user_id: str
    city_id: int
    city_name: str
    station_id: int | None
    station_name: str | None
    min_aqi_threshold: int
    min_severity: str
    is_enabled: bool
    channels: list[str]
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PushSubscriptionCreate(BaseModel):
    """Browser Web Push subscription payload."""

    endpoint: str = Field(..., description="Browser push service endpoint URL")
    p256dh: str = Field(..., description="User client public key (p256dh)")
    auth: str = Field(..., description="User client authentication secret")


class AlertProcessResponse(BaseModel):
    """Summary of a background alert processing run."""

    success: bool
    locations_evaluated: int
    alerts_generated: int
    notifications_dispatched: int
    deduplicated_count: int
    errors: list[str] = Field(default_factory=list)
    processed_at: datetime


class AlertStatusResponse(BaseModel):
    """Status of the alerts and notifications engine."""

    alerts_enabled: bool
    last_processed_at: datetime | None
    last_processing_result: str | None
    enabled_channels: list[str]
    providers: dict[str, bool]


class AlertTestNotificationRequest(BaseModel):
    """Payload for development-only notification channel testing."""

    channel: str = Field(..., pattern=r"^(push|in_app)$", description="Target test channel")
    destination: str | None = Field(None, description="Destination email or subscription endpoint")
    city: str = Field(default="Delhi", description="Test city name")
    aqi: int = Field(default=220, ge=0, le=500, description="Test AQI value")
    category: str = Field(default="Poor", description="Test category")


class AlertTestNotificationResponse(BaseModel):
    """Response from development-only notification test."""

    success: bool
    channel: str
    destination: str | None
    message: str
    dispatched_at: datetime
