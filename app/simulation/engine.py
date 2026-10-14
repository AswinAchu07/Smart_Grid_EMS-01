"""Chronological simulation engine executing multi-period energy management.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np

from app.battery.model import Battery
from app.ems.rule_based import RuleBasedEMS, EMSDispatchDecision
from app.optimization.lp_solver import OptimizationEMS
from app.core.constants import EMSStrategy


@dataclass
class SimulationSummary:
    """Consolidated results of a multi-period simulation run."""
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
    records: List[Dict[str, Any]]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "total_steps": self.total_steps,
            "total_cost": round(self.total_cost, 2),
            "total_solar_kwh": round(self.total_solar_kwh, 2),
            "total_load_kwh": round(self.total_load_kwh, 2),
            "total_grid_import_kwh": round(self.total_grid_import_kwh, 2),
            "total_grid_export_kwh": round(self.total_grid_export_kwh, 2),
            "net_grid_kwh": round(self.net_grid_kwh, 2),
            "peak_grid_demand_kw": round(self.peak_grid_demand_kw, 2),
            "solar_self_consumption_pct": round(self.solar_self_consumption_pct, 2),
            "renewable_penetration_pct": round(self.renewable_penetration_pct, 2),
            "battery_cycles": round(self.battery_cycles, 2),
            "final_soc": round(self.final_soc, 4),
            "metrics": self.metrics,
        }


class SimulationEngine:
    """Executes time-series microgrid energy simulation under various EMS control strategies."""

    def __init__(self, battery: Optional[Battery] = None):
        self.battery = battery or Battery()

    def run_unmanaged(
        self,
        df: pd.DataFrame,
        dt_hours: float = 1.0,
    ) -> SimulationSummary:
        """Baseline with NO battery storage. Solar directly supplies load, surplus exported, deficit imported."""
        records = []
        total_cost = 0.0
        total_solar = 0.0
        total_load = 0.0
        total_import = 0.0
        total_export = 0.0
        peak_demand = 0.0

        for i, row in df.iterrows():
            ts_str = str(row.get("timestamp", f"Step_{i}"))
            solar = max(0.0, float(row["solar_power_kw"]))
            load = max(0.0, float(row["load_power_kw"]))
            p_imp = float(row.get("grid_import_price", 0.18))
            p_exp = float(row.get("grid_export_price", 0.08))

            if solar >= load:
                s_to_load = load
                s_to_grid = solar - load
                g_imp = 0.0
                g_exp = s_to_grid
            else:
                s_to_load = solar
                s_to_grid = 0.0
                g_imp = load - solar
                g_exp = 0.0

            step_cost = (g_imp * p_imp - g_exp * p_exp) * dt_hours
            total_cost += step_cost
            total_solar += solar * dt_hours
            total_load += load * dt_hours
            total_import += g_imp * dt_hours
            total_export += g_exp * dt_hours
            peak_demand = max(peak_demand, g_imp)

            records.append({
                "step": int(i),
                "timestamp": ts_str,
                "solar_kw": round(solar, 3),
                "load_kw": round(load, 3),
                "solar_to_load_kw": round(s_to_load, 3),
                "solar_to_battery_kw": 0.0,
                "solar_to_grid_kw": round(s_to_grid, 3),
                "battery_to_load_kw": 0.0,
                "grid_import_kw": round(g_imp, 3),
                "grid_export_kw": round(g_exp, 3),
                "soc": round(self.battery.soc, 4),
                "price_per_kwh": round(p_imp, 4),
                "cost": round(step_cost, 4),
                "balance_error": 0.0,
            })

        self_consumption = (
            ((total_solar - total_export) / total_solar * 100.0) if total_solar > 0 else 0.0
        )
        ren_penetration = (
            ((total_load - total_import) / total_load * 100.0) if total_load > 0 else 0.0
        )

        return SimulationSummary(
            strategy=EMSStrategy.UNMANAGED.value,
            total_steps=len(records),
            total_cost=total_cost,
            total_solar_kwh=total_solar,
            total_load_kwh=total_load,
            total_grid_import_kwh=total_import,
            total_grid_export_kwh=total_export,
            net_grid_kwh=total_import - total_export,
            peak_grid_demand_kw=peak_demand,
            solar_self_consumption_pct=self_consumption,
            renewable_penetration_pct=ren_penetration,
            battery_cycles=0.0,
            final_soc=self.battery.soc,
            records=records,
            metrics={},
        )

    def run_rule_based(
        self,
        df: pd.DataFrame,
        dt_hours: float = 1.0,
    ) -> SimulationSummary:
        """Execute simulation using deterministic Rule-Based EMS."""
        records = []
        total_cost = 0.0
        total_solar = 0.0
        total_load = 0.0
        total_import = 0.0
        total_export = 0.0
        peak_demand = 0.0

        for i, row in df.iterrows():
            ts_str = str(row.get("timestamp", f"Step_{i}"))
            solar = max(0.0, float(row["solar_power_kw"]))
            load = max(0.0, float(row["load_power_kw"]))
            p_imp = float(row.get("grid_import_price", 0.18))
            p_exp = float(row.get("grid_export_price", 0.08))

            dec = RuleBasedEMS.step(
                solar_kw=solar,
                load_kw=load,
                battery=self.battery,
                import_price=p_imp,
                export_price=p_exp,
                dt_hours=dt_hours,
            )

            total_cost += dec.cost
            total_solar += solar * dt_hours
            total_load += load * dt_hours
            total_import += dec.grid_import_kw * dt_hours
            total_export += dec.grid_export_kw * dt_hours
            peak_demand = max(peak_demand, dec.grid_import_kw)

            rec = dec.to_dict()
            rec["step"] = int(i)
            rec["timestamp"] = ts_str
            rec["price_per_kwh"] = round(p_imp, 4)
            records.append(rec)

        self_consumption = (
            ((total_solar - total_export) / total_solar * 100.0) if total_solar > 0 else 0.0
        )
        ren_penetration = (
            ((total_load - total_import) / total_load * 100.0) if total_load > 0 else 0.0
        )
        cycles = self.battery.total_discharged_kwh / max(1.0, self.battery.capacity_kwh)

        return SimulationSummary(
            strategy=EMSStrategy.RULE_BASED.value,
            total_steps=len(records),
            total_cost=total_cost,
            total_solar_kwh=total_solar,
            total_load_kwh=total_load,
            total_grid_import_kwh=total_import,
            total_grid_export_kwh=total_export,
            net_grid_kwh=total_import - total_export,
            peak_grid_demand_kw=peak_demand,
            solar_self_consumption_pct=self_consumption,
            renewable_penetration_pct=ren_penetration,
            battery_cycles=cycles,
            final_soc=self.battery.soc,
            records=records,
            metrics={},
        )

    def run_optimization(
        self,
        df: pd.DataFrame,
        dt_hours: float = 1.0,
        horizon_chunk: int = 24,
    ) -> SimulationSummary:
        """Execute simulation using Optimization EMS in day-ahead chunks."""
        records = []
        total_cost = 0.0
        total_solar = 0.0
        total_load = 0.0
        total_import = 0.0
        total_export = 0.0
        peak_demand = 0.0

        n = len(df)
        for start_idx in range(0, n, horizon_chunk):
            end_idx = min(start_idx + horizon_chunk, n)
            chunk_df = df.iloc[start_idx:end_idx].reset_index(drop=True)

            solar_list = [max(0.0, float(v)) for v in chunk_df["solar_power_kw"].values]
            load_list = [max(0.0, float(v)) for v in chunk_df["load_power_kw"].values]
            p_imp_list = [float(v) for v in chunk_df.get("grid_import_price", pd.Series([0.18]*len(chunk_df))).values]
            p_exp_list = [float(v) for v in chunk_df.get("grid_export_price", pd.Series([0.08]*len(chunk_df))).values]

            opt_res = OptimizationEMS.optimize_horizon(
                solar_forecast=solar_list,
                load_forecast=load_forecast if (load_forecast := load_list) else load_list,
                battery_initial=self.battery,
                import_prices=p_imp_list,
                export_prices=p_exp_list,
                dt_hours=dt_hours,
            )

            for step_offset, dec in enumerate(opt_res.decisions):
                global_idx = start_idx + step_offset
                ts_str = str(chunk_df.loc[step_offset, "timestamp"]) if "timestamp" in chunk_df.columns else f"Step_{global_idx}"

                # Update live battery state
                # Charge power: solar_to_battery + grid_to_battery (approx)
                ch_pwr = dec.solar_to_battery_kw
                dis_pwr = dec.battery_to_load_kw
                self.battery.step(charge_kw=ch_pwr, discharge_kw=dis_pwr, dt_hours=dt_hours)

                total_cost += dec.cost
                total_solar += dec.solar_kw * dt_hours
                total_load += dec.load_kw * dt_hours
                total_import += dec.grid_import_kw * dt_hours
                total_export += dec.grid_export_kw * dt_hours
                peak_demand = max(peak_demand, dec.grid_import_kw)

                rec = dec.to_dict()
                rec["step"] = global_idx
                rec["timestamp"] = ts_str
                rec["price_per_kwh"] = round(p_imp_list[step_offset], 4)
                records.append(rec)

        self_consumption = (
            ((total_solar - total_export) / total_solar * 100.0) if total_solar > 0 else 0.0
        )
        ren_penetration = (
            ((total_load - total_import) / total_load * 100.0) if total_load > 0 else 0.0
        )
        cycles = self.battery.total_discharged_kwh / max(1.0, self.battery.capacity_kwh)

        return SimulationSummary(
            strategy=EMSStrategy.OPTIMIZATION.value,
            total_steps=len(records),
            total_cost=total_cost,
            total_solar_kwh=total_solar,
            total_load_kwh=total_load,
            total_grid_import_kwh=total_import,
            total_grid_export_kwh=total_export,
            net_grid_kwh=total_import - total_export,
            peak_grid_demand_kw=peak_demand,
            solar_self_consumption_pct=self_consumption,
            renewable_penetration_pct=ren_penetration,
            battery_cycles=cycles,
            final_soc=self.battery.soc,
            records=records,
            metrics={},
        )
