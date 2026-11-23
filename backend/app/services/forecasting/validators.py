"""Validation helpers for air quality forecasting horizons, parameters, and datasets."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.city import City
from app.models.monitoring_station import MonitoringStation

# Standard supported forecasting horizons in hours
SUPPORTED_HORIZONS: list[int] = [1, 6, 12, 24, 48, 72]

# Map label string to horizon integer hours
HORIZON_LABEL_MAP = {
    "1h": 1,
    "6h": 6,
    "12h": 12,
    "24h": 24,
    "48h": 48,
    "72h": 72,
}


class ForecastValidator:
    """Validates forecasting horizons, entities, and data volume constraints."""

    @staticmethod
    def parse_horizon(horizon_str: str | None) -> int | None:
        """Convert a horizon string like '24h' or '24' into integer hours."""
        if not horizon_str or horizon_str.lower() in ("all", "default"):
            return None

        cleaned = horizon_str.strip().lower()
        if cleaned in HORIZON_LABEL_MAP:
            return HORIZON_LABEL_MAP[cleaned]

        try:
            val = int(cleaned.rstrip("h"))
            if val in SUPPORTED_HORIZONS:
                return val
        except ValueError:
            pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported horizon '{horizon_str}'. Supported "
                f"horizons: {sorted(list(HORIZON_LABEL_MAP.keys()))}."
            ),
        )

    @staticmethod
    def validate_horizons_list(horizons: list[str] | None) -> list[int]:
        """Validate a list of horizon strings and return unique integer hours."""
        if not horizons:
            return list(SUPPORTED_HORIZONS)

        parsed: set[int] = set()
        for h in horizons:
            parsed.add(ForecastValidator.parse_horizon(h) or 24)
        return sorted(list(parsed))

    @staticmethod
    def resolve_city_and_station(
        db: Session,
        city_name: str,
        station_id: int | None = None,
    ) -> tuple[City, MonitoringStation | None]:
        """Validate and resolve City and optional MonitoringStation entities."""
        city_stmt = select(City).where(City.name.ilike(city_name.strip()))
        city = db.execute(city_stmt).scalar_one_or_none()
        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City '{city_name}' not found. Please provide a supported city.",
            )

        station = None
        if station_id is not None:
            station_stmt = select(MonitoringStation).where(
                MonitoringStation.id == station_id,
                MonitoringStation.city_id == city.id,
            )
            station = db.execute(station_stmt).scalar_one_or_none()
            if not station:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Monitoring station with ID {station_id} not found in city '{city_name}'."
                    ),
                )

        return city, station
