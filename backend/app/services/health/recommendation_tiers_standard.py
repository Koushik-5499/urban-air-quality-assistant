"""Tiered health recommendations for Good, Satisfactory, and Moderate AQI bands."""

from app.integrations.ai.schemas import RecommendationItem


def build_no_data_recommendations() -> list[RecommendationItem]:
    """Build default precautionary recommendations when no AQI telemetry is available."""
    return [
        RecommendationItem(
            title="Monitor Local Air Quality Updates",
            description=(
                "No live telemetry is currently available. Exercise standard urban "
                "environmental precautions and follow local municipal advisories."
            ),
            target_group="General adults",
            priority="low",
            reason=(
                "Absence of real-time monitoring data requires baseline precautionary "
                "vigilance."
            ),
            supporting_source="Central Pollution Control Board (CPCB)",
        )
    ]


def build_good_recommendations() -> list[RecommendationItem]:
    """Build recommendations for CPCB Good AQI (0-50)."""
    return [
        RecommendationItem(
            title="Unrestricted Outdoor Physical Activity",
            description=(
                "Air quality is ideal. You can freely run, cycle, and engage in "
                "high-intensity outdoor cardiovascular workouts."
            ),
            target_group="General adults",
            priority="low",
            reason="Pollutant concentrations are well within safe physiological limits.",
            supporting_source="WHO Global Air Quality Guidelines (2021)",
        ),
        RecommendationItem(
            title="Natural Indoor Air Ventilation",
            description=(
                "Open windows and doors to let fresh ambient air circulate throughout "
                "residential and commercial indoor spaces."
            ),
            target_group="General adults",
            priority="low",
            reason="Outdoor air is cleaner than typical unventilated indoor environments.",
            supporting_source="CPCB National Air Quality Index (2014)",
        ),
        RecommendationItem(
            title="Normal Outdoor Play for Children",
            description=(
                "Children can engage in full outdoor school sports, playground "
                "activities, and games without air quality restrictions."
            ),
            target_group="Children",
            priority="low",
            reason="Minimal airborne particulates protect developing pediatric airways.",
            supporting_source="WHO Child Health and the Environment",
        ),
    ]


def build_satisfactory_recommendations() -> list[RecommendationItem]:
    """Build recommendations for CPCB Satisfactory AQI (51-100)."""
    return [
        RecommendationItem(
            title="Regular Outdoor Activities Safe",
            description=(
                "Outdoor exercise, commuting, and sports can proceed normally for the "
                "vast majority of people."
            ),
            target_group="General adults",
            priority="low",
            reason="Concentrations cause negligible physiological burden in healthy adults.",
            supporting_source="CPCB NAQI (2014)",
        ),
        RecommendationItem(
            title="Monitor Symptoms for Sensitive Individuals",
            description=(
                "Individuals with severe asthma or chronic bronchitis should observe "
                "if prolonged intense workouts trigger coughing or throat irritation."
            ),
            target_group="People with asthma",
            priority="medium",
            reason="Minor respiratory irritation may manifest in hyper-reactive airways.",
            supporting_source="WHO Air Quality Guidelines (2021)",
        ),
        RecommendationItem(
            title="Standard Indoor Ventilation",
            description="Continue opening windows during daytime hours for fresh air circulation.",
            target_group="General adults",
            priority="low",
            reason="Ambient air quality remains acceptable for ventilation.",
            supporting_source="CPCB Guidelines",
        ),
    ]


def build_moderate_recommendations(dominant: str) -> list[RecommendationItem]:
    """Build recommendations for CPCB Moderate AQI (101-200)."""
    return [
        RecommendationItem(
            title="Schedule Outdoor Workouts Outside Peak Traffic",
            description=(
                "Shift running, cycling, or intense sports to early morning or late "
                "evening when vehicular emissions are lower."
            ),
            target_group="General adults",
            priority="medium",
            reason=(
                f"Elevated {dominant} levels compound during rush "
                f"hours, increasing inhaled particulate dose."
            ),
            supporting_source="CPCB Health Statement",
        ),
        RecommendationItem(
            title="Take Frequent Breaks for Sensitive Groups",
            description=(
                "Children, elderly individuals, and asthma patients should reduce "
                "prolonged heavy outdoor exertion and take regular rest periods."
            ),
            target_group="People with asthma",
            priority="high",
            reason=(
                "Breathing discomfort is clinically observed in reactive airways at "
                "this concentration."
            ),
            supporting_source="CPCB NAQI (2014)",
        ),
        RecommendationItem(
            title="Strategic Window Ventilation",
            description=(
                "Keep windows closed during peak morning traffic hours if living "
                "adjacent to busy urban roads or transit corridors."
            ),
            target_group="General adults",
            priority="medium",
            reason=(
                "Prevents roadway combustion gases and coarse resuspension from "
                "entering living spaces."
            ),
            supporting_source="WHO Air Quality Guidelines (2021)",
        ),
    ]
