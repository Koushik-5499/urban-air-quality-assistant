"""Rule-based engine producing structured, proportional health recommendations."""

from app.integrations.ai.schemas import AQIContextSnapshot, RecommendationItem
from app.services.health.recommendation_tiers_severe import (
    build_poor_recommendations,
    build_severe_recommendations,
    build_very_poor_recommendations,
)
from app.services.health.recommendation_tiers_standard import (
    build_good_recommendations,
    build_moderate_recommendations,
    build_no_data_recommendations,
    build_satisfactory_recommendations,
)

AQI_GOOD_MAX = 50
AQI_SATISFACTORY_MAX = 100
AQI_MODERATE_MAX = 200
AQI_POOR_MAX = 300
AQI_VERY_POOR_MAX = 400


class RecommendationEngine:
    """Generates structured, category-specific health recommendations based on verified AQI."""

    @classmethod
    def generate_recommendations(
        cls,
        snapshot: AQIContextSnapshot,
    ) -> list[RecommendationItem]:
        """Produce structured recommendations proportional to current environmental conditions."""
        aqi = snapshot.aqi
        dominant = snapshot.dominant_pollutant or "particulates"

        if aqi is None:
            return build_no_data_recommendations()
        if aqi <= AQI_GOOD_MAX:
            return build_good_recommendations()
        if aqi <= AQI_SATISFACTORY_MAX:
            return build_satisfactory_recommendations()
        if aqi <= AQI_MODERATE_MAX:
            return build_moderate_recommendations(dominant)
        if aqi <= AQI_POOR_MAX:
            return build_poor_recommendations()
        if aqi <= AQI_VERY_POOR_MAX:
            return build_very_poor_recommendations()
        return build_severe_recommendations()
