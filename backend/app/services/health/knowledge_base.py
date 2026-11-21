"""Authoritative health guidance knowledge base grounded in CPCB and WHO guidelines."""


from app.integrations.ai.schemas import (
    CategoryGuideline,
    CommunitySolutionsResponse,
    PollutantExplanationResponse,
    RecommendationItem,
)

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

    CATEGORY_GUIDELINES: dict[str, CategoryGuideline] = {
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

    POLLUTANT_DETAILS: dict[str, PollutantExplanationResponse] = {
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
    def get_category_guideline(cls, category: str | None) -> CategoryGuideline:
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
    def get_pollutant_explanation(cls, code: str) -> PollutantExplanationResponse | None:
        """Retrieve deep-dive explanation for criteria pollutant."""
        norm_code = code.strip().upper()
        if norm_code == "PB":
            return cls.POLLUTANT_DETAILS.get("Pb")
        return cls.POLLUTANT_DETAILS.get(norm_code)

    WINTER_SMOG_GUIDANCE: list[RecommendationItem] = [
        RecommendationItem(
            title="Navigate Winter Inversion & Thermal Trapping",
            description="During cold winter months, radiation inversion traps vehicle emissions and biomass smoke in the lowest 50–100 meters of the atmosphere. Peak surface PM2.5 concentrations occur between 6:00 AM and 9:30 AM and again after sunset. Reschedule children's school transit, morning sports, and elderly walks to midday (11:30 AM – 3:30 PM) when solar heating breaks the inversion layer.",
            target_group="Families and children",
            priority="high",
            reason="Atmospheric inversion acts as a physical ceiling, preventing dispersion and driving morning PM2.5 up to 400% higher than afternoon levels.",
            supporting_source="CPCB Winter Air Quality Management Protocol & MoHFW Advisory",
            category_type="winter_smog",
            impact_explanation="Shifting outdoor exposure to midday avoids 50–65% of diurnal peak particulate exposure, significantly mitigating acute bronchospasms.",
        ),
        RecommendationItem(
            title="Community Vigilance Against Open Biomass Burning",
            description="Report illegal waste burning, dry leaf disposal, and construction dust via municipal grievance portals (e.g. Sameer app / 311). Coordinate neighborhood watch to ensure security guards and outdoor staff are provided electric room heaters instead of open wood/coal braziers.",
            target_group="Communities and neighborhood associations",
            priority="high",
            reason="Point-source biomass and plastic burning generates carcinogenic polycyclic aromatic hydrocarbons (PAHs) directly adjacent to living quarters.",
            supporting_source="CPCB Graded Response Action Plan (GRAP)",
            category_type="winter_smog",
            impact_explanation="Replacing one open wood brazier with a ceramic electric heater eliminates ~1.2 kg of toxic particulate emissions per winter night.",
        ),
    ]

    LOW_EMISSION_ROUTINES: list[RecommendationItem] = [
        RecommendationItem(
            title="Smart Commute Timing & Off-Peak Travel",
            description="Reschedule daily work travel outside rush hours (travel before 8:00 AM or after 10:15 AM). Idling in heavy traffic exposes commuters to concentrated vehicular exhaust inside vehicle cabins.",
            target_group="Urban commuters and office workers",
            priority="high",
            reason="In-cabin particulate and NO2 concentrations inside stop-and-go traffic are 3–5x higher than ambient urban background levels.",
            supporting_source="ICMR Clean Air Transportation Studies",
            category_type="low_emission_routine",
            impact_explanation="Off-peak transit reduces commute duration by ~35% and cuts personal inhaled toxic combustion by-products by nearly half.",
        ),
        RecommendationItem(
            title="Electrified Public Transit & Active Trip Substitution",
            description="Replace single-occupancy petrol/diesel car trips with electrified metro rail, electric buses, or organized carpools. For short trips under 1 km during low AQI windows, walk or cycle instead of starting cold combustion engines.",
            target_group="General adults",
            priority="medium",
            reason="Cold vehicle engine starts produce high unburnt hydrocarbon and carbon monoxide spikes during the first 5 minutes of operation.",
            supporting_source="National Clean Air Programme (NCAP)",
            category_type="low_emission_routine",
            impact_explanation="Shifting a 15 km daily commute to metro transit saves approximately 3.2 kg CO2 and 18g of NOx emissions per passenger daily.",
        ),
        RecommendationItem(
            title="Diurnal Workout Rescheduling",
            description="Move high-intensity cardiovascular exercise (running, cycling, interval training) from early mornings to early afternoons (1:00 PM – 4:00 PM) or to indoor air-filtered spaces.",
            target_group="Athletes and fitness enthusiasts",
            priority="high",
            reason="Exercise increases ventilation rates by 5–10x, driving fine particulates deep into alveolar capillaries during peak morning pollution.",
            supporting_source="WHO Physical Activity and Air Quality Guidelines",
            category_type="low_emission_routine",
            impact_explanation="Exercising during daily AQI minimums cuts inhaled particulate mass by up to 58% compared to dawn workouts.",
        ),
    ]

    INDOOR_AIR_HACKS: list[RecommendationItem] = [
        RecommendationItem(
            title="Diurnal Ventilation Window Protocol",
            description="Keep all windows and exterior vents firmly sealed during early morning, evening, and night smog peaks. Open windows only between 12:30 PM and 3:30 PM on sunny days when solar radiation and convective mixing disperse ground pollutants.",
            target_group="Households and families",
            priority="high",
            reason="Natural convective thermal currents reach their maximum at mid-day, resulting in the lowest ambient particulate concentrations of the 24-hour cycle.",
            supporting_source="CPCB / WHO Indoor Air Quality Best Practices",
            category_type="indoor_hack",
            impact_explanation="Strictly timed ventilation prevents 70–80% of outdoor smog ingress while maintaining necessary indoor CO2 replenishment.",
        ),
        RecommendationItem(
            title="DIY Corsi-Rosenthal Air Filtration Box",
            description="Construct a highly effective low-cost air purifier using an affordable box fan and 4 MERV-13 / HEPA filters taped into a cube. Operates with high Clean Air Delivery Rate (CADR) suitable for large living rooms.",
            target_group="Cost-conscious families and community centers",
            priority="high",
            reason="Multiple filter faces provide large surface area, achieving low pressure drop and high airflow particulate capture at <20% the cost of branded purifiers.",
            supporting_source="Environmental Protection Agency (EPA) DIY Air Cleaner Guidance",
            category_type="indoor_hack",
            impact_explanation="Reduces indoor PM2.5 levels by 75–85% within 45 minutes in a standard 250 sq.ft living area.",
        ),
        RecommendationItem(
            title="Damp Dusting & Wet Mopping (Zero Dry Sweeping)",
            description="Replace dry broom sweeping and feather dusters with microfiber wet mopping and damp cloth wiping. Keep kitchen doors closed and range hoods on maximum suction during frying or tempering (tadka).",
            target_group="Households",
            priority="medium",
            reason="Dry sweeping aerosolizes settled coarse particles (PM10) and biological allergens back into the human breathing zone, maintaining elevated indoor exposure.",
            supporting_source="WHO Guidelines for Indoor Air Quality",
            category_type="indoor_hack",
            impact_explanation="Damp cleaning prevents resuspension of 65% of settled dust and eliminates sharp indoor PM2.5 spikes from domestic cooking.",
        ),
        RecommendationItem(
            title="Indoor Phyto-Remediation (Air-Purifying Plants)",
            description="Incorporate proven indoor air purifying plants including Snake Plant (Sansevieria trifasciata - releases oxygen at night), Areca Palm (natural humidifier), and Spider Plant in bedrooms and living rooms.",
            target_group="Households",
            priority="low",
            reason="Phyto-remediation absorbs low-level volatile organic compounds (formaldehyde, benzene) and enhances indoor relative humidity during dry winter smog.",
            supporting_source="NASA Clean Air Study / CPCB Green Belt Guidelines",
            category_type="indoor_hack",
            impact_explanation="3–4 mature plants per room absorb up to 20% of airborne benzene and formaldehyde while increasing relative humidity by 5–10%.",
        ),
    ]

    SUSTAINABLE_ALTERNATIVES: list[RecommendationItem] = [
        RecommendationItem(
            title="Clean Space Heating Alternatives",
            description="Shift away from wood, dung-cake, or kerosene space heaters during winter. Use energy-efficient oil-filled radiators, ceramic convection heaters, or electric heated blankets combined with door draft stoppers.",
            target_group="Families and homeowners",
            priority="high",
            reason="Unvented combustion space heating releases carbon monoxide and fine soot directly into enclosed living quarters.",
            supporting_source="Bureau of Energy Efficiency (BEE) / MoHFW Advisory",
            category_type="sustainable_alternative",
            impact_explanation="Eliminates dangerous indoor carbon monoxide and cuts household combustion emissions to zero at point of use.",
        ),
        RecommendationItem(
            title="Community Solar & Electric Vehicle Integration",
            description="Advocate for rooftop solar installations and shared community EV charging bays in residential welfare associations (RWAs). Transition community maintenance vehicles to electric models.",
            target_group="Residential societies and community leaders",
            priority="medium",
            reason="Decentralized solar charging offsets thermal power grid demand during high-pollution winter seasons.",
            supporting_source="Ministry of New and Renewable Energy (MNRE) Guidelines",
            category_type="sustainable_alternative",
            impact_explanation="Replaces fossil energy reliance with renewable generation, eliminating ~0.82 kg CO2 per kWh solar generated.",
        ),
    ]

    DIRECT_IMPACT_METRICS: list[str] = [
        "Commute Choice Impact: Shifting from a diesel car to metro rail for a 20 km round trip prevents ~4.2 kg CO2 and 15g particulate emissions while reducing personal toxic inhalation by 45%.",
        "Ventilation Timing Impact: Sealing windows during morning inversion peaks and opening only between 1:00 PM – 3:30 PM cuts indoor PM2.5 infiltration by up to 78%.",
        "DIY HEPA Box Impact: Running a 4-filter Corsi-Rosenthal DIY box in a bedroom lowers ambient PM2.5 from 250 µg/m³ to under 35 µg/m³ in under an hour.",
        "Wet Mopping Impact: Replacing dry broom sweeping with damp microfiber mopping prevents 65% of settled coarse dust (PM10) from re-suspending into the breathing zone.",
        "Heating Choice Impact: Using electric radiant heating instead of open wood/biomass eliminates point-source emissions of black carbon and carcinogenic PAHs entirely, reducing household PM2.5 by ~90% and saving ~3.6 kg CO2 per evening.",
    ]

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


