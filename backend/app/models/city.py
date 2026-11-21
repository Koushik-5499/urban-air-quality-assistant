"""SQLAlchemy model for Indian Cities."""

from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.monitoring_station import MonitoringStation
    from app.models.pollutant_reading import PollutantReading
    from app.models.aqi_reading import AQIReading
    from app.models.alert import Alert


class City(Base):
    """City entity representing monitored urban areas."""

    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("name", "state", name="uq_city_name_state"),
        Index("ix_city_name_state", "name", "state"),
    )

    # Relationships
    stations: Mapped[List["MonitoringStation"]] = relationship(
        "MonitoringStation",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    pollutant_readings: Mapped[List["PollutantReading"]] = relationship(
        "PollutantReading",
        back_populates="city",
    )
    aqi_readings: Mapped[List["AQIReading"]] = relationship(
        "AQIReading",
        back_populates="city",
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="city",
    )

