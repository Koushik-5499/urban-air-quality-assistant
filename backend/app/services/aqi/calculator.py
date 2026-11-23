"""Pure computational logic for CPCB Indian National Air Quality Index (NAQI)."""

from app.services.aqi.breakpoints import CPCB_BREAKPOINTS
from app.services.aqi.categories import get_aqi_category
from app.services.aqi.dominant_pollutant import DominantPollutantResolver
from app.services.aqi.validators import AQIValidator


class AQICalculator:
    """Calculates sub-indices and overall NAQI following CPCB methodology."""

    @classmethod
    def calculate_sub_index(
        cls,
        pollutant_code: str,
        concentration: float,
        unit: str = "µg/m³",
    ) -> int | None:
        """Compute the CPCB sub-index for a single pollutant concentration
        using linear interpolation.

        Formula:
            I_p = I_low + ((I_high - I_low) / (B_high - B_low)) * (C_p - B_low)

        Returns integer sub-index between 0 and 500, or None if input is invalid.
        """
        is_valid, _ = AQIValidator.validate_concentration(pollutant_code, concentration, unit)
        if not is_valid:
            return None

        breakpoints = CPCB_BREAKPOINTS.get(pollutant_code)
        if not breakpoints:
            return None

        # Check lowest boundary (C_p == 0)
        if concentration <= 0.0:
            return 0

        # Find matching breakpoint range
        for bp in breakpoints:
            # Handle boundary inclusion:
            # In CPCB, if C_p is within [c_low, c_high]
            if bp.c_low <= concentration <= bp.c_high:
                # Linear interpolation
                c_range = bp.c_high - bp.c_low
                i_range = bp.i_high - bp.i_low
                if c_range == 0:
                    return bp.i_high

                sub_index = bp.i_low + (i_range / c_range) * (concentration - bp.c_low)
                return max(0, min(500, round(sub_index)))

        # Concentration exceeds the highest severe breakpoint:
        # Cap at 500 as per CPCB NAQI standard ceiling
        return 500

    @classmethod
    def calculate_overall_aqi(
        cls,
        sub_indices: dict[str, int],
    ) -> tuple[int | None, str | None, str | None, bool, str, list[str]]:
        """Calculate composite CPCB Overall NAQI from individual pollutant sub-indices.

        Returns:
            (
            overall_aqi,
            aqi_category,
            dominant_pollutant,
            is_sufficient,
            explanation,
            missing_requirements,
        )
        """
        if not sub_indices:
            return (
                None,
                None,
                None,
                False,
                "No valid pollutant sub-indices provided.",
                ["No pollutant data available"],
            )

        # Check CPCB data sufficiency
        is_sufficient, explanation, missing = AQIValidator.evaluate_data_sufficiency(
            list(sub_indices.keys())
        )

        dominant = DominantPollutantResolver.resolve_dominant_pollutant(sub_indices)

        if not is_sufficient:
            return None, None, dominant, False, explanation, missing

        # Overall AQI = max(sub-indices)
        overall_aqi = max(sub_indices.values())
        category = get_aqi_category(overall_aqi)

        return (
            overall_aqi,
            category,
            dominant,
            True,
            f"Overall AQI calculated successfully using CPCB worst-pollutant rule "
            f"(Dominant: {dominant}).",
            [],
        )
