"""SQLAlchemy model for individual pollutant concentration readings."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.monitoring_station import MonitoringStation


class PollutantReading(Base):
    """Pollutant reading recorded at a station or city level."""

    __tablename__ = "pollutant_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("monitoring_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    pollutant_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    concentration: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="µg/m³", nullable=False)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(100), default="CPCB", nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    data_quality: Mapped[str] = mapped_column(String(50), default="valid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("concentration >= 0", name="ck_pollutant_concentration_non_negative"),
        Index("ix_pollutant_city_code_measured", "city_id", "pollutant_code", "measured_at"),
        Index("ix_pollutant_station_code_measured", "station_id", "pollutant_code", "measured_at"),
    )

    # Relationships
    city: Mapped["City"] = relationship("City", back_populates="pollutant_readings")
    station: Mapped[Optional["MonitoringStation"]] = relationship(
        "MonitoringStation",
        back_populates="pollutant_readings",
    )
