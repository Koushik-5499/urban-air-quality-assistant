"""Rule-based engine producing structured, proportional health recommendations."""

from app.integrations.ai.schemas import AQIContextSnapshot, RecommendationItem


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

        recommendations: list[RecommendationItem] = []

        # 1. Good (0-50)
        if aqi <= 50:
            recommendations.append(
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
                )
            )
            recommendations.append(
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
                )
            )
            recommendations.append(
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
                )
            )

        # 2. Satisfactory (51-100)
        elif aqi <= 100:
            recommendations.append(
                RecommendationItem(
                    title="Regular Outdoor Activities Safe",
                    description=(
                        "Outdoor exercise, commuting, and sports can proceed normally for the "
                        "vast majority of people."
                    ),
                    target_group="General adults",
                    priority="low",
                    reason=(
                        "Concentrations cause negligible physiological burden in healthy adults."
                    ),
                    supporting_source="CPCB NAQI (2014)",
                )
            )
            recommendations.append(
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
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Standard Indoor Ventilation",
                    description=(
                        "Continue opening windows during daytime hours for fresh air circulation."
                    ),
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
                )
            )
            recommendations.append(
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
                )
            )
            recommendations.append(
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
                )
            )

        # 4. Poor (201-300)
        elif aqi <= 300:
            recommendations.append(
                RecommendationItem(
                    title="Substitute Outdoor Exercise with Indoor Alternatives",
                    description=(
                        "Avoid outdoor running, jogging, and intense cardiovascular exercise. "
                        "Exercise indoors in a well-ventilated space."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "High respiration rates during outdoor exercise drastically increase "
                        "deep-alveolar deposition of fine particulates."
                    ),
                    supporting_source="CPCB NAQI (2014)",
                    category_type="general_health",
                    impact_explanation=(
                        "Moving workouts indoors cuts inhaled particulate mass by up to 58%."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Wear N95/FFP2 Respirator During Commute",
                    description=(
                        "Wear a properly fitted, certified N95 or FFP2 particulate respirator "
                        "when commuting along busy roads. Cloth and surgical masks do not "
                        "filter fine particles."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "Certified respirators filter sub-micron particles, substantially "
                        "reducing inhaled mass."
                    ),
                    supporting_source="MoHFW Health Advisory on Air Pollution",
                    category_type="general_health",
                    impact_explanation=(
                        "A sealed N95 respirator reduces inhaled particulate dose by up to 95%."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Keep Windows Closed and Use HEPA Air Purifiers",
                    description=(
                        "Close windows to reduce outdoor pollution ingress. Run indoor "
                        "mechanical air purifiers with true HEPA filtration in bedrooms."
                    ),
                    target_group="Vulnerable groups",
                    priority="high",
                    reason=(
                        "Indoor particulate concentrations can be lowered by 50-80% using "
                        "mechanical HEPA filtration in sealed rooms."
                    ),
                    supporting_source="WHO Clean Air Guidelines",
                    category_type="indoor_hack",
                    impact_explanation=(
                        "Mechanical HEPA filtration reduces bedroom PM2.5 by 50–80% within 1 hour."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Protect Children During School Hours",
                    description=(
                        "Schools should curtail intense outdoor athletic competitions and "
                        "prolonged playground sports."
                    ),
                    target_group="Children",
                    priority="high",
                    reason=(
                        "Pediatric lungs breathe more air per kilogram of body weight, "
                        "increasing vulnerability."
                    ),
                    supporting_source="ICMR / WHO Advisory",
                    category_type="winter_smog",
                    impact_explanation=(
                        "Canceling outdoor morning sports protects developing pediatric "
                        "airways from acute inflammation."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Low-Emission Commute Routine & Inversion Awareness",
                    description=(
                        "Reschedule travel outside peak traffic hours (before 8 AM or after 10 "
                        "AM). Shift to electrified metro transit or carpooling to reduce "
                        "roadway exposure."
                    ),
                    target_group="Commuters & Families",
                    priority="high",
                    reason=(
                        "Inversion layers concentrate morning diesel emissions at surface "
                        "breathing height."
                    ),
                    supporting_source="CPCB Winter Air Action Plan",
                    category_type="low_emission_routine",
                    impact_explanation=(
                        "Cuts personal toxic combustion gas inhalation by ~45% and saves 2.8 "
                        "kg CO2 per round trip."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Indoor Air Quality Hack: Diurnal Ventilation & Wet Dusting",
                    description=(
                        "Keep windows sealed during morning and evening smog peaks; open only "
                        "between 1:00 PM – 3:30 PM. Use damp microfiber mopping instead of dry "
                        "brooming to prevent PM10 resuspension."
                    ),
                    target_group="Households",
                    priority="high",
                    reason=(
                        "Solar convective mixing creates diurnal lows in ambient particulate "
                        "concentrations."
                    ),
                    supporting_source="WHO Indoor Air Quality Guidelines",
                    category_type="indoor_hack",
                    impact_explanation=(
                        "Timed ventilation and wet mopping prevent 75% of particulate "
                        "infiltration into living quarters."
                    ),
                )
            )

        # 5. Very Poor (301-400)
        elif aqi <= 400:
            recommendations.append(
                RecommendationItem(
                    title="Strictly Avoid Outdoor Morning Walks & Sports",
                    description=(
                        "All segments of the population should cease outdoor running, cycling, "
                        "and morning walks, particularly during early morning thermal "
                        "inversion hours."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "Atmospheric inversion traps high concentrations of toxic particulates "
                        "near ground level."
                    ),
                    supporting_source="CPCB Health Statement",
                    category_type="winter_smog",
                    impact_explanation=(
                        "Avoiding dawn walks avoids up to 60% of diurnal peak PM2.5 inhalation."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Remain Indoors for Vulnerable Populations",
                    description=(
                        "Elderly citizens, pregnant individuals, and people with heart or "
                        "respiratory disease should strictly stay indoors in air-cleaned "
                        "rooms."
                    ),
                    target_group="People with respiratory or cardiovascular conditions",
                    priority="high",
                    reason=(
                        "High risk of acute cardiovascular stress, elevated blood pressure, "
                        "and asthma attacks."
                    ),
                    supporting_source="MoHFW Advisory",
                    category_type="general_health",
                    impact_explanation=(
                        "Strict indoor isolation reduces risk of emergency respiratory "
                        "hospital admissions by ~70%."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Operate Continuous Indoor Air Filtration",
                    description=(
                        "Run HEPA air purifiers continuously on auto or medium settings in "
                        "bedrooms. Seal gaps under doors and window sills with draft stoppers."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "Maintaining indoor air isolation mitigates continuous 24-hour "
                        "systemic inflammation."
                    ),
                    supporting_source="WHO Clean Air Guidelines",
                    category_type="indoor_hack",
                    impact_explanation=(
                        "Continuous HEPA filtration maintains bedroom PM2.5 below safe "
                        "thresholds (<35 µg/m³)."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Keep Rescue Medication Accessible",
                    description=(
                        "Patients with asthma, COPD, or cardiac conditions must keep "
                        "prescribed inhalers and medications on hand and seek prompt medical "
                        "attention if distress occurs."
                    ),
                    target_group="People with asthma",
                    priority="high",
                    reason=(
                        "Acute bronchospasm incidence correlates strongly with Very Poor AQI "
                        "episodes."
                    ),
                    supporting_source="CPCB Guidelines / ICMR",
                    category_type="general_health",
                    impact_explanation=(
                        "Readily accessible rescue bronchodilators prevent hypoxia in acute "
                        "flare-ups."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="DIY Corsi-Rosenthal Box Air Cleaner",
                    description=(
                        "Assemble a high-CADR DIY air cleaner using a standard box fan and 4 "
                        "MERV-13 or HEPA filters. Run continuously in bedrooms and common "
                        "living spaces."
                    ),
                    target_group="Households and communities",
                    priority="high",
                    reason=(
                        "Achieves commercial-grade Clean Air Delivery Rate at a fraction of "
                        "appliance costs."
                    ),
                    supporting_source="EPA DIY Air Cleaners Protocol",
                    category_type="indoor_hack",
                    impact_explanation=(
                        "Lowers indoor PM2.5 from 300+ µg/m³ to under 35 µg/m³ in under 45 minutes."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Sustainable Space Heating: Zero Biomass Burning",
                    description=(
                        "Do not burn wood, leaves, or coal for space heating. Utilize "
                        "energy-efficient electric heaters or thermal blankets, and report "
                        "open burning to municipal authorities."
                    ),
                    target_group="Communities",
                    priority="high",
                    reason=(
                        "Biomass burning releases highly toxic polycyclic aromatic "
                        "hydrocarbons directly at breathing level."
                    ),
                    supporting_source="CPCB Clean Air Taskforce",
                    category_type="sustainable_alternative",
                    impact_explanation=(
                        "Eliminates extreme localized particulate spikes that exceed 800 µg/m³."
                    ),
                )
            )

        # 6. Severe (401-500)
        else:
            recommendations.append(
                RecommendationItem(
                    title="Emergency Precaution: Complete Outdoor Avoidance",
                    description=(
                        "Avoid all non-essential outdoor movement. Healthy individuals and "
                        "vulnerable groups must stay indoors in sealed spaces."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "Severe air pollution causes systemic inflammatory responses and acute "
                        "respiratory illness across the entire population."
                    ),
                    supporting_source="CPCB NAQI (2014)",
                    category_type="winter_smog",
                    impact_explanation=(
                        "Zero-exposure shelter protocol prevents toxic alveolar deposition of "
                        "millions of fine combustion particles."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Suspend All Outdoor School & Sporting Activities",
                    description=(
                        "Children should not participate in any outdoor physical activities. "
                        "Schools should transition sports indoors or reschedule."
                    ),
                    target_group="Children",
                    priority="high",
                    reason=(
                        "Pediatric respiratory tracts are at severe risk of acute inflammatory "
                        "injury."
                    ),
                    supporting_source="MoHFW Advisory",
                    category_type="winter_smog",
                    impact_explanation=(
                        "Halts high-exertion ventilation that forces heavy particulate burdens "
                        "into developing airways."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Wet Mopping & Indoor Seal Protocols",
                    description=(
                        "Keep all windows and doors closed. Use wet-mopping rather than "
                        "dry-sweeping or vacuuming without HEPA exhaust to prevent indoor dust "
                        "resuspension."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "Wet cleaning captures settled particles without creating secondary "
                        "airborne exposure."
                    ),
                    supporting_source="WHO Guidelines",
                    category_type="indoor_hack",
                    impact_explanation=(
                        "Wet mopping eliminates 65% of resuspendable dust without aerosolizing "
                        "allergens."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Mandatory N95 Respirator for Unavoidable Transit",
                    description=(
                        "If outdoor transit is unavoidable, wear a snugly fitted N95/FFP2 "
                        "respirator. Avoid exertion while walking."
                    ),
                    target_group="General adults",
                    priority="high",
                    reason=(
                        "Direct inhalation of Severe particulate concentrations rapidly "
                        "deposits millions of micro-particles into bronchial pathways."
                    ),
                    supporting_source="MoHFW / CPCB Guidelines",
                    category_type="general_health",
                    impact_explanation=(
                        "Filters up to 95% of fine and ultrafine particles from reaching lung "
                        "tissue."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Seek Prompt Medical Care for Respiratory Distress",
                    description=(
                        "Consult a healthcare professional or emergency clinic immediately if "
                        "experiencing chest tightness, continuous coughing, dizziness, or "
                        "wheezing."
                    ),
                    target_group="Vulnerable groups",
                    priority="high",
                    reason=(
                        "Immediate medical intervention is required for severe respiratory or "
                        "cardiac exacerbations."
                    ),
                    supporting_source="MoHFW Emergency Advisory",
                    category_type="general_health",
                    impact_explanation=(
                        "Early medical attention reduces risk of irreversible cardiopulmonary "
                        "decompensation."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Low-Emission Emergency Protocol: Shift to Electric & Remote",
                    description=(
                        "Strictly avoid all non-essential combustion vehicle trips. Use "
                        "virtual meetings and electric deliveries to prevent compounding "
                        "localized smog."
                    ),
                    target_group="Commuters & Organizations",
                    priority="high",
                    reason=(
                        "Vehicular emissions during stagnant wind conditions remain trapped in "
                        "urban street canyons."
                    ),
                    supporting_source="NCAP Emergency Advisory",
                    category_type="low_emission_routine",
                    impact_explanation=(
                        "Cutting vehicular road trips cuts immediate urban NO2 and black "
                        "carbon spikes by up to 40%."
                    ),
                )
            )
            recommendations.append(
                RecommendationItem(
                    title="Emergency Sustainable Heating: Strictly No Biomass or Coal",
                    description=(
                        "Under no circumstances burn wood, coal, crop stubble, or municipal "
                        "waste for heating during Severe pollution episodes. Use electric "
                        "radiant heaters or additional blankets."
                    ),
                    target_group="Households & Communities",
                    priority="high",
                    reason=(
                        "Open biomass burning during stagnant-air Severe episodes can increase "
                        "local PM2.5 by over 1,000 µg/m³."
                    ),
                    supporting_source="CPCB / NCAP Stubble Burning Advisory",
                    category_type="sustainable_alternative",
                    impact_explanation=(
                        "Eliminating one household biomass fire prevents ~2.4 kg of black "
                        "carbon and carcinogenic PAH emissions per evening."
                    ),
                )
            )

        return recommendations
