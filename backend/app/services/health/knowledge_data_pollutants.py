"""Detailed CPCB & WHO reference educational metadata for each criteria pollutant."""

from app.integrations.ai.schemas import PollutantExplanationResponse
from app.services.health.knowledge_data_guidelines import MEDICAL_DISCLAIMER

POLLUTANT_DETAILS: dict[str, PollutantExplanationResponse] = {
    "PM2.5": PollutantExplanationResponse(
        pollutant_code="PM2.5",
        full_name="Fine Particulate Matter (Diameter ≤ 2.5 µm)",
        unit="µg/m³",
        description=(
            "Microscopic airborne solid particles and liquid droplets 30 times finer than a "
            "strand of human hair. Because of their tiny size, they bypass upper airway "
            "defenses and penetrate deep into pulmonary alveoli and the bloodstream."
        ),
        common_sources=[
            "Vehicular exhaust (particularly diesel engines)",
            "Biomass, crop residue, and solid waste burning",
            "Coal-fired thermal power plants and industrial combustion",
            "Construction dust and atmospheric chemical reactions (secondary aerosols)",
        ],
        health_effects=[
            "Deep lung penetration causing pulmonary inflammation and oxidative stress",
            "Aggravation of asthma, chronic obstructive pulmonary disease (COPD), and "
            "bronchitis",
            "Translocation into bloodstream increasing risks of hypertension, heart "
            "attack, and stroke",
            "Adverse birth outcomes and impaired pediatric lung development with chronic "
            "exposure",
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
        description=(
            "Inhalable particles capable of penetrating the upper respiratory tract, "
            "including the nasal passages and bronchi."
        ),
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
        description=(
            "A reddish-brown, highly reactive gas belonging to the group of nitrogen oxides "
            "(NOx), formed primarily during high-temperature fuel combustion."
        ),
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
            "Keep automobile windows closed with recirculation enabled during heavy "
            "traffic jams.",
        ],
        cpcb_standard_24h="80 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
        sources=["CPCB NAAQS", "WHO Nitrogen Dioxide Review"],
        disclaimer=MEDICAL_DISCLAIMER,
    ),
    "SO2": PollutantExplanationResponse(
        pollutant_code="SO2",
        full_name="Sulfur Dioxide",
        unit="µg/m³",
        description=(
            "A pungent, colorless gas released during the burning of sulfur-containing fossil "
            "fuels and smelting of mineral ores."
        ),
        common_sources=[
            "Coal and oil burning at thermal power plants",
            "Industrial refining and chemical manufacturing",
            "Heavy-duty marine shipping and unrefined heavy oil combustion",
        ],
        health_effects=[
            "Severe irritation of the eyes, mucous membranes, and respiratory tract",
            "Rapid reflex bronchoconstriction within minutes of inhalation for people "
            "with asthma",
            "Precursor to secondary sulfate aerosols and acid precipitation",
        ],
        reduction_measures=[
            "Individuals with asthma should remain indoors when local SO2 levels spike "
            "near industrial zones.",
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
        description=(
            "A colorless, odorless, tasteless, and highly toxic gas produced by the "
            "incomplete combustion of carbon-based fuels."
        ),
        common_sources=[
            "Incomplete combustion in motor vehicle engines, especially in slow, "
            "congested traffic",
            "Faulty indoor gas water heaters, wood-burning stoves, and generators",
            "Biomass burning and tobacco smoke",
        ],
        health_effects=[
            "Binds to hemoglobin with 200x greater affinity than oxygen, forming "
            "carboxyhemoglobin",
            "Impairs oxygen delivery to critical organs, particularly the brain and heart",
            "Causes headaches, dizziness, fatigue, and chest pain in individuals with "
            "ischemic heart disease",
        ],
        reduction_measures=[
            "Never run generators, charcoal grills, or vehicle engines inside closed "
            "spaces or garages.",
            "Ensure regular servicing and chimney venting of gas heating appliances.",
            "Install certified Carbon Monoxide alarms in homes utilizing fuel-burning "
            "equipment.",
        ],
        cpcb_standard_24h="2.0 mg/m³ (8-hour standard: 2.0 mg/m³, 1-hour: 4.0 mg/m³)",
        sources=["CPCB NAAQS", "WHO Environmental Health Criteria for CO"],
        disclaimer=MEDICAL_DISCLAIMER,
    ),
    "O3": PollutantExplanationResponse(
        pollutant_code="O3",
        full_name="Ground-Level Ozone",
        unit="µg/m³",
        description=(
            "A secondary photochemical pollutant formed when precursor gases (NOx and "
            "Volatile Organic Compounds) react in ambient air under intense solar radiation."
        ),
        common_sources=[
            "Secondary atmospheric formation: not emitted directly from tailpipes or chimneys",
            "Precursor emissions from vehicles, solvent evaporation, and industrial "
            "chemicals under sunlight",
        ],
        health_effects=[
            "Potent oxidant causing direct cellular damage to alveolar and bronchiolar "
            "epithelium",
            "Reduces lung capacity, causing chest pain, throat irritation, and persistent "
            "coughing",
            "Particularly hazardous to outdoor workers, athletes, and children playing "
            "outside in afternoons",
        ],
        reduction_measures=[
            "Schedule outdoor cardiovascular sports for early morning when solar "
            "photochemical reaction rates are lowest.",
            "Avoid outdoor recreation during mid-afternoon hours (1:00 PM to 5:00 PM) on "
            "sunny summer days.",
        ],
        cpcb_standard_24h="100 µg/m³ (8-hour standard: 100 µg/m³)",
        sources=["CPCB NAAQS", "WHO Ozone Health Impact Assessment"],
        disclaimer=MEDICAL_DISCLAIMER,
    ),
    "NH3": PollutantExplanationResponse(
        pollutant_code="NH3",
        full_name="Ammonia",
        unit="µg/m³",
        description=(
            "A pungent alkaline gas that reacts rapidly in the atmosphere with acidic gases "
            "(SO2 and NOx) to form secondary ammonium aerosols."
        ),
        common_sources=[
            "Agricultural livestock waste and synthetic fertilizer decomposition",
            "Untreated municipal sewage and open drainage systems",
            "Refrigeration systems and industrial fertilizer synthesis",
        ],
        health_effects=[
            "Eye, nose, and upper respiratory tract irritation",
            "Forms secondary ammonium fine particulate matter (PM2.5) that penetrates "
            "deeply into the lungs",
        ],
        reduction_measures=[
            "Avoid prolonged exposure near open, untreated municipal drains or "
            "agricultural slurry pits.",
        ],
        cpcb_standard_24h="400 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
        sources=["CPCB NAAQS", "WHO Guidelines for Air Quality"],
        disclaimer=MEDICAL_DISCLAIMER,
    ),
    "Pb": PollutantExplanationResponse(
        pollutant_code="Pb",
        full_name="Lead",
        unit="µg/m³",
        description=(
            "A heavy metal toxicant present in airborne dust, historically from leaded fuels "
            "and currently from industrial smelting and battery recycling."
        ),
        common_sources=[
            "Lead-acid battery recycling and manufacturing facilities",
            "Non-ferrous metal smelting and foundry operations",
            "Resuspension of contaminated industrial soil and legacy lead paint",
        ],
        health_effects=[
            "Systemic neurotoxicant with no known safe blood concentration in children",
            "Impairs pediatric neurodevelopment, cognitive IQ, and behavioral executive "
            "function",
            "Accumulates in bones and organs, contributing to kidney dysfunction and "
            "cardiovascular disease",
        ],
        reduction_measures=[
            "Maintain strict wet-cleaning protocols in areas near battery recycling or "
            "smelting sites.",
            "Ensure children wash hands thoroughly before meals after playing outdoors.",
        ],
        cpcb_standard_24h="1.0 µg/m³ (CPCB 24-hour National Ambient Air Quality Standard)",
        sources=["CPCB NAAQS", "WHO Guidelines on Lead Exposure and Health"],
        disclaimer=MEDICAL_DISCLAIMER,
    ),
}

