"""
Uncertainty estimation and prediction interval calculation based on empirical validation
residuals.
"""

import math
from dataclasses import dataclass


@dataclass
class UncertaintyEstimate:
    """Interval bounds and uncertainty classification for a predicted point."""

    lower_bound: int | None
    upper_bound: int | None
    uncertainty_status: str  # "estimated", "high_uncertainty", "unavailable"
    standard_error: float | None
    confidence_level: float = 0.90
    methodology: str = "empirical_residual_variance_with_horizon_expansion"


class UncertaintyEstimator:
    """
    Computes calibrated prediction intervals that widen monotonically with the forecast
    horizon.
    """

    @staticmethod
    def calculate_residual_standard_deviation(
        actuals: list[float],
        predictions: list[float],
    ) -> float | None:
        """Compute sample standard deviation of residuals (errors)."""
        if not actuals or len(actuals) != len(predictions) or len(actuals) < 3:
            return None

        residuals = [a - p for a, p in zip(actuals, predictions)]
        mean_res = sum(residuals) / float(len(residuals))
        variance = sum((r - mean_res) ** 2 for r in residuals) / float(len(residuals) - 1)
        return math.sqrt(variance)

    @classmethod
    def estimate_interval(
        cls,
        predicted_aqi: float,
        horizon_hours: int,
        residual_std: float | None,
        sample_count: int = 0,
        z_multiplier: float = 1.645,  # 90% confidence interval
    ) -> UncertaintyEstimate:
        """Calculate calibrated lower and upper prediction bounds.

        The prediction interval expands with the square root of horizon step:
        SE(h) = residual_std * sqrt(1 + (h / 24))
        """
        # If insufficient validation samples exist, do not fabricate artificial intervals
        if residual_std is None or sample_count < 6:
            return UncertaintyEstimate(
                lower_bound=None,
                upper_bound=None,
                uncertainty_status="unavailable",
                standard_error=None,
                methodology="uncalibrated_insufficient_sample_size",
            )

        # Monotonically expanding standard error with horizon
        # Horizon decay scaling: at 24h, variance doubles; at 72h, variance expands by 4x
        horizon_factor = math.sqrt(1.0 + (float(horizon_hours) / 24.0))
        se_h = residual_std * horizon_factor

        half_width = z_multiplier * se_h

        lower = max(0, int(round(predicted_aqi - half_width)))
        upper = min(500, int(round(predicted_aqi + half_width)))

        # Assign uncertainty status based on horizon and data volume
        if horizon_hours >= 48 or sample_count < 15:
            status_label = "high_uncertainty"
        else:
            status_label = "estimated"

        return UncertaintyEstimate(
            lower_bound=lower,
            upper_bound=upper,
            uncertainty_status=status_label,
            standard_error=round(se_h, 2),
            confidence_level=0.90,
            methodology="empirical_residual_variance_with_horizon_expansion",
        )
