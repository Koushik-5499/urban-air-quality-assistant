"""Historical air quality data preparation and chronological time-series splitting."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aqi_reading import AQIReading

logger = logging.getLogger(__name__)


@dataclass
class PreparedDataset:
    """Structured time-series dataset prepared for forecast model training and evaluation."""

    timestamps: list[datetime] = field(default_factory=list)
    aqi_values: list[float] = field(default_factory=list)
    dominant_pollutants: list[str] = field(default_factory=list)
    sample_count: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_simulated: bool = False
    data_quality: str = "verified_cpcb"
    coverage_hours: float = 0.0
    missing_intervals_count: int = 0
    is_sufficient: bool = False
    insufficiency_reason: str | None = None


@dataclass
class DatasetSplits:
    """Chronologically partitioned training, validation, and test sets without data leakage."""

    train_timestamps: list[datetime]
    train_values: list[float]
    val_timestamps: list[datetime]
    val_values: list[float]
    test_timestamps: list[datetime]
    test_values: list[float]


class DataPreparationService:
    """Extracts, cleans, and splits historical AQI measurements for forecasting."""

    @classmethod
    def load_and_prepare_dataset(
        cls,
        db: Session,
        city_id: int,
        station_id: int | None = None,
        min_required_samples: int = 24,
    ) -> PreparedDataset:
        """Query chronological AQI observations and clean data for modeling."""
        filters = [AQIReading.city_id == city_id]
        if station_id is not None:
            filters.append(AQIReading.station_id == station_id)

        stmt = select(AQIReading).where(*filters).order_by(AQIReading.measured_at.asc())
        all_readings = list(db.execute(stmt).scalars().all())

        if not all_readings:
            return PreparedDataset(
                is_sufficient=False,
                insufficiency_reason="No historical AQI records found for this location.",
            )

        # 1. Deduplicate by measurement timestamp (keeping latest entry)
        deduped: dict[datetime, AQIReading] = {}
        for r in all_readings:
            ts = r.measured_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            deduped[ts] = r

        sorted_timestamps = sorted(deduped.keys())
        sorted_readings = [deduped[t] for t in sorted_timestamps]

        # 2. Check real CPCB vs simulated data availability
        real_readings = [r for r in sorted_readings if not r.is_simulated]
        use_simulated = False

        if len(real_readings) >= min_required_samples:
            # Sufficient verified real CPCB observations available
            working_readings = real_readings
            data_quality = "verified_cpcb"
        elif len(sorted_readings) >= min_required_samples:
            # Fall back to simulated observations where real telemetry is sparse
            working_readings = sorted_readings
            use_simulated = any(r.is_simulated for r in working_readings)
            data_quality = "simulated" if use_simulated else "verified_cpcb"
        else:
            total_count = len(sorted_readings)
            return PreparedDataset(
                sample_count=total_count,
                start_time=sorted_timestamps[0] if sorted_timestamps else None,
                end_time=sorted_timestamps[-1] if sorted_timestamps else None,
                is_sufficient=False,
                insufficiency_reason=(
                    f"Insufficient historical data: found {total_count} observations, "
                    f"minimum {min_required_samples} required for valid time-series forecasting."
                ),
            )

        timestamps: list[datetime] = []
        aqi_values: list[float] = []
        dominant_pollutants: list[str] = []

        # 3. Detect missing time intervals (> 3 hours gap between consecutive readings)
        missing_intervals = 0
        prev_time: datetime | None = None

        for r in working_readings:
            t = r.measured_at
            if t.tzinfo is None:
                t = t.replace(tzinfo=UTC)

            if prev_time is not None:
                gap_hours = (t - prev_time).total_seconds() / 3600.0
                if gap_hours > 3.0:
                    missing_intervals += 1
            prev_time = t

            # Discard invalid or out-of-range AQI values (< 0 or > 500)
            val = float(r.aqi_value)
            if 0.0 <= val <= 500.0:
                timestamps.append(t)
                aqi_values.append(val)
                dominant_pollutants.append(r.dominant_pollutant or "PM2.5")

        if len(aqi_values) < min_required_samples:
            return PreparedDataset(
                sample_count=len(aqi_values),
                is_sufficient=False,
                insufficiency_reason=(
                    f"After filtering invalid values, only {len(aqi_values)} valid readings remain "
                    f"(minimum {min_required_samples} required)."
                ),
            )

        start_t = timestamps[0]
        end_t = timestamps[-1]
        coverage_hours = (end_t - start_t).total_seconds() / 3600.0

        return PreparedDataset(
            timestamps=timestamps,
            aqi_values=aqi_values,
            dominant_pollutants=dominant_pollutants,
            sample_count=len(aqi_values),
            start_time=start_t,
            end_time=end_t,
            is_simulated=use_simulated,
            data_quality=data_quality,
            coverage_hours=round(coverage_hours, 1),
            missing_intervals_count=missing_intervals,
            is_sufficient=True,
        )

    @classmethod
    def split_chronological(
        cls,
        dataset: PreparedDataset,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> DatasetSplits:
        """Partition time-series chronologically into train, validation, and test subsets.

        Strict chronological ordering is maintained to avoid data leakage.
        """
        n = dataset.sample_count
        if n < 4:
            raise ValueError(f"Dataset has only {n} samples, insufficient for splitting.")

        train_end = max(2, int(n * train_ratio))
        val_end = max(train_end + 1, int(n * (train_ratio + val_ratio)))

        if val_end >= n:
            val_end = n - 1

        train_ts = dataset.timestamps[:train_end]
        train_y = dataset.aqi_values[:train_end]

        val_ts = dataset.timestamps[train_end:val_end]
        val_y = dataset.aqi_values[train_end:val_end]

        test_ts = dataset.timestamps[val_end:]
        test_y = dataset.aqi_values[val_end:]

        return DatasetSplits(
            train_timestamps=train_ts,
            train_values=train_y,
            val_timestamps=val_ts,
            val_values=val_y,
            test_timestamps=test_ts,
            test_values=test_y,
        )
