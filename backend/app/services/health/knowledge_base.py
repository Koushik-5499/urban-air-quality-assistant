"""Authoritative health guidance knowledge base grounded in CPCB and WHO guidelines."""

from typing import Dict, List, Optional
from app.integrations.ai.schemas import CategoryGuideline, PollutantExplanationResponse

MEDICAL_DISCLAIMER = (
    "Disclaimer: This guidance is provided for educational and environmental awareness purposes only. "
    "It does not constitute professional medical advice, clinical diagnosis, or individual treatment recommendations. "
    "Air purifiers and particulate masks reduce exposure but do not guarantee complete protection. "
    "Individuals experiencing breathing difficulties, chest tightness, or worsening respiratory or cardiovascular symptoms "
    "should consult a qualified healthcare provider immediately."
)

AUTHORITATIVE_SOURCES = [
    "Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change, Govt of India - National Air Quality Index (2014)",
    "World Health Organization (WHO) Global Air Quality Guidelines: Particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide (2021)",
    "Ministry of Health and Family Welfare (MoHFW), Govt of India - Health Advisory on Air Pollution",
    "Indian Council of Medical Research (ICMR) - Air Pollution and Non-Communicable Diseases Study",
]

TARGET_GROUPS = [
    "General adults",
    "Children",
    "Older adults",
    "Pregnant people",
    "People with asthma",
    "People with chronic respiratory or cardiovascular conditions",
]


class HealthKnowledgeBase:
    """Provides structured, scientifically validated public health guidance."""

    CATEGORY_GUIDELINES: Dict[str, CategoryGuideline] = {
        "Good": CategoryGuideline(
            category="Good",
            aqi_range="0–50",
            health_statement="Minimal health impact.",
            general_guidance="Air quality is ideal for all normal outdoor activities, exercise, and ventilation.",
            vulnerable_guidance="Safe for children, elderly individuals, and individuals with existing medical conditions.",
            precautions=[
                "Enjoy unrestricted outdoor exercise and recreational sports.",
                "Ventilate indoor spaces with fresh outdoor air.",
                "No masks or air filtration required.",
            ],
        ),
        "Satisfactory": CategoryGuideline(
            category="Satisfactory",
            aqi_range="51–100",
            health_statement="Minor breathing discomfort to sensitive people.",
            general_guidance="Air quality is acceptable for the general public. Outdoor activities are safe.",
            vulnerable_guidance="Unusually sensitive individuals with asthma may notice mild respiratory irritation during prolonged heavy exertion.",
            precautions=[
                "General public can engage in regular outdoor work and recreation.",
                "Sensitive individuals should monitor for mild symptoms such as throat irritation or coughing.",
                "Keep quick-relief inhalers accessible if you have asthma.",
            ],
        ),
        "Moderate": CategoryGuideline(
            category="Moderate",
            aqi_range="101–200",
            health_statement="Breathing discomfort to people with lungs, asthma and heart diseases.",
            general_guidance="Most healthy people can engage in outdoor activities, but may experience slight fatigue during prolonged intense exertion.",
            vulnerable_guidance="Children, seniors, and individuals with asthma or heart conditions should take frequent breaks during outdoor activities.",
            precautions=[
                "Shift intense outdoor workouts away from peak traffic hours (morning and evening rushes).",
                "Keep windows closed during high-traffic hours if living near major roads.",
                "Sensitive groups should reduce prolonged outdoor cardiovascular exertion.",
                "Stay well-hydrated to support mucosal clearance.",
            ],
        ),
        "Poor": CategoryGuideline(
            category="Poor",
            aqi_range="201–300",
            health_statement="Breathing discomfort to most people on prolonged exposure.",
            general_guidance="Healthy individuals will likely experience throat irritation, dry cough, or eye burning during extended outdoor exertion.",
            vulnerable_guidance="Children, older adults, and individuals with respiratory/cardiovascular disease should avoid strenuous outdoor exertion.",
            precautions=[
                "Avoid prolonged outdoor cardiovascular exercise; exercise indoors in a clean-air environment.",
                "Wear a well-fitted, certified particulate respirator (N95 or FFP2) when commuting outdoors.",
                "Close windows and use indoor air purifiers with true HEPA filtration if available.",
                "Avoid indoor pollution sources like incense sticks, smoking, or unvented biomass cooking.",
            ],
        ),
        "Very Poor": CategoryGuideline(
            category="Very Poor",
            aqi_range="301–400",
            health_statement="Respiratory illness on prolonged exposure.",
            general_guidance="Healthy adults will experience significant irritation. Prolonged exposure poses serious health risks.",
            vulnerable_guidance="High risk of asthma exacerbation and cardiovascular stress. Vulnerable individuals should remain indoors.",
            precautions=[
                "Strictly avoid outdoor sports, morning walks, and outdoor jogging.",
                "Schools should suspend outdoor morning assemblies and physical education classes.",
                "Wear N95/FFP2 respirators when stepping outdoors; surgical or cloth masks do not filter fine particulates.",
                "Run indoor HEPA purifiers continuously in bedrooms and living areas.",
                "Keep prescribed respiratory medications (e.g., bronchodilators) on hand.",
            ],
        ),
        "Severe": CategoryGuideline(
            category="Severe",
            aqi_range="401–500",
            health_statement="Affects healthy people and seriously impacts those with existing diseases.",
            general_guidance="Emergency air quality condition. Severe health risks for all segments of the population.",
            vulnerable_guidance="Extreme hazard for children, pregnant people, older adults, and those with heart/lung disease. Risk of acute hospital visits.",
            precautions=[
                "Stay indoors and minimize physical exertion.",
                "Seal doors and windows; use wet mopping rather than dry sweeping to minimize indoor dust.",
                "Operate high-efficiency HEPA air purifiers in sealed rooms.",
                "Non-essential outdoor travel should be avoided.",
                "Seek urgent medical evaluation if experiencing shortness of breath, wheezing, or chest pain.",
            ],
        ),
    }

    POLLUTANT_DETAILS: Dict[str, PollutantExplanationResponse] = {
        "PM2.5": PollutantExplanationResponse(
            pollutant_code="PM2.5",
            full_name="Fine Particulate Matter (Diameter ≤ 2.5 µm)",
            unit="µg/m³",
            description="Microscopic airborne solid particles and liquid droplets 30 times finer than a strand of human hair. Because of their tiny size, they bypass upper airway defenses and penetrate deep into pulmonary alveoli and the bloodstream.",
            common_sources=[
                "Vehicular exhaust (particularly diesel engines)",
                "Biomass, crop residue, and solid waste burning",
                "Coal-fired thermal power plants and industrial combustion",
                "Construction dust and atmospheric chemical reactions (secondary aerosols)",
            ],
            health_effects=[
                "Deep lung penetration causing pulmonary inflammation and oxidative stress",
                "Aggravation of asthma, chronic obstructive pulmonary disease (COPD), and bronchitis",
                "Translocation into bloodstream increasing risks of hypertension, heart attack, and stroke",
                "Adverse birth outcomes and impaired pediatric lung development with chronic exposure",
            ],
            reduction_measures=[
                "Wear certified N95, KN95, or FFP2 respirators outdoors in high concentrations.",
                "Utilize mechanical HEPA air purifiers indoors to filter sub-micron particles.",
                "Keep windows closed during early morning and late evening thermal inversion hours.",
                "Avoid adding indoor particulates via incense, mosquito coils, or tobacco smoke.",
            ],
            cpcb_standard_24h="60 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
            sources=[
                "CPCB National Ambient Air Quality Standards (NAAQS)",
                "WHO Air Quality Guidelines (2021) - PM2.5 Guidance",
            ],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "PM10": PollutantExplanationResponse(
            pollutant_code="PM10",
            full_name="Respirable Coarse Particulate Matter (Diameter ≤ 10 µm)",
            unit="µg/m³",
            description="Inhalable particles capable of penetrating the upper respiratory tract, including the nasal passages and bronchi.",
            common_sources=[
                "Road dust resuspension from vehicular traffic",
                "Construction, demolition, and building excavation",
                "Agricultural tilling and dust storms",
                "Industrial handling of bulk powders and minerals",
            ],
            health_effects=[
                "Upper respiratory tract irritation (coughing, throat scratchiness, sneezing)",
                "Eye irritation and conjunctival inflammation",
                "Bronchial spasms in individuals with asthma or reactive airway disease",
            ],
            reduction_measures=[
                "Avoid walking near dusty roads and active construction sites.",
                "Use wet mopping indoors to remove coarse dust without re-suspending it.",
                "Wear protective eyewear and masks in dusty ambient conditions.",
            ],
            cpcb_standard_24h="100 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
            sources=[
                "CPCB National Ambient Air Quality Standards",
                "WHO Air Quality Guidelines (2021)",
            ],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "NO2": PollutantExplanationResponse(
            pollutant_code="NO2",
            full_name="Nitrogen Dioxide",
            unit="µg/m³",
            description="A reddish-brown, highly reactive gas belonging to the group of nitrogen oxides (NOx), formed primarily during high-temperature fuel combustion.",
            common_sources=[
                "Motor vehicle internal combustion engines (especially diesel)",
                "Fossil-fuel power stations and industrial boilers",
                "Unvented indoor gas stoves, kerosene heaters, and generators",
            ],
            health_effects=[
                "Inflammation of airways lining, predisposing to respiratory infections",
                "Triggering of bronchoconstriction in patients with asthma",
                "Key precursor in the photochemical generation of harmful ground-level Ozone",
            ],
            reduction_measures=[
                "Avoid walking or exercising in immediate proximity to heavy-traffic arterials.",
                "Ensure robust kitchen exhaust ventilation when using domestic gas cooking stoves.",
                "Keep automobile windows closed with recirculation enabled during heavy traffic jams.",
            ],
            cpcb_standard_24h="80 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
            sources=["CPCB NAAQS", "WHO Nitrogen Dioxide Review"],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "SO2": PollutantExplanationResponse(
            pollutant_code="SO2",
            full_name="Sulfur Dioxide",
            unit="µg/m³",
            description="A pungent, colorless gas released during the burning of sulfur-containing fossil fuels and smelting of mineral ores.",
            common_sources=[
                "Coal and oil burning at thermal power plants",
                "Industrial refining and chemical manufacturing",
                "Heavy-duty marine shipping and unrefined heavy oil combustion",
            ],
            health_effects=[
                "Severe irritation of the eyes, mucous membranes, and respiratory tract",
                "Rapid reflex bronchoconstriction within minutes of inhalation for people with asthma",
                "Precursor to secondary sulfate aerosols and acid precipitation",
            ],
            reduction_measures=[
                "Individuals with asthma should remain indoors when local SO2 levels spike near industrial zones.",
                "Keep prescribed asthma rescue medication readily available.",
            ],
            cpcb_standard_24h="80 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
            sources=["CPCB NAAQS", "WHO Guidelines for Sulfur Dioxide"],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "CO": PollutantExplanationResponse(
            pollutant_code="CO",
            full_name="Carbon Monoxide",
            unit="mg/m³",
            description="A colorless, odorless, tasteless, and highly toxic gas produced by the incomplete combustion of carbon-based fuels.",
            common_sources=[
                "Incomplete combustion in motor vehicle engines, especially in slow, congested traffic",
                "Faulty indoor gas water heaters, wood-burning stoves, and generators",
                "Biomass burning and tobacco smoke",
            ],
            health_effects=[
                "Binds to hemoglobin with 200x greater affinity than oxygen, forming carboxyhemoglobin",
                "Impairs oxygen delivery to critical organs, particularly the brain and heart",
                "Causes headaches, dizziness, fatigue, and chest pain in individuals with ischemic heart disease",
            ],
            reduction_measures=[
                "Never run generators, charcoal grills, or vehicle engines inside closed spaces or garages.",
                "Ensure regular servicing and chimney venting of gas heating appliances.",
                "Install certified Carbon Monoxide alarms in homes utilizing fuel-burning equipment.",
            ],
            cpcb_standard_24h="2.0 mg/m³ (8-hour standard: 2.0 mg/m³, 1-hour: 4.0 mg/m³)",
            sources=["CPCB NAAQS", "WHO Environmental Health Criteria for CO"],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "O3": PollutantExplanationResponse(
            pollutant_code="O3",
            full_name="Ground-Level Ozone",
            unit="µg/m³",
            description="A secondary photochemical pollutant formed when precursor gases (NOx and Volatile Organic Compounds) react in ambient air under intense solar radiation.",
            common_sources=[
                "Secondary atmospheric formation: not emitted directly from tailpipes or chimneys",
                "Precursor emissions from vehicles, solvent evaporation, and industrial chemicals under sunlight",
            ],
            health_effects=[
                "Potent oxidant causing direct cellular damage to alveolar and bronchiolar epithelium",
                "Reduces lung capacity, causing chest pain, throat irritation, and persistent coughing",
                "Particularly hazardous to outdoor workers, athletes, and children playing outside in afternoons",
            ],
            reduction_measures=[
                "Schedule outdoor cardiovascular sports for early morning when solar photochemical reaction rates are lowest.",
                "Avoid outdoor recreation during mid-afternoon hours (1:00 PM to 5:00 PM) on sunny summer days.",
            ],
            cpcb_standard_24h="100 µg/m³ (8-hour standard: 100 µg/m³)",
            sources=["CPCB NAAQS", "WHO Ozone Health Impact Assessment"],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "NH3": PollutantExplanationResponse(
            pollutant_code="NH3",
            full_name="Ammonia",
            unit="µg/m³",
            description="A pungent alkaline gas that reacts rapidly in the atmosphere with acidic gases (SO2 and NOx) to form secondary ammonium aerosols.",
            common_sources=[
                "Agricultural livestock waste and synthetic fertilizer decomposition",
                "Untreated municipal sewage and open drainage systems",
                "Refrigeration systems and industrial fertilizer synthesis",
            ],
            health_effects=[
                "Eye, nose, and upper respiratory tract irritation",
                "Forms secondary ammonium fine particulate matter (PM2.5) that penetrates deeply into the lungs",
            ],
            reduction_measures=[
                "Avoid prolonged exposure near open, untreated municipal drains or agricultural slurry pits.",
            ],
            cpcb_standard_24h="400 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
            sources=["CPCB NAAQS", "WHO Guidelines for Air Quality"],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
        "Pb": PollutantExplanationResponse(
            pollutant_code="Pb",
            full_name="Lead",
            unit="µg/m³",
            description="A heavy metal toxicant present in airborne dust, historically from leaded fuels and currently from industrial smelting and battery recycling.",
            common_sources=[
                "Lead-acid battery recycling and manufacturing facilities",
                "Non-ferrous metal smelting and foundry operations",
                "Resuspension of contaminated industrial soil and legacy lead paint",
            ],
            health_effects=[
                "Systemic neurotoxicant with no known safe blood concentration in children",
                "Impairs pediatric neurodevelopment, cognitive IQ, and behavioral executive function",
                "Accumulates in bones and organs, contributing to kidney dysfunction and cardiovascular disease",
            ],
            reduction_measures=[
                "Maintain strict wet-cleaning protocols in areas near battery recycling or smelting sites.",
                "Ensure children wash hands thoroughly before meals after playing outdoors.",
            ],
            cpcb_standard_24h="1.0 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
            sources=["CPCB NAAQS", "WHO Guidelines on Lead Exposure and Health"],
            disclaimer=MEDICAL_DISCLAIMER,
        ),
    }

    @classmethod
    def get_category_guideline(cls, category: Optional[str]) -> CategoryGuideline:
        """Retrieve authoritative guideline for a given NAQI category."""
        cat_key = category or "Moderate"
        # Normalize category
        if "good" in cat_key.lower():
            return cls.CATEGORY_GUIDELINES["Good"]
        elif "satis" in cat_key.lower():
            return cls.CATEGORY_GUIDELINES["Satisfactory"]
        elif "mod" in cat_key.lower():
            return cls.CATEGORY_GUIDELINES["Moderate"]
        elif "very" in cat_key.lower():
            return cls.CATEGORY_GUIDELINES["Very Poor"]
        elif "poor" in cat_key.lower():
            return cls.CATEGORY_GUIDELINES["Poor"]
        elif "sev" in cat_key.lower():
            return cls.CATEGORY_GUIDELINES["Severe"]
        return cls.CATEGORY_GUIDELINES["Moderate"]

    @classmethod
    def get_pollutant_explanation(cls, code: str) -> Optional[PollutantExplanationResponse]:
        """Retrieve deep-dive explanation for criteria pollutant."""
        norm_code = code.strip().upper()
        if norm_code == "PB":
            return cls.POLLUTANT_DETAILS.get("Pb")
        return cls.POLLUTANT_DETAILS.get(norm_code)

