"""Service coordinating full multi-day simulations and database persistence.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session

from app.core.constants import EMSStrategy
from app.battery.model import Battery
from app.data.pipeline import SmartGridDataPipeline
from app.simulation.engine import SimulationEngine, SimulationSummary
from app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    SimulationRecordSchema,
)
from app.db.models import SimulationRun, SimulationRecord, BatteryConfig, User


class SimulationService:
    """Orchestrates simulation execution, hardware configuration linking, and result serialization."""

    def __init__(self, data_path: str = "data/sample/smart_grid_data.csv"):
        self.data_path = data_path
        self.pipeline = SmartGridDataPipeline(data_path=data_path)

    def run_simulation(
        self,
        req: SimulationRequest,
        db: Optional[Session] = None,
        user: Optional[User] = None,
    ) -> SimulationResponse:
        """Run microgrid simulation according to requested parameters and persist to database."""
        # 1. Load dataset test slice
        raw_df = self.pipeline.get_or_create_raw_data()
        df_clean = self.pipeline.preprocessor.clean_and_normalize(raw_df)
        train_df, val_df, test_df = self.pipeline.preprocessor.chronological_split(df_clean)

        sim_df = test_df.iloc[: req.duration_hours].reset_index(drop=True)

        # 2. Configure battery
        battery = Battery()
        if req.battery_config_id and db:
            db_bat = db.query(BatteryConfig).filter(BatteryConfig.id == req.battery_config_id).first()
            if db_bat:
                battery = Battery(
                    capacity_kwh=db_bat.capacity_kwh,
                    initial_soc=req.initial_soc if req.initial_soc is not None else db_bat.initial_soc,
                    min_soc=db_bat.min_soc,
                    max_soc=db_bat.max_soc,
                    max_charge_power_kw=db_bat.max_charge_power_kw,
                    max_discharge_power_kw=db_bat.max_discharge_power_kw,
                    charge_efficiency=db_bat.charge_efficiency,
                    discharge_efficiency=db_bat.discharge_efficiency,
                )
        elif req.initial_soc is not None:
            battery.soc = req.initial_soc

        # 3. Execute Simulation Engine
        engine = SimulationEngine(battery=battery)
        if req.strategy == EMSStrategy.UNMANAGED:
            summary = engine.run_unmanaged(sim_df)
        elif req.strategy == EMSStrategy.RULE_BASED:
            summary = engine.run_rule_based(sim_df)
        else:
            summary = engine.run_optimization(sim_df)

        record_schemas = [
            SimulationRecordSchema(
                step=r["step"],
                timestamp=r["timestamp"],
                solar_kw=r["solar_kw"],
                load_kw=r["load_kw"],
                solar_to_load_kw=r["solar_to_load_kw"],
                solar_to_battery_kw=r["solar_to_battery_kw"],
                solar_to_grid_kw=r["solar_to_grid_kw"],
                battery_to_load_kw=r["battery_to_load_kw"],
                grid_import_kw=r["grid_import_kw"],
                grid_export_kw=r["grid_export_kw"],
                soc=r.get("soc", r.get("resulting_soc", 0.5)),
                price_per_kwh=r.get("price_per_kwh", 0.18),
                cost=r["cost"],
            )
            for r in summary.records
        ]

        db_id = None
        # 4. Persist to DB if requested
        if db and req.save_to_db:
            db_sim = SimulationRun(
                user_id=user.id if user else None,
                name=f"{req.strategy.value} Simulation ({req.duration_hours}h)",
                strategy=req.strategy.value,
                battery_config_id=req.battery_config_id,
                total_steps=summary.total_steps,
                total_cost=summary.total_cost,
                total_grid_import_kwh=summary.total_grid_import_kwh,
                total_grid_export_kwh=summary.total_grid_export_kwh,
                total_solar_kwh=summary.total_solar_kwh,
                total_load_kwh=summary.total_load_kwh,
                peak_grid_demand_kw=summary.peak_grid_demand_kw,
                solar_utilization_pct=summary.solar_self_consumption_pct,
                battery_utilization_pct=summary.battery_cycles,
                metrics_summary=summary.to_dict(),
            )
            db.add(db_sim)
            db.flush()

            for rec in record_schemas:
                rec_db = SimulationRecord(
                    simulation_id=db_sim.id,
                    step=rec.step,
                    timestamp=rec.timestamp,
                    solar_kw=rec.solar_kw,
                    load_kw=rec.load_kw,
                    solar_to_load_kw=rec.solar_to_load_kw,
                    solar_to_bat_kw=rec.solar_to_battery_kw,
                    solar_to_grid_kw=rec.solar_to_grid_kw,
                    bat_to_load_kw=rec.battery_to_load_kw,
                    grid_import_kw=rec.grid_import_kw,
                    grid_export_kw=rec.grid_export_kw,
                    soc=rec.soc,
                    price_per_kwh=rec.price_per_kwh,
                    cost=rec.cost,
                )
                db.add(rec_db)
            db.commit()
            db_id = db_sim.id

        return SimulationResponse(
            id=db_id,
            strategy=summary.strategy,
            total_steps=summary.total_steps,
            total_cost=summary.total_cost,
            total_solar_kwh=summary.total_solar_kwh,
            total_load_kwh=summary.total_load_kwh,
            total_grid_import_kwh=summary.total_grid_import_kwh,
            total_grid_export_kwh=summary.total_grid_export_kwh,
            net_grid_kwh=summary.net_grid_kwh,
            peak_grid_demand_kw=summary.peak_grid_demand_kw,
            solar_self_consumption_pct=summary.solar_self_consumption_pct,
            renewable_penetration_pct=summary.renewable_penetration_pct,
            battery_cycles=summary.battery_cycles,
            final_soc=summary.final_soc,
            records=record_schemas,
        )
