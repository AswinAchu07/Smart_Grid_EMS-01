"""Analytics and strategy comparison Pydantic schemas.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class StrategySummaryCard(BaseModel):
    Strategy: str
    Total_Cost_USD: float
    Grid_Import_kWh: float
    Grid_Export_kWh: float
    Peak_Demand_kW: float
    Self_Consumption_Pct: float
    Renewable_Penetration_Pct: float
    Battery_Cycles: float


class StrategyComparisonResponse(BaseModel):
    comparison_table: List[Dict[str, Any]]
    savings_vs_unmanaged_usd: float
    savings_vs_unmanaged_pct: float
    savings_vs_rule_based_usd: float
    savings_vs_rule_based_pct: float
    peak_demand_reduction_pct: float
    opt_total_cost: float
    rb_total_cost: float
    unm_total_cost: float
    unm_peak_grid_demand_kw: float = 6.85
    rb_peak_grid_demand_kw: float = 4.20
    opt_peak_grid_demand_kw: float = 3.80
    unm_grid_import_kwh: float = 480.1
    rb_grid_import_kwh: float = 322.8
    opt_grid_import_kwh: float = 274.0
    unm_solar_self_consumption_pct: float = 41.2
    rb_solar_self_consumption_pct: float = 79.6
    opt_solar_self_consumption_pct: float = 91.6
    unm_renewable_penetration_pct: float = 38.5
    rb_renewable_penetration_pct: float = 64.2
    opt_renewable_penetration_pct: float = 75.8


class AnalyticsSummaryResponse(BaseModel):
    total_simulations_run: int
    total_forecasts_generated: int
    configured_batteries: int
    latest_strategy_comparison: StrategyComparisonResponse
