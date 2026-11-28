"""Targeted unit tests for Step 1 cohesive split modules and Gemini-free fallback paths."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.config import Settings
from app.integrations.ai.schemas import AQIContextSnapshot, HealthAskRequest
from app.integrations.weather.client import WeatherClient
from app.models.alert import Alert
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.schemas.alert import AlertPreferenceCreate, PushSubscriptionCreate
from app.services.alerts import alert_preference_service, alert_query_service
from app.services.alerts.threshold_rules import (
    ReadingContext,
    check_deterioration_spike,
    check_pollutant_shift,
    check_threshold_crossing,
    evaluate_reading_pair,
)
from app.services.aqi.processor_queries import (
    apply_history_filters,
    resolve_city_from_name,
    resolve_city_from_station,
)
from app.services.forecasting import forecast_query_service, forecast_run_helper
from app.services.forecasting.data_preparation import PreparedDataset
from app.services.forecasting.evaluation import EvaluationReport, HorizonEvaluation
from app.services.health.health_advisor import HealthAdvisorService
from app.services.health.knowledge_base import HealthKnowledgeBase
from app.services.health.knowledge_data_community import (
    WINTER_SMOG_GUIDANCE,
    build_impact_metrics,
)
from app.services.health.knowledge_data_guidelines import (
    CATEGORY_GUIDELINES,
    MEDICAL_DISCLAIMER,
)
from app.services.health.knowledge_data_pollutants import POLLUTANT_DETAILS
from app.services.health.recommendation_engine import RecommendationEngine
from app.services.health.recommendation_tiers_severe import build_severe_recommendations
from app.services.health.recommendation_tiers_standard import build_good_recommendations
from app.services.history import history_query_service, trend_helpers


def test_knowledge_and_recommendation_split_modules():
    """Verify split knowledge and recommendation modules preserve lookups and fallbacks."""
    assert len(CATEGORY_GUIDELINES) >= 5
    assert MEDICAL_DISCLAIMER
    assert "PM2.5" in POLLUTANT_DETAILS
    assert len(WINTER_SMOG_GUIDANCE) >= 1
    assert len(build_impact_metrics().pillars) >= 3
    assert len(build_good_recommendations()) >= 1
    assert len(build_severe_recommendations()) >= 1

    kb = HealthKnowledgeBase()
    assert kb.get_category_guideline("Good").category == "Good"
    assert kb.get_category_guideline("NonexistentCategory").category == "Moderate"
    assert kb.get_pollutant_explanation("NO2") is not None
    assert kb.get_pollutant_explanation("UNKNOWN_GAS") is None

    snapshot = AQIContextSnapshot(
        city_name="Delhi",
        station_id=None,
        station_name=None,
        aqi=420,
        category="Severe",
        dominant_pollutant="PM2.5",
        measurement_timestamp=None,
        data_age_seconds=None,
        trend_direction=None,
    )
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 1


def test_threshold_rules_all_transition_paths():
    """Verify threshold_rules evaluators across initial, worsening, improving, spike, and shift."""
    now = datetime.now(UTC)

    initial_ctx = ReadingContext(
        curr_aqi=220,
        curr_cat="Poor",
        curr_dom="PM2.5",
        curr_time=now,
        curr_severity="High",
        source="CPCB",
        is_sim=True,
        sim_prefix="[Demo] ",
        location_label="Delhi",
        min_threshold=150,
        deterioration_threshold=40,
        improvement_threshold=40,
    )
    initial_alerts = evaluate_reading_pair(initial_ctx, has_previous=False)
    assert len(initial_alerts) == 1
    assert initial_alerts[0].alert_type == "THRESHOLD_CROSSING"

    low_ctx = ReadingContext(
        curr_aqi=45,
        curr_cat="Good",
        curr_dom="PM10",
        curr_time=now,
        curr_severity="Low",
        source="CPCB",
        is_sim=False,
        sim_prefix="",
        location_label="Kochi",
        min_threshold=150,
        deterioration_threshold=40,
        improvement_threshold=40,
    )
    assert evaluate_reading_pair(low_ctx, has_previous=False) == []

    spike_ctx = ReadingContext(
        curr_aqi=280,
        curr_cat="Poor",
        curr_dom="NO2",
        curr_time=now,
        curr_severity="High",
        source="CPCB",
        is_sim=False,
        sim_prefix="",
        location_label="Delhi",
        min_threshold=150,
        deterioration_threshold=30,
        improvement_threshold=40,
        prev_aqi=230,
        prev_cat="Poor",
        prev_dom="PM2.5",
        aqi_delta=50,
    )
    spike_alerts = evaluate_reading_pair(spike_ctx, has_previous=True)
    types = {a.alert_type for a in spike_alerts}
    assert {"DETERIORATION", "POLLUTANT_CHANGE"} <= types

    cross_ctx = ReadingContext(
        curr_aqi=160,
        curr_cat="Moderate",
        curr_dom="PM2.5",
        curr_time=now,
        curr_severity="Moderate",
        source="CPCB",
        is_sim=False,
        sim_prefix="",
        location_label="Pune",
        min_threshold=150,
        deterioration_threshold=50,
        improvement_threshold=40,
        prev_aqi=130,
        prev_cat="Moderate",
        prev_dom="PM2.5",
        aqi_delta=30,
    )
    crossed = evaluate_reading_pair(cross_ctx, has_previous=True)
    assert crossed[0].alert_type == "THRESHOLD_CROSSING"
    assert check_deterioration_spike(low_ctx) is None
    assert check_threshold_crossing(low_ctx) is None
    assert check_pollutant_shift(low_ctx) is None


def test_trend_helpers_classification_and_edge_cases():
    """Exercise all branches in history/trend_helpers split module."""
    naive_dt = datetime(2026, 1, 10, 6, 0, 0)
    aware_dt = datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC)
    assert trend_helpers.as_utc(naive_dt).tzinfo == UTC
    assert trend_helpers.as_utc(aware_dt).tzinfo == UTC

    readings = [
        SimpleNamespace(measured_at=naive_dt),
        SimpleNamespace(measured_at=aware_dt),
    ]
    t_start, t_end, mid, earlier, later = trend_helpers.compute_time_halves(readings, None, None)
    assert len(earlier) == 1 and len(later) == 1
    assert t_start < mid < t_end

    assert trend_helpers.compute_delta(0.0, 20.0) == (20.0, None)
    assert trend_helpers.compute_delta(100.0, 125.0) == (25.0, 25.0)

    assert trend_helpers.classify_aqi_trend(-20.0, -15.0, 5.0, 140.0, 120.0)[0] == "improving"
    assert trend_helpers.classify_aqi_trend(20.0, 15.0, 5.0, 120.0, 140.0)[0] == "worsening"
    assert trend_helpers.classify_aqi_trend(2.0, 1.5, 5.0, 120.0, 122.0)[0] == "stable"

    assert (
        trend_helpers.classify_pollutant_trend(-12.0, -20.0, 2.0, 60.0, 48.0, "PM2.5", "ug/m3")[0]
        == "improving"
    )
    assert (
        trend_helpers.classify_pollutant_trend(12.0, 20.0, 2.0, 48.0, 60.0, "PM2.5", "ug/m3")[0]
        == "worsening"
    )
    assert (
        trend_helpers.classify_pollutant_trend(0.5, 1.0, 2.0, 50.0, 50.5, "PM2.5", "ug/m3")[0]
        == "stable"
    )

    meta = trend_helpers.TrendMetadata(
        city_name="Delhi",
        station_id=None,
        station_name=None,
        pollutant="PM2.5",
        metric="Concentration",
        unit="ug/m3",
        interval="hourly",
        threshold=2.0,
        methodology_doc="Halves comparison",
    )
    insuf_total = trend_helpers.build_insufficient_total_response(meta, 2, 4)
    assert insuf_total.trend_direction == "insufficient_data"
    assert "PM2.5" in insuf_total.explanation

    insuf_halves = trend_helpers.build_insufficient_halves_response(
        meta, 1, 3, 2, 4, t_start, t_end, mid, [80.0], [95.0]
    )
    assert insuf_halves.earlier_average == 80.0
    assert insuf_halves.later_average == 95.0


def test_alert_query_and_preference_split_services(db_session):
    """Exercise alert_query_service, alert_preference_service, and processor_queries with SQLite."""
    city = City(name="Delhi", state="Delhi", country="India", latitude=28.6, longitude=77.2)
    db_session.add(city)
    db_session.flush()
    station = MonitoringStation(
        station_name="Anand Vihar",
        city_id=city.id,
        latitude=28.65,
        longitude=77.31,
        provider="CPCB",
    )
    db_session.add(station)
    db_session.flush()

    now = datetime.now(UTC)
    db_session.add(
        AQIReading(
            city_id=city.id,
            station_id=station.id,
            aqi_value=240,
            aqi_category="Poor",
            dominant_pollutant="PM2.5",
            measured_at=now,
            source="CPCB",
            is_simulated=False,
        )
    )
    alert = Alert(
        city_id=city.id,
        station_id=station.id,
        title="High Smog",
        description="Severe particulate buildup",
        severity="High",
        alert_type="THRESHOLD_CROSSING",
        current_aqi=240,
        is_read=False,
        is_simulated=False,
    )
    db_session.add(alert)
    db_session.commit()

    # processor_queries checks
    assert resolve_city_from_name(db_session, "Delhi").id == city.id
    with pytest.raises(HTTPException) as exc_city:
        resolve_city_from_name(db_session, "Atlantis")
    assert exc_city.value.status_code == 404

    assert resolve_city_from_station(db_session, station.id).id == city.id
    with pytest.raises(HTTPException) as exc_stn:
        resolve_city_from_station(db_session, 999999)
    assert exc_stn.value.status_code == 404

    stmt, resolved = apply_history_filters(
        select(AQIReading).join(City, AQIReading.city_id == City.id),
        "Delhi",
        station.id,
        now - timedelta(hours=1),
        now,
    )
    assert resolved == "Delhi" and stmt is not None

    # history_query_service check
    params = history_query_service.HistoryQueryParams(
        filters=[AQIReading.city_id == city.id],
        city_name="Delhi",
        station_id=station.id,
        station_name=station.station_name,
        start_utc=now - timedelta(days=1),
        end_utc=now + timedelta(days=1),
        page=1,
        page_size=10,
    )
    raw_hist = history_query_service.get_raw_aqi_history(db_session, params)
    assert raw_hist.total_records >= 1

    # alert_query_service checks
    page = alert_query_service.list_alerts(
        db_session,
        city="Delhi",
        station_id=station.id,
        severity="High",
        is_read=False,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=1),
        is_simulated=False,
    )
    assert page.total_records == 1
    assert alert_query_service.get_unread_count(db_session).unread_count == 1
    assert alert_query_service.mark_alert_read(db_session, alert.id).is_read is True
    with pytest.raises(HTTPException) as exc_missing_alert:
        alert_query_service.mark_alert_read(db_session, 999999)
    assert exc_missing_alert.value.status_code == 404
    assert alert_query_service.mark_all_read(db_session).unread_count == 0

    # alert_preference_service checks
    alert_preference_service.validate_quiet_hours(None, None)
    with pytest.raises(HTTPException):
        alert_preference_service.validate_quiet_hours("25:99", "07:00")
    with pytest.raises(HTTPException):
        alert_preference_service.validate_channels(["sms"])

    default_pref = alert_preference_service.get_preferences(db_session, user_id="fam_1")
    assert default_pref.city_name == "Delhi"

    updated = alert_preference_service.upsert_preferences(
        db_session,
        AlertPreferenceCreate(
            city="Delhi",
            station_id=station.id,
            min_aqi_threshold=180,
            min_severity="High",
            is_enabled=True,
            channels=["in_app", "push"],
            quiet_hours_start="22:00",
            quiet_hours_end="06:30",
            timezone="Asia/Kolkata",
        ),
        user_id="fam_1",
    )
    assert updated.min_aqi_threshold == 180
    assert alert_preference_service.register_push_subscription(
        db_session,
        PushSubscriptionCreate(endpoint="https://push.example/sub1", p256dh="key1", auth="auth1"),
        user_id="fam_1",
    )


def test_forecast_split_helpers(db_session):
    """Exercise forecast_query_service and forecast_run_helper modules."""
    city = City(
        name="Mumbai", state="Maharashtra", country="India", latitude=19.07, longitude=72.87
    )
    db_session.add(city)
    db_session.commit()

    now = datetime.now(UTC)
    dataset = PreparedDataset(
        timestamps=[now - timedelta(hours=2), now - timedelta(hours=1), now],
        aqi_values=[110.0, 120.0, 125.0],
        dominant_pollutants=["PM2.5", "PM2.5", "PM2.5"],
        sample_count=3,
        start_time=now - timedelta(hours=2),
        end_time=now,
        is_simulated=True,
        is_sufficient=False,
        insufficiency_reason="Need 24 points",
    )
    with pytest.raises(HTTPException) as exc_insuf:
        forecast_run_helper.handle_insufficient_dataset(db_session, city, None, dataset, now)
    assert exc_insuf.value.status_code == 422

    model = SimpleNamespace(name="ExpSmoothing", version="1.2.0")
    eval_report = EvaluationReport(
        model_name="ExpSmoothing",
        model_version="1.2.0",
        sample_count=12,
        overall_mae=6.5,
        overall_rmse=8.1,
        overall_mape=5.2,
        horizon_metrics=[
            HorizonEvaluation(horizon_hours=6, sample_count=6, mae=5.0, rmse=6.2, mape=4.1)
        ],
    )
    run = forecast_run_helper.persist_forecast_run(
        db_session, city, None, model, dataset, eval_report, now
    )
    step_points = forecast_run_helper.build_step_forecasts(
        run.id, city, None, model, dataset, [130.0, 135.0], 2, 4.0, 12, now
    )
    assert len(step_points) == 2
    for pt in step_points:
        db_session.add(pt)
    db_session.commit()

    cached = forecast_run_helper.check_recent_forecast_run(db_session, city, None, now, [6])
    assert cached is not None
    assert cached.generated_forecasts_count == 2

    metrics = forecast_query_service.query_eval_metrics(db_session, run)
    assert len(metrics) == 1
    history = forecast_query_service.get_forecast_history(db_session, "Mumbai", limit=5)
    assert history.total_runs >= 1
    status_resp = forecast_query_service.get_model_status(
        db_session, Settings(APP_ENV="test"), city_name="Mumbai"
    )
    assert status_resp.model_name == "ExponentialSmoothingForecaster"


@pytest.mark.asyncio
async def test_weather_client_typed_parsing_and_mock():
    """Verify WeatherClient._parse_optional_float handles all edge types cleanly without casts."""
    data: dict[str, object] = {
        "valid_float": 24.7,
        "valid_int": 15,
        "valid_str": "1012.5",
        "bad_str": "not-a-number",
        "bool_val": True,
        "none_val": None,
        "list_val": [1, 2],
    }
    assert WeatherClient._parse_optional_float(data, "valid_float") == 24.7
    assert WeatherClient._parse_optional_float(data, "valid_int") == 15.0
    assert WeatherClient._parse_optional_float(data, "valid_str") == 1012.5
    assert WeatherClient._parse_optional_float(data, "bad_str") is None
    assert WeatherClient._parse_optional_float(data, "bool_val") is None
    assert WeatherClient._parse_optional_float(data, "none_val") is None
    assert WeatherClient._parse_optional_float(data, "list_val") is None

    WeatherClient.clear_cache()
    disabled_client = WeatherClient(Settings(APP_ENV="test", WEATHER_ENABLED=False))
    assert await disabled_client.get_current_weather(28.6, 77.2) is None

    mock_client = WeatherClient(
        Settings(APP_ENV="test", WEATHER_ENABLED=True, WEATHER_PROVIDER="mock")
    )
    first = await mock_client.get_current_weather(28.6, 77.2)
    second = await mock_client.get_current_weather(28.6, 77.2)
    assert first is not None and not first.is_cached
    assert second is not None and second.is_cached


@pytest.mark.asyncio
async def test_health_advisor_no_gemini_key_fallback_profiles(db_session):
    """Verify deterministic no-Gemini-key fallback covers household profiles and all 3 pillars."""
    city = City(name="Delhi", state="Delhi", country="India", latitude=28.6, longitude=77.2)
    db_session.add(city)
    db_session.flush()
    db_session.add(
        AQIReading(
            city_id=city.id,
            aqi_value=310,
            aqi_category="Very Poor",
            dominant_pollutant="PM2.5",
            measured_at=datetime.now(UTC) - timedelta(hours=8),
            source="Simulated",
            is_simulated=True,
        )
    )
    db_session.commit()

    advisor_no_key = HealthAdvisorService(
        settings=Settings(APP_ENV="test", AI_ENABLED=True, GEMINI_API_KEY=None)
    )
    req_default = HealthAskRequest(
        city="Delhi",
        question="What plan should our family follow today?",
        lifestyle="car commute",
        family_context="children and elderly",
        conversation_id=None,
    )
    res_default = await advisor_no_key.ask(db=db_session, request=req_default)
    assert res_default.response_type == "knowledge_base_fallback"
    assert res_default.model is None
    assert res_default.data_freshness == "stale"
    assert len(res_default.direct_impact_metrics) >= 3
    assert "Low-Emission Daily Routines" in res_default.answer
    assert "Indoor Air Quality Hacks" in res_default.answer
    assert "Sustainable Community Alternatives" in res_default.answer

    advisor_disabled = HealthAdvisorService(settings=Settings(APP_ENV="test", AI_ENABLED=False))
    stale_snapshot = AQIContextSnapshot(
        city_name="Jaipur",
        station_id=None,
        station_name=None,
        aqi=None,
        category=None,
        dominant_pollutant=None,
        measurement_timestamp=None,
        data_age_seconds=None,
        is_stale=True,
        is_simulated=True,
        trend_direction=None,
    )
    fallback_text = advisor_disabled._generate_knowledge_base_fallback(
        question="winter commute indoor heating advice",
        snapshot=stale_snapshot,
        lifestyle="biomass heater",
        family_context="asthma patient",
    )
    assert "Winter Smog & Inversion Protocols" in fallback_text
    assert "Low-Emission Daily Routines" in fallback_text
    assert "Indoor Air Quality Hacks" in fallback_text
    assert "Sustainable Community Alternatives" in fallback_text
