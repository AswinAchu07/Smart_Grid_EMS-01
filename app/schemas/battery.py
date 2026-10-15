"""Battery hardware configuration and live status Pydantic schemas.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BatteryConfigBase(BaseModel):
    name: str = Field(default="Standard 10kWh Li-ion", description="Battery profile name")
    capacity_kwh: float = Field(default=10.0, gt=0, description="Total storage capacity in kWh")
    initial_soc: float = Field(default=0.50, ge=0.0, le=1.0, description="Initial SOC fraction")
    min_soc: float = Field(default=0.15, ge=0.0, le=1.0, description="Minimum allowable SOC fraction")
    max_soc: float = Field(default=0.95, ge=0.0, le=1.0, description="Maximum allowable SOC fraction")
    max_charge_power_kw: float = Field(default=5.0, gt=0, description="Max charging power rating in kW")
    max_discharge_power_kw: float = Field(default=5.0, gt=0, description="Max discharging power rating in kW")
    charge_efficiency: float = Field(default=0.95, ge=0.5, le=1.0, description="Charging roundtrip sub-efficiency")
    discharge_efficiency: float = Field(default=0.95, ge=0.5, le=1.0, description="Discharging roundtrip sub-efficiency")


class BatteryConfigCreate(BatteryConfigBase):
    pass


class BatteryConfigUpdate(BaseModel):
    name: Optional[str] = None
    capacity_kwh: Optional[float] = Field(default=None, gt=0)
    initial_soc: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    min_soc: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_soc: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_charge_power_kw: Optional[float] = Field(default=None, gt=0)
    max_discharge_power_kw: Optional[float] = Field(default=None, gt=0)
    charge_efficiency: Optional[float] = Field(default=None, ge=0.5, le=1.0)
    discharge_efficiency: Optional[float] = Field(default=None, ge=0.5, le=1.0)


class BatteryConfigResponse(BatteryConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    is_active: bool
    created_at: datetime


class BatteryStatusResponse(BaseModel):
    """Real-time battery operational telemetry."""
    capacity_kwh: float
    soc: float
    soc_pct: float
    stored_energy_kwh: float
    min_soc: float
    max_soc: float
    max_charge_power_kw: float
    max_discharge_power_kw: float
    charge_efficiency: float
    discharge_efficiency: float
    total_charged_kwh: float
    total_discharged_kwh: float
    equivalent_cycles: float
    soh: float = 1.0
    soh_pct: float = 100.0
    effective_capacity_kwh: Optional[float] = None


class BatteryDegradationRequest(BaseModel):
    """Input payload to evaluate physics-informed battery degradation."""
    soc_trajectory: list[float] = Field(description="Sequential SOC trajectory values between 0 and 1")
    capacity_kwh: float = Field(default=10.0, gt=0, description="Nominal battery capacity in kWh")
    initial_soh: float = Field(default=1.0, ge=0.5, le=1.0, description="Initial State of Health (0.5 to 1.0)")
    dt_hours: float = Field(default=1.0, gt=0, description="Timestep duration in hours")
    temp_celsius: float = Field(default=25.0, ge=-20.0, le=60.0, description="Ambient operating temperature °C")


class BatteryDegradationResponse(BaseModel):
    """Comprehensive ASTM E1049-85 Rainflow & physics degradation assessment."""
    initial_soh: float
    final_soh: float
    final_soh_pct: float
    soh_loss_pct: float
    cyclic_damage: float
    calendar_damage: float
    total_damage: float
    cycle_count_half: int
    cycle_count_full: int
    equivalent_full_cycles: float
    economic_degradation_cost: float
    projected_rul_years: float
    dod_histogram: dict[str, float]
    mean_soc_pct: float
    duration_hours: float

