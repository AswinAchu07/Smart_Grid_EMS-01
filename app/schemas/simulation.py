"""Simulation execution and result recording Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import EMSStrategy


class SimulationRequest(BaseModel):
    """Payload to trigger a multi-day microgrid simulation."""
    strategy: EMSStrategy = Field(default=EMSStrategy.OPTIMIZATION, description="EMS Strategy")
    duration_hours: int = Field(default=168, ge=24, le=8760, description="Simulation duration in hours (e.g. 168 = 7 days)")
    battery_config_id: Optional[int] = Field(default=None, description="Optional custom battery config ID")
    initial_soc: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    save_to_db: bool = Field(default=True, description="Whether to persist simulation records to the database")


class SimulationRecordSchema(BaseModel):
    step: int
    timestamp: str
    solar_kw: float
    load_kw: float
    solar_to_load_kw: float
    solar_to_battery_kw: float
    solar_to_grid_kw: float
    battery_to_load_kw: float
    grid_import_kw: float
    grid_export_kw: float
    soc: float
    price_per_kwh: float
    cost: float


class SimulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    strategy: str
    total_steps: int
    total_cost: float
    total_solar_kwh: float
    total_load_kwh: float
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    net_grid_kwh: float
    peak_grid_demand_kw: float
    solar_self_consumption_pct: float
    renewable_penetration_pct: float
    battery_cycles: float
    final_soc: float
    records: List[SimulationRecordSchema]
