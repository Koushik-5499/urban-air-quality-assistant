"""City repository for database CRUD operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.city import City
from app.repositories.base import BaseRepository
from app.schemas.city import CityCreate, CityUpdate


class CityRepository(BaseRepository):
    """Repository handling database operations for City entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_id(self, city_id: int) -> City | None:
        """Retrieve a city by its primary key ID."""
        return self.db.get(City, city_id)

    def get_by_name_and_state(self, name: str, state: str) -> City | None:
        """Retrieve a city by its unique combination of name and state."""
        statement = select(City).where(City.name == name, City.state == state)
        return self.db.execute(statement).scalar_one_or_none()

    def list_cities(self, skip: int = 0, limit: int = 100) -> list[City]:
        """Retrieve all registered cities ordered by name."""
        statement = select(City).order_by(City.name).offset(skip).limit(limit)
        return list(self.db.execute(statement).scalars().all())

    def create(self, city_in: CityCreate) -> City:
        """Persist a new city record."""
        city = City(
            name=city_in.name,
            state=city_in.state,
            country=city_in.country,
            latitude=city_in.latitude,
            longitude=city_in.longitude,
        )
        self.db.add(city)
        self.db.commit()
        self.db.refresh(city)
        return city

    def update(self, city: City, city_in: CityUpdate) -> City:
        """Update fields of an existing city record."""
        update_data = city_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(city, field, value)
        self.db.commit()
        self.db.refresh(city)
        return city

    def health_check(self) -> bool:
        """Return True if the backing store is reachable."""
        return self._probe_db()
