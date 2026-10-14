"""Strategy Benchmarks, Analytics, and Financial Comparison Dashboard Page.
Performs quantitative three-way benchmarking comparing Unmanaged, Rule-Based,
and MILP Optimization strategies, accompanied by an Indian solar rooftop/BESS ROI sizing model.
"""

import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while DASHBOARD_DIR in sys.path:
    sys.path.remove(DASHBOARD_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import streamlit as st
import pandas as pd
from app.services.analytics_service import AnalyticsService
from dashboard.components.sidebar import render_sidebar_controls
from dashboard.components.charts import plot_strategy_cost_comparison, plot_roi_payback_curve
from dashboard.components.metrics_cards import (
    render_kpi_card,
    render_strategy_comparison_cards,
    render_stat_strip,
    render_section_header,
    render_page_header,
    inject_custom_css,
    format_inr,
    render_html,
)

st.set_page_config(
    page_title="Analytics & Strategy Benchmark - SmartGrid Bharat",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()
params = render_sidebar_controls()

# Executive Page Header
render_page_header(
    title="Comparative Strategy Benchmarks & Financial Analytics",
    subtitle=f"Quantitative empirical evaluation of {params['sim_duration_hours']}-hour microgrid dispatch across Unmanaged, Rule-Based, and MILP Optimization under State DISCOM tariffs.",
    badges=[
        ("Benchmark: 3-Way Comparative", "info"),
        (f"Horizon: {params['sim_duration_hours']} Hours", "neutral"),
        ("Currency: INR (₹)", "success"),
    ],
)

from dashboard.cache import get_cached_benchmark_comparison_data
from app.schemas.analytics import StrategyComparisonResponse

comp_dict = get_cached_benchmark_comparison_data(
    duration_hours=params["sim_duration_hours"],
    capacity_kwh=params["capacity_kwh"],
    max_power_kw=params["max_power_kw"],
    efficiency=params["efficiency"],
    initial_soc=params["initial_soc"],
)
comp = StrategyComparisonResponse(**comp_dict)

# 1. PRIMARY STRATEGY COMPARISON HERO CARDS
render_strategy_comparison_cards(
    unm_cost_inr=format_inr(comp.unm_total_cost),
    unm_peak_kw=comp.unm_peak_grid_demand_kw,
    unm_grid_import_kwh=comp.unm_grid_import_kwh,
    unm_self_consumption_pct=comp.unm_solar_self_consumption_pct,
    rb_cost_inr=format_inr(comp.rb_total_cost),
    rb_savings_inr=format_inr(comp.savings_vs_unmanaged_usd),
    rb_savings_pct=comp.savings_vs_unmanaged_pct,
    rb_peak_kw=comp.rb_peak_grid_demand_kw,
    rb_grid_import_kwh=comp.rb_grid_import_kwh,
    rb_self_consumption_pct=comp.rb_solar_self_consumption_pct,
    opt_cost_inr=format_inr(comp.opt_total_cost),
    opt_savings_vs_unm_inr=format_inr(comp.savings_vs_unmanaged_usd),
    opt_savings_vs_unm_pct=comp.savings_vs_unmanaged_pct,
    opt_savings_vs_rb_inr=format_inr(comp.savings_vs_rule_based_usd),
    opt_peak_kw=comp.opt_peak_grid_demand_kw,
    opt_grid_import_kwh=comp.opt_grid_import_kwh,
    opt_self_consumption_pct=comp.opt_solar_self_consumption_pct,
)

# 2. COMPARATIVE COST VISUALIZATION
render_section_header(
    title="Electricity Operating Bill Comparison (₹ INR)",
    subtitle="Monetary expenditure comparison across all three dispatch strategies with annotated percentage reductions",
)

st.plotly_chart(
    plot_strategy_cost_comparison(comp.model_dump()),
    use_container_width=True,
)

# 3. DETAILED PERFORMANCE MATRIX TABLE
render_section_header(
    title="Technical & Economic Performance Matrix (Indian Grid Metrics)",
    subtitle="Comprehensive multi-dimensional evaluation across electrical power, energy, and financial KPIs",
)

matrix_data = [
    {
        "Performance Dimension": "Total Electricity Operating Bill (₹ INR)",
        "Unmanaged (No Storage)": format_inr(comp.unm_total_cost),
        "Rule-Based EMS (Baseline)": format_inr(comp.rb_total_cost),
        "MILP Optimization (Proposed)": format_inr(comp.opt_total_cost),
        "Optimization Advantage": f"{(comp.unm_total_cost - comp.opt_total_cost)/comp.unm_total_cost*100:.1f}% Net Savings",
    },
    {
        "Performance Dimension": "Peak DISCOM Power Demand (kW)",
        "Unmanaged (No Storage)": f"{comp.unm_peak_grid_demand_kw:.2f} kW",
        "Rule-Based EMS (Baseline)": f"{comp.rb_peak_grid_demand_kw:.2f} kW",
        "MILP Optimization (Proposed)": f"{comp.opt_peak_grid_demand_kw:.2f} kW",
        "Optimization Advantage": f"{comp.peak_demand_reduction_pct:.1f}% Peak Shaving",
    },
    {
        "Performance Dimension": "Total Grid Import Dependency (kWh / Units)",
        "Unmanaged (No Storage)": f"{comp.unm_grid_import_kwh:,.1f} Units",
        "Rule-Based EMS (Baseline)": f"{comp.rb_grid_import_kwh:,.1f} Units",
        "MILP Optimization (Proposed)": f"{comp.opt_grid_import_kwh:,.1f} Units",
        "Optimization Advantage": f"{((comp.unm_grid_import_kwh - comp.opt_grid_import_kwh)/comp.unm_grid_import_kwh*100):.1f}% Dependency Drop",
    },
    {
        "Performance Dimension": "Solar Self-Consumption Ratio (%)",
        "Unmanaged (No Storage)": f"{comp.unm_solar_self_consumption_pct:.1f}%",
        "Rule-Based EMS (Baseline)": f"{comp.rb_solar_self_consumption_pct:.1f}%",
        "MILP Optimization (Proposed)": f"{comp.opt_solar_self_consumption_pct:.1f}%",
        "Optimization Advantage": f"+{comp.opt_solar_self_consumption_pct - comp.unm_solar_self_consumption_pct:.1f}% Local Utilization",
    },
    {
        "Performance Dimension": "Renewable Penetration Ratio (%)",
        "Unmanaged (No Storage)": f"{comp.unm_renewable_penetration_pct:.1f}%",
        "Rule-Based EMS (Baseline)": f"{comp.rb_renewable_penetration_pct:.1f}%",
        "MILP Optimization (Proposed)": f"{comp.opt_renewable_penetration_pct:.1f}%",
        "Optimization Advantage": f"+{comp.opt_renewable_penetration_pct - comp.unm_renewable_penetration_pct:.1f}% Clean Energy Share",
    },
]

matrix_df = pd.DataFrame(matrix_data)
st.dataframe(matrix_df, use_container_width=True, hide_index=True)

# 4. SIZING & CAPITAL PAYBACK PROJECTION (Differentiated Non-Card Layout)
render_section_header(
    title="Asset Sizing & Capital Payback Projection",
    subtitle="Simulate capital expenditure and financial breakeven based on Indian benchmarks (₹48,000/kWp Solar, ₹28,000/kWh BESS)",
    badge_text="CAPEX & ROI",
)

rc1, rc2 = st.columns(2)
with rc1:
    calc_pv = st.slider(
        "Solar PV Array Nameplate (kWp)",
        min_value=2.0,
        max_value=25.0,
        value=6.0,
        step=1.0,
        help="Installed rooftop solar PV capacity at ₹48,000/kWp turnkey (MNRE Benchmark).",
    )
with rc2:
    calc_bat = st.slider(
        "BESS Storage Sizing (kWh / Units)",
        min_value=5.0,
        max_value=50.0,
        value=10.0,
        step=2.5,
        help="Installed electrochemical battery storage capacity at ₹28,000/kWh turnkey.",
    )

# Compute annual savings estimate in INR
savings_hourly_inr = (comp.savings_vs_unmanaged_usd * 85.0) / max(1, params["sim_duration_hours"])
est_annual_savings_inr = savings_hourly_inr * 8760 * (calc_pv / 6.0) * (0.7 + 0.3 * (calc_bat / 10.0))

pv_cost_inr = calc_pv * 48000.0
bat_cost_inr = calc_bat * 28000.0
total_capex_inr = pv_cost_inr + bat_cost_inr
payback_years = total_capex_inr / max(1000.0, est_annual_savings_inr)

# Render as horizontal telemetry ribbon strip (not repetitive isolated boxes)
render_stat_strip([
    {
        "label": "Total Turnkey CAPEX",
        "val": format_inr(total_capex_inr, is_already_inr=True),
        "sub": f"PV: {format_inr(pv_cost_inr, is_already_inr=True)} | BESS: {format_inr(bat_cost_inr, is_already_inr=True)}",
        "color": "var(--text-primary)",
    },
    {
        "label": "Projected Annual Savings",
        "val": f"{format_inr(est_annual_savings_inr, is_already_inr=True)} / yr",
        "sub": "Under State DISCOM ToD tariff schedule",
        "color": "#F59E0B",
    },
    {
        "label": "Estimated Payback Horizon",
        "val": f"{payback_years:.1f} Years",
        "sub": "15-Year nominal asset lifespan",
        "color": "#10B981" if payback_years < 6.5 else "#94A3B8",
    },
    {
        "label": "Levelized Cost of Energy (LCOE)",
        "val": f"₹{(total_capex_inr / (calc_pv * 1400 * 15)):.2f} / Unit",
        "sub": "Estimated 15-year lifetime generation",
        "color": "#38BDF8",
    },
])

st.plotly_chart(
    plot_roi_payback_curve(
        years=15,
        pv_kw=calc_pv,
        bat_kwh=calc_bat,
        annual_savings_inr=est_annual_savings_inr,
    ),
    use_container_width=True,
)

# 5. DATA EXPORT ACTION
render_html("<div style='margin-top: 14px;'></div>")
csv_data = matrix_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Benchmark Summary Report (CSV)",
    data=csv_data,
    file_name=f"smartgrid_bharat_benchmark_{params['sim_duration_hours']}h.csv",
    mime="text/csv",
)
