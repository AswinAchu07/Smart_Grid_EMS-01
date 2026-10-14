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
from dashboard.components.charts import plot_battery_soc, plot_battery_soc_gauge
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
    subtitle="Electrochemical storage telemetry enforcing physical State-of-Charge (SOC) bounds, converter limits, and cycle degradation prevention.",
    badges=[
        ("Chemistry: LiFePO4 (LFP)", "success"),
        ("Thermal Ceiling: 45°C", "info"),
        ("Safe Operating Band: 15% - 95%", "warning"),
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

# 3. DEGRADATION & THERMAL SAFETY (Indian Standards)
render_section_header(
    title="Asset Longevity & BIS Thermal Protection",
    subtitle="Degradation cost modeling and high ambient temperature safety mechanisms",
)

c1, c2 = st.columns(2)

with c1:
    render_html("""
    <div class="ems-panel">
        <div class="ems-panel-header">
            <span class="ems-panel-title">Cycle Aging & Degradation Formulation</span>
            <span class="ems-status-pill">BIS IS 16046</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; margin-bottom: 10px;">
            The LiFePO4 chemistry provides ~5,000 equivalent full cycles to 80% State of Health (SOH). A linear cell wear penalty is embedded into the mathematical optimization objective.
        </p>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-muted); line-height: 1.6;">
            <div>&bull; <b>Wear Penalty:</b> ₹0.40 / Unit throughput</div>
            <div>&bull; <b>Arbitrage Hurdle:</b> Discharges only when (ToD_Peak - ToD_OffPeak) &gt; ₹0.40 / Unit</div>
            <div>&bull; <b>Mutual Exclusivity:</b> P_charge(t) &times; P_discharge(t) = 0 strictly verified</div>
        </div>
    </div>
    """)

with c2:
    render_html("""
    <div class="ems-panel">
        <div class="ems-panel-header">
            <span class="ems-panel-title">Thermal & Chemical Safety Constraints</span>
            <span class="ems-status-pill">THERMAL LIMITS</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; margin-bottom: 10px;">
            Physical boundaries protect against high-voltage lithium plating during overcharging and phase collapse during excessive deep-discharge under Indian summer conditions (ambient up to 45°C).
        </p>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-muted); line-height: 1.6;">
            <div>&bull; <b>C-Rate Limit:</b> Max 0.5C (symmetric charge/discharge) prevents thermal runaway</div>
            <div>&bull; <b>Lower Floor (15% SOC):</b> Preserves active lithium inventory</div>
            <div>&bull; <b>Upper Ceiling (95% SOC):</b> Mitigates cathode degradation and gas evolution</div>
        </div>
    </div>
    """)
