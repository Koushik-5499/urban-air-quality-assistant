"""NAQI category health guidelines, disclaimers, and authoritative citations."""

from app.integrations.ai.schemas import CategoryGuideline

MEDICAL_DISCLAIMER = (
    "Disclaimer: This guidance is provided for educational and environmental awareness "
    "purposes only. "
    "It does not constitute professional medical advice, clinical diagnosis, or individual "
    "treatment recommendations. "
    "Air purifiers and particulate masks reduce exposure but do not guarantee complete "
    "protection. "
    "Individuals experiencing breathing difficulties, chest tightness, or worsening "
    "respiratory or cardiovascular symptoms "
    "should consult a qualified healthcare provider immediately."
)

AUTHORITATIVE_SOURCES = [
    "Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate "
    "Change, Govt of India - National Air Quality Index (2014)",
    "World Health Organization (WHO) Global Air Quality Guidelines: Particulate matter (PM2.5 "
    "and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide (2021)",
    "Ministry of Health and Family Welfare (MoHFW), Govt of India - Health Advisory on Air "
    "Pollution",
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

CATEGORY_GUIDELINES: dict[str, CategoryGuideline] = {
    "Good": CategoryGuideline(
        category="Good",
        aqi_range="0–50",
        health_statement="Minimal health impact.",
        general_guidance=(
            "Air quality is ideal for all normal outdoor activities, exercise, and ventilation."
        ),
        vulnerable_guidance=(
            "Safe for children, elderly individuals, and individuals with existing medical "
            "conditions."
        ),
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
        general_guidance=(
            "Air quality is acceptable for the general public. Outdoor activities are safe."
        ),
        vulnerable_guidance=(
            "Unusually sensitive individuals with asthma may notice mild respiratory "
            "irritation during prolonged heavy exertion."
        ),
        precautions=[
            "General public can engage in regular outdoor work and recreation.",
            "Sensitive individuals should monitor for mild symptoms such as throat "
            "irritation or coughing.",
            "Keep quick-relief inhalers accessible if you have asthma.",
        ],
    ),
    "Moderate": CategoryGuideline(
        category="Moderate",
        aqi_range="101–200",
        health_statement=(
            "Breathing discomfort to people with lungs, asthma and heart diseases."
        ),
        general_guidance=(
            "Most healthy people can engage in outdoor activities, but may experience slight "
            "fatigue during prolonged intense exertion."
        ),
        vulnerable_guidance=(
            "Children, seniors, and individuals with asthma or heart conditions should take "
            "frequent breaks during outdoor activities."
        ),
        precautions=[
            "Shift intense outdoor workouts away from peak traffic hours (morning and "
            "evening rushes).",
            "Keep windows closed during high-traffic hours if living near major roads.",
            "Sensitive groups should reduce prolonged outdoor cardiovascular exertion.",
            "Stay well-hydrated to support mucosal clearance.",
        ],
    ),
    "Poor": CategoryGuideline(
        category="Poor",
        aqi_range="201–300",
        health_statement="Breathing discomfort to most people on prolonged exposure.",
        general_guidance=(
            "Healthy individuals will likely experience throat irritation, dry cough, or eye "
            "burning during extended outdoor exertion."
        ),
        vulnerable_guidance=(
            "Children, older adults, and individuals with respiratory/cardiovascular disease "
            "should avoid strenuous outdoor exertion."
        ),
        precautions=[
            "Avoid prolonged outdoor cardiovascular exercise; exercise indoors in a "
            "clean-air environment.",
            "Wear a well-fitted, certified particulate respirator (N95 or FFP2) when "
            "commuting outdoors.",
            "Close windows and use indoor air purifiers with true HEPA filtration if "
            "available.",
            "Avoid indoor pollution sources like incense sticks, smoking, or unvented "
            "biomass cooking.",
        ],
    ),
    "Very Poor": CategoryGuideline(
        category="Very Poor",
        aqi_range="301–400",
        health_statement="Respiratory illness on prolonged exposure.",
        general_guidance=(
            "Healthy adults will experience significant irritation. Prolonged exposure poses "
            "serious health risks."
        ),
        vulnerable_guidance=(
            "High risk of asthma exacerbation and cardiovascular stress. Vulnerable "
            "individuals should remain indoors."
        ),
        precautions=[
            "Strictly avoid outdoor sports, morning walks, and outdoor jogging.",
            "Schools should suspend outdoor morning assemblies and physical education classes.",
            "Wear N95/FFP2 respirators when stepping outdoors; surgical or cloth masks do "
            "not filter fine particulates.",
            "Run indoor HEPA purifiers continuously in bedrooms and living areas.",
            "Keep prescribed respiratory medications (e.g., bronchodilators) on hand.",
        ],
    ),
    "Severe": CategoryGuideline(
        category="Severe",
        aqi_range="401–500",
        health_statement=(
            "Affects healthy people and seriously impacts those with existing diseases."
        ),
        general_guidance=(
            "Emergency air quality condition. Severe health risks for all segments of the "
            "population."
        ),
        vulnerable_guidance=(
            "Extreme hazard for children, pregnant people, older adults, and those with "
            "heart/lung disease. Risk of acute hospital visits."
        ),
        precautions=[
            "Stay indoors and minimize physical exertion.",
            "Seal doors and windows; use wet mopping rather than dry sweeping to minimize "
            "indoor dust.",
            "Operate high-efficiency HEPA air purifiers in sealed rooms.",
            "Non-essential outdoor travel should be avoided.",
            "Seek urgent medical evaluation if experiencing shortness of breath, "
            "wheezing, or chest pain.",
        ],
    ),
}
