"""Rule-based engine producing structured, proportional health recommendations."""

from typing import List, Optional
from app.integrations.ai.schemas import AQIContextSnapshot, RecommendationItem


class RecommendationEngine:
    """Generates structured, category-specific health recommendations based on verified AQI."""

    @classmethod
    def generate_recommendations(
        cls,
        snapshot: AQIContextSnapshot,
    ) -> List[RecommendationItem]:
        """Produce structured recommendations proportional to current environmental conditions."""
        aqi = snapshot.aqi
        dominant = snapshot.dominant_pollutant or "particulates"
        category = snapshot.category or "Moderate"

        if aqi is None:
            return [
                RecommendationItem(
                    title="Monitor Local Air Quality Updates",
                    description="No live telemetry is currently available. Exercise standard urban environmental precautions and follow local municipal advisories.",
                    target_group="General adults",
                    priority="low",
                    reason="Absence of real-time monitoring data requires baseline precautionary vigilance.",
                    supporting_source="Central Pollution Control Board (CPCB)",
                )
            ]

        recommendations: List[RecommendationItem] = []

        # 1. Good (0-50)
        if aqi <= 50:
            recommendations.append(
                RecommendationItem(
                    title="Unrestricted Outdoor Physical Activity",
                    description="Air quality is ideal. You can freely run, cycle, and engage in high-intensity outdoor cardiovascular workouts.",
                    target_group="General adults",
                    priority="low",
                    reason="Pollutant concentrations are well within safe physiological limits.",
                    supporting_source="WHO Global Air Quality Guidelines (2021)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Natural Indoor Air Ventilation",
                    description="Open windows and doors to let fresh ambient air circulate throughout residential and commercial indoor spaces.",
                    target_group="General adults",
                    priority="low",
                    reason="Outdoor air is cleaner than typical unventilated indoor environments.",
                    supporting_source="CPCB National Air Quality Index (2014)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Normal Outdoor Play for Children",
                    description="Children can engage in full outdoor school sports, playground activities, and games without air quality restrictions.",
                    target_group="Children",
                    priority="low",
                    reason="Minimal airborne particulates protect developing pediatric airways.",
                    supporting_source="WHO Child Health and the Environment",
                )
            )

        # 2. Satisfactory (51-100)
        elif aqi <= 100:
            recommendations.append(
                RecommendationItem(
                    title="Regular Outdoor Activities Safe",
                    description="Outdoor exercise, commuting, and sports can proceed normally for the vast majority of people.",
                    target_group="General adults",
                    priority="low",
                    reason="Concentrations cause negligible physiological burden in healthy adults.",
                    supporting_source="CPCB NAQI (2014)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Monitor Symptoms for Sensitive Individuals",
                    description="Individuals with severe asthma or chronic bronchitis should observe if prolonged intense workouts trigger coughing or throat irritation.",
                    target_group="People with asthma",
                    priority="medium",
                    reason="Minor respiratory irritation may manifest in hyper-reactive airways.",
                    supporting_source="WHO Air Quality Guidelines (2021)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Standard Indoor Ventilation",
                    description="Continue opening windows during daytime hours for fresh air circulation.",
                    target_group="General adults",
                    priority="low",
                    reason="Ambient air quality remains acceptable for ventilation.",
                    supporting_source="CPCB Guidelines",
                )
            )

        # 3. Moderate (101-200)
        elif aqi <= 200:
            recommendations.append(
                RecommendationItem(
                    title="Schedule Outdoor Workouts Outside Peak Traffic",
                    description="Shift running, cycling, or intense sports to early morning or late evening when vehicular emissions are lower.",
                    target_group="General adults",
                    priority="medium",
                    reason=f"Elevated {dominant} levels compound during rush hours, increasing inhaled particulate dose.",
                    supporting_source="CPCB Health Statement",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Take Frequent Breaks for Sensitive Groups",
                    description="Children, elderly individuals, and asthma patients should reduce prolonged heavy outdoor exertion and take regular rest periods.",
                    target_group="People with asthma",
                    priority="high",
                    reason="Breathing discomfort is clinically observed in reactive airways at this concentration.",
                    supporting_source="CPCB NAQI (2014)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Strategic Window Ventilation",
                    description="Keep windows closed during peak morning traffic hours if living adjacent to busy urban roads or transit corridors.",
                    target_group="General adults",
                    priority="medium",
                    reason="Prevents roadway combustion gases and coarse resuspension from entering living spaces.",
                    supporting_source="WHO Air Quality Guidelines (2021)",
                )
            )

        # 4. Poor (201-300)
        elif aqi <= 300:
            recommendations.append(
                RecommendationItem(
                    title="Substitute Outdoor Exercise with Indoor Alternatives",
                    description="Avoid outdoor running, jogging, and intense cardiovascular exercise. Exercise indoors in a well-ventilated space.",
                    target_group="General adults",
                    priority="high",
                    reason="High respiration rates during outdoor exercise drastically increase deep-alveolar deposition of fine particulates.",
                    supporting_source="CPCB NAQI (2014)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Wear N95/FFP2 Respirator During Commute",
                    description="Wear a properly fitted, certified N95 or FFP2 particulate respirator when commuting along busy roads. Cloth and surgical masks do not filter fine particles.",
                    target_group="General adults",
                    priority="high",
                    reason="Certified respirators filter sub-micron particles, substantially reducing inhaled mass.",
                    supporting_source="MoHFW Health Advisory on Air Pollution",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Keep Windows Closed and Use HEPA Air Purifiers",
                    description="Close windows to reduce outdoor pollution ingress. Run indoor mechanical air purifiers with true HEPA filtration in bedrooms.",
                    target_group="Vulnerable groups",
                    priority="high",
                    reason="Indoor particulate concentrations can be lowered by 50-80% using mechanical HEPA filtration in sealed rooms.",
                    supporting_source="WHO Clean Air Guidelines",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Protect Children During School Hours",
                    description="Schools should curtail intense outdoor athletic competitions and prolonged playground sports.",
                    target_group="Children",
                    priority="high",
                    reason="Pediatric lungs breathe more air per kilogram of body weight, increasing vulnerability.",
                    supporting_source="ICMR / WHO Advisory",
                )
            )

        # 5. Very Poor (301-400)
        elif aqi <= 400:
            recommendations.append(
                RecommendationItem(
                    title="Strictly Avoid Outdoor Morning Walks & Sports",
                    description="All segments of the population should cease outdoor running, cycling, and morning walks, particularly during early morning thermal inversion hours.",
                    target_group="General adults",
                    priority="high",
                    reason="Atmospheric inversion traps high concentrations of toxic particulates near ground level.",
                    supporting_source="CPCB Health Statement",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Remain Indoors for Vulnerable Populations",
                    description="Elderly citizens, pregnant individuals, and people with heart or respiratory disease should strictly stay indoors in air-cleaned rooms.",
                    target_group="People with respiratory or cardiovascular conditions",
                    priority="high",
                    reason="High risk of acute cardiovascular stress, elevated blood pressure, and asthma attacks.",
                    supporting_source="MoHFW Advisory",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Operate Continuous Indoor Air Filtration",
                    description="Run HEPA air purifiers continuously on auto or medium settings in bedrooms. Seal gaps under doors and window sills with draft stoppers.",
                    target_group="General adults",
                    priority="high",
                    reason="Maintaining indoor air isolation mitigates continuous 24-hour systemic inflammation.",
                    supporting_source="WHO Clean Air Guidelines",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Keep Rescue Medication Accessible",
                    description="Patients with asthma, COPD, or cardiac conditions must keep prescribed inhalers and medications on hand and seek prompt medical attention if distress occurs.",
                    target_group="People with asthma",
                    priority="high",
                    reason="Acute bronchospasm incidence correlates strongly with Very Poor AQI episodes.",
                    supporting_source="CPCB Guidelines / ICMR",
                )
            )

        # 6. Severe (401-500)
        else:
            recommendations.append(
                RecommendationItem(
                    title="Emergency Precaution: Complete Outdoor Avoidance",
                    description="Avoid all non-essential outdoor movement. Healthy individuals and vulnerable groups must stay indoors in sealed spaces.",
                    target_group="General adults",
                    priority="high",
                    reason="Severe air pollution causes systemic inflammatory responses and acute respiratory illness across the entire population.",
                    supporting_source="CPCB NAQI (2014)",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Suspend All Outdoor School & Sporting Activities",
                    description="Children should not participate in any outdoor physical activities. Schools should transition sports indoors or reschedule.",
                    target_group="Children",
                    priority="high",
                    reason="Pediatric respiratory tracts are at severe risk of acute inflammatory injury.",
                    supporting_source="MoHFW Advisory",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Wet Mopping & Indoor Seal Protocols",
                    description="Keep all windows and doors closed. Use wet-mopping rather than dry-sweeping or vacuuming without HEPA exhaust to prevent indoor dust resuspension.",
                    target_group="General adults",
                    priority="high",
                    reason="Wet cleaning captures settled particles without creating secondary airborne exposure.",
                    supporting_source="WHO Guidelines",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Mandatory N95 Respirator for Unavoidable Transit",
                    description="If outdoor transit is unavoidable, wear a snugly fitted N95/FFP2 respirator. Avoid exertion while walking.",
                    target_group="General adults",
                    priority="high",
                    reason="Direct inhalation of Severe particulate concentrations rapidly deposits millions of micro-particles into bronchial pathways.",
                    supporting_source="MoHFW / CPCB Guidelines",
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Seek Prompt Medical Care for Respiratory Distress",
                    description="Consult a healthcare professional or emergency clinic immediately if experiencing chest tightness, continuous coughing, dizziness, or wheezing.",
                    target_group="Vulnerable groups",
                    priority="high",
                    reason="Immediate medical intervention is required for severe respiratory or cardiac exacerbations.",
                    supporting_source="MoHFW Emergency Advisory",
                )
            )

        return recommendations

