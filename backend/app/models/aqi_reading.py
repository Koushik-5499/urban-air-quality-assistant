"""SQLAlchemy model for Air Quality Index (AQI) composite readings."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.city import City
    from app.models.monitoring_station import MonitoringStation


class AQIReading(Base):
    """Composite Air Quality Index reading."""

    __tablename__ = "aqi_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    station_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("monitoring_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    aqi_value: Mapped[int] = mapped_column(Integer, nullable=False)
    aqi_category: Mapped[str] = mapped_column(String(50), nullable=False)
    dominant_pollutant: Mapped[str | None] = mapped_column(String(20), nullable=True)
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
        CheckConstraint("aqi_value >= 0", name="ck_aqi_value_non_negative"),
        Index("ix_aqi_city_measured", "city_id", "measured_at"),
        Index("ix_aqi_station_measured", "station_id", "measured_at"),
    )

    # Relationships
    city: Mapped["City"] = relationship("City", back_populates="aqi_readings")
    station: Mapped[Optional["MonitoringStation"]] = relationship(
        "MonitoringStation",
        back_populates="aqi_readings",
    )
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="aqi_reading")
