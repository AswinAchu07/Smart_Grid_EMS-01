"""SQLAlchemy ORM models for Users, BatteryConfigs, Forecasts, and Simulations.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.constants import UserRole, EMSStrategy, TargetType, ForecastingModelType


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """User account model supporting Role-Based Access Control (RBAC)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.VIEWER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    battery_configs: Mapped[List["BatteryConfig"]] = relationship("BatteryConfig", back_populates="user", cascade="all, delete-orphan")
    forecast_runs: Mapped[List["ForecastRun"]] = relationship("ForecastRun", back_populates="user", cascade="all, delete-orphan")
    simulation_runs: Mapped[List["SimulationRun"]] = relationship("SimulationRun", back_populates="user", cascade="all, delete-orphan")


class BatteryConfig(Base):
    """Configurable Battery Storage Parameters."""
    __tablename__ = "battery_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), default="Default 10kWh Li-ion", nullable=False)
    capacity_kwh: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    initial_soc: Mapped[float] = mapped_column(Float, default=0.50, nullable=False)
    min_soc: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    max_soc: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    max_charge_power_kw: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    max_discharge_power_kw: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    charge_efficiency: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    discharge_efficiency: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="battery_configs")
    simulations: Mapped[List["SimulationRun"]] = relationship("SimulationRun", back_populates="battery_config")


class ForecastRun(Base):
    """Metadata and summary statistics for a solar or load ML forecasting job."""
    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "solar" or "load"
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    r2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="forecast_runs")
    data_points: Mapped[List["ForecastDataPoint"]] = relationship("ForecastDataPoint", back_populates="forecast_run", cascade="all, delete-orphan")


class ForecastDataPoint(Base):
    """Individual predicted vs actual telemetry points for forecasting."""
    __tablename__ = "forecast_data_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    forecast_id: Mapped[int] = mapped_column(Integer, ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    forecast_run: Mapped["ForecastRun"] = relationship("ForecastRun", back_populates="data_points")


class SimulationRun(Base):
    """Full time-horizon simulation run record."""
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(150), default="EMS Simulation Run", nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)  # "RULE_BASED" or "OPTIMIZATION"
    battery_config_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("battery_configs.id", ondelete="SET NULL"), nullable=True)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_grid_import_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_grid_export_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_solar_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_load_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    peak_grid_demand_kw: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    solar_utilization_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    battery_utilization_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metrics_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="simulation_runs")
    battery_config: Mapped[Optional["BatteryConfig"]] = relationship("BatteryConfig", back_populates="simulations")
    records: Mapped[List["SimulationRecord"]] = relationship("SimulationRecord", back_populates="simulation_run", cascade="all, delete-orphan")


class SimulationRecord(Base):
    """Granular timestep-by-timestep power balance telemetry."""
    __tablename__ = "simulation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    simulation_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(50), nullable=False)
    solar_kw: Mapped[float] = mapped_column(Float, nullable=False)
    load_kw: Mapped[float] = mapped_column(Float, nullable=False)
    solar_to_load_kw: Mapped[float] = mapped_column(Float, nullable=False)
    solar_to_bat_kw: Mapped[float] = mapped_column(Float, nullable=False)
    solar_to_grid_kw: Mapped[float] = mapped_column(Float, nullable=False)
    bat_to_load_kw: Mapped[float] = mapped_column(Float, nullable=False)
    grid_import_kw: Mapped[float] = mapped_column(Float, nullable=False)
    grid_export_kw: Mapped[float] = mapped_column(Float, nullable=False)
    soc: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    simulation_run: Mapped["SimulationRun"] = relationship("SimulationRun", back_populates="records")
