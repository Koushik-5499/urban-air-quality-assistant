"""CPCB NAQI Category ranges, color codes, and advisory statements."""

from typing import Dict, NamedTuple


class CategoryInfo(NamedTuple):
    """Categorical metadata according to CPCB NAQI."""

    category: str
    aqi_range: str
    color_hex: str
    health_statement: str


CATEGORIES: Dict[str, CategoryInfo] = {
    "Good": CategoryInfo(
        category="Good",
        aqi_range="0–50",
        color_hex="#16A34A",
        health_statement="Minimal health impact. Air quality is considered satisfactory.",
    ),
    "Satisfactory": CategoryInfo(
        category="Satisfactory",
        aqi_range="51–100",
        color_hex="#65A30D",
        health_statement="Minor breathing discomfort to sensitive individuals.",
    ),
    "Moderately Polluted": CategoryInfo(
        category="Moderately Polluted",
        aqi_range="101–200",
        color_hex="#EAB308",
        health_statement="Breathing discomfort to people with lungs, asthma and heart diseases.",
    ),
    "Poor": CategoryInfo(
        category="Poor",
        aqi_range="201–300",
        color_hex="#F97316",
        health_statement="Breathing discomfort to most people on prolonged exposure.",
    ),
    "Very Poor": CategoryInfo(
        category="Very Poor",
        aqi_range="301–400",
        color_hex="#DC2626",
        health_statement="Respiratory illness on prolonged exposure; pronounced effect on people with lung and heart diseases.",
    ),
    "Severe": CategoryInfo(
        category="Severe",
        aqi_range="401–500",
        color_hex="#7F1D1D",
        health_statement="Affects healthy people and seriously impacts those with existing diseases.",
    ),
}


def get_aqi_category(aqi_value: int) -> str:
    """Map a numerical AQI index to its official CPCB category name."""
    if aqi_value <= 50:
        return "Good"
    elif aqi_value <= 100:
        return "Satisfactory"
    elif aqi_value <= 200:
        return "Moderately Polluted"
    elif aqi_value <= 300:
        return "Poor"
    elif aqi_value <= 400:
        return "Very Poor"
    else:
        return "Severe"


def get_category_info(aqi_value: int) -> CategoryInfo:
    """Retrieve full category info including health advisory and display color."""
    cat_name = get_aqi_category(aqi_value)
    return CATEGORIES[cat_name]

