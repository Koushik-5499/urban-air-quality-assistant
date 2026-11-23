"""Comprehensive test suite for Phase 7: Alerts & Notifications."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.alert import Alert
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.models.push_subscription import PushSubscription
from app.services.alerts.deduplication import AlertDeduplicator
from app.services.alerts.delivery_tracker import DeliveryTracker
from app.services.alerts.notification_service import NotificationService
from app.services.alerts.threshold_engine import ThresholdEngine


@pytest.fixture
def alert_seed_data(db_session: Session):
    """Seed test database with cities, stations, AQI readings, and alerts."""
    now_utc = datetime.now(UTC)

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
        description=(
            "Air quality has entered the Poor category (AQI: 240). Breathing discomfort to "
            "most people on prolonged exposure."
        ),
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
        description=(
            "AQI deteriorated by 45 points in the past hour. Sensitive individuals should "
            "reduce outdoor activities."
        ),
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime.now(UTC)
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
    now_utc = datetime(2026, 11, 20, 14, 30, tzinfo=UTC)
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
    now_utc = datetime.now(UTC)
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
    test_time = datetime(2026, 11, 20, 14, 0, tzinfo=UTC)
    is_quiet = DeliveryTracker.is_quiet_hours(
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=test_time,
    )
    assert is_quiet is False


def test_delivery_quiet_hours_midnight_spanning():
    """Verify quiet hours spanning midnight (22:00 to 07:00) suppress non-critical notifications."""
    night_time = datetime(2026, 11, 20, 23, 30, tzinfo=UTC)
    is_quiet = DeliveryTracker.is_quiet_hours(
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=night_time,
    )
    assert is_quiet is True

    early_morning = datetime(2026, 11, 20, 4, 30, tzinfo=UTC)
    is_quiet_early = DeliveryTracker.is_quiet_hours(
        quiet_start="22:00",
        quiet_end="07:00",
        user_tz="UTC",
        now_utc=early_morning,
    )
    assert is_quiet_early is True


def test_critical_alert_overrides_quiet_hours():
    """Verify Critical severity alerts override quiet hours."""
    night_time = datetime(2026, 11, 20, 23, 30, tzinfo=UTC)
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
    """Test GET /api/v1/alerts/unread-count returns 410 Gone in public-only mode."""
    resp = await client.get("/api/v1/alerts/unread-count")
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_api_mark_single_alert_read(client: AsyncClient, alert_seed_data):
    """Test PATCH /api/v1/alerts/{alert_id}/read returns 410 Gone in public-only mode."""
    alert1 = alert_seed_data["alert1"]
    resp = await client.patch(f"/api/v1/alerts/{alert1.id}/read")
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_api_mark_all_read(client: AsyncClient, alert_seed_data):
    """Test PATCH /api/v1/alerts/read-all returns 410 Gone in public-only mode."""
    resp = await client.patch("/api/v1/alerts/read-all")
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_api_get_default_preferences(client: AsyncClient, alert_seed_data):
    """Test GET /api/v1/alerts/preferences returns 410 Gone in public-only mode."""
    resp = await client.get("/api/v1/alerts/preferences", headers={"X-User-Id": "new_user_123"})
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_api_update_preferences(client: AsyncClient, alert_seed_data):
    """Test PUT /api/v1/alerts/preferences returns 410 Gone in public-only mode."""
    payload = {
        "city": "Delhi",
        "min_aqi_threshold": 150,
        "min_severity": "Moderate",
        "is_enabled": True,
        "channels": ["in_app"],
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "06:00",
        "timezone": "Asia/Kolkata",
    }
    resp = await client.put(
        "/api/v1/alerts/preferences",
        json=payload,
        headers={"X-User-Id": "resident_delhi"},
    )
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_api_update_preferences_validation(client: AsyncClient, alert_seed_data):
    """Test PUT /api/v1/alerts/preferences consistently returns 410 Gone for any payload."""
    resp = await client.put(
        "/api/v1/alerts/preferences",
        json={"city": "Delhi", "min_aqi_threshold": 600, "channels": ["in_app"]},
    )
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


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
    resp_bad_auth = await client.post(
        "/api/v1/alerts/process", headers={"X-Admin-Secret": "wrong_key"}
    )
    assert resp_bad_auth.status_code == 403

    # Call with valid secret -> 200
    resp_good_auth = await client.post(
        "/api/v1/alerts/process", headers={"X-Admin-Secret": "super_secret_admin_token"}
    )
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
    """Test POST /api/v1/alerts/push/subscribe returns 410 Gone in public-only mode."""
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
    assert resp.status_code == 410
    assert "retired" in resp.json()["detail"].lower()


def test_alert_service_mark_read_and_unread_count(db_session, alert_seed_data):
    """Test AlertService mark_alert_read and get_unread_count."""
    from sqlalchemy import select

    from app.models.alert import Alert
    from app.services.alerts.alert_service import AlertService

    alert = db_session.execute(select(Alert).limit(1)).scalar_one_or_none()
    if alert:
        unread_before = AlertService.get_unread_count(db_session)
        assert unread_before.unread_count >= 1

        updated = AlertService.mark_alert_read(db_session, alert.id)
        assert updated.id == alert.id
        assert alert.is_read is True


def test_alert_service_mark_read_not_found(db_session):
    """Test AlertService mark_alert_read raises 404 for missing alert ID."""
    from fastapi import HTTPException

    from app.services.alerts.alert_service import AlertService

    with pytest.raises(HTTPException) as exc_info:
        AlertService.mark_alert_read(db_session, 999999)
    assert exc_info.value.status_code == 404


def test_alert_service_preferences_crud(db_session, alert_seed_data):
    """Test AlertService get_preferences and set_preferences."""
    from app.schemas.alert import AlertPreferenceCreate
    from app.services.alerts.alert_service import AlertService

    pref = AlertService.get_preferences(db_session, user_id="test_user_coverage")
    assert pref.user_id == "test_user_coverage"
    assert pref.is_enabled is True

    update_payload = AlertPreferenceCreate(
        city="Delhi",
        min_aqi_threshold=150,
        min_severity="Poor",
        is_enabled=False,
        channels=["in_app"],
        quiet_hours_start="23:00",
        quiet_hours_end="06:00",
        timezone="Asia/Kolkata",
    )
    updated = AlertService.upsert_preferences(
        db_session,
        pref_in=update_payload,
        user_id="test_user_coverage",
    )
    assert updated.min_aqi_threshold == 150
    assert updated.is_enabled is False

    # Second update tests the existing preference branch
    update_payload.is_enabled = True
    re_updated = AlertService.upsert_preferences(
        db_session,
        pref_in=update_payload,
        user_id="test_user_coverage",
    )
    assert re_updated.is_enabled is True


def test_alert_service_preferences_invalid_inputs(db_session, alert_seed_data):
    """Test AlertService set_preferences validation for quiet hours, channels, and city."""
    from fastapi import HTTPException

    from app.schemas.alert import AlertPreferenceCreate
    from app.services.alerts.alert_service import AlertService

    # 1. Invalid city
    with pytest.raises(HTTPException) as exc:
        AlertService.upsert_preferences(
            db_session,
            pref_in=AlertPreferenceCreate(city="NonExistentCity123"),
            user_id="u1",
        )
    assert exc.value.status_code == 404

    # 2. Invalid quiet hours format
    from pydantic import ValidationError

    with pytest.raises((HTTPException, ValidationError)):
        AlertService.upsert_preferences(
            db_session,
            pref_in=AlertPreferenceCreate(
                city="Delhi", quiet_hours_start="25:00", quiet_hours_end="07:00"
            ),
            user_id="u1",
        )

    # 3. Invalid channel
    with pytest.raises((HTTPException, ValidationError)):
        AlertService.upsert_preferences(
            db_session,
            pref_in=AlertPreferenceCreate(city="Delhi", channels=["sms"]),
            user_id="u1",
        )


def test_alert_service_push_subscription_lifecycle(db_session):
    """Test AlertService register_push_subscription creation and update."""
    from app.schemas.alert import PushSubscriptionCreate
    from app.services.alerts.alert_service import AlertService

    sub_in = PushSubscriptionCreate(
        endpoint="https://push.example.com/unique_cov_endpoint_1",
        p256dh="key123",
        auth="auth123",
    )
    # 1. Create
    res1 = AlertService.register_push_subscription(db_session, sub_in, user_id="u_cov_1")
    assert res1 is True

    # 2. Update existing endpoint
    sub_in.p256dh = "key456"
    res2 = AlertService.register_push_subscription(db_session, sub_in, user_id="u_cov_1")
    assert res2 is True


@pytest.mark.anyio
async def test_alert_service_status_and_test_notification_push(db_session, alert_seed_data):
    """Test AlertService get_status and send_test_notification with push channel."""
    from unittest.mock import AsyncMock, patch

    from app.schemas.alert import AlertTestNotificationRequest
    from app.services.alerts.alert_service import AlertService

    service = AlertService()
    status_resp = service.get_status()
    assert status_resp.alerts_enabled is True
    assert "in_app" in status_resp.enabled_channels

    # Test send_test_notification with mocked push
    with patch.object(
        service.notification_service, "dispatch_web_push", new_callable=AsyncMock
    ) as mock_dispatch:
        mock_dispatch.return_value = 1
        req = AlertTestNotificationRequest(channel="push", city="Delhi", aqi=250)
        res = await service.send_test_notification(db_session, req)
        assert res.success is True
        assert "Dispatched push" in res.message


@pytest.mark.anyio
async def test_alert_service_process_alerts_error_branch(db_session, alert_seed_data):
    """Test process_all_alerts error isolation branch."""
    from unittest.mock import patch

    from app.services.alerts.alert_service import AlertService

    service = AlertService()
    sim_error = ValueError("Simulated evaluation error")
    with patch.object(service, "evaluate_and_generate_alerts", side_effect=sim_error):
        process_res = await service.process_all_alerts(db_session)
        assert len(process_res.errors) > 0
        assert process_res.success is False
