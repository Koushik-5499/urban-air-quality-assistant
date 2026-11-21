"""SQLAlchemy model for environmental air quality alerts."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.aqi_reading import AQIReading
    from app.models.monitoring_station import MonitoringStation


class Alert(Base):
    """Air quality notification and threshold alert."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    aqi_reading_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("aqi_readings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    station_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("monitoring_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    current_aqi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_aqi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    threshold_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aqi_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dominant_pollutant: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="CPCB", nullable=False)
    dedup_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    delivery_status: Mapped[str] = mapped_column(String(50), default="delivered", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_alerts_city_severity_created", "city_id", "severity", "created_at"),
    )

    # Relationships
    city: Mapped["City"] = relationship("City", back_populates="alerts")
    aqi_reading: Mapped[Optional["AQIReading"]] = relationship("AQIReading", back_populates="alerts")
    station: Mapped[Optional["MonitoringStation"]] = relationship("MonitoringStation")

