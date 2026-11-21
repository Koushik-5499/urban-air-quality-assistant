"""Comprehensive tests for Phase 6: AI Health Advisor service, providers, guardrails, and endpoints."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.seed import seed_cities
from app.integrations.ai.base import BaseAIProvider
from app.integrations.ai.exceptions import (
    AIAuthError,
    AIRateLimitError,
    AITimeoutError,
)
from app.integrations.ai.gemini_provider import GeminiProvider
from app.integrations.ai.schemas import (
    AICompletionRequest,
    AICompletionResponse,
    ChatMessage,
)
from app.models.aqi_reading import AQIReading
from app.models.city import City
from app.models.monitoring_station import MonitoringStation
from app.services.health.context_builder import ContextBuilder
from app.services.health.health_advisor import HealthAdvisorService
from app.services.health.knowledge_base import HealthKnowledgeBase
from app.services.health.recommendation_engine import RecommendationEngine
from app.services.health.safety_validator import HealthSafetyValidator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def health_test_data(db_session: Session):
    """Seed database with fresh and stale readings for Delhi and Mumbai."""
    seed_cities(db_session)
    delhi = db_session.query(City).filter(City.name == "Delhi").first()
    mumbai = db_session.query(City).filter(City.name == "Mumbai").first()

    now_utc = datetime.now(UTC)

    # Fresh reading for Delhi: AQI 240 (Poor), dominant PM2.5, observed
    st_delhi = MonitoringStation(
        station_name="Anand Vihar Sensor",
        external_station_id="DEL_AV_99",
        city_id=delhi.id,
        latitude=28.65,
        longitude=77.31,
        provider="CPCB",
        is_active=True,
    )
    db_session.add(st_delhi)
    db_session.flush()

    delhi_reading = AQIReading(
        city_id=delhi.id,
        station_id=st_delhi.id,
        aqi_value=240,
        aqi_category="Poor",
        dominant_pollutant="PM2.5",
        measured_at=now_utc - timedelta(minutes=45),  # 45 min old -> fresh
        source="CPCB",
        is_simulated=False,
        data_quality="valid",
    )
    db_session.add(delhi_reading)

    # Stale reading for Mumbai: AQI 65 (Satisfactory), dominant PM10, simulated
    mumbai_reading = AQIReading(
        city_id=mumbai.id,
        station_id=None,
        aqi_value=65,
        aqi_category="Satisfactory",
        dominant_pollutant="PM10",
        measured_at=now_utc - timedelta(hours=8),  # 8 hours old -> stale!
        source="SIMULATED",
        is_simulated=True,
        data_quality="valid",
    )
    db_session.add(mumbai_reading)
    db_session.commit()

    return {
        "delhi": delhi,
        "mumbai": mumbai,
        "st_delhi": st_delhi,
    }


class MockAIProvider(BaseAIProvider):
    """Deterministic mock provider for unit testing."""

    def __init__(self, response_text: str = "Mock AI health response.", should_fail: Exception | None = None):
        self.response_text = response_text
        self.should_fail = should_fail
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "mock_gemini"

    def get_model_name(self) -> str:
        return "gemini-2.5-flash-mock"

    async def generate_response(self, request: AICompletionRequest) -> AICompletionResponse:
        self.calls += 1
        if self.should_fail:
            raise self.should_fail
        return AICompletionResponse(
            content=self.response_text,
            model=self.get_model_name(),
            finish_reason="STOP",
        )


# ---------------------------------------------------------------------------
# Unit Tests: Provider, Config & Exceptions
# ---------------------------------------------------------------------------

def test_gemini_provider_unconfigured():
    """Verify GeminiProvider identifies unconfigured state when API key is missing."""
    provider = GeminiProvider(api_key=None, settings=Settings(GEMINI_API_KEY=None))
    assert provider.is_configured() is False
    assert provider.get_provider_name() == "gemini"


@pytest.mark.anyio
async def test_gemini_provider_missing_key_raises_auth_error():
    """Verify generate_response raises AIAuthError if key is missing."""
    provider = GeminiProvider(api_key="", settings=Settings(GEMINI_API_KEY=None))
    req = AICompletionRequest(prompt="Is it safe to run?")
    with pytest.raises(AIAuthError) as exc_info:
        await provider.generate_response(req)
    assert "missing" in str(exc_info.value).lower() or "not configured" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_gemini_provider_timeout_handling():
    """Verify GeminiProvider raises AITimeoutError when client call times out."""
    provider = GeminiProvider(api_key="test-key", timeout=1, max_retries=1)

    mock_client = MagicMock()
    # Simulate timeout by sleeping longer than timeout
    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(2)
        return MagicMock(text="Too late")

    mock_client.aio.models.generate_content = slow_generate
    provider._client = mock_client

    req = AICompletionRequest(prompt="Test prompt")
    with pytest.raises(AITimeoutError):
        await provider.generate_response(req)


@pytest.mark.anyio
async def test_gemini_provider_rate_limit_and_retries():
    """Verify GeminiProvider retries and maps 429 to AIRateLimitError."""
    provider = GeminiProvider(api_key="test-key", timeout=5, max_retries=1)

    mock_client = MagicMock()
    # Mock error containing 429
    mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("429 Resource has been exhausted"))
    provider._client = mock_client

    req = AICompletionRequest(prompt="Test prompt")
    with pytest.raises(AIRateLimitError):
        await provider.generate_response(req)

    # 1 initial try + 1 retry = 2 attempts
    assert mock_client.aio.models.generate_content.call_count == 2


# ---------------------------------------------------------------------------
# Unit Tests: Context Builder & Freshness
# ---------------------------------------------------------------------------

def test_context_builder_fresh_data(db_session: Session, health_test_data):
    """Verify context builder reports fresh data correctly."""
    snapshot = ContextBuilder.build_snapshot(db_session, "Delhi")
    assert snapshot.city_name == "Delhi"
    assert snapshot.aqi == 240
    assert snapshot.category == "Poor"
    assert snapshot.dominant_pollutant == "PM2.5"
    assert snapshot.is_stale is False
    assert snapshot.is_simulated is False
    assert snapshot.station_name == "Anand Vihar Sensor"


def test_context_builder_stale_and_simulated_data(db_session: Session, health_test_data):
    """Verify context builder detects stale readings (> 5 hours old) and simulation flag."""
    snapshot = ContextBuilder.build_snapshot(db_session, "Mumbai")
    assert snapshot.city_name == "Mumbai"
    assert snapshot.aqi == 65
    assert snapshot.category == "Satisfactory"
    assert snapshot.is_stale is True
    assert snapshot.is_simulated is True


def test_context_builder_unknown_city(db_session: Session):
    """Verify context builder handles non-existent city gracefully."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        ContextBuilder.build_snapshot(db_session, "UnknownCity999")
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Unit Tests: Recommendation Engine
# ---------------------------------------------------------------------------

def test_recommendation_engine_poor_aqi():
    """Verify recommendations for Poor AQI emphasize indoor alternatives and N95 masks."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(
        city_name="Delhi",
        aqi=250,
        category="Poor",
        dominant_pollutant="PM2.5",
        is_stale=False,
        is_simulated=False,
    )
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 3
    titles = [r.title for r in recs]
    assert any("N95" in t or "Respirator" in t for t in titles)
    assert any("Indoor" in t or "Exercise" in t for t in titles)


def test_recommendation_engine_good_aqi():
    """Verify recommendations for Good AQI encourage outdoor activity and ventilation."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(
        city_name="Bengaluru",
        aqi=35,
        category="Good",
        dominant_pollutant="PM10",
        is_stale=False,
        is_simulated=False,
    )
    recs = RecommendationEngine.generate_recommendations(snapshot)
    titles = [r.title for r in recs]
    assert any("Unrestricted" in t or "Outdoor" in t for t in titles)


# ---------------------------------------------------------------------------
# Unit Tests: Safety Validator & Guardrails
# ---------------------------------------------------------------------------

def test_safety_validator_rejects_empty_and_oversized_questions():
    """Verify question length validation."""
    with pytest.raises(Exception):
        HealthSafetyValidator.validate_question("")

    with pytest.raises(Exception):
        HealthSafetyValidator.validate_question("a" * 501)

    valid_q = HealthSafetyValidator.validate_question("Is it safe to go for a run in Delhi today?")
    assert valid_q == "Is it safe to go for a run in Delhi today?"


def test_safety_validator_rejects_excessive_history():
    """Verify history bounding (max 10 turns)."""
    history = [ChatMessage(role="user", content=f"Q{i}") for i in range(11)]
    with pytest.raises(Exception) as exc:
        HealthSafetyValidator.validate_history(history)
    assert "maximum limit" in str(exc.value)


def test_safety_validator_sanitizes_prescriptions_and_appends_disclaimer():
    """Verify dangerous prescription instructions are sanitized and disclaimer is guaranteed."""
    unsafe_text = "You should take 500mg of amoxicillin and stop your prescription immediately."
    cleaned = HealthSafetyValidator.validate_and_sanitize_response(unsafe_text)

    assert "licensed healthcare professional" in cleaned
    assert "Disclaimer:" in cleaned


# ---------------------------------------------------------------------------
# Unit Tests: Health Knowledge Base
# ---------------------------------------------------------------------------

def test_knowledge_base_guidelines():
    """Verify guidelines exist for all 6 categories."""
    for cat in ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]:
        g = HealthKnowledgeBase.get_category_guideline(cat)
        assert g.category.lower() == cat.lower() or cat.lower() in g.category.lower()
        assert len(g.precautions) > 0


def test_knowledge_base_pollutants():
    """Verify all 8 criteria pollutants have comprehensive descriptions."""
    for code in ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "NH3", "Pb"]:
        expl = HealthKnowledgeBase.get_pollutant_explanation(code)
        assert expl is not None
        assert expl.pollutant_code.upper() == code.upper()
        assert len(expl.common_sources) > 0
        assert len(expl.health_effects) > 0
        assert len(expl.reduction_measures) > 0


# ---------------------------------------------------------------------------
# Integration Tests: Endpoints via AsyncClient
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_health_status(client: AsyncClient):
    """Verify GET /api/v1/health/status returns operational status without leaking secrets."""
    response = await client.get("/api/v1/health/status")
    assert response.status_code == 200
    data = response.json()

    assert "ai_enabled" in data
    assert "provider" in data
    assert "model" in data
    assert "available" in data
    assert "api_key_configured" in data
    # Ensure no secret key is exposed in the response
    assert "key" not in data or data.get("key") is None


@pytest.mark.anyio
async def test_get_health_guidelines(client: AsyncClient):
    """Verify GET /api/v1/health/guidelines returns structured CPCB/WHO guidance."""
    response = await client.get("/api/v1/health/guidelines")
    assert response.status_code == 200
    data = response.json()

    assert len(data["guidelines"]) == 6
    assert "General adults" in data["target_groups_covered"]
    assert "Disclaimer:" in data["disclaimer"]


@pytest.mark.anyio
async def test_get_pollutant_explanation_endpoint(client: AsyncClient):
    """Verify GET /api/v1/health/pollutants/{pollutant_code}."""
    # 1. Valid pollutant: PM2.5
    resp = await client.get("/api/v1/health/pollutants/PM2.5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pollutant_code"] == "PM2.5"
    assert data["unit"] == "µg/m³"
    assert len(data["common_sources"]) > 0

    # 2. Case insensitive: pb
    resp_pb = await client.get("/api/v1/health/pollutants/pb")
    assert resp_pb.status_code == 200
    assert resp_pb.json()["pollutant_code"] == "Pb"

    # 3. Invalid pollutant: CH4 -> 404
    resp_invalid = await client.get("/api/v1/health/pollutants/CH4")
    assert resp_invalid.status_code == 404


@pytest.mark.anyio
async def test_get_health_recommendations_endpoint(client: AsyncClient, health_test_data):
    """Verify GET /api/v1/health/recommendations uses verified live context."""
    response = await client.get("/api/v1/health/recommendations?city=Delhi")
    assert response.status_code == 200
    data = response.json()

    assert data["city"] == "Delhi"
    assert data["aqi_context"]["aqi"] == 240
    assert data["aqi_context"]["category"] == "Poor"
    assert data["aqi_context"]["is_stale"] is False
    assert len(data["recommendations"]) >= 3


@pytest.mark.anyio
async def test_post_health_ask_ai_generated(client: AsyncClient, db_session: Session, health_test_data):
    """Verify POST /api/v1/health/ask produces an AI-grounded response with verified context."""
    mock_provider = MockAIProvider(response_text="Based on Delhi's Poor AQI of 240, running outdoors is not advisable.")
    advisor = HealthAdvisorService(ai_provider=mock_provider)

    from app.api.v1.endpoints.health import get_health_advisor
    from app.main import app

    app.dependency_overrides[get_health_advisor] = lambda: advisor

    try:
        payload = {
            "city": "Delhi",
            "question": "Is it safe to go jogging in Delhi this afternoon?",
            "conversation_history": [
                {"role": "user", "content": "Hello advisor"},
                {"role": "model", "content": "Hello! How can I assist you?"},
            ],
        }
        response = await client.post("/api/v1/health/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["response_type"] == "ai_generated"
        assert "Delhi" in data["answer"] or "240" in data["answer"]
        assert data["aqi_context"]["aqi"] == 240
        assert data["data_freshness"] == "fresh"
        assert len(data["recommendations"]) >= 3
        assert "Disclaimer:" in data["disclaimer"]
        assert mock_provider.calls == 1
    finally:
        app.dependency_overrides.pop(get_health_advisor, None)


@pytest.mark.anyio
async def test_post_health_ask_knowledge_base_fallback(client: AsyncClient, db_session: Session, health_test_data):
    """Verify POST /api/v1/health/ask falls back to knowledge base when AI provider fails."""
    # Simulate a provider failure (e.g. timeout or rate-limit)
    failing_provider = MockAIProvider(should_fail=AITimeoutError("Gemini call timed out"))
    advisor = HealthAdvisorService(ai_provider=failing_provider)

    from app.api.v1.endpoints.health import get_health_advisor
    from app.main import app

    app.dependency_overrides[get_health_advisor] = lambda: advisor

    try:
        payload = {
            "city": "Delhi",
            "question": "What precautions should older adults take right now?",
        }
        response = await client.post("/api/v1/health/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Fallback response verification
        assert data["response_type"] == "knowledge_base_fallback"
        assert "CPCB" in data["answer"]
        assert "Poor" in data["answer"]
        assert data["aqi_context"]["aqi"] == 240
        assert len(data["recommendations"]) >= 3
        assert "Disclaimer:" in data["disclaimer"]
    finally:
        app.dependency_overrides.pop(get_health_advisor, None)


@pytest.mark.anyio
async def test_post_health_ask_city_isolation(client: AsyncClient, db_session: Session, health_test_data):
    """Verify requesting health guidance for Mumbai does not bleed Delhi's AQI context."""
    mock_provider = MockAIProvider(response_text="Guidance for Mumbai")
    advisor = HealthAdvisorService(ai_provider=mock_provider)

    from app.api.v1.endpoints.health import get_health_advisor
    from app.main import app

    app.dependency_overrides[get_health_advisor] = lambda: advisor

    try:
        payload = {
            "city": "Mumbai",
            "question": "Should children play outdoors?",
        }
        response = await client.post("/api/v1/health/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["aqi_context"]["city_name"] == "Mumbai"
        assert data["aqi_context"]["aqi"] == 65
        assert data["aqi_context"]["category"] == "Satisfactory"
        assert data["aqi_context"]["is_stale"] is True  # Stale detection verified
        assert data["data_freshness"] == "stale"
    finally:
        app.dependency_overrides.pop(get_health_advisor, None)


# ---------------------------------------------------------------------------
# Challenge 6 Alignment & Community Solutions Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_community_solutions_endpoint(client: AsyncClient):
    """Verify Challenge 6 community solutions endpoint returns structured guidance across all 5 pillars."""
    response = await client.get("/api/v1/health/community-solutions")
    assert response.status_code == 200
    data = response.json()

    assert "Winter Smog" in data["title"]
    assert len(data["winter_smog_guidance"]) >= 2
    assert len(data["low_emission_routines"]) >= 3
    assert len(data["indoor_air_hacks"]) >= 3
    assert len(data["sustainable_alternatives"]) >= 2
    assert len(data["direct_impact_analysis"]) >= 4

    # Verify impact explanations are quantified
    for item in data["winter_smog_guidance"] + data["low_emission_routines"] + data["indoor_air_hacks"]:
        assert item["impact_explanation"] is not None
        assert any(unit in item["impact_explanation"] for unit in ("%", "kg", "µg/m³"))


def test_recommendation_engine_challenge_pillars():
    """Verify recommendation engine categorizes guidance into specific Challenge 6 pillars."""
    from app.integrations.ai.schemas import AQIContextSnapshot

    poor_snapshot = AQIContextSnapshot(
        city_name="Delhi",
        aqi=260,
        category="Poor",
        dominant_pollutant="PM2.5",
        is_stale=False,
        is_simulated=False,
    )
    recs = RecommendationEngine.generate_recommendations(poor_snapshot)

    category_types = {r.category_type for r in recs}
    assert "indoor_hack" in category_types
    assert "low_emission_routine" in category_types
    assert any(r.impact_explanation is not None for r in recs)


@pytest.mark.anyio
async def test_knowledge_base_fallback_winter_smog_enrichment(client: AsyncClient, health_test_data):
    """Verify knowledge-base fallback answer dynamically appends winter smog & direct impact guidance."""
    from app.api.v1.endpoints.health import get_health_advisor
    from app.main import app

    failing_provider = MockAIProvider(should_fail=True)
    advisor = HealthAdvisorService(ai_provider=failing_provider)
    app.dependency_overrides[get_health_advisor] = lambda: advisor

    try:
        payload = {
            "city": "Delhi",
            "question": "How should my family protect children during severe winter smog?",
        }
        response = await client.post("/api/v1/health/ask", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["response_type"] == "knowledge_base_fallback"
        assert "Winter Smog & Inversion Protocols for Families" in data["answer"]
        assert "Direct Impact" in data["answer"]
    finally:
        app.dependency_overrides.pop(get_health_advisor, None)


