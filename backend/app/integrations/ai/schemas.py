"""Schemas for AI completion requests, chat context, recommendations, and responses."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """Single message entry in a multi-turn conversation."""

    role: str = Field(..., pattern="^(user|model|assistant|system)$", description="Role of message sender")
    content: str = Field(..., min_length=1, max_length=1000, description="Message text content")


class AICompletionRequest(BaseModel):
    """Payload sent to an AI provider for completion."""

    prompt: str = Field(..., min_length=1, description="Primary prompt content")
    system_instruction: Optional[str] = Field(None, description="System persona and safety instruction")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Prior conversation context")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(default=1024, ge=50, le=4096, description="Maximum tokens to generate")


class AICompletionResponse(BaseModel):
    """Standardized response from an AI provider."""

    content: str = Field(..., description="Generated text response")
    model: str = Field(..., description="Model identifier used")
    finish_reason: str = Field(default="STOP", description="Finish reason")
    usage_tokens: Optional[int] = Field(None, description="Token usage count if reported")


class RecommendationItem(BaseModel):
    """Structured actionable environmental health guidance item."""

    title: str = Field(..., description="Short actionable heading (e.g. 'Minimize Morning Outdoor Running')")
    description: str = Field(..., description="Clear practical recommendation instructions")
    target_group: str = Field(..., description="Target population (e.g. 'Children', 'Asthma Patients', 'General Adults')")
    priority: str = Field(..., pattern="^(high|medium|low)$", description="Priority level: high, medium, low")
    reason: str = Field(..., description="Underlying physiological or environmental justification")
    supporting_source: str = Field(..., description="Authoritative reference (e.g. 'CPCB NAQI / WHO 2021')")


class AQIContextSnapshot(BaseModel):
    """Verified environmental air quality context used to ground health guidance."""

    city_name: str = Field(..., description="City name")
    station_id: Optional[int] = Field(None, description="Station ID if available")
    station_name: Optional[str] = Field(None, description="Station name if available")
    aqi: Optional[int] = Field(None, description="Current composite NAQI")
    category: Optional[str] = Field(None, description="CPCB NAQI Category")
    dominant_pollutant: Optional[str] = Field(None, description="Dominant criteria pollutant")
    measurement_timestamp: Optional[datetime] = Field(None, description="Timestamp of measurement in UTC")
    data_age_seconds: Optional[int] = Field(None, description="Age of data in seconds")
    is_stale: bool = Field(default=False, description="Whether data exceeds staleness threshold (5 hours)")
    is_simulated: bool = Field(default=False, description="Whether telemetry is simulated")
    data_source: str = Field(default="CPCB", description="Source provider")
    trend_direction: Optional[str] = Field(None, description="Recent trend direction (improving, worsening, stable, insufficient_data)")


class HealthAskRequest(BaseModel):
    """Request payload for POST /api/v1/health/ask."""

    city: str = Field(..., min_length=1, max_length=100, description="City name to establish air quality context")
    question: str = Field(..., min_length=2, max_length=500, description="User health question")
    conversation_id: Optional[str] = Field(None, max_length=100, description="Optional client conversation tracking ID")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        max_length=10,
        description="Bounded conversation history (up to 10 turns)",
    )


class HealthAskResponse(BaseModel):
    """Response payload for POST /api/v1/health/ask."""

    answer: str = Field(..., description="Contextual health guidance answer")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Structured actionable advice")
    aqi_context: AQIContextSnapshot = Field(..., description="Verified environmental context snapshot")
    sources: List[str] = Field(default_factory=list, description="Authoritative public health references cited")
    disclaimer: str = Field(..., description="Standard non-medical disclaimer")
    data_freshness: str = Field(..., description="Telemetry status description ('fresh', 'stale', 'no_data')")
    response_type: str = Field(..., description="'ai_generated' or 'knowledge_base_fallback'")
    model: Optional[str] = Field(None, description="Configured model identifier used")


class HealthRecommendationsResponse(BaseModel):
    """Response payload for GET /api/v1/health/recommendations."""

    city: str = Field(..., description="City name")
    station_id: Optional[int] = Field(None, description="Station ID if filtered")
    aqi_context: AQIContextSnapshot = Field(..., description="Current environmental context")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Structured recommendations")
    sources: List[str] = Field(default_factory=list, description="Authoritative references")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


class CategoryGuideline(BaseModel):
    """Guidelines for a specific AQI category."""

    category: str = Field(..., description="CPCB NAQI Category")
    aqi_range: str = Field(..., description="AQI numerical range")
    health_statement: str = Field(..., description="Official CPCB health statement")
    general_guidance: str = Field(..., description="Guidance for general public")
    vulnerable_guidance: str = Field(..., description="Guidance for sensitive populations")
    precautions: List[str] = Field(default_factory=list, description="Practical preventive steps")


class HealthGuidelinesResponse(BaseModel):
    """Response payload for GET /api/v1/health/guidelines."""

    title: str = Field(default="CPCB & WHO Air Quality Health Guidelines", description="Title")
    guidelines: List[CategoryGuideline] = Field(default_factory=list, description="Category-specific guidance")
    target_groups_covered: List[str] = Field(default_factory=list, description="Vulnerable populations covered")
    sources: List[str] = Field(default_factory=list, description="Authoritative sources")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


class PollutantExplanationResponse(BaseModel):
    """Response payload for GET /api/v1/health/pollutants/{pollutant_code}."""

    pollutant_code: str = Field(..., description="Criteria pollutant code (PM2.5, PM10, etc.)")
    full_name: str = Field(..., description="Full descriptive name")
    unit: str = Field(..., description="Standard measurement unit")
    description: str = Field(..., description="What the pollutant is and its physical properties")
    common_sources: List[str] = Field(default_factory=list, description="Primary urban emission sources")
    health_effects: List[str] = Field(default_factory=list, description="Potential health impacts")
    reduction_measures: List[str] = Field(default_factory=list, description="Practical exposure mitigation steps")
    cpcb_standard_24h: str = Field(..., description="CPCB National Ambient Air Quality Standard benchmark")
    sources: List[str] = Field(default_factory=list, description="Authoritative references")
    disclaimer: str = Field(..., description="Standard medical disclaimer")


class HealthStatusResponse(BaseModel):
    """Response payload for GET /api/v1/health/status."""

    ai_enabled: bool = Field(..., description="Whether AI health assistant features are enabled")
    provider: str = Field(..., description="Configured provider ('gemini' or 'mock')")
    model: str = Field(..., description="Model identifier")
    available: bool = Field(..., description="Whether provider is currently configured and operational")
    api_key_configured: bool = Field(..., description="Whether a valid API key is present in environment")

    model_config = ConfigDict(from_attributes=True)

