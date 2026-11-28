"""Authoritative health guidance knowledge base grounded in CPCB and WHO guidelines."""

from app.integrations.ai.schemas import (
    CategoryGuideline,
    CommunitySolutionsResponse,
    ImpactMetricsResponse,
    PollutantExplanationResponse,
)
from app.services.health.knowledge_data_community import (
    DIRECT_IMPACT_METRICS,
    INDOOR_AIR_HACKS,
    LOW_EMISSION_ROUTINES,
    SUSTAINABLE_ALTERNATIVES,
    WINTER_SMOG_GUIDANCE,
    build_impact_metrics,
)
from app.services.health.knowledge_data_guidelines import (
    AUTHORITATIVE_SOURCES,
    CATEGORY_GUIDELINES,
    MEDICAL_DISCLAIMER,
    TARGET_GROUPS,
)
from app.services.health.knowledge_data_pollutants import POLLUTANT_DETAILS

_CATEGORY_ALIASES = (
    ("good", "Good"),
    ("satis", "Satisfactory"),
    ("mod", "Moderate"),
    ("very", "Very Poor"),
    ("poor", "Poor"),
    ("sev", "Severe"),
)


class HealthKnowledgeBase:
    """Provides structured, scientifically validated public health guidance."""

    CATEGORY_GUIDELINES = CATEGORY_GUIDELINES
    POLLUTANT_DETAILS = POLLUTANT_DETAILS
    WINTER_SMOG_GUIDANCE = WINTER_SMOG_GUIDANCE
    LOW_EMISSION_ROUTINES = LOW_EMISSION_ROUTINES
    INDOOR_AIR_HACKS = INDOOR_AIR_HACKS
    SUSTAINABLE_ALTERNATIVES = SUSTAINABLE_ALTERNATIVES
    DIRECT_IMPACT_METRICS = DIRECT_IMPACT_METRICS

    @classmethod
    def get_category_guideline(cls, category: str | None) -> CategoryGuideline:
        """Retrieve authoritative guideline for a given NAQI category."""
        cat_key = (category or "Moderate").lower()
        for token, canonical in _CATEGORY_ALIASES:
            if token in cat_key:
                return cls.CATEGORY_GUIDELINES[canonical]
        return cls.CATEGORY_GUIDELINES["Moderate"]

    @classmethod
    def get_pollutant_explanation(cls, code: str) -> PollutantExplanationResponse | None:
        """Retrieve deep-dive explanation for criteria pollutant."""
        norm_code = code.strip().upper()
        if norm_code == "PB":
            return cls.POLLUTANT_DETAILS.get("Pb")
        return cls.POLLUTANT_DETAILS.get(norm_code)

    @classmethod
    def get_community_solutions(cls) -> CommunitySolutionsResponse:
        """Retrieve complete Challenge 6 community guidance and sustainable alternatives."""
        return CommunitySolutionsResponse(
            title="Winter Smog Navigation, Low-Emission Routines & Indoor Air Quality Hacks",
            challenge_vertical="Urban Air Quality Monitoring & Health Advisory for Indian Cities",
            winter_smog_guidance=cls.WINTER_SMOG_GUIDANCE,
            low_emission_routines=cls.LOW_EMISSION_ROUTINES,
            indoor_air_hacks=cls.INDOOR_AIR_HACKS,
            sustainable_alternatives=cls.SUSTAINABLE_ALTERNATIVES,
            direct_impact_analysis=cls.DIRECT_IMPACT_METRICS,
            sources=AUTHORITATIVE_SOURCES,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    @classmethod
    def get_impact_metrics(cls) -> ImpactMetricsResponse:
        """Return typed quantified impact metrics for all five Challenge 6 pillars."""
        return build_impact_metrics()


__all__ = [
    "AUTHORITATIVE_SOURCES",
    "HealthKnowledgeBase",
    "MEDICAL_DISCLAIMER",
    "TARGET_GROUPS",
]
