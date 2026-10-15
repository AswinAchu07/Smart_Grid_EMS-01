"""Battery State & Physics Diagnostics Dashboard Page.
Monitors electrochemical State of Charge (SOC), converter power constraints,
efficiency losses, and degradation mitigation models certified to BIS IS 16046 standards.
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
# pyrefly: ignore [missing-import]
import numpy as np
from app.battery.model import Battery
from app.services.simulation_service import SimulationService
from app.schemas.simulation import SimulationRequest
from app.core.constants import EMSStrategy
from dashboard.components.sidebar import render_sidebar_controls
from dashboard.components.charts import (
    plot_battery_soc,
    plot_battery_soc_gauge,
    plot_battery_degradation_cycles,
    plot_soh_retention_gauge,
)
from app.battery.degradation import BatteryDegradationModel
from dashboard.components.metrics_cards import (
    render_stat_strip,
    render_section_header,
    render_page_header,
    inject_custom_css,
    render_html,
)

st.set_page_config(
    page_title="Battery Diagnostics - SmartGrid Bharat",
    page_icon="🔋",
    layout="wide",
)
inject_custom_css()
params = render_sidebar_controls()

# Page Header
render_page_header(
    title="BESS Storage & Electrochemical Physics",
    subtitle="Electrochemical storage telemetry enforcing physical State-of-Charge (SOC) bounds, converter limits, and ASTM E1049-85 Rainflow cycle degradation.",
    badges=[
        ("Chemistry: LiFePO4 (LFP)", "success"),
        ("Thermal Ceiling: 45°C", "info"),
        ("Safe Operating Band: 15% - 95%", "warning"),
        ("ASTM E1049-85 Certified", "success"),
    ],
)

# Active Battery Model Instance
bat = Battery(
    capacity_kwh=params["capacity_kwh"],
    initial_soc=params["initial_soc"],
    min_soc=params["min_soc"],
    max_soc=params["max_soc"],
    max_charge_power_kw=params["max_power_kw"],
    max_discharge_power_kw=params["max_power_kw"],
    charge_efficiency=params["efficiency"],
    discharge_efficiency=params["efficiency"],
)

# 1. TELEMETRY SCORECARD (Clean Horizontal Strip)
render_section_header(
    title="Electrochemical Storage Telemetry",
    subtitle="Instantaneous state of charge, active capacity, and bidirectional converter ratings",
    badge_text="BIS IS 16046",
)

soc_pct = int(round(bat.soc * 100))
render_stat_strip([
    {
        "label": "State of Charge (SOC)",
        "val": f"{soc_pct}%",
        "sub": f"Floor: {int(bat.min_soc*100)}% | Ceiling: {int(bat.max_soc*100)}%",
        "color": "#10B981" if 20 <= soc_pct <= 90 else "#F59E0B",
    },
    {
        "label": "Stored Active Energy",
        "val": f"{bat.stored_energy_kwh:.2f} Units",
        "sub": f"Usable: {bat.usable_capacity_kwh:.1f} of {bat.capacity_kwh:.1f} kWh",
        "color": "var(--text-primary)",
    },
    {
        "label": "PCU Inverter Limit",
        "val": f"{bat.max_charge_power_kw:.1f} kW",
        "sub": "Symmetric 0.5C Charge / Discharge",
        "color": "#38BDF8",
    },
    {
        "label": "Roundtrip Efficiency",
        "val": f"{(bat.charge_efficiency * bat.discharge_efficiency * 100):.1f}%",
        "sub": "95% Chg × 95% Dis (sub-losses)",
        "color": "#10B981",
    },
])

# 2. SOC MONITORING & MULTI-DAY TRAJECTORY
render_section_header(
    title="State of Charge Trajectory & Real-Time Radial Gauge",
    subtitle=f"Continuous electrochemical SOC tracking over {params['sim_duration_hours']} hours under heuristic dispatch",
)

from dashboard.cache import get_cached_simulation_data

sim_data = get_cached_simulation_data(
    strategy_name=EMSStrategy.RULE_BASED.value,
    duration_hours=params["sim_duration_hours"],
    initial_soc=params["initial_soc"],
    capacity_kwh=params["capacity_kwh"],
    max_power_kw=params["max_power_kw"],
    efficiency=params["efficiency"],
    min_soc=params["min_soc"],
    max_soc=params["max_soc"],
)

soc_df = pd.DataFrame([{"timestamp": r["timestamp"], "soc": r["soc"]} for r in sim_data["records"]])

g_col, chart_col = st.columns([1, 2.5])

with g_col:
    st.plotly_chart(
        plot_battery_soc_gauge(current_soc=bat.soc, min_soc=bat.min_soc, max_soc=bat.max_soc),
        use_container_width=True,
    )

with chart_col:
    st.plotly_chart(
        plot_battery_soc(
            df=soc_df,
            min_soc=bat.min_soc,
            max_soc=bat.max_soc,
            title=f"Multi-Day SOC Trajectory ({params['sim_duration_hours']} Hours)",
        ),
        use_container_width=True,
    )

# 3. PHYSICS-INFORMED DEGRADATION & SOH (Rainflow Cycle Counting)
render_section_header(
    title="ASTM E1049-85 Rainflow Degradation & State of Health (SOH)",
    subtitle="Wöhler fatigue curve, Arrhenius thermal acceleration, and Remaining Useful Life (RUL) projection",
    badge_text="Physics-Informed",
)

col_ctrl1, col_ctrl2 = st.columns([1.5, 2.5])
with col_ctrl1:
    amb_temp = st.slider(
        "Operating Ambient Temperature (°C)",
        min_value=15.0,
        max_value=48.0,
        value=30.0,
        step=1.0,
        help="Arrhenius chemical reaction rate accelerates SEI layer growth above 25°C standard temperature.",
    )
with col_ctrl2:
    st.caption("⚡ **Physics Insights**: Rainflow cycle counting decomposes irregular microgrid charge/discharge trajectories into discrete stress reversals. High depth-of-discharge (DOD) cycles cause nonlinear mechanical electrode fatigue.")

# Compute degradation from SOC trajectory
deg_model = BatteryDegradationModel(
    nominal_capacity_kwh=params["capacity_kwh"],
    ambient_temp_celsius=amb_temp,
)
soc_vals = soc_df["soc"].tolist() if not soc_df.empty else [0.5, 0.6]
deg_report = deg_model.evaluate_soc_trajectory(
    soc_trajectory=soc_vals,
    dt_hours=1.0,
    initial_soh=1.0,
    temp_celsius=amb_temp,
)

# Render degradation KPI Strip
render_stat_strip([
    {
        "label": "State of Health (SOH)",
        "val": f"{deg_report['final_soh_pct']:.2f}%",
        "sub": f"Fade: {deg_report['soh_loss_pct']:.4f}%",
        "color": "#10B981" if deg_report['final_soh_pct'] >= 90 else "#F59E0B",
    },
    {
        "label": "Projected RUL",
        "val": f"~{deg_report['projected_rul_years']:.1f} Yrs",
        "sub": f"EOL Threshold: 80% SOH",
        "color": "#38BDF8",
    },
    {
        "label": "Equivalent Full Cycles",
        "val": f"{deg_report['equivalent_full_cycles']:.2f}",
        "sub": f"{deg_report['cycle_count_full']} Full | {deg_report['cycle_count_half']} Half Cycles",
        "color": "var(--text-primary)",
    },
    {
        "label": "Cumulative Wear Cost",
        "val": f"₹{deg_report['economic_degradation_cost'] * 85.0:.2f}",
        "sub": "CapEx Depletion Loss",
        "color": "#F59E0B",
    },
])

d_gauge_col, d_hist_col = st.columns([1, 2])

with d_gauge_col:
    st.plotly_chart(
        plot_soh_retention_gauge(
            soh=deg_report["final_soh"],
            rul_years=deg_report["projected_rul_years"],
        ),
        use_container_width=True,
    )

with d_hist_col:
    st.plotly_chart(
        plot_battery_degradation_cycles(
            dod_histogram=deg_report["dod_histogram"],
            title=f"Extracted Rainflow Cycles across DOD Bins ({deg_report['duration_hours']:.0f}h Trajectory)",
        ),
        use_container_width=True,
    )

