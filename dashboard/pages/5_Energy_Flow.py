"""Microgrid Energy Flow & Power Balance Dashboard Page.
Visualizes multi-source power balance compliant with Central Electricity Authority (CEA) regulations,
complemented by a cumulative Sankey flow diagram and an interactive dispatch logic calculator.
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
from app.services.simulation_service import SimulationService
from app.services.ems_service import EMSService
from app.schemas.simulation import SimulationRequest
from app.core.constants import EMSStrategy
from dashboard.components.sidebar import render_sidebar_controls
from dashboard.components.charts import plot_energy_flow_stacked, plot_energy_sankey
from dashboard.components.metrics_cards import (
    render_stat_strip,
    render_section_header,
    render_page_header,
    inject_custom_css,
    render_html,
)

st.set_page_config(
    page_title="Power Flow - SmartGrid Bharat",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()
params = render_sidebar_controls()

# Page Header
render_page_header(
    title="Power Flow & Energy Balance",
    subtitle=f"Analysis of multi-source power balance over {params['sim_duration_hours']} hours, commercial load fulfillment, and cumulative inter-asset energy routing.",
    badges=[
        ("Conservation: Verified (CEA)", "success"),
        (f"Horizon: {params['sim_duration_hours']}h", "info"),
        ("Feeder: Net Metered", "neutral"),
    ],
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

sim_records_df = pd.DataFrame(sim_data["records"])

# 1. MULTI-SOURCE POWER BALANCE
render_section_header(
    title=f"Multi-Source Power Dispatch & Load Fulfillment ({params['sim_duration_hours']} Hours)",
    subtitle="Decomposition of load power supply: Direct Solar PV, BESS Discharge, and State DISCOM Import",
)

st.plotly_chart(
    plot_energy_flow_stacked(sim_records_df, title=f"Continuous Load Fulfillment Decomposition ({params['sim_duration_hours']}h)"),
    use_container_width=True,
)

# 2. CUMULATIVE PERIOD SANKEY DIAGRAM
render_section_header(
    title="Cumulative Energy Flow Distribution (kWh / Units)",
    subtitle="Tracing aggregate energy transfers from rooftop solar through BESS storage to facility loads and DISCOM export",
)

st.plotly_chart(
    plot_energy_sankey(sim_records_df),
    use_container_width=True,
)

# 3. INTERACTIVE DISPATCH CALCULATOR
render_section_header(
    title="Instantaneous Dispatch Simulator",
    subtitle="Simulate point-in-time generation and demand conditions to test controller routing decisions and power balance",
    badge_text="REAL-TIME DISPATCH ENGINE",
)

c1, c2, c3 = st.columns(3)
with c1:
    in_solar = st.number_input("Rooftop Solar PV (kW)", min_value=0.0, max_value=15.0, value=5.2, step=0.5, help="Instantaneous solar output")
with c2:
    in_load = st.number_input("Facility Demand (kW)", min_value=0.2, max_value=15.0, value=3.0, step=0.5, help="Instantaneous commercial load consumption")
with c3:
    in_soc = st.slider("Current BESS SOC (%)", min_value=15, max_value=95, value=50, step=5, help="Current battery state of charge") / 100.0

ems_svc = EMSService()
step_dec = ems_svc.get_rule_based_decision(
    solar_kw=in_solar,
    load_kw=in_load,
    current_soc=in_soc,
    battery_capacity=params["capacity_kwh"],
)

# Render results in a clean unified horizontal strip
render_stat_strip([
    {
        "label": "Solar to Load",
        "val": f"{step_dec.solar_to_load_kw:.2f} kW",
        "sub": "Direct on-site solar power",
        "color": "#F59E0B",
    },
    {
        "label": "Solar to Battery",
        "val": f"{step_dec.solar_to_battery_kw:.2f} kW",
        "sub": "Surplus generation charging",
        "color": "#10B981",
    },
    {
        "label": "Solar to Export",
        "val": f"{step_dec.solar_to_grid_kw:.2f} kW",
        "sub": "Net meter APPC feed-in",
        "color": "#CBD5E1",
    },
    {
        "label": "Battery to Load",
        "val": f"{step_dec.battery_to_load_kw:.2f} kW",
        "sub": "BESS discharge support",
        "color": "#10B981",
    },
    {
        "label": "DISCOM Import Needed",
        "val": f"{step_dec.grid_import_kw:.2f} kW",
        "sub": "Grid deficit import",
        "color": "#F43F5E",
    },
])
