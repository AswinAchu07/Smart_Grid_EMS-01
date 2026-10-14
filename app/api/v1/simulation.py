"""Microgrid simulation execution and historical record endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import SimulationRun, User
from app.api.deps import get_current_user_optional
from app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    SimulationRecordSchema,
)
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])
simulation_service = SimulationService()


@router.post("/run", response_model=SimulationResponse)
def run_simulation(
    req: SimulationRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Run chronological multi-period simulation across specified duration and EMS strategy."""
    return simulation_service.run_simulation(req=req, db=db, user=user)


@router.get("/{simulation_id}", response_model=SimulationResponse)
def get_simulation_run(
    simulation_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full results and granular telemetry records for a stored simulation."""
    sim = db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation with ID {simulation_id} not found.",
        )

    records = [
        SimulationRecordSchema(
            step=r.step,
            timestamp=r.timestamp,
            solar_kw=r.solar_kw,
            load_kw=r.load_kw,
            solar_to_load_kw=r.solar_to_load_kw,
            solar_to_battery_kw=r.solar_to_bat_kw,
            solar_to_grid_kw=r.solar_to_grid_kw,
            battery_to_load_kw=r.bat_to_load_kw,
            grid_import_kw=r.grid_import_kw,
            grid_export_kw=r.grid_export_kw,
            soc=r.soc,
            price_per_kwh=r.price_per_kwh,
            cost=r.cost,
        )
        for r in sim.records
    ]

    return SimulationResponse(
        id=sim.id,
        strategy=sim.strategy,
        total_steps=sim.total_steps,
        total_cost=sim.total_cost,
        total_solar_kwh=sim.total_solar_kwh,
        total_load_kwh=sim.total_load_kwh,
        total_grid_import_kwh=sim.total_grid_import_kwh,
        total_grid_export_kwh=sim.total_grid_export_kwh,
        net_grid_kwh=sim.total_grid_import_kwh - sim.total_grid_export_kwh,
        peak_grid_demand_kw=sim.peak_grid_demand_kw,
        solar_self_consumption_pct=sim.solar_utilization_pct,
        renewable_penetration_pct=sim.metrics_summary.get("renewable_penetration_pct", 0.0) if sim.metrics_summary else 0.0,
        battery_cycles=sim.battery_utilization_pct,
        final_soc=records[-1].soc if records else 0.5,
        records=records,
    )
