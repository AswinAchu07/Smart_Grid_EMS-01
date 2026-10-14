"""Energy Management System (EMS) decision and optimization Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.constants import EMSStrategy


class EMSStepRequest(BaseModel):
    """Input parameters for a single-step EMS decision."""
    solar_kw: float = Field(..., ge=0.0, description="Current solar PV generation in kW")
    load_kw: float = Field(..., ge=0.0, description="Current electrical demand in kW")
    current_soc: float = Field(default=0.5, ge=0.0, le=1.0, description="Current battery SOC fraction")
    import_price: float = Field(default=0.18, ge=0.0, description="Grid import price ($/kWh)")
    export_price: float = Field(default=0.08, ge=0.0, description="Grid export feed-in price ($/kWh)")
    dt_hours: float = Field(default=1.0, gt=0.0, description="Timestep interval in hours")
    battery_capacity_kwh: float = Field(default=10.0, gt=0.0)


class EMSStepResponse(BaseModel):
    """Output energy flows for a single-step EMS decision."""
    strategy: str = EMSStrategy.RULE_BASED.value
    solar_kw: float
    load_kw: float
    solar_to_load_kw: float
    solar_to_battery_kw: float
    solar_to_grid_kw: float
    battery_to_load_kw: float
    grid_import_kw: float
    grid_export_kw: float
    resulting_soc: float
    cost: float
    energy_balance_error: float


class OptimizationRequest(BaseModel):
    """Payload to trigger multi-period MILP optimal dispatch."""
    solar_forecast: List[float] = Field(..., min_length=1, description="Hourly solar generation profile (kW)")
    load_forecast: List[float] = Field(..., min_length=1, description="Hourly electricity load profile (kW)")
    initial_soc: float = Field(default=0.50, ge=0.0, le=1.0)
    battery_capacity_kwh: float = Field(default=10.0, gt=0.0)
    import_prices: Optional[List[float]] = None
    export_prices: Optional[List[float]] = None
    dt_hours: float = Field(default=1.0, gt=0.0)


class OptimizationResponse(BaseModel):
    """Optimal schedule across the entire requested horizon."""
    status: str
    is_feasible: bool
    total_cost: float
    decisions: List[EMSStepResponse]
    soc_trajectory: List[float]
    solver_message: str
