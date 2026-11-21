"""Schemas for AI completion requests, chat context, recommendations, and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """Single message entry in a multi-turn conversation."""

    role: str = Field(..., pattern="^(user|model|assistant|system)$", description="Role of message sender")
    content: str = Field(..., min_length=1, max_length=1000, description="Message text content")


class AICompletionRequest(BaseModel):
    """Payload sent to an AI provider for completion."""

    prompt: str = Field(..., min_length=1, description="Primary prompt content")
    system_instruction: str | None = Field(None, description="System persona and safety instruction")
    conversation_history: list[ChatMessage] = Field(default_factory=list, description="Prior conversation context")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(default=1024, ge=50, le=4096, description="Maximum tokens to generate")


class AICompletionResponse(BaseModel):
    """Standardized response from an AI provider."""

    content: str = Field(..., description="Generated text response")
    model: str = Field(..., description="Model identifier used")
    finish_reason: str = Field(default="STOP", description="Finish reason")
    usage_tokens: int | None = Field(None, description="Token usage count if reported")


class RecommendationItem(BaseModel):
    """Structured actionable environmental health guidance item."""

    title: str = Field(..., description="Short actionable heading (e.g. 'Minimize Morning Outdoor Running')")
    description: str = Field(..., description="Clear practical recommendation instructions")
    target_group: str = Field(..., description="Target population (e.g. 'Children', 'Asthma Patients', 'General Adults')")
    priority: str = Field(..., pattern="^(high|medium|low)$", description="Priority level: high, medium, low")
    reason: str = Field(..., description="Underlying physiological or environmental justification")
    supporting_source: str = Field(..., description="Authoritative reference (e.g. 'CPCB NAQI / WHO 2021')")
    category_type: str = Field(
        default="general_health",
        description="Pillar: winter_smog, low_emission_routine, indoor_hack, sustainable_alternative, general_health",
    )
    impact_explanation: str | None = Field(
        default=None,
        description="Quantified direct impact of this choice (e.g. 'Reduces PM2.5 inhalation by ~45%, cuts 2.4kg CO2/day')",
    )


class AQIContextSnapshot(BaseModel):
    """Verified environmental air quality context used to ground health guidance."""

    city_name: str = Field(..., description="City name")
    station_id: int | None = Field(None, description="Station ID if available")
    station_name: str | None = Field(None, description="Station name if available")
    aqi: int | None = Field(None, description="Current composite NAQI")
    category: str | None = Field(None, description="CPCB NAQI Category")
    dominant_pollutant: str | None = Field(None, description="Dominant criteria pollutant")
    measurement_timestamp: datetime | None = Field(None, description="Timestamp of measurement in UTC")
    data_age_seconds: int | None = Field(None, description="Age of data in seconds")
    is_stale: bool = Field(default=False, description="Whether data exceeds staleness threshold (5 hours)")
    is_simulated: bool = Field(default=False, description="Whether telemetry is simulated")
    data_source: str = Field(default="CPCB", description="Source provider")
    trend_direction: str | None = Field(None, description="Recent trend direction (improving, worsening, stable, insufficient_data)")


class HealthAskRequest(BaseModel):
    """Request payload for POST /api/v1/health/ask."""

    city: str = Field(..., min_length=1, max_length=100, description="City name to establish air quality context")
    question: str = Field(..., min_length=2, max_length=500, description="User health question")
    lifestyle: str | None = Field(
        None,
        max_length=100,
        description="User lifestyle persona (e.g. 'family_with_children', 'daily_commuter', 'elderly_caregiver', 'outdoor_enthusiast', 'remote_worker', 'community_organizer')",
    )
    family_context: str | None = Field(
        None,
        max_length=200,
        description="Household or community context (e.g. 'school_children_and_infants', 'multigenerational_seniors', 'asthma_vulnerable')",
    )
    conversation_id: str | None = Field(None, max_length=100, description="Optional client conversation tracking ID")
    conversation_history: list[ChatMessage] | None = Field(
        default=None,
        max_length=10,
        description="Bounded conversation history (up to 10 turns)",
    )


class HealthAskResponse(BaseModel):
    """Response payload for POST /api/v1/health/ask."""

    answer: str = Field(..., description="Contextual health guidance answer")
    recommendations: list[RecommendationItem] = Field(default_factory=list, description="Structured actionable advice")
    aqi_context: AQIContextSnapshot = Field(..., description="Verified environmental context snapshot")
    sources: list[str] = Field(default_factory=list, description="Authoritative public health references cited")
    disclaimer: str = Field(..., description="Standard non-medical disclaimer")
    data_freshness: str = Field(..., description="Telemetry status description ('fresh', 'stale', 'no_data')")
    response_type: str = Field(..., description="'ai_generated' or 'knowledge_base_fallback'")
    model: str | None = Field(None, description="Configured model identifier used")
    lifestyle_persona: str | None = Field(None, description="Lifestyle persona used to tailor health guidance")
    direct_impact_metrics: list[str] = Field(default_factory=list, description="Quantified direct impacts of choices")


class HealthRecommendationsResponse(BaseModel):
    """Response payload for GET /api/v1/health/recommendations."""

    city: str = Field(..., description="City name")
    station_id: int | None = Field(None, description="Station ID if filtered")
    aqi_context: AQIContextSnapshot = Field(..., description="Current environmental context")
    recommendations: list[RecommendationItem] = Field(default_factory=list, description="Structured recommendations")
    sources: list[str] = Field(default_factory=list, description="Authoritative references")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


class CategoryGuideline(BaseModel):
    """Guidelines for a specific AQI category."""

    category: str = Field(..., description="CPCB NAQI Category")
    aqi_range: str = Field(..., description="AQI numerical range")
    health_statement: str = Field(..., description="Official CPCB health statement")
    general_guidance: str = Field(..., description="Guidance for general public")
    vulnerable_guidance: str = Field(..., description="Guidance for sensitive populations")
    precautions: list[str] = Field(default_factory=list, description="Practical preventive steps")


class HealthGuidelinesResponse(BaseModel):
    """Response payload for GET /api/v1/health/guidelines."""

    title: str = Field(default="CPCB & WHO Air Quality Health Guidelines", description="Title")
    guidelines: list[CategoryGuideline] = Field(default_factory=list, description="Category-specific guidance")
    target_groups_covered: list[str] = Field(default_factory=list, description="Vulnerable populations covered")
    sources: list[str] = Field(default_factory=list, description="Authoritative sources")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


class PollutantExplanationResponse(BaseModel):
    """Response payload for GET /api/v1/health/pollutants/{pollutant_code}."""

    pollutant_code: str = Field(..., description="Criteria pollutant code (PM2.5, PM10, etc.)")
    full_name: str = Field(..., description="Full descriptive name")
    unit: str = Field(..., description="Standard measurement unit")
    description: str = Field(..., description="What the pollutant is and its physical properties")
    common_sources: list[str] = Field(default_factory=list, description="Primary urban emission sources")
    health_effects: list[str] = Field(default_factory=list, description="Potential health impacts")
    reduction_measures: list[str] = Field(default_factory=list, description="Practical exposure mitigation steps")
    cpcb_standard_24h: str = Field(..., description="CPCB National Ambient Air Quality Standard benchmark")
    sources: list[str] = Field(default_factory=list, description="Authoritative references")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


class HealthStatusResponse(BaseModel):
    """Response payload for GET /api/v1/health/status."""

    ai_enabled: bool = Field(..., description="Whether AI health assistant features are enabled")
    provider: str = Field(..., description="Configured provider ('gemini' or 'mock')")
    model: str = Field(..., description="Model identifier")
    available: bool = Field(..., description="Whether provider is currently configured and operational")
    api_key_configured: bool = Field(..., description="Whether a valid API key is present in environment")

    model_config = ConfigDict(from_attributes=True)


class CommunitySolutionsResponse(BaseModel):
    """Response payload for Challenge 6 community solutions and winter smog guidance."""

    title: str = Field(
        default="Winter Smog Navigation, Low-Emission Routines & Indoor Air Quality Hacks",
        description="Section title",
    )
    challenge_vertical: str = Field(
        default="Urban Air Quality Monitoring & Health Advisory for Indian Cities",
        description="Hackathon challenge vertical",
    )
    winter_smog_guidance: list[RecommendationItem] = Field(
        default_factory=list,
        description="Protocols for families navigating severe winter smog and nocturnal inversion layers",
    )
    low_emission_routines: list[RecommendationItem] = Field(
        default_factory=list,
        description="Daily low-emission scheduling, commute timing, and active transit options",
    )
    indoor_air_hacks: list[RecommendationItem] = Field(
        default_factory=list,
        description="Low-cost indoor hacks: diurnal ventilation timing, DIY HEPA filtration, wet cleaning",
    )
    sustainable_alternatives: list[RecommendationItem] = Field(
        default_factory=list,
        description="Clean energy and lifestyle alternatives tailored to location and urban lifestyle",
    )
    direct_impact_analysis: list[str] = Field(
        default_factory=list,
        description="Direct quantified explanations of how individual and community choices cut pollution and exposure",
    )
    sources: list[str] = Field(default_factory=list, description="Authoritative environmental and clinical references")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


