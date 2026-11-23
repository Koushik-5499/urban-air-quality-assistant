"""Input validation and CPCB NAQI data sufficiency evaluation."""

from app.services.aqi.breakpoints import POLLUTANT_INFO

# CPCB minimum requirement: at least one particulate matter pollutant must be monitored
PARTICULATE_POLLUTANTS: set[str] = {"PM2.5", "PM10"}
MINIMUM_POLLUTANTS_FOR_OVERALL_AQI = 3


class AQIValidator:
    """Validates concentrations, units, and data sufficiency according to CPCB guidelines."""

    @staticmethod
    def validate_concentration(
        pollutant_code: str, concentration: float, unit: str
    ) -> tuple[bool, str | None]:
        """Validate whether a concentration value and unit are suitable for NAQI calculation."""
        if concentration is None or concentration < 0.0:
            return False, f"Concentration must be a non-negative number; got {concentration}."

        if pollutant_code not in POLLUTANT_INFO:
            return False, f"Pollutant '{pollutant_code}' is not supported by CPCB NAQI."

        expected_unit = POLLUTANT_INFO[pollutant_code].unit
        # Normalize unit string
        clean_unit = unit.strip().lower().replace("3", "³")
        clean_expected = expected_unit.strip().lower().replace("3", "³")

        if clean_unit != clean_expected:
            return (
                False,
                f"Incompatible unit '{unit}' for {pollutant_code}. "
                f"CPCB NAQI requires '{expected_unit}'.",
            )

        return True, None

    @staticmethod
    def evaluate_data_sufficiency(available_pollutants: list[str]) -> tuple[bool, str, list[str]]:
        """Evaluate if available pollutants meet CPCB minimum requirements for an Overall NAQI.

        Official CPCB Rule:
        1. At least 3 pollutants must be monitored.
        2. At least one of PM2.5 or PM10 must be included.
        """
        available_set = set(available_pollutants)
        has_particulate = bool(available_set.intersection(PARTICULATE_POLLUTANTS))
        count = len(available_set)

        missing_requirements: list[str] = []
        if count < MINIMUM_POLLUTANTS_FOR_OVERALL_AQI:
            missing_requirements.append(
                f"At least 3 criteria pollutants required "
                f"(got {count}: {', '.join(sorted(available_set)) or 'none'})"
            )

        if not has_particulate:
            missing_requirements.append(
                "At least one particulate pollutant (PM2.5 or PM10) is mandatory"
            )

        if not missing_requirements:
            return True, "Sufficient data for CPCB Overall NAQI calculation.", []

        explanation = (
            "Insufficient pollutant coverage under CPCB NAQI criteria: "
            + "; ".join(missing_requirements)
            + ". Sub-indices computed, but overall AQI cannot be officially determined."
        )
        return False, explanation, missing_requirements
