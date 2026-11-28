"""Parameter objects and transition evaluation helpers for ThresholdEngine."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

POLLUTANT_SHIFT_MIN_AQI = 150


class AlertCondition(BaseModel):
    """Detected alert condition metadata."""

    alert_type: str
    severity: str
    title: str
    description: str
    current_aqi: int
    previous_aqi: int | None
    threshold_value: int | None
    aqi_category: str
    dominant_pollutant: str | None
    measurement_timestamp: datetime
    source: str
    is_simulated: bool


@dataclass(frozen=True, slots=True)
class ConditionSpec:
    """Typed parameter object describing an AlertCondition to construct."""

    alert_type: str
    severity: str
    title: str
    description: str
    threshold_value: int | None


@dataclass(frozen=True, slots=True)
class ReadingContext:
    """Typed context capturing current and optional prior AQI readings for rule evaluation."""

    curr_aqi: int
    curr_cat: str
    curr_dom: str
    curr_time: datetime
    curr_severity: str
    source: str
    is_sim: bool
    sim_prefix: str
    location_label: str
    min_threshold: int
    deterioration_threshold: int
    improvement_threshold: int
    prev_aqi: int | None = None
    prev_cat: str | None = None
    prev_dom: str | None = None
    aqi_delta: int = 0


def build_condition(ctx: ReadingContext, spec: ConditionSpec) -> AlertCondition:
    """Construct an AlertCondition from paired ReadingContext and ConditionSpec objects."""
    return AlertCondition(
        alert_type=spec.alert_type,
        severity=spec.severity,
        title=spec.title,
        description=spec.description,
        current_aqi=ctx.curr_aqi,
        previous_aqi=ctx.prev_aqi,
        threshold_value=spec.threshold_value,
        aqi_category=ctx.curr_cat,
        dominant_pollutant=ctx.curr_dom,
        measurement_timestamp=ctx.curr_time,
        source=ctx.source,
        is_simulated=ctx.is_sim,
    )


def check_initial_threshold(ctx: ReadingContext) -> AlertCondition | None:
    """Scenario 1: First observation above minimum threshold."""
    if ctx.curr_aqi < ctx.min_threshold:
        return None
    return build_condition(
        ctx,
        ConditionSpec(
            alert_type="THRESHOLD_CROSSING",
            severity=ctx.curr_severity,
            title=f"{ctx.sim_prefix}Air Quality Alert: {ctx.curr_cat} in {ctx.location_label}",
            description=(
                f"Current AQI is {ctx.curr_aqi} ({ctx.curr_cat}), "
                f"driven primarily by {ctx.curr_dom}. "
                "Air quality has reached elevated pollution levels."
            ),
            threshold_value=ctx.min_threshold,
        ),
    )


def check_category_worsening(ctx: ReadingContext) -> AlertCondition | None:
    """Scenario 2a: Category worsening transition."""
    if ctx.prev_aqi is None or not (
        ctx.curr_aqi > ctx.prev_aqi and ctx.curr_aqi >= ctx.min_threshold
    ):
        return None
    return build_condition(
        ctx,
        ConditionSpec(
            alert_type="CATEGORY_CHANGE",
            severity=ctx.curr_severity,
            title=(
                f"{ctx.sim_prefix}Air Quality Worsened to {ctx.curr_cat} in {ctx.location_label}"
            ),
            description=(
                f"AQI transitioned from {ctx.prev_aqi} ({ctx.prev_cat}) "
                f"to {ctx.curr_aqi} ({ctx.curr_cat}). "
                f"Dominant pollutant is {ctx.curr_dom}. "
                "Increased health precautions are advised."
            ),
            threshold_value=ctx.min_threshold,
        ),
    )


def check_category_improvement(ctx: ReadingContext) -> AlertCondition | None:
    """Scenario 2b: Significant improvement transition."""
    if ctx.prev_aqi is None or not (
        ctx.curr_aqi < ctx.prev_aqi and abs(ctx.aqi_delta) >= ctx.improvement_threshold
    ):
        return None
    return build_condition(
        ctx,
        ConditionSpec(
            alert_type="IMPROVEMENT",
            severity="Low",
            title=(
                f"{ctx.sim_prefix}Air Quality Improved to {ctx.curr_cat} in {ctx.location_label}"
            ),
            description=(
                f"AQI improved significantly by {abs(ctx.aqi_delta)} points, "
                f"dropping from {ctx.prev_aqi} ({ctx.prev_cat}) "
                f"to {ctx.curr_aqi} ({ctx.curr_cat})."
            ),
            threshold_value=ctx.min_threshold,
        ),
    )


def check_deterioration_spike(ctx: ReadingContext) -> AlertCondition | None:
    """Scenario 3: Same-category spike in AQI."""
    if ctx.prev_aqi is None or not (
        ctx.aqi_delta >= ctx.deterioration_threshold and ctx.curr_aqi >= ctx.min_threshold
    ):
        return None
    return build_condition(
        ctx,
        ConditionSpec(
            alert_type="DETERIORATION",
            severity=ctx.curr_severity,
            title=f"{ctx.sim_prefix}Sudden Pollution Spike in {ctx.location_label}",
            description=(
                f"AQI spiked by +{ctx.aqi_delta} points (from {ctx.prev_aqi} to {ctx.curr_aqi}) "
                "within the recent monitoring period. "
                f"Category remains {ctx.curr_cat} with {ctx.curr_dom} as dominant pollutant."
            ),
            threshold_value=ctx.deterioration_threshold,
        ),
    )


def check_threshold_crossing(ctx: ReadingContext) -> AlertCondition | None:
    """Scenario 4: User-defined threshold crossing."""
    if ctx.prev_aqi is None or not (ctx.prev_aqi < ctx.min_threshold <= ctx.curr_aqi):
        return None
    return build_condition(
        ctx,
        ConditionSpec(
            alert_type="THRESHOLD_CROSSING",
            severity=ctx.curr_severity,
            title=(
                f"{ctx.sim_prefix}AQI Crossed Threshold ({ctx.min_threshold}) "
                f"in {ctx.location_label}"
            ),
            description=(
                f"AQI has crossed your alert threshold of {ctx.min_threshold}. "
                f"Current AQI is {ctx.curr_aqi} ({ctx.curr_cat}), "
                f"up from {ctx.prev_aqi}."
            ),
            threshold_value=ctx.min_threshold,
        ),
    )


def check_pollutant_shift(ctx: ReadingContext) -> AlertCondition | None:
    """Scenario 5: Dominant pollutant change at elevated levels."""
    if not (
        ctx.prev_dom
        and ctx.curr_dom != ctx.prev_dom
        and ctx.curr_aqi >= POLLUTANT_SHIFT_MIN_AQI
    ):
        return None
    return build_condition(
        ctx,
        ConditionSpec(
            alert_type="POLLUTANT_CHANGE",
            severity=ctx.curr_severity,
            title=f"{ctx.sim_prefix}Dominant Pollutant Shift in {ctx.location_label}",
            description=(
                f"Primary pollution driver shifted from {ctx.prev_dom} to {ctx.curr_dom}. "
                f"Current AQI is {ctx.curr_aqi} ({ctx.curr_cat})."
            ),
            threshold_value=None,
        ),
    )


def dispatch_same_category_or_change(ctx: ReadingContext) -> AlertCondition | None:
    """Route to the appropriate condition evaluator based on category transition or drift."""
    if ctx.curr_cat != ctx.prev_cat:
        worsening = check_category_worsening(ctx)
        if worsening is not None:
            return worsening
        return check_category_improvement(ctx)
    if ctx.aqi_delta >= ctx.deterioration_threshold and ctx.curr_aqi >= ctx.min_threshold:
        return check_deterioration_spike(ctx)
    return check_threshold_crossing(ctx)


def evaluate_reading_pair(
    ctx: ReadingContext, has_previous: bool
) -> list[AlertCondition]:
    """Evaluate threshold, category-transition, and pollutant-shift conditions."""
    if not has_previous:
        cond = check_initial_threshold(ctx)
        return [cond] if cond else []

    conditions: list[AlertCondition] = []
    cond = dispatch_same_category_or_change(ctx)
    if cond:
        conditions.append(cond)
    shift = check_pollutant_shift(ctx)
    if shift:
        conditions.append(shift)
    return conditions
