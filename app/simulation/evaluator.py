"""Comparative performance evaluation and financial KPI calculator for microgrid EMS.
"""

from typing import Dict, Any, List
import pandas as pd
from app.simulation.engine import SimulationSummary


class PerformanceEvaluator:
    """Computes technical, energetic, and economic KPIs comparing baseline vs optimized EMS."""

    @staticmethod
    def compare_strategies(
        unmanaged: SimulationSummary,
        rule_based: SimulationSummary,
        optimized: SimulationSummary,
    ) -> Dict[str, Any]:
        """Compute relative percentage improvements and absolute savings across all 3 strategies."""
        unmanaged_cost = unmanaged.total_cost
        rb_cost = rule_based.total_cost
        opt_cost = optimized.total_cost

        # Financial savings
        savings_rb_vs_unm_usd = unmanaged_cost - rb_cost
        savings_rb_vs_unm_pct = (savings_rb_vs_unm_usd / unmanaged_cost * 100.0) if unmanaged_cost > 0 else 0.0

        savings_opt_vs_unm_usd = unmanaged_cost - opt_cost
        savings_opt_vs_unm_pct = (savings_opt_vs_unm_usd / unmanaged_cost * 100.0) if unmanaged_cost > 0 else 0.0

        savings_opt_vs_rb_usd = rb_cost - opt_cost
        savings_opt_vs_rb_pct = (savings_opt_vs_rb_usd / rb_cost * 100.0) if rb_cost > 0 else 0.0

        # Peak demand reduction
        peak_unm = unmanaged.peak_grid_demand_kw
        peak_rb = rule_based.peak_grid_demand_kw
        peak_opt = optimized.peak_grid_demand_kw
        peak_reduction_pct = ((peak_unm - peak_opt) / peak_unm * 100.0) if peak_unm > 0 else 0.0

        comparison_table = [
            {
                "Strategy": "Unmanaged (No Battery)",
                "Total Cost ($)": round(unmanaged.total_cost, 2),
                "Grid Import (kWh)": round(unmanaged.total_grid_import_kwh, 2),
                "Grid Export (kWh)": round(unmanaged.total_grid_export_kwh, 2),
                "Peak Demand (kW)": round(unmanaged.peak_grid_demand_kw, 2),
                "Self-Consumption (%)": round(unmanaged.solar_self_consumption_pct, 2),
                "Renewable Penetration (%)": round(unmanaged.renewable_penetration_pct, 2),
                "Battery Cycles": 0.0,
            },
            {
                "Strategy": "Rule-Based EMS (Baseline)",
                "Total Cost ($)": round(rule_based.total_cost, 2),
                "Grid Import (kWh)": round(rule_based.total_grid_import_kwh, 2),
                "Grid Export (kWh)": round(rule_based.total_grid_export_kwh, 2),
                "Peak Demand (kW)": round(rule_based.peak_grid_demand_kw, 2),
                "Self-Consumption (%)": round(rule_based.solar_self_consumption_pct, 2),
                "Renewable Penetration (%)": round(rule_based.renewable_penetration_pct, 2),
                "Battery Cycles": round(rule_based.battery_cycles, 2),
            },
            {
                "Strategy": "Optimization EMS (Proposed ML/MILP)",
                "Total Cost ($)": round(optimized.total_cost, 2),
                "Grid Import (kWh)": round(optimized.total_grid_import_kwh, 2),
                "Grid Export (kWh)": round(optimized.total_grid_export_kwh, 2),
                "Peak Demand (kW)": round(optimized.peak_grid_demand_kw, 2),
                "Self-Consumption (%)": round(optimized.solar_self_consumption_pct, 2),
                "Renewable Penetration (%)": round(optimized.renewable_penetration_pct, 2),
                "Battery Cycles": round(optimized.battery_cycles, 2),
            },
        ]

        return {
            "comparison_table": comparison_table,
            "savings_vs_unmanaged_usd": round(savings_opt_vs_unm_usd, 2),
            "savings_vs_unmanaged_pct": round(savings_opt_vs_unm_pct, 2),
            "savings_vs_rule_based_usd": round(savings_opt_vs_rb_usd, 2),
            "savings_vs_rule_based_pct": round(savings_opt_vs_rb_pct, 2),
            "peak_demand_reduction_pct": round(peak_reduction_pct, 2),
            "opt_total_cost": round(opt_cost, 2),
            "rb_total_cost": round(rb_cost, 2),
            "unm_total_cost": round(unmanaged_cost, 2),
            "unm_peak_grid_demand_kw": round(peak_unm, 2),
            "rb_peak_grid_demand_kw": round(peak_rb, 2),
            "opt_peak_grid_demand_kw": round(peak_opt, 2),
            "unm_grid_import_kwh": round(unmanaged.total_grid_import_kwh, 2),
            "rb_grid_import_kwh": round(rule_based.total_grid_import_kwh, 2),
            "opt_grid_import_kwh": round(optimized.total_grid_import_kwh, 2),
            "unm_solar_self_consumption_pct": round(unmanaged.solar_self_consumption_pct, 2),
            "rb_solar_self_consumption_pct": round(rule_based.solar_self_consumption_pct, 2),
            "opt_solar_self_consumption_pct": round(optimized.solar_self_consumption_pct, 2),
            "unm_renewable_penetration_pct": round(unmanaged.renewable_penetration_pct, 2),
            "rb_renewable_penetration_pct": round(rule_based.renewable_penetration_pct, 2),
            "opt_renewable_penetration_pct": round(optimized.renewable_penetration_pct, 2),
        }
