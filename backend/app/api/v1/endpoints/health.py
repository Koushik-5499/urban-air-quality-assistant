"""API v1 Health endpoints covering service health and the AI Health Advisor."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.init_db import check_database_health
from app.db.session import get_db
from app.integrations.ai.schemas import (
    HealthAskRequest,
    HealthAskResponse,
    HealthGuidelinesResponse,
    HealthRecommendationsResponse,
    HealthStatusResponse,
    PollutantExplanationResponse,
)
from app.schemas.health import HealthResponse
from app.services.health.health_advisor import HealthAdvisorService

router = APIRouter()


def get_health_advisor(
    settings: Settings = Depends(get_settings),
) -> HealthAdvisorService:
    """Dependency provider for HealthAdvisorService."""
    return HealthAdvisorService(settings=settings)


@router.get(
    "",
    response_model=HealthResponse,
    summary="API v1 Health Check",
    description="Check the operational status of the v1 API service and database connectivity.",
)
async def get_v1_health(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Return service health status, version, and database connectivity."""
    db_health = check_database_health()
    overall_status = "healthy" if db_health["healthy"] else "degraded"
    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        service=settings.APP_NAME,
        timestamp=datetime.now(UTC),
        environment=settings.APP_ENV,
        database=db_health["status"],
    )


@router.post(
    "/ask",
    response_model=HealthAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AI Health Assistant",
    description="Ask a health inquiry grounded in live, verified city air quality observations.",
)
async def ask_health_assistant(
    request: HealthAskRequest,
    db: Session = Depends(get_db),
    advisor: HealthAdvisorService = Depends(get_health_advisor),
) -> HealthAskResponse:
    """Answer user questions with verified AQI context and evidence-based guidance."""
    return await advisor.ask(db=db, request=request)


@router.get(
    "/recommendations",
    response_model=HealthRecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Health Recommendations",
    description="Retrieve structured, actionable health recommendations for a specific city.",
)
def get_health_recommendations(
    city: str = Query(..., description="City name to fetch current recommendations for"),
    station_id: int | None = Query(None, description="Optional monitoring station ID"),
    db: Session = Depends(get_db),
    advisor: HealthAdvisorService = Depends(get_health_advisor),
) -> HealthRecommendationsResponse:
    """Return categorized health recommendations based on current AQI conditions."""
    return advisor.get_recommendations(db=db, city=city, station_id=station_id)


@router.get(
    "/guidelines",
    response_model=HealthGuidelinesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Health Guidelines",
    description="Retrieve authoritative CPCB and WHO health guidance across all NAQI categories and vulnerable groups.",
)
def get_health_guidelines(
    advisor: HealthAdvisorService = Depends(get_health_advisor),
) -> HealthGuidelinesResponse:
    """Return general and vulnerable-group guidance for all 6 NAQI categories."""
    return advisor.get_guidelines()


@router.get(
    "/pollutants/{pollutant_code}",
    response_model=PollutantExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Pollutant Health Explanation",
    description="Retrieve detailed sources, health impacts, and mitigation measures for a criteria pollutant.",
)
def get_pollutant_explanation(
    pollutant_code: str,
    advisor: HealthAdvisorService = Depends(get_health_advisor),
) -> PollutantExplanationResponse:
    """Return educational breakdown of specific air pollutant."""
    return advisor.get_pollutant_explanation(pollutant_code=pollutant_code)


@router.get(
    "/status",
    response_model=HealthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Health Advisor Status",
    description="Check whether the AI provider is configured and available without exposing sensitive secrets.",
)
def get_ai_status(
    advisor: HealthAdvisorService = Depends(get_health_advisor),
) -> HealthStatusResponse:
    """Return AI model identifier, provider status, and availability."""
    return advisor.get_status()
