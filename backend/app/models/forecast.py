"""SQLAlchemy models for Air Quality Forecasting runs, predictions, and evaluations."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ForecastRun(Base):
    """Tracks a single execution of model training and forecast generation."""

    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("monitoring_stations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    training_data_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_data_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evaluation_mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluation_rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluation_mape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    city: Mapped["City"] = relationship("City", backref="forecast_runs")  # noqa: F821
    station: Mapped[Optional["MonitoringStation"]] = relationship("MonitoringStation", backref="forecast_runs")  # noqa: F821
    forecasts: Mapped[List["AQIForecast"]] = relationship(
        "AQIForecast", back_populates="run", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["ForecastEvaluation"]] = relationship(
        "ForecastEvaluation", back_populates="run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ForecastRun(id={self.id}, city_id={self.city_id}, model={self.model_name}, status={self.status})>"
        )


class AQIForecast(Base):
    """Stores individual predicted AQI points with uncertainty intervals and horizon."""

    __tablename__ = "aqi_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id: Mapped[int] = mapped_column(
        ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("monitoring_stations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    forecast_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_aqi: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_category: Mapped[str] = mapped_column(String(50), nullable=False)
    dominant_pollutant: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lower_bound: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    upper_bound: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uncertainty_status: Mapped[str] = mapped_column(String(50), nullable=False, default="estimated")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    run: Mapped["ForecastRun"] = relationship("ForecastRun", back_populates="forecasts")
    city: Mapped["City"] = relationship("City")  # noqa: F821
    station: Mapped[Optional["MonitoringStation"]] = relationship("MonitoringStation")  # noqa: F821

    __table_args__ = (
        UniqueConstraint(
            "forecast_run_id",
            "city_id",
            "station_id",
            "forecast_timestamp",
            "horizon_hours",
            name="uq_forecast_run_point",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AQIForecast(id={self.id}, city_id={self.city_id}, horizon={self.horizon_hours}h, "
            f"predicted_aqi={self.predicted_aqi}, category={self.predicted_category})>"
        )


class ForecastEvaluation(Base):
    """Detailed evaluation metrics calculated per prediction horizon for a forecast run."""

    __tablename__ = "forecast_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id: Mapped[int] = mapped_column(
        ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mae: Mapped[float] = mapped_column(Float, nullable=False)
    rmse: Mapped[float] = mapped_column(Float, nullable=False)
    mape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    run: Mapped["ForecastRun"] = relationship("ForecastRun", back_populates="evaluations")

    __table_args__ = (
        UniqueConstraint(
            "forecast_run_id",
            "horizon_hours",
            name="uq_forecast_eval_horizon",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ForecastEvaluation(run_id={self.forecast_run_id}, horizon={self.horizon_hours}h, "
            f"MAE={self.mae:.2f}, RMSE={self.rmse:.2f})>"
        )

