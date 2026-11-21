"""Health Advisor Service coordinating AI generation, context grounding, and fallback guidance."""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.ai.base import BaseAIProvider
from app.integrations.ai.exceptions import AIProviderError
from app.integrations.ai.gemini_provider import GeminiProvider
from app.integrations.ai.schemas import (
    AICompletionRequest,
    AQIContextSnapshot,
    HealthAskRequest,
    HealthAskResponse,
    HealthGuidelinesResponse,
    HealthRecommendationsResponse,
    HealthStatusResponse,
    PollutantExplanationResponse,
)
from app.services.health.context_builder import ContextBuilder
from app.services.health.knowledge_base import (
    AUTHORITATIVE_SOURCES,
    MEDICAL_DISCLAIMER,
    TARGET_GROUPS,
    HealthKnowledgeBase,
)
from app.services.health.recommendation_engine import RecommendationEngine
from app.services.health.safety_validator import HealthSafetyValidator

logger = logging.getLogger(__name__)


class HealthAdvisorService:
    """Orchestrates verified environmental context injection, Gemini generation, and knowledge-base fallbacks."""

    def __init__(
        self,
        ai_provider: BaseAIProvider | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.ai_provider = ai_provider or GeminiProvider(settings=self.settings)

    def get_status(self) -> HealthStatusResponse:
        """Check AI advisor readiness and provider configuration without exposing secrets."""
        is_configured = self.ai_provider.is_configured()
        is_enabled = self.settings.AI_ENABLED
        return HealthStatusResponse(
            ai_enabled=is_enabled,
            provider=self.ai_provider.get_provider_name(),
            model=self.ai_provider.get_model_name(),
            available=is_enabled and is_configured,
            api_key_configured=is_configured,
        )

    def get_guidelines(self) -> HealthGuidelinesResponse:
        """Retrieve complete category-specific health guidelines and protective guidance."""
        categories = list(HealthKnowledgeBase.CATEGORY_GUIDELINES.values())
        return HealthGuidelinesResponse(
            title="CPCB & WHO Environmental Air Quality Health Guidelines",
            guidelines=categories,
            target_groups_covered=TARGET_GROUPS,
            sources=AUTHORITATIVE_SOURCES,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    def get_pollutant_explanation(self, pollutant_code: str) -> PollutantExplanationResponse:
        """Retrieve comprehensive educational and health information for a criteria pollutant."""
        explanation = HealthKnowledgeBase.get_pollutant_explanation(pollutant_code)
        if not explanation:
            valid_codes = list(HealthKnowledgeBase.POLLUTANT_DETAILS.keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pollutant '{pollutant_code}' is not supported. Supported pollutants: {valid_codes}.",
            )
        return explanation

    def get_recommendations(
        self,
        db: Session,
        city: str,
        station_id: int | None = None,
    ) -> HealthRecommendationsResponse:
        """Generate structured, verified health recommendations for a specific city or station."""
        snapshot = ContextBuilder.build_snapshot(db, city_name=city, station_id=station_id)
        recommendations = RecommendationEngine.generate_recommendations(snapshot)

        return HealthRecommendationsResponse(
            city=snapshot.city_name,
            station_id=snapshot.station_id,
            aqi_context=snapshot,
            recommendations=recommendations,
            sources=AUTHORITATIVE_SOURCES,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    async def ask(
        self,
        db: Session,
        request: HealthAskRequest,
    ) -> HealthAskResponse:
        """Answer user health inquiries grounded in live verified air quality observations."""
        # 1. Validate user inputs
        clean_question = HealthSafetyValidator.validate_question(request.question)
        clean_history = HealthSafetyValidator.validate_history(request.conversation_history)

        # 2. Build verified environmental context
        snapshot = ContextBuilder.build_snapshot(db, city_name=request.city)

        freshness_label = "no_data"
        if snapshot.aqi is not None:
            freshness_label = "stale" if snapshot.is_stale else "fresh"

        # 3. Generate deterministic rule-based recommendations
        recommendations = RecommendationEngine.generate_recommendations(snapshot)

        # 4. Attempt AI completion if enabled and configured
        ai_enabled = self.settings.AI_ENABLED and self.ai_provider.is_configured()

        if ai_enabled:
            context_str = ContextBuilder.format_context_for_prompt(snapshot)
            system_instruction = HealthSafetyValidator.build_system_instruction(context_str)

            ai_request = AICompletionRequest(
                prompt=clean_question,
                system_instruction=system_instruction,
                conversation_history=clean_history,
                temperature=0.2,
                max_tokens=1024,
            )

            try:
                ai_response = await self.ai_provider.generate_response(ai_request)
                validated_answer = HealthSafetyValidator.validate_and_sanitize_response(ai_response.content)

                return HealthAskResponse(
                    answer=validated_answer,
                    recommendations=recommendations,
                    aqi_context=snapshot,
                    sources=AUTHORITATIVE_SOURCES,
                    disclaimer=MEDICAL_DISCLAIMER,
                    data_freshness=freshness_label,
                    response_type="ai_generated",
                    model=self.ai_provider.get_model_name(),
                )

            except AIProviderError as exc:
                logger.warning("AI provider failed (%s), falling back to knowledge base: %s", type(exc).__name__, exc)
            except Exception as exc:
                logger.error("Unexpected error during AI health advisor call: %s", exc)

        # 5. Deterministic Knowledge-Base Fallback (when AI is disabled, unconfigured, or failing)
        fallback_answer = self._generate_knowledge_base_fallback(
            question=clean_question,
            snapshot=snapshot,
        )

        return HealthAskResponse(
            answer=fallback_answer,
            recommendations=recommendations,
            aqi_context=snapshot,
            sources=AUTHORITATIVE_SOURCES,
            disclaimer=MEDICAL_DISCLAIMER,
            data_freshness=freshness_label,
            response_type="knowledge_base_fallback",
            model=None,
        )

    def _generate_knowledge_base_fallback(
        self,
        question: str,
        snapshot: AQIContextSnapshot,
    ) -> str:
        """Synthesize a safe, authoritative fallback answer using structured knowledge base rules."""
        city = snapshot.city_name
        aqi = snapshot.aqi
        category = snapshot.category or "Moderate"
        dominant = snapshot.dominant_pollutant or "particulate matter"
        guideline = HealthKnowledgeBase.get_category_guideline(category)

        header = f"### Air Quality Guidance for {city}\n\n"
        if aqi is not None:
            header += f"Current air quality is categorized as **{category}** (AQI: {aqi}, dominant pollutant: {dominant}).\n\n"
            if snapshot.is_stale:
                header += "> **Note on Data Freshness**: The latest available measurement is over 5 hours old. Current ambient conditions may differ.\n\n"
            if snapshot.is_simulated:
                header += "> **Demonstration Note**: Current telemetry reflects simulated demonstration data.\n\n"
        else:
            header += f"Real-time observation data is currently unavailable for {city}. General urban air quality precautions apply.\n\n"

        body = (
            f"**Official CPCB Impact**: {guideline.health_statement}\n\n"
            f"**General Public Recommendation**: {guideline.general_guidance}\n\n"
            f"**For Sensitive & Vulnerable Groups**: {guideline.vulnerable_guidance}\n\n"
            "**Key Protective Steps**:\n"
        )
        for p in guideline.precautions:
            body += f"- {p}\n"

        footer = (
            "\n*(Notice: The AI generation service is currently operating in offline mode. "
            "This guidance is provided directly from the verified CPCB and WHO public health knowledge base.)*\n\n"
            + MEDICAL_DISCLAIMER
        )

        return header + body + footer

