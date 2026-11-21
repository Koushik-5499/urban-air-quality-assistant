"""SQLAlchemy model for environmental monitoring stations."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.aqi_reading import AQIReading
    from app.models.city import City
    from app.models.pollutant_reading import PollutantReading


class MonitoringStation(Base):
    """Monitoring station located in a city."""

    __tablename__ = "monitoring_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    external_station_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[str] = mapped_column(String(100), default="CPCB", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    city: Mapped["City"] = relationship("City", back_populates="stations")
    pollutant_readings: Mapped[list["PollutantReading"]] = relationship(
        "PollutantReading",
        back_populates="station",
    )
    aqi_readings: Mapped[list["AQIReading"]] = relationship(
        "AQIReading",
        back_populates="station",
    )

