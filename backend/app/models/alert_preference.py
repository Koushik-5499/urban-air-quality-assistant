"""SQLAlchemy model for user alert preferences."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.monitoring_station import MonitoringStation


class AlertPreference(Base):
    """User preferences for air quality notifications and alerts."""

    __tablename__ = "alert_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), default="default_user", nullable=False, index=True)
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    station_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("monitoring_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    min_aqi_threshold: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    min_severity: Mapped[str] = mapped_column(String(50), default="Moderate", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    channels: Mapped[str] = mapped_column(String(200), default="in_app", nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # e.g. "22:00"
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)    # e.g. "07:00"
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
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
        UniqueConstraint("user_id", "city_id", name="uq_user_city_preference"),
    )

    # Relationships
    city: Mapped["City"] = relationship("City")
    station: Mapped[Optional["MonitoringStation"]] = relationship("MonitoringStation")

