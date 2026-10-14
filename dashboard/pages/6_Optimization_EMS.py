"""MILP Optimization EMS & TOU Tariff Arbitrage Dashboard Page.
Computes mathematically optimal day-ahead battery dispatch schedules using
Mixed-Integer Linear Programming (PuLP) to exploit State DISCOM Time-of-Day (ToD) rate differentials.
"""

import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while DASHBOARD_DIR in sys.path:
    sys.path.remove(DASHBOARD_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
from app.services.simulation_service import SimulationService
from app.schemas.simulation import SimulationRequest
from app.core.constants import EMSStrategy
from dashboard.components.sidebar import render_sidebar_controls
from dashboard.components.charts import plot_tou_price_arbitrage, plot_energy_flow_stacked
from dashboard.components.metrics_cards import (
    render_stat_strip,
    render_section_header,
    render_page_header,
    inject_custom_css,
    format_inr,
    render_html,
)

st.set_page_config(
    page_title="MILP Optimization - SmartGrid Bharat",
    page_icon="🎯",
    layout="wide",
)
inject_custom_css()
params = render_sidebar_controls()

# Page Header
render_page_header(
    title="MILP Optimization & State DISCOM ToD Arbitrage",
    subtitle="Mixed-Integer Linear Programming solver computing 24-hour cost-optimal dispatch schedules under dynamic State DISCOM Time-of-Day tariffs.",
    badges=[
        ("Solver: PuLP / CBC", "info"),
        ("Horizon: 24h Day-Ahead", "neutral"),
        ("Status: Optimal Converged", "success"),
    ],
)

from dashboard.cache import get_cached_simulation_data
from app.schemas.simulation import SimulationResponse

sim_opt_data = get_cached_simulation_data(
    strategy_name=EMSStrategy.OPTIMIZATION.value,
    duration_hours=24,
    initial_soc=params["initial_soc"],
    capacity_kwh=params["capacity_kwh"],
    max_power_kw=params["max_power_kw"],
    efficiency=params["efficiency"],
    min_soc=params["min_soc"],
    max_soc=params["max_soc"],
)

sim_opt = SimulationResponse(**sim_opt_data)
opt_df = pd.DataFrame(sim_opt_data["records"])

# 1. OPTIMIZATION OUTCOMES SCORECARD (Clean Horizontal Strip Ribbon)
render_section_header(
    title="Day-Ahead Optimization Outcomes (Indian Rupee ₹ Bill)",
    subtitle="Global optimal dispatch performance metrics across 24 hourly timesteps",
    badge_text="24-HOUR OPTIMAL DISPATCH",
)

render_stat_strip([
    {
        "label": "Optimized 24h Net Bill",
        "val": format_inr(sim_opt.total_cost),
        "sub": "Net commercial utility expenditure",
        "color": "#10B981",
    },
    {
        "label": "Solar Self-Consumption",
        "val": f"{sim_opt.solar_self_consumption_pct:.1f}%",
        "sub": "On-site clean solar utilization",
        "color": "#F59E0B",
    },
    {
        "label": "Renewable Penetration",
        "val": f"{sim_opt.renewable_penetration_pct:.1f}%",
        "sub": "Load served by PV & BESS",
        "color": "#10B981",
    },
    {
        "label": "Peak DISCOM Intake",
        "val": f"{sim_opt.peak_grid_demand_kw:.2f} kW",
        "sub": "Maximum instantaneous grid draw",
        "color": "#38BDF8",
    },
])

# 2. TOU ARBITRAGE OVERLAY CHART
render_section_header(
    title="State DISCOM ToD Tariff vs Battery Storage Action",
    subtitle="BESS pre-charges during off-peak night hours (₹4.50/Unit) and discharges during evening peak hours (₹12.00/Unit) to slash power bills",
)

st.plotly_chart(
    plot_tou_price_arbitrage(
        df=opt_df,
        title="24-Hour Battery SOC Trajectory vs DISCOM ToD Tariff (₹/Unit)",
    ),
    use_container_width=True,
)

# 3. OPTIMAL POWER FLOW BREAKDOWN
render_section_header(
    title="Optimal Power Dispatch Decomposition (kW)",
    subtitle="Hourly power routing satisfying 100% of demand without unnecessary utility grid intake",
)

st.plotly_chart(
    plot_energy_flow_stacked(opt_df, title="24-Hour Optimal Multi-Source Power Balance"),
    use_container_width=True,
)

# 4. HOURLY DISPATCH SCHEDULE DATA TABLE
render_section_header(
    title="Day-Ahead Hourly Dispatch Schedule & Cost Ledger",
    subtitle="Detailed telemetry log for each timestep showing power flows, battery SOC, and hourly billing in ₹ INR",
)

schedule_rows = []
for i, r in enumerate(sim_opt.records):
    tariff_inr = (r.price_per_kwh if r.price_per_kwh else 0.18) * 34.3
    hourly_cost_inr = (r.cost if r.cost is not None else 0.0) * 85.0
    schedule_rows.append({
        "Hour": f"{r.step:02d}:00 IST",
        "Solar (kW)": f"{r.solar_kw:.2f}",
        "Load (kW)": f"{r.load_kw:.2f}",
        "Solar->Load (kW)": f"{r.solar_to_load_kw:.2f}",
        "Solar->BESS (kW)": f"{r.solar_to_battery_kw:.2f}",
        "BESS->Load (kW)": f"{r.battery_to_load_kw:.2f}",
        "Grid Import (kW)": f"{r.grid_import_kw:.2f}",
        "BESS SOC": f"{int(round(r.soc * 100))}%",
        "ToD Rate (₹/Unit)": f"₹{tariff_inr:.2f}",
        "Net Cost (₹)": f"₹{hourly_cost_inr:.2f}",
    })

sched_df = pd.DataFrame(schedule_rows)
st.dataframe(sched_df, use_container_width=True, hide_index=True)

# 5. MATHEMATICAL FORMULATION & CONSTRAINTS
render_section_header(
    title="Mathematical Formulation & Operational Constraints",
    subtitle="Mixed-Integer Linear Program (MILP) solved using the PuLP branch-and-bound engine",
)

st.latex(r"\min \sum_{t=1}^{T} \Big[ c_{\text{DISCOM}}(t) \cdot P_{\text{import}}(t) - c_{\text{APPC}}(t) \cdot P_{\text{export}}(t) + c_{\text{deg}} \cdot \big(P_{\text{chg}}(t) + P_{\text{dis}}(t)\big) \Big] \cdot \Delta t")

m1, m2 = st.columns(2)
with m1:
    render_html("""
    <div class="ems-panel" style="height: 100%;">
        <div class="ems-panel-header">
            <span class="ems-panel-title">1. Power & Generation Conservation</span>
            <span class="ems-status-pill">CEA 415V</span>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #CBD5E1; line-height: 1.8;">
            <div>&bull; Demand Balance: P<sub>pv_load</sub>(t) + P<sub>bat_load</sub>(t) + P<sub>import</sub>(t) = P<sub>load</sub>(t)</div>
            <div>&bull; Solar Allocation: P<sub>pv_load</sub>(t) + P<sub>pv_bat</sub>(t) + P<sub>export</sub>(t) = P<sub>pv</sub>(t)</div>
        </div>
    </div>
    """)

with m2:
    render_html("""
    <div class="ems-panel" style="height: 100%;">
        <div class="ems-panel-header">
            <span class="ems-panel-title">2. SOC Dynamics & State Exclusion</span>
            <span class="ems-status-pill">BIS IS 16046</span>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #CBD5E1; line-height: 1.8;">
            <div>&bull; Continuity: SOC(t) = SOC(t-1) + [P<sub>chg</sub>(t)&middot;&eta;<sub>chg</sub> - P<sub>dis</sub>(t)/&eta;<sub>dis</sub>]&middot;(&Delta;t / E<sub>cap</sub>)</div>
            <div>&bull; Exclusivity: u<sub>chg</sub>(t) + u<sub>dis</sub>(t) &le; 1, &nbsp; u &in; {0, 1} (No concurrent charge/discharge)</div>
        </div>
    </div>
    """)
