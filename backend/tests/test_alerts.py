"""Comprehensive test suite for Phase 7: Alerts & Notifications."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.alert import Alert
from app.models.alert_preference import AlertPreference
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.push_subscription import PushSubscription
from app.schemas.alert import AlertPreferenceCreate, AlertTestNotificationRequest, PushSubscriptionCreate
from app.services.alerts.alert_generator import AlertGenerator
from app.services.alerts.alert_service import AlertService
from app.services.alerts.deduplication import AlertDeduplicator
from app.services.alerts.delivery_tracker import DeliveryTracker
from app.services.alerts.notification_service import NotificationService
from app.services.alerts.threshold_engine import AlertCondition, ThresholdEngine


@pytest.fixture
def alert_seed_data(db_session: Session):
    """Seed test database with cities, stations, AQI readings, and alerts."""
    now_utc = datetime.now(timezone.utc)

    # 1. Cities
    delhi = City(
        name="Delhi",
        state="Delhi",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
    )
    bengaluru = City(
        name="Bengaluru",
        state="Karnataka",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
    )
    db_session.add_all([delhi, bengaluru])
    db_session.flush()

    # 2. Stations
    delhi_station = MonitoringStation(
        station_name="Anand Vihar CAAQMS",
        external_station_id="DEL_AV_01",
        city_id=delhi.id,
        latitude=28.6469,
        longitude=77.3160,
        provider="CPCB",
        is_active=True,
    )
    bengaluru_station = MonitoringStation(
        station_name="BTM Layout CAAQMS",
        external_station_id="BLR_BTM_01",
        city_id=bengaluru.id,
        latitude=12.9166,
        longitude=77.6101,
        provider="CPCB",
        is_active=True,
    )
    db_session.add_all([delhi_station, bengaluru_station])
    db_session.flush()

    # 3. Readings
    delhi_reading_old = AQIReading(
        city_id=delhi.id,
        station_id=delhi_station.id,
        aqi_value=180,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        source="CPCB",
        is_simulated=False,
        measured_at=now_utc - timedelta(hours=2),
    )
    delhi_reading_curr = AQIReading(
        city_id=delhi.id,
        station_id=delhi_station.id,
        aqi_value=240,
        aqi_category="Poor",
        dominant_pollutant="PM2.5",
        source="CPCB",
        is_simulated=False,
        measured_at=now_utc - timedelta(minutes=15),
    )
    db_session.add_all([delhi_reading_old, delhi_reading_curr])
    db_session.flush()

    # 4. Alerts
    alert1 = Alert(
        city_id=delhi.id,
        station_id=delhi_station.id,
        aqi_reading_id=delhi_reading_curr.id,
        title="Air Quality Deteriorated to Poor",
        description="Air quality has entered the Poor category (AQI: 240). Breathing discomfort to most people on prolonged exposure.",
        severity="High",
        alert_type="CATEGORY_CHANGE",
        current_aqi=240,
        previous_aqi=180,
        threshold_value=200,
        aqi_category="Poor",
        dominant_pollutant="PM2.5",
        source="CPCB",
        dedup_key="test_delhi_cat_change_1",
        delivery_status="delivered",
        is_read=False,
        is_simulated=False,
        created_at=now_utc - timedelta(minutes=10),
        expires_at=now_utc + timedelta(hours=24),
    )
    alert2 = Alert(
        city_id=delhi.id,
        station_id=delhi_station.id,
        title="[Simulated] Air Quality Deterioration Spike",
        description="AQI deteriorated by 45 points in the past hour. Sensitive individuals should reduce outdoor activities.",
        severity="Moderate",
        alert_type="DETERIORATION",
        current_aqi=190,
        previous_aqi=145,
        threshold_value=30,
        aqi_category="Moderate",
        dominant_pollutant="PM10",
        source="Simulated Engine",
        dedup_key="test_delhi_deterioration_1",
        delivery_status="delivered",
        is_read=True,
        is_simulated=True,
        created_at=now_utc - timedelta(hours=1),
        expires_at=now_utc + timedelta(hours=23),
    )
    db_session.add_all([alert1, alert2])
    db_session.flush()

    return {
        "delhi": delhi,
        "bengaluru": bengaluru,
        "delhi_station": delhi_station,
        "bengaluru_station": bengaluru_station,
        "alert1": alert1,
        "alert2": alert2,
    }


# ===========================================================================
# 1. Threshold Engine Unit Tests
# ===========================================================================


def test_severity_mapping():
    """Verify NAQI AQI severity mapping according to CPCB guidelines."""
    assert ThresholdEngine.get_severity_for_aqi(25) == "Low"  # Good
    assert ThresholdEngine.get_severity_for_aqi(85) == "Low"  # Satisfactory
    assert ThresholdEngine.get_severity_for_aqi(150) == "Moderate"  # Moderate
    assert ThresholdEngine.get_severity_for_aqi(250) == "High"  # Poor
    assert ThresholdEngine.get_severity_for_aqi(350) == "High"  # Very Poor
    assert ThresholdEngine.get_severity_for_aqi(450) == "Critical"  # Severe

    assert ThresholdEngine.get_severity_for_category("Good") == "Low"
    assert ThresholdEngine.get_severity_for_category("Satisfactory") == "Low"
    assert ThresholdEngine.get_severity_for_category("Moderate") == "Moderate"
    assert ThresholdEngine.get_severity_for_category("Poor") == "High"
    assert ThresholdEngine.get_severity_for_category("Very Poor") == "High"
    assert ThresholdEngine.get_severity_for_category("Severe") == "Critical"


def test_category_change_detection():
    """Verify detection when AQI crosses into a worse NAQI category."""
    now_utc = datetime.now(timezone.utc)
    prev = AQIReading(
        aqi_value=180,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(hours=1),
        source="CPCB",
        is_simulated=False,
    )
    curr = AQIReading(
        aqi_value=220,
        aqi_category="Poor",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    alerts = ThresholdEngine.evaluate_readings(
        current_reading=curr,
        previous_reading=prev,
        city_name="Delhi",
    )
    category_alerts = [a for a in alerts if a.alert_type == "CATEGORY_CHANGE"]
    assert len(category_alerts) == 1
    assert category_alerts[0].severity == "High"
    assert "Poor" in category_alerts[0].title


def test_threshold_crossing_detection():
    """Verify detection when AQI crosses threshold boundaries."""
    now_utc = datetime.now(timezone.utc)
    prev = AQIReading(
        aqi_value=90,
        aqi_category="Satisfactory",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(hours=1),
        source="CPCB",
        is_simulated=False,
    )
    curr = AQIReading(
        aqi_value=115,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    alerts = ThresholdEngine.evaluate_readings(
        current_reading=curr,
        previous_reading=prev,
        city_name="Delhi",
        min_threshold=100,
    )
    assert len(alerts) >= 1
    assert any(a.alert_type in ("CATEGORY_CHANGE", "THRESHOLD_CROSSING") for a in alerts)


def test_deterioration_spike_detection():
    """Verify detection when AQI worsens rapidly by >= 30 points within same category."""
    now_utc = datetime.now(timezone.utc)
    prev = AQIReading(
        aqi_value=140,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(hours=1),
        source="CPCB",
        is_simulated=False,
    )
    curr = AQIReading(
        aqi_value=175,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    alerts = ThresholdEngine.evaluate_readings(
        current_reading=curr,
        previous_reading=prev,
        city_name="Delhi",
        deterioration_threshold=30,
    )
    deterioration_alerts = [a for a in alerts if a.alert_type == "DETERIORATION"]
    assert len(deterioration_alerts) == 1
    assert "Spike" in deterioration_alerts[0].title
    assert deterioration_alerts[0].severity == "Moderate"


def test_improvement_detection():
    """Verify detection when AQI improves significantly by >= 40 points."""
    now_utc = datetime.now(timezone.utc)
    prev = AQIReading(
        aqi_value=210,
        aqi_category="Poor",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(hours=1),
        source="CPCB",
        is_simulated=False,
    )
    curr = AQIReading(
        aqi_value=150,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    alerts = ThresholdEngine.evaluate_readings(
        current_reading=curr,
        previous_reading=prev,
        city_name="Delhi",
        improvement_threshold=40,
    )
    improvement_alerts = [a for a in alerts if a.alert_type == "IMPROVEMENT"]
    assert len(improvement_alerts) == 1
    assert "Improved" in improvement_alerts[0].title
    assert improvement_alerts[0].severity == "Low"


def test_dominant_pollutant_change():
    """Verify detection when the primary pollutant driver shifts."""
    now_utc = datetime.now(timezone.utc)
    prev = AQIReading(
        aqi_value=160,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(hours=1),
        source="CPCB",
        is_simulated=False,
    )
    curr = AQIReading(
        aqi_value=165,
        aqi_category="Moderate",
        dominant_pollutant="NO2",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=False,
    )
    alerts = ThresholdEngine.evaluate_readings(
        current_reading=curr,
        previous_reading=prev,
        city_name="Delhi",
    )
    pollutant_alerts = [a for a in alerts if a.alert_type == "POLLUTANT_CHANGE"]
    assert len(pollutant_alerts) == 1
    assert "Shift" in pollutant_alerts[0].title


def test_stale_data_detection():
    """Verify generation of STALE_DATA alert when latest observation is > 24 hours old."""
    now_utc = datetime.now(timezone.utc)
    stale_timestamp = now_utc - timedelta(hours=26)
    alert = ThresholdEngine.check_stale_data(
        city_id=1,
        city_name="Delhi",
        last_recorded_at=stale_timestamp,
    )
    assert alert is not None
    assert alert.alert_type == "STALE_DATA"
    assert "Data Outdated" in alert.title
    assert alert.severity == "Low"


def test_simulated_data_prefixing():
    """Verify simulation labeling: [SIMULATED DATA] prefix when is_simulated=True."""
    now_utc = datetime.now(timezone.utc)
    prev = AQIReading(
        aqi_value=180,
        aqi_category="Moderate",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(hours=1),
        source="CPCB",
        is_simulated=True,
    )
    curr = AQIReading(
        aqi_value=240,
        aqi_category="Poor",
        dominant_pollutant="PM2.5",
        measured_at=now_utc,
        source="CPCB",
        is_simulated=True,
    )
    alerts = ThresholdEngine.evaluate_readings(
        current_reading=curr,
        previous_reading=prev,
        city_name="Delhi",
    )
    assert len(alerts) > 0
    for a in alerts:
        assert a.title.startswith("[SIMULATED DATA] ")
        assert a.is_simulated is True


# ===========================================================================
# 2. Deduplication Engine Unit Tests
# ===========================================================================


def test_deduplication_key_generation():
    """Verify deterministic deduplication key generation format."""
    now_utc = datetime(2026, 11, 20, 14, 30, tzinfo=timezone.utc)
    key = AlertDeduplicator.generate_key(
        city_id=1,
        station_id=2,
        alert_type="CATEGORY_CHANGE",
        current_aqi=250,
        measurement_timestamp=now_utc,
    )
    assert key == "1:2:CATEGORY_CHANGE:250:2026112014"


def test_deduplication_suppresses_duplicate_in_window(db_session: Session, alert_seed_data):
    """Verify that an identical alert within the deduplication window is suppressed."""
    now_utc = datetime.now(timezone.utc)
    # alert1 in alert_seed_data has dedup_key="test_delhi_cat_change_1"
    is_dup = AlertDeduplicator.is_duplicate(
        db=db_session,
        dedup_key="test_delhi_cat_change_1",
        now_utc=now_utc,
        window_hours=2,
    )
    assert is_dup is True

    # Unknown key should not be duplicate
    is_dup_new = AlertDeduplicator.is_duplicate(
        db=db_session,
        dedup_key="brand_new_key_12345",
        now_utc=now_utc,
        window_hours=2,
    )
    assert is_dup_new is False


# ===========================================================================
# 3. Delivery Tracker & Quiet Hours Unit Tests
# ===========================================================================


def test_delivery_normal_hours():
    """Verify non-quiet daytime hours allow immediate notification dispatch."""
    test_time = datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc)
    is_quiet = DeliveryTracker.is_quiet_hours(
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=test_time,
    )
    assert is_quiet is False


def test_delivery_quiet_hours_midnight_spanning():
    """Verify quiet hours spanning midnight (22:00 to 07:00) suppress non-critical notifications."""
    night_time = datetime(2026, 11, 20, 23, 30, tzinfo=timezone.utc)
    is_quiet = DeliveryTracker.is_quiet_hours(
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=night_time,
    )
    assert is_quiet is True

    early_morning = datetime(2026, 11, 20, 4, 30, tzinfo=timezone.utc)
    is_quiet_early = DeliveryTracker.is_quiet_hours(
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=early_morning,
    )
    assert is_quiet_early is True


def test_critical_alert_overrides_quiet_hours():
    """Verify Critical severity alerts override quiet hours."""
    night_time = datetime(2026, 11, 20, 23, 30, tzinfo=timezone.utc)
    can_deliver = DeliveryTracker.can_deliver_now(
        severity="Critical",
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=night_time,
    )
    assert can_deliver is True

    can_deliver_high = DeliveryTracker.can_deliver_now(
        severity="High",
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=night_time,
    )
    assert can_deliver_high is False


# ===========================================================================
# 4. Notification Service Unit Tests
# ===========================================================================


@pytest.mark.anyio
async def test_email_dispatch_disabled():
    """Verify email dispatch returns False without error when email notifications are disabled."""
    settings = Settings(EMAIL_NOTIFICATIONS_ENABLED=False)
    service = NotificationService(settings=settings)
    result = await service.dispatch_email(
        recipient_email="user@example.com",
        subject="Test Alert",
        html_content="<p>Test</p>",
        text_content="Test",
    )
    assert result is False


@pytest.mark.anyio
async def test_email_dispatch_mocked_success():
    """Verify successful email delivery formatting via Resend API mock."""
    settings = Settings(
        EMAIL_NOTIFICATIONS_ENABLED=True,
        RESEND_API_KEY="re_test_key_12345",
        ALERT_EMAIL_FROM="Air Quality Assistant <alerts@test.com>",
    )
    service = NotificationService(settings=settings)

    mock_resp = Response(
        status_code=200,
        json={"id": "email_msg_12345"},
        request=MagicMock(),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success = await service.dispatch_email(
            recipient_email="resident@example.com",
            subject="Air Quality Alert",
            html_content="<p>Alert Body</p>",
            text_content="Alert Body",
        )
        assert success is True
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer re_test_key_12345"
        assert call_kwargs["json"]["to"] == ["resident@example.com"]


@pytest.mark.anyio
async def test_web_push_dispatch_disabled(db_session: Session):
    """Verify web push dispatch returns 0 when web push is disabled in configuration."""
    settings = Settings(WEB_PUSH_ENABLED=False)
    service = NotificationService(settings=settings)
    sent_count = await service.dispatch_web_push(
        db=db_session,
        user_id="default_user",
        title="Test Alert",
        body="Test Body",
    )
    assert sent_count == 0


@pytest.mark.anyio
async def test_web_push_dispatch_mocked(db_session: Session):
    """Verify web push dispatch attempts delivery and removes 410 Gone subscriptions."""
    settings = Settings(
        WEB_PUSH_ENABLED=True,
        VAPID_PUBLIC_KEY="test_public_key",
        VAPID_PRIVATE_KEY="test_private_key",
        VAPID_SUBJECT="mailto:admin@example.com",
    )
    service = NotificationService(settings=settings)

    # Add a mock subscription
    sub = PushSubscription(
        user_id="user_push_test",
        endpoint="https://push.example.com/sub/123",
        p256dh="mock_p256dh_key",
        auth="mock_auth_secret",
    )
    db_session.add(sub)
    db_session.commit()

    with patch("app.services.alerts.notification_service.webpush") as mock_webpush:
        mock_webpush.return_value = None
        count = await service.dispatch_web_push(
            db=db_session,
            user_id="user_push_test",
            title="Air Quality Warning",
            body="AQI is High in your area",
        )
        assert count == 1
        assert mock_webpush.called


# ===========================================================================
# 5. REST API Endpoints Tests
# ===========================================================================


@pytest.mark.anyio
async def test_api_list_alerts(client: AsyncClient, alert_seed_data):
    """Test GET /api/v1/alerts pagination and response schema."""
    resp = await client.get("/api/v1/alerts?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert "total_records" in data
    assert data["total_records"] >= 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["alerts"]) >= 2

    # Check alert structure
    alert_item = data["alerts"][0]
    assert "title" in alert_item
    assert "severity" in alert_item
    assert "alert_type" in alert_item
    assert "city_name" in alert_item


@pytest.mark.anyio
async def test_api_list_alerts_filters(client: AsyncClient, alert_seed_data):
    """Test GET /api/v1/alerts filtering by severity, city, is_read, and is_simulated."""
    # Filter by severity High
    resp_sev = await client.get("/api/v1/alerts?severity=High")
    assert resp_sev.status_code == 200
    data_sev = resp_sev.json()
    assert all(a["severity"] == "High" for a in data_sev["alerts"])

    # Filter by is_read False
    resp_unread = await client.get("/api/v1/alerts?is_read=false")
    assert resp_unread.status_code == 200
    data_unread = resp_unread.json()
    assert all(a["is_read"] is False for a in data_unread["alerts"])

    # Filter by is_simulated True
    resp_sim = await client.get("/api/v1/alerts?is_simulated=true")
    assert resp_sim.status_code == 200
    data_sim = resp_sim.json()
    assert all(a["is_simulated"] is True for a in data_sim["alerts"])

    # Filter by city Delhi
    resp_city = await client.get("/api/v1/alerts?city=Delhi")
    assert resp_city.status_code == 200
    data_city = resp_city.json()
    assert all(a["city_name"] == "Delhi" for a in data_city["alerts"])


@pytest.mark.anyio
async def test_api_unread_count(client: AsyncClient, alert_seed_data):
    """Test GET /api/v1/alerts/unread-count."""
    resp = await client.get("/api/v1/alerts/unread-count")
    assert resp.status_code == 200
    data = resp.json()
    assert "unread_count" in data
    assert data["unread_count"] >= 1


@pytest.mark.anyio
async def test_api_mark_single_alert_read(client: AsyncClient, alert_seed_data):
    """Test PATCH /api/v1/alerts/{alert_id}/read marks alert as read."""
    alert1 = alert_seed_data["alert1"]
    resp = await client.patch(f"/api/v1/alerts/{alert1.id}/read")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == alert1.id
    assert data["is_read"] is True

    # 404 for invalid ID
    resp_404 = await client.patch("/api/v1/alerts/999999/read")
    assert resp_404.status_code == 404


@pytest.mark.anyio
async def test_api_mark_all_read(client: AsyncClient, alert_seed_data):
    """Test PATCH /api/v1/alerts/read-all marks all alerts read."""
    resp = await client.patch("/api/v1/alerts/read-all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 0

    # Verify unread count is now 0
    resp_count = await client.get("/api/v1/alerts/unread-count")
    assert resp_count.json()["unread_count"] == 0


@pytest.mark.anyio
async def test_api_get_default_preferences(client: AsyncClient, alert_seed_data):
    """Test GET /api/v1/alerts/preferences returns defaults when no preference exists."""
    resp = await client.get("/api/v1/alerts/preferences", headers={"X-User-Id": "new_user_123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "new_user_123"
    assert data["min_aqi_threshold"] == 100
    assert "in_app" in data["channels"]
    assert data["is_enabled"] is True


@pytest.mark.anyio
async def test_api_update_preferences(client: AsyncClient, alert_seed_data):
    """Test PUT /api/v1/alerts/preferences creates and updates preferences."""
    payload = {
        "city": "Delhi",
        "min_aqi_threshold": 150,
        "min_severity": "Moderate",
        "is_enabled": True,
        "channels": ["in_app", "email"],
        "email": "user@delhi.org",
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "06:00",
        "timezone": "Asia/Kolkata",
    }
    resp = await client.put(
        "/api/v1/alerts/preferences",
        json=payload,
        headers={"X-User-Id": "resident_delhi"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["city_name"] == "Delhi"
    assert data["min_aqi_threshold"] == 150
    assert "email" in data["channels"]
    assert data["email"] == "user@delhi.org"
    assert data["quiet_hours_start"] == "23:00"


@pytest.mark.anyio
async def test_api_update_preferences_validation(client: AsyncClient, alert_seed_data):
    """Test PUT /api/v1/alerts/preferences rejects invalid threshold, bad quiet hours, missing email."""
    # Invalid threshold > 500
    resp_threshold = await client.put(
        "/api/v1/alerts/preferences",
        json={"city": "Delhi", "min_aqi_threshold": 600, "channels": ["in_app"]},
    )
    assert resp_threshold.status_code == 422

    # Missing email when 'email' channel specified
    resp_no_email = await client.put(
        "/api/v1/alerts/preferences",
        json={"city": "Delhi", "min_aqi_threshold": 120, "channels": ["email"]},
    )
    assert resp_no_email.status_code == 400
    assert "Email address is required" in resp_no_email.json()["detail"]

    # Invalid quiet hours pattern
    resp_bad_qh = await client.put(
        "/api/v1/alerts/preferences",
        json={"city": "Delhi", "min_aqi_threshold": 100, "quiet_hours_start": "25:00", "channels": ["in_app"]},
    )
    assert resp_bad_qh.status_code == 422


@pytest.mark.anyio
async def test_api_alert_status(client: AsyncClient):
    """Test GET /api/v1/alerts/status returns operational status."""
    resp = await client.get("/api/v1/alerts/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts_enabled" in data
    assert "enabled_channels" in data
    assert "providers" in data
    assert data["providers"]["in_app"] is True


@pytest.mark.anyio
async def test_api_process_alerts_endpoint(client: AsyncClient, alert_seed_data):
    """Test POST /api/v1/alerts/process evaluates conditions and produces response."""
    resp = await client.post("/api/v1/alerts/process")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "locations_evaluated" in data
    assert "alerts_generated" in data


@pytest.mark.anyio
async def test_api_process_alerts_forbidden_secret(client: AsyncClient, monkeypatch):
    """Test POST /api/v1/alerts/process enforces X-Admin-Secret when configured."""
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "ALERT_ADMIN_SECRET", "super_secret_admin_token")

    # Call without secret -> 403
    resp_no_auth = await client.post("/api/v1/alerts/process")
    assert resp_no_auth.status_code == 403

    # Call with wrong secret -> 403
    resp_bad_auth = await client.post("/api/v1/alerts/process", headers={"X-Admin-Secret": "wrong_key"})
    assert resp_bad_auth.status_code == 403

    # Call with valid secret -> 200
    resp_good_auth = await client.post("/api/v1/alerts/process", headers={"X-Admin-Secret": "super_secret_admin_token"})
    assert resp_good_auth.status_code == 200


@pytest.mark.anyio
async def test_api_test_notification_in_app(client: AsyncClient):
    """Test POST /api/v1/alerts/test-notification with in_app channel."""
    payload = {
        "channel": "in_app",
        "city": "Delhi",
        "aqi": 210,
        "category": "Poor",
    }
    resp = await client.post("/api/v1/alerts/test-notification", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["channel"] == "in_app"


@pytest.mark.anyio
async def test_api_push_subscription(client: AsyncClient):
    """Test POST /api/v1/alerts/push/subscribe registers a browser push subscription."""
    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/sample_push_token_999",
        "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9h0qvqKEA9+LLmHsPtw24Raq1",
        "auth": "tBHItJI5svbpez7KI4CCXg==",
    }
    resp = await client.post(
        "/api/v1/alerts/push/subscribe",
        json=payload,
        headers={"X-User-Id": "mobile_user_1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
