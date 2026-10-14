"""Service executing single-step EMS decisions and multi-period MILP optimizations.
"""

from typing import Dict, Any, List
from app.battery.model import Battery
from app.ems.rule_based import RuleBasedEMS
from app.optimization.lp_solver import OptimizationEMS
from app.services.battery_service import BatteryService
from app.schemas.ems import (
    EMSStepRequest,
    EMSStepResponse,
    OptimizationRequest,
    OptimizationResponse,
)


class EMSService:
    """Provides decision-making endpoints for single-step dispatch and multi-step optimization."""

    @staticmethod
    def get_single_step_decision(req: EMSStepRequest) -> EMSStepResponse:
        """Calculate immediate power flows using Rule-Based EMS."""
        live_bat = BatteryService.get_live_battery()
        # Create temporary battery with specified SOC to avoid mutating global state unexpectedly
        bat_copy = Battery(
            capacity_kwh=req.battery_capacity_kwh,
            initial_soc=req.current_soc,
            min_soc=live_bat.min_soc,
            max_soc=live_bat.max_soc,
            max_charge_power_kw=live_bat.max_charge_power_kw,
            max_discharge_power_kw=live_bat.max_discharge_power_kw,
            charge_efficiency=live_bat.charge_efficiency,
            discharge_efficiency=live_bat.discharge_efficiency,
        )

        dec = RuleBasedEMS.step(
            solar_kw=req.solar_kw,
            load_kw=req.load_kw,
            battery=bat_copy,
            import_price=req.import_price,
            export_price=req.export_price,
            dt_hours=req.dt_hours,
        )

        return EMSStepResponse(
            strategy="RULE_BASED",
            solar_kw=dec.solar_kw,
            load_kw=dec.load_kw,
            solar_to_load_kw=dec.solar_to_load_kw,
            solar_to_battery_kw=dec.solar_to_battery_kw,
            solar_to_grid_kw=dec.solar_to_grid_kw,
            battery_to_load_kw=dec.battery_to_load_kw,
            grid_import_kw=dec.grid_import_kw,
            grid_export_kw=dec.grid_export_kw,
            resulting_soc=dec.resulting_soc,
            cost=dec.cost,
            energy_balance_error=dec.energy_balance_error,
        )

    @classmethod
    def get_rule_based_decision(
        cls,
        solar_kw: float,
        load_kw: float,
        current_soc: float,
        battery_capacity: float = 10.0,
        import_price: float = 0.18,
        export_price: float = 0.08,
        dt_hours: float = 1.0,
    ) -> EMSStepResponse:
        """Convenience method for calculating single-step rule-based dispatch."""
        req = EMSStepRequest(
            solar_kw=solar_kw,
            load_kw=load_kw,
            current_soc=current_soc,
            battery_capacity_kwh=battery_capacity,
            import_price=import_price,
            export_price=export_price,
            dt_hours=dt_hours,
        )
        return cls.get_single_step_decision(req)

    @staticmethod
    def run_optimization(req: OptimizationRequest) -> OptimizationResponse:
        """Run MILP optimization solver over the requested time horizon."""
        live_bat = BatteryService.get_live_battery()
        temp_bat = Battery(
            capacity_kwh=req.battery_capacity_kwh,
            initial_soc=req.initial_soc,
            min_soc=live_bat.min_soc,
            max_soc=live_bat.max_soc,
            max_charge_power_kw=live_bat.max_charge_power_kw,
            max_discharge_power_kw=live_bat.max_discharge_power_kw,
            charge_efficiency=live_bat.charge_efficiency,
            discharge_efficiency=live_bat.discharge_efficiency,
        )

        res = OptimizationEMS.optimize_horizon(
            solar_forecast=req.solar_forecast,
            load_forecast=req.load_forecast,
            battery_initial=temp_bat,
            import_prices=req.import_prices,
            export_prices=req.export_prices,
            dt_hours=req.dt_hours,
        )

        decision_schemas = [
            EMSStepResponse(
                strategy="OPTIMIZATION",
                solar_kw=d.solar_kw,
                load_kw=d.load_kw,
                solar_to_load_kw=d.solar_to_load_kw,
                solar_to_battery_kw=d.solar_to_battery_kw,
                solar_to_grid_kw=d.solar_to_grid_kw,
                battery_to_load_kw=d.battery_to_load_kw,
                grid_import_kw=d.grid_import_kw,
                grid_export_kw=d.grid_export_kw,
                resulting_soc=d.resulting_soc,
                cost=d.cost,
                energy_balance_error=d.energy_balance_error,
            )
            for d in res.decisions
        ]

        return OptimizationResponse(
            status=res.status,
            is_feasible=res.is_feasible,
            total_cost=res.total_cost,
            decisions=decision_schemas,
            soc_trajectory=res.soc_trajectory,
            solver_message=res.solver_message,
        )
