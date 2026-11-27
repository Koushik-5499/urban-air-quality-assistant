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
    CommunitySolutionsResponse,
    HealthAskRequest,
    HealthAskResponse,
    HealthGuidelinesResponse,
    HealthRecommendationsResponse,
    HealthStatusResponse,
    ImpactMetricsResponse,
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
    """Orchestrates verified environmental context, Gemini generation, and knowledge fallbacks."""

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

    def get_community_solutions(self) -> CommunitySolutionsResponse:
        """Retrieve structured community solutions: winter smog, low-emission routines, hacks."""
        return HealthKnowledgeBase.get_community_solutions()

    def get_impact_metrics(self) -> ImpactMetricsResponse:
        """Retrieve CPCB/WHO-sourced quantified health impact metrics for Challenge 6 pillars."""
        return HealthKnowledgeBase.get_impact_metrics()

    def get_pollutant_explanation(self, pollutant_code: str) -> PollutantExplanationResponse:
        """Retrieve comprehensive educational and health information for a criteria pollutant."""
        explanation = HealthKnowledgeBase.get_pollutant_explanation(pollutant_code)
        if not explanation:
            valid_codes = list(HealthKnowledgeBase.POLLUTANT_DETAILS.keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Pollutant '{pollutant_code}' is not supported. "
                    f"Supported pollutants: {valid_codes}."
                ),
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
        impact_metrics = list(HealthKnowledgeBase.DIRECT_IMPACT_METRICS)
        lifestyle_persona = request.lifestyle or "family_with_children"

        # 4. Attempt AI completion if enabled and configured
        ai_enabled = self.settings.AI_ENABLED and self.ai_provider.is_configured()

        if ai_enabled:
            context_str = ContextBuilder.format_context_for_prompt(
                snapshot=snapshot,
                lifestyle=request.lifestyle,
                family_context=request.family_context,
            )
            system_instruction = HealthSafetyValidator.build_system_instruction(
                context_str=context_str,
                lifestyle=request.lifestyle,
                family_context=request.family_context,
            )

            ai_request = AICompletionRequest(
                prompt=clean_question,
                system_instruction=system_instruction,
                conversation_history=clean_history,
                temperature=0.2,
                max_tokens=1024,
            )

            try:
                ai_response = await self.ai_provider.generate_response(ai_request)
                validated_answer = HealthSafetyValidator.validate_and_sanitize_response(
                    ai_response.content
                )

                return HealthAskResponse(
                    answer=validated_answer,
                    recommendations=recommendations,
                    aqi_context=snapshot,
                    sources=AUTHORITATIVE_SOURCES,
                    disclaimer=MEDICAL_DISCLAIMER,
                    data_freshness=freshness_label,
                    response_type="ai_generated",
                    model=self.ai_provider.get_model_name(),
                    lifestyle_persona=lifestyle_persona,
                    direct_impact_metrics=impact_metrics,
                )

            except AIProviderError as exc:
                logger.warning(
                    "AI provider failed (%s), falling back to knowledge base: %s",
                    type(exc).__name__,
                    exc,
                )
            except Exception as exc:
                # Top-level AI advisor boundary ensuring deterministic fallback on error
                logger.exception("Unexpected error during AI health advisor call: %s", exc)

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
            lifestyle_persona=lifestyle_persona,
            direct_impact_metrics=impact_metrics,
        )

    @staticmethod
    def _build_fallback_header(
        city: str, aqi: int | None, category: str, dominant: str, snapshot: "AQIContextSnapshot"
    ) -> str:
        """Build the header section for the knowledge-base fallback response."""
        header = f"### Air Quality Guidance for {city}\n\n"
        if aqi is not None:
            header += (
                f"Current air quality is categorized as **{category}** "
                f"(AQI: {aqi}, dominant pollutant: {dominant}).\n\n"
            )
            if snapshot.is_stale:
                header += (
                    "> **Note on Data Freshness**: The latest available measurement "
                    "is over 5 hours old. Current ambient conditions may differ.\n\n"
                )
            if snapshot.is_simulated:
                header += (
                    "> **Demonstration Note**: Current telemetry reflects "
                    "simulated demonstration data.\n\n"
                )
        else:
            header += (
                f"Real-time observation data is currently unavailable for {city}. "
                "General urban air quality precautions apply.\n\n"
            )
        return header

    @staticmethod
    def _build_winter_smog_section() -> str:
        return (
            "**Winter Smog & Inversion Protocols for Families**:\n"
            "- Avoid early morning (6:00 AM – 9:30 AM) outdoor exposure when "
            "cold ground air traps vehicular soot and particulate matter.\n"
            "- Reschedule children's school bus waiting or morning sports to midday "
            "when convective heating breaks the inversion layer.\n"
            "- *Direct Impact*: Midday rescheduling cuts peak particulate "
            "inhalation by up to 52%."
        )

    @staticmethod
    def _build_commute_section() -> str:
        return (
            "**Low-Emission Daily Routines**:\n"
            "- Travel during off-peak windows (before 8 AM or after 10 AM) to avoid "
            "high stop-and-go in-cabin pollution.\n"
            "- Shift to electrified metro rail or electric buses for daily urban commutes.\n"
            "- *Direct Impact*: Metro transit saves ~3.2 kg CO2 per passenger daily "
            "and lowers in-cabin toxic gas exposure by 45%."
        )

    @staticmethod
    def _build_indoor_section() -> str:
        return (
            "**Indoor Air Quality Hacks**:\n"
            "- Diurnal Ventilation: Keep windows tightly sealed during morning and nighttime "
            "smog; open only between 12:30 PM – 3:30 PM on sunny days.\n"
            "- DIY Filtration: A box fan fitted with MERV-13 or HEPA filters "
            "(Corsi-Rosenthal box) reduces room PM2.5 by 75–85% at minimal cost.\n"
            "- Damp Cleaning: Always wet-mop instead of dry-sweeping to prevent "
            "resuspending coarse PM10 particles.\n"
            "- Air-Purifying Plants: Snake plants and Areca palms naturally absorb VOCs "
            "and refresh indoor spaces."
        )

    @staticmethod
    def _build_sustainable_section() -> str:
        return (
            "**Sustainable Community Alternatives**:\n"
            "- Use clean electric radiant or ceramic space heaters instead of "
            "open biomass/wood burning.\n"
            "- Report neighborhood garbage or leaf burning immediately through "
            "municipal clean-air apps.\n"
            "- *Direct Impact*: Eliminating open biomass burning removes localized "
            "PM2.5 spikes exceeding 800 µg/m³."
        )

    _WINTER_WORDS = ("winter", "smog", "inversion", "fog", "cold", "child", "school")
    _COMMUTE_WORDS = ("commute", "routine", "transit", "work", "travel", "carpool", "metro")
    _INDOOR_WORDS = ("indoor", "hack", "purif", "filter", "window", "ventilat", "plant", "clean")
    _SUSTAIN_WORDS = ("sustainab", "heat", "burn", "solar", "waste", "community")

    def _build_extra_sections(self, question: str) -> str:
        """Return contextual sections based on keyword matching in the question."""
        q_lower = question.lower()
        sections: list[str] = []
        if any(w in q_lower for w in self._WINTER_WORDS):
            sections.append(self._build_winter_smog_section())
        if any(w in q_lower for w in self._COMMUTE_WORDS):
            sections.append(self._build_commute_section())
        if any(w in q_lower for w in self._INDOOR_WORDS):
            sections.append(self._build_indoor_section())
        if any(w in q_lower for w in self._SUSTAIN_WORDS):
            sections.append(self._build_sustainable_section())
        return ("\n" + "\n\n".join(sections) + "\n") if sections else ""

    def _generate_knowledge_base_fallback(
        self,
        question: str,
        snapshot: "AQIContextSnapshot",
    ) -> str:
        """Synthesize a safe fallback answer using structured knowledge base rules."""
        city = snapshot.city_name
        aqi = snapshot.aqi
        category = snapshot.category or "Moderate"
        dominant = snapshot.dominant_pollutant or "particulate matter"
        guideline = HealthKnowledgeBase.get_category_guideline(category)

        header = self._build_fallback_header(city, aqi, category, dominant, snapshot)

        body = (
            f"**Official CPCB Impact**: {guideline.health_statement}\n\n"
            f"**General Public Recommendation**: {guideline.general_guidance}\n\n"
            f"**For Sensitive & Vulnerable Groups**: {guideline.vulnerable_guidance}\n\n"
            "**Key Protective Steps**:\n"
        )
        for p in guideline.precautions:
            body += f"- {p}\n"

        body += self._build_extra_sections(question)

        footer = (
            "\n*(Notice: The AI generation service is currently operating in offline mode. "
            "This guidance is provided directly from the verified CPCB and WHO "
            "public health knowledge base.)*\n\n" + MEDICAL_DISCLAIMER
        )

        return header + body + footer
