"""Validation utilities for historical queries, intervals, dates, and entities."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.city import City
from app.models.monitoring_station import MonitoringStation

VALID_POLLUTANTS: set[str] = {
    "PM2.5",
    "PM10",
    "NO2",
    "SO2",
    "CO",
    "O3",
    "NH3",
    "PB",
}

VALID_INTERVALS: set[str] = {
    "hourly",
    "daily",
    "weekly",
    "monthly",
}

MAX_RAW_QUERY_DAYS = 366
MAX_AGGREGATED_QUERY_DAYS = 1825  # 5 years


class HistoryValidator:
    """Validates inputs, date boundaries, pollutant codes, and resolves location entities."""

    @staticmethod
    def ensure_utc(dt: datetime | None) -> datetime | None:
        """Normalize datetime to UTC timezone."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @classmethod
    def validate_date_range(
        cls,
        start_date: datetime | None,
        end_date: datetime | None,
        is_aggregated: bool = False,
    ) -> tuple[datetime | None, datetime | None]:
        """Validate start and end dates, ensuring valid chronological ordering and range limits."""
        start_utc = cls.ensure_utc(start_date)
        end_utc = cls.ensure_utc(end_date)

        if start_utc and end_utc:
            if start_utc > end_utc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"start_date ({start_utc.isoformat()}) cannot "
                        f"be after end_date ({end_utc.isoformat()})."
                    ),
                )

            max_days = MAX_AGGREGATED_QUERY_DAYS if is_aggregated else MAX_RAW_QUERY_DAYS
            span_days = (end_utc - start_utc).total_seconds() / 86400.0
            if span_days > max_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Requested date range exceeds maximum allowed limit "
                        f"of {max_days} days (requested {span_days:.1f} days)."
                    ),
                )

        return start_utc, end_utc

    @classmethod
    def validate_interval(cls, interval: str | None) -> str | None:
        """Validate aggregation interval string."""
        if not interval:
            return None
        interval_norm = interval.lower().strip()
        if interval_norm not in VALID_INTERVALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported interval '{interval}'. Supported "
                    f"intervals: {sorted(list(VALID_INTERVALS))}."
                ),
            )
        return interval_norm

    @classmethod
    def validate_pollutant_code(cls, code: str | None) -> str | None:
        """Validate and normalize pollutant code."""
        if not code:
            return None
        normalized = code.strip().upper()
        # Handle Pb case
        if normalized == "PB":
            canon = "Pb"
        else:
            canon = normalized

        if canon.upper() not in VALID_POLLUTANTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid pollutant code '{code}'. Supported criteria "
                    f"pollutants: {sorted(list(VALID_POLLUTANTS))}."
                ),
            )
        return canon

    @staticmethod
    def validate_pagination(page: int, page_size: int) -> tuple[int, int]:
        """Validate pagination parameters."""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1.",
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100.",
            )
        return page, page_size

    @staticmethod
    def resolve_city(db: Session, city_name: str | None) -> City | None:
        """Find City entity by case-insensitive name, raising 404 if name provided but not found."""
        if not city_name:
            return None
        stmt = select(City).where(City.name.ilike(city_name.strip()))
        city = db.execute(stmt).scalar_one_or_none()
        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City '{city_name}' is not found in the supported cities database.",
            )
        return city

    @staticmethod
    def resolve_station(db: Session, station_id: int | None) -> MonitoringStation | None:
        """Find MonitoringStation entity, raising 404 if station_id provided but not found."""
        if station_id is None:
            return None
        station = db.get(MonitoringStation, station_id)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitoring station with ID {station_id} is not found.",
            )
        return station

    @classmethod
    def validate_comparison_targets(
        cls,
        cities: list[str] | None,
        stations: list[int] | None,
    ) -> tuple[list[str], list[int]]:
        """Validate that comparison request contains between 2 and 10 distinct targets."""
        parsed_cities: list[str] = []
        if cities:
            for item in cities:
                if "," in item:
                    parsed_cities.extend([c.strip() for c in item.split(",") if c.strip()])
                elif item.strip():
                    parsed_cities.append(item.strip())

        parsed_stations: list[int] = []
        if stations:
            for s in stations:
                if isinstance(s, str) and "," in s:
                    for sub in s.split(","):
                        if sub.strip().isdigit():
                            parsed_stations.append(int(sub.strip()))
                elif isinstance(s, int):
                    parsed_stations.append(s)

        total_targets = len(parsed_cities) + len(parsed_stations)
        if total_targets < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Comparison requires at least 2 locations (provided {total_targets}).",
            )
        if total_targets > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Comparison supports a maximum of 10 locations (provided {total_targets}).",
            )

        return parsed_cities, parsed_stations
