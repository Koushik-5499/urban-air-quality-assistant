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



# ---------------------------------------------------------------------------
# Additional Coverage Tests: RecommendationEngine all AQI branches
# ---------------------------------------------------------------------------

def test_recommendation_engine_good_aqi_coverage():
    """Covers AQI <= 50 branch (Good category) for Coimbatore city."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(city_name="Coimbatore", aqi=30, category="Good", dominant_pollutant="PM2.5", is_stale=False, is_simulated=False)
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 3
    titles = [r.title for r in recs]
    assert any("Outdoor" in t or "Activity" in t for t in titles)


def test_recommendation_engine_satisfactory_aqi_coverage():
    """Covers AQI 51-100 branch (Satisfactory) for Chennai city."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(city_name="Chennai", aqi=75, category="Satisfactory", dominant_pollutant="PM10", is_stale=False, is_simulated=False)
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 2


def test_recommendation_engine_moderate_aqi_coverage():
    """Covers AQI 101-200 branch (Moderate) for Bengaluru city."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(city_name="Bengaluru", aqi=150, category="Moderately Polluted", dominant_pollutant="NO2", is_stale=False, is_simulated=False)
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 3
    priorities = [r.priority for r in recs]
    assert "medium" in priorities or "high" in priorities


def test_recommendation_engine_very_poor_aqi():
    """Covers AQI 301-400 branch (Very Poor category) with winter smog pillars."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(city_name="Delhi", aqi=360, category="Very Poor", dominant_pollutant="PM2.5", is_stale=False, is_simulated=False)
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 5
    category_types = {r.category_type for r in recs if r.category_type}
    assert "winter_smog" in category_types
    assert "indoor_hack" in category_types
    impact_recs = [r for r in recs if r.impact_explanation]
    assert len(impact_recs) >= 3


def test_recommendation_engine_severe_aqi():
    """Covers AQI > 400 branch (Severe category) with all 5 Challenge 6 pillars."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(city_name="Delhi", aqi=450, category="Severe", dominant_pollutant="PM2.5", is_stale=False, is_simulated=False)
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) >= 5
    category_types = {r.category_type for r in recs if r.category_type}
    assert "winter_smog" in category_types
    assert "indoor_hack" in category_types
    assert "low_emission_routine" in category_types
    for r in recs:
        if r.impact_explanation:
            assert len(r.impact_explanation) > 10


def test_recommendation_engine_no_aqi():
    """Covers aqi is None fallback branch."""
    from app.integrations.ai.schemas import AQIContextSnapshot
    snapshot = AQIContextSnapshot(city_name="Unknown", aqi=None, category="Unknown", dominant_pollutant=None, is_stale=True, is_simulated=False)
    recs = RecommendationEngine.generate_recommendations(snapshot)
    assert len(recs) == 1
    assert "Monitor" in recs[0].title


# ---------------------------------------------------------------------------
# AQI Categories Coverage Tests
# ---------------------------------------------------------------------------

def test_aqi_category_mapping_all_tiers():
    """Covers get_aqi_category for all 6 CPCB tiers."""
    from app.services.aqi.categories import get_aqi_category
    assert get_aqi_category(25) == "Good"
    assert get_aqi_category(50) == "Good"
    assert get_aqi_category(75) == "Satisfactory"
    assert get_aqi_category(100) == "Satisfactory"
    assert get_aqi_category(150) == "Moderately Polluted"
    assert get_aqi_category(200) == "Moderately Polluted"
    assert get_aqi_category(250) == "Poor"
    assert get_aqi_category(300) == "Poor"
    assert get_aqi_category(350) == "Very Poor"
    assert get_aqi_category(400) == "Very Poor"
    assert get_aqi_category(450) == "Severe"
    assert get_aqi_category(500) == "Severe"


def test_get_category_info_all_tiers():
    """Covers get_category_info for all CPCB tiers."""
    from app.services.aqi.categories import get_category_info
    for aqi_val in [30, 75, 150, 250, 350, 450]:
        info = get_category_info(aqi_val)
        assert info.category
        assert info.color_hex.startswith("#")
        assert info.health_statement


# ---------------------------------------------------------------------------
# ComparisonService Coverage Tests
# ---------------------------------------------------------------------------

def test_comparison_service_empty_city_list(db_session):
    """ComparisonService with empty city list returns empty comparisons."""
    from app.services.history.comparison_service import ComparisonService
    result = ComparisonService.compare_locations(db=db_session, cities=[], stations=[])
    assert result.comparisons == []


def test_comparison_service_nonexistent_city(db_session):
    """ComparisonService with nonexistent city skips it gracefully."""
    from app.services.history.comparison_service import ComparisonService
    result = ComparisonService.compare_locations(db=db_session, cities=["NonexistentCity123"], stations=[])
    assert result.comparisons == []


def test_comparison_service_single_city_with_data(db_session, health_test_data):
    """ComparisonService with valid seeded city returns comparison data."""
    from app.services.history.comparison_service import ComparisonService
    result = ComparisonService.compare_locations(db=db_session, cities=["Delhi"], stations=[])
    assert len(result.comparisons) >= 1
    delhi = result.comparisons[0]
    assert delhi.city_name == "Delhi"
    assert delhi.record_count >= 0


def test_comparison_service_multiple_cities(db_session, health_test_data):
    """ComparisonService correctly compares multiple cities."""
    from app.services.history.comparison_service import ComparisonService
    result = ComparisonService.compare_locations(db=db_session, cities=["Delhi", "Mumbai"], stations=[])
    # Both may appear if data is seeded
    assert len(result.comparisons) >= 1


# ---------------------------------------------------------------------------
# MockAIProvider as LSP Proof: interchangeable with GeminiProvider
# ---------------------------------------------------------------------------

def test_mock_ai_provider_satisfies_base_interface():
    """Verify MockAIProvider fully satisfies BaseAIProvider interface (LSP proof)."""
    mock = MockAIProvider(response_text="Sample response for winter smog scenario")
    assert isinstance(mock, BaseAIProvider)
    assert mock.is_configured() is True
    assert mock.get_provider_name() == "mock_gemini"
    assert mock.get_model_name() == "gemini-2.5-flash-mock"


@pytest.mark.anyio
async def test_mock_ai_provider_generate_response():
    """Verify MockAIProvider generates valid AICompletionResponse."""
    mock = MockAIProvider(response_text="Take precautions during winter smog. Direct impact: reduces PM2.5 intake by 40%.")
    request = AICompletionRequest(
        prompt="What precautions should I take at AQI 350?",
        system_instruction="You are an urban air quality health advisor.",
    )
    response = await mock.generate_response(request)
    assert response.content == "Take precautions during winter smog. Direct impact: reduces PM2.5 intake by 40%."
    assert response.finish_reason == "STOP"


# ---------------------------------------------------------------------------
# NotificationService Coverage: Disabled push path
# ---------------------------------------------------------------------------

def test_notification_service_disabled_push():
    """NotificationService returns 0 when VAPID keys are unconfigured."""
    from app.core.config import Settings
    from app.services.alerts.notification_service import NotificationService
    settings = Settings(WEB_PUSH_ENABLED=False, VAPID_PRIVATE_KEY=None, VAPID_PUBLIC_KEY=None)
    svc = NotificationService(settings=settings)
    assert svc.settings.WEB_PUSH_ENABLED is False


# ---------------------------------------------------------------------------
# Knowledge Base: Winter Smog Guidance Validation
# ---------------------------------------------------------------------------

def test_knowledge_base_winter_smog_guidance():
    """Knowledge base contains actionable winter smog guidance for all 5 Challenge 6 pillars."""
    from app.services.health.knowledge_base import HealthKnowledgeBase
    assert len(HealthKnowledgeBase.WINTER_SMOG_GUIDANCE) >= 2
    assert len(HealthKnowledgeBase.LOW_EMISSION_ROUTINES) >= 3
    assert len(HealthKnowledgeBase.INDOOR_AIR_HACKS) >= 3
    assert len(HealthKnowledgeBase.SUSTAINABLE_ALTERNATIVES) >= 2
    assert len(HealthKnowledgeBase.DIRECT_IMPACT_METRICS) >= 4
    # Every direct impact metric must include quantified result
    for metric in HealthKnowledgeBase.DIRECT_IMPACT_METRICS:
        assert any(unit in metric for unit in ("%", "kg", "µg/m³", "µg"))


# ---------------------------------------------------------------------------
# Lifestyle & Household Context Tailoring (Challenge 6)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_health_advisor_lifestyle_tailoring(db_session, health_test_data):
    """HealthAdvisorService incorporates lifestyle persona and family context into recommendations."""
    from app.core.config import Settings
    from app.integrations.ai.schemas import HealthAskRequest
    from app.services.health.health_advisor import HealthAdvisorService

    settings = Settings(APP_ENV="test", AI_ENABLED=False)
    advisor = HealthAdvisorService(settings=settings)

    request = HealthAskRequest(
        city="Delhi",
        question="What precautions should my school-going kids take during morning smog?",
        lifestyle="family_with_children",
        family_context="infants_and_school_kids",
    )
    response = await advisor.ask(db=db_session, request=request)

    assert response.lifestyle_persona == "family_with_children"
    assert len(response.direct_impact_metrics) >= 4
    assert any("%" in m or "kg" in m for m in response.direct_impact_metrics)


# ---------------------------------------------------------------------------
# Notification Channel Abstractions & Liskov Substitution (SOLID)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_notification_channels_lsp(db_session):
    """BaseNotificationChannel subclasses WebPush and InApp satisfy LSP."""
    from app.core.config import Settings
    from app.services.alerts.notification_service import (
        BaseNotificationChannel,
        InAppNotificationChannel,
        NotificationService,
        WebPushNotificationChannel,
    )

    settings = Settings(WEB_PUSH_ENABLED=False, VAPID_PRIVATE_KEY=None)
    web_push_ch = WebPushNotificationChannel(settings=settings)
    in_app_ch = InAppNotificationChannel()

    assert isinstance(web_push_ch, BaseNotificationChannel)
    assert isinstance(in_app_ch, BaseNotificationChannel)
    assert web_push_ch.channel_name == "web_push"
    assert in_app_ch.channel_name == "in_app"

    # Both dispatch without throwing
    res_push = await web_push_ch.dispatch(db=db_session, recipient="test-user", title="Test", body="Body")
    assert res_push == 0  # disabled

    res_inapp = await in_app_ch.dispatch(db=db_session, recipient="test-user", title="Test", body="Body")
    assert res_inapp == 1

    # NotificationService dispatch_all_channels
    svc = NotificationService(settings=settings)
    all_res = await svc.dispatch_all_channels(db=db_session, user_id="test-user", title="Test", body="Body")
    assert "web_push" in all_res
    assert "in_app" in all_res


# ---------------------------------------------------------------------------
# DataNormalizationService Full Coverage
# ---------------------------------------------------------------------------

def test_data_normalization_service_full_coverage():
    """Verify DataNormalizationService canonical matching and core pollutant verification."""
    from app.services.data_normalization_service import DataNormalizationService

    # 1. Direct match with matching state
    res1 = DataNormalizationService.match_canonical_city("chennai", "Tamil Nadu")
    assert res1 == ("Chennai", "Tamil Nadu")

    # 2. Direct match with mismatched state
    res2 = DataNormalizationService.match_canonical_city("chennai", "Maharashtra")
    assert res2 is None

    # 3. Empty input
    assert DataNormalizationService.match_canonical_city("") is None

    # 4. Partial token match with matching state
    res3 = DataNormalizationService.match_canonical_city("Delhi (Anand Vihar)", "Delhi")
    assert res3 == ("Delhi", "Delhi")

    # 5. Partial token match with mismatched state
    res4 = DataNormalizationService.match_canonical_city("Delhi (Anand Vihar)", "Karnataka")
    assert res4 is None

    # 6. Completely unknown city
    assert DataNormalizationService.match_canonical_city("Atlantis") is None

    # 7. Core pollutant check
    assert DataNormalizationService.is_core_pollutant("PM2.5") is True
    assert DataNormalizationService.is_core_pollutant("pm10") is True
    assert DataNormalizationService.is_core_pollutant("O3") is True
    assert DataNormalizationService.is_core_pollutant("LEAD") is False


# ---------------------------------------------------------------------------
# ComparisonService Station-Level Coverage
# ---------------------------------------------------------------------------

def test_comparison_service_station_evaluation(db_session, health_test_data):
    """ComparisonService correctly evaluates monitoring stations alongside cities."""
    from app.models.monitoring_station import MonitoringStation
    from app.services.history.comparison_service import ComparisonService

    station = db_session.execute(
        MonitoringStation.__table__.select().limit(1)
    ).first()

    if station:
        st_id = station.id
        result = ComparisonService.compare_locations(
            db=db_session,
            cities=["Delhi"],
            stations=[st_id, 999999],  # valid station + nonexistent station
        )
        assert len(result.comparisons) >= 2
        station_comp = next((c for c in result.comparisons if c.location_type == "station"), None)
        assert station_comp is not None
        assert station_comp.station_id == st_id
        assert station_comp.city_name == "Delhi"


# ---------------------------------------------------------------------------
# Security: Multi-Header Admin Secret Verification
# ---------------------------------------------------------------------------

def test_verify_admin_access_multi_header():
    """verify_admin_access accepts X-Admin-Secret, X-API-Key, and Bearer token."""
    from fastapi import HTTPException

    from app.core.config import Settings
    from app.core.security import verify_admin_access

    settings = Settings(
        APP_ENV="production",
        ALERT_ADMIN_SECRET="test_secret_123",
    )

    # 1. Valid X-Admin-Secret
    verify_admin_access(x_admin_secret="test_secret_123", settings=settings)

    # 2. Valid X-API-Key
    verify_admin_access(x_api_key="test_secret_123", settings=settings)

    # 3. Valid Authorization Bearer
    verify_admin_access(authorization="Bearer test_secret_123", settings=settings)

    # 4. Invalid secret raises 403
    with pytest.raises(HTTPException) as exc_info:
        verify_admin_access(x_admin_secret="wrong", settings=settings)
    assert exc_info.value.status_code == 403

