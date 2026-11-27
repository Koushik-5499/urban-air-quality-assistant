"""Repeatable seed utility for Indian cities."""

import sys
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories.city_repository import CityRepository
from app.schemas.city import CityCreate

logger = get_logger("app.db.seed")

# The 10 officially supported Indian cities with approximate coordinates
SUPPORTED_CITIES: list[dict[str, Any]] = [
    {
        "name": "Coimbatore",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 11.0168,
        "longitude": 76.9558,
    },
    {
        "name": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 13.0827,
        "longitude": 80.2707,
    },
    {
        "name": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
    },
    {
        "name": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "latitude": 17.3850,
        "longitude": 78.4867,
    },
    {
        "name": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 19.0760,
        "longitude": 72.8777,
    },
    {
        "name": "Delhi",
        "state": "Delhi",
        "country": "India",
        "latitude": 28.6139,
        "longitude": 77.2090,
    },
    {
        "name": "Kochi",
        "state": "Kerala",
        "country": "India",
        "latitude": 9.9312,
        "longitude": 76.2673,
    },
    {
        "name": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 18.5204,
        "longitude": 73.8567,
    },
    {
        "name": "Kolkata",
        "state": "West Bengal",
        "country": "India",
        "latitude": 22.5726,
        "longitude": 88.3639,
    },
    {
        "name": "Thoothukudi",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 8.7642,
        "longitude": 78.1348,
    },
]


def seed_cities(db: Session) -> dict[str, int]:
    """Idempotently seed the ten supported Indian cities.

    Checks for existing records by (name, state) pair before inserting.
    Never overwrites or duplicates existing data.
    """
    repo = CityRepository(db)
    inserted = 0
    existing = 0

    for city_data in SUPPORTED_CITIES:
        c_name = str(city_data["name"])
        c_state = str(city_data["state"])
        found = repo.get_by_name_and_state(name=c_name, state=c_state)
        if found:
            existing += 1
        else:
            repo.create(
                CityCreate(
                    name=c_name,
                    state=c_state,
                    country=str(city_data["country"]),
                    latitude=float(city_data["latitude"]),
                    longitude=float(city_data["longitude"]),
                )
            )
            inserted += 1

    return {
        "inserted": inserted,
        "existing": existing,
        "total": len(SUPPORTED_CITIES),
    }


def main() -> None:
    """CLI execution entrypoint for python -m app.db.seed."""
    db = SessionLocal()
    try:
        results = seed_cities(db)
        logger.info(
            "City seeding completed: %s inserted, %s already existed (Total: %s).",
            results["inserted"],
            results["existing"],
            results["total"],
        )
    except SQLAlchemyError as exc:
        logger.error("Database error seeding cities: %s", exc)
        sys.exit(1)
    except Exception as exc:
        # Top-level CLI boundary catch for unexpected runtime crashes
        logger.exception("Unexpected error seeding cities: %s", exc)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
