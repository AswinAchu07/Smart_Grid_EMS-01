"""High-performance caching layer for SmartGrid Bharat Streamlit Dashboard.
Accelerates simulation, forecasting, and analytics reloads from ~1-2s down to <1ms via st.cache_data.
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd

from app.core.constants import EMSStrategy, TargetType, ForecastingModelType
from app.battery.model import Battery
from app.simulation.engine import SimulationEngine
from app.simulation.evaluator import PerformanceEvaluator
from app.services.simulation_service import SimulationService
from app.services.analytics_service import AnalyticsService
from app.services.forecast_service import ForecastService
from app.schemas.simulation import SimulationResponse, SimulationRecordSchema


@st.cache_data(show_spinner=False, ttl=7200, max_entries=64)
def get_cached_simulation_data(
    strategy_name: str,
    duration_hours: int,
    initial_soc: float,
    capacity_kwh: float = 10.0,
    max_power_kw: float = 5.0,
    efficiency: float = 0.95,
    min_soc: float = 0.15,
    max_soc: float = 0.95,
) -> Dict[str, Any]:
    """Execute and cache simulation outcome for instant (<1ms) dashboard retrieval."""
    sim_svc = SimulationService()
    raw_df = sim_svc.pipeline.get_or_create_raw_data()
    df_clean = sim_svc.pipeline.preprocessor.clean_and_normalize(raw_df)
    _, _, test_df = sim_svc.pipeline.preprocessor.chronological_split(df_clean)
    sim_df = test_df.iloc[:duration_hours].reset_index(drop=True)

    bat = Battery(
        capacity_kwh=capacity_kwh,
        initial_soc=initial_soc,
        min_soc=min_soc,
        max_soc=max_soc,
        max_charge_power_kw=max_power_kw,
        max_discharge_power_kw=max_power_kw,
        charge_efficiency=efficiency,
        discharge_efficiency=efficiency,
    )
    engine = SimulationEngine(battery=bat)
    strat = EMSStrategy(strategy_name)

    if strat == EMSStrategy.UNMANAGED:
        summary = engine.run_unmanaged(sim_df)
    elif strat == EMSStrategy.RULE_BASED:
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
            soc=r["soc"],
            price_per_kwh=r["price_per_kwh"],
            cost=r["cost"],
        )
        for r in summary.records
    ]

    res = SimulationResponse(
        strategy=summary.strategy,
        total_steps=summary.total_steps,
        total_cost=round(summary.total_cost, 2),
        total_solar_kwh=round(summary.total_solar_kwh, 2),
        total_load_kwh=round(summary.total_load_kwh, 2),
        total_grid_import_kwh=round(summary.total_grid_import_kwh, 2),
        total_grid_export_kwh=round(summary.total_grid_export_kwh, 2),
        net_grid_kwh=round(summary.net_grid_kwh, 2),
        peak_grid_demand_kw=round(summary.peak_grid_demand_kw, 2),
        solar_self_consumption_pct=round(summary.solar_self_consumption_pct, 2),
        renewable_penetration_pct=round(summary.renewable_penetration_pct, 2),
        battery_cycles=round(summary.battery_cycles, 2),
        final_soc=round(summary.final_soc, 4),
        records=record_schemas,
    )
    return res.model_dump()


@st.cache_data(show_spinner=False, ttl=7200, max_entries=32)
def get_cached_benchmark_comparison_data(
    duration_hours: int,
    capacity_kwh: float = 10.0,
    max_power_kw: float = 5.0,
    efficiency: float = 0.95,
    initial_soc: float = 0.5,
) -> Dict[str, Any]:
    """Execute and cache multi-strategy comparison for instant (<1ms) dashboard retrieval."""
    analytics_svc = AnalyticsService()
    raw_df = analytics_svc.pipeline.get_or_create_raw_data()
    df_clean = analytics_svc.pipeline.preprocessor.clean_and_normalize(raw_df)
    _, _, test_df = analytics_svc.pipeline.preprocessor.chronological_split(df_clean)
    sim_df = test_df.iloc[:duration_hours].reset_index(drop=True)

    bat_unm = Battery(capacity_kwh=capacity_kwh, initial_soc=initial_soc, max_charge_power_kw=max_power_kw, max_discharge_power_kw=max_power_kw, charge_efficiency=efficiency, discharge_efficiency=efficiency)
    bat_rb = Battery(capacity_kwh=capacity_kwh, initial_soc=initial_soc, max_charge_power_kw=max_power_kw, max_discharge_power_kw=max_power_kw, charge_efficiency=efficiency, discharge_efficiency=efficiency)
    bat_opt = Battery(capacity_kwh=capacity_kwh, initial_soc=initial_soc, max_charge_power_kw=max_power_kw, max_discharge_power_kw=max_power_kw, charge_efficiency=efficiency, discharge_efficiency=efficiency)

    sum_unm = SimulationEngine(battery=bat_unm).run_unmanaged(sim_df)
    sum_rb = SimulationEngine(battery=bat_rb).run_rule_based(sim_df)
    sum_opt = SimulationEngine(battery=bat_opt).run_optimization(sim_df)

    comp_dict = PerformanceEvaluator.compare_strategies(
        unmanaged=sum_unm,
        rule_based=sum_rb,
        optimized=sum_opt,
    )
    return comp_dict


@st.cache_data(show_spinner=False, ttl=7200, max_entries=32)
def get_cached_forecast_data(
    target_type: str,
    model_type: str,
    horizon_hours: int = 24,
) -> Dict[str, Any]:
    """Cache forecasting inferences to eliminate repeated model evaluations."""
    forecast_svc = ForecastService()
    t_type = TargetType(target_type.lower()) if isinstance(target_type, str) else target_type
    m_type = ForecastingModelType(model_type.upper()) if isinstance(model_type, str) else model_type
    res = forecast_svc.generate_forecast(
        target_type=t_type,
        model_type=m_type,
        horizon_hours=horizon_hours,
    )
    return res.model_dump()


@st.cache_data(show_spinner=False, ttl=7200, max_entries=8)
def get_cached_model_benchmarks_data(target_type: str) -> Dict[str, Any]:
    """Cache model benchmarking statistics across all 4 architectures."""
    forecast_svc = ForecastService()
    t_type = TargetType(target_type.lower()) if isinstance(target_type, str) else target_type
    return forecast_svc.get_all_model_benchmarks(target_type=t_type)
