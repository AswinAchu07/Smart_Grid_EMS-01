"""Main Streamlit Entry Application: SmartGrid Bharat Solar PV & Battery EMS.
Alternative entry point synchronized with the Indian industrial operations design system.
"""

import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import streamlit as st
import pandas as pd
import numpy as np

from app.core.config import settings
from app.services.analytics_service import AnalyticsService
from dashboard.components.sidebar import render_sidebar_controls
from dashboard.components.metrics_cards import (
    render_stat_strip,
    render_section_header,
    render_page_header,
    inject_custom_css,
    format_inr,
    render_html,
)

st.set_page_config(
    page_title="SmartGrid Bharat EMS Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
sidebar_params = render_sidebar_controls()

render_page_header(
    title="SmartGrid Bharat Operations Console",
    subtitle="Operational dispatch engine integrating machine learning forecasting with State DISCOM Time-of-Day (ToD) tariff arbitrage.",
    badges=[
        ("Grid: 50.02 Hz Synced", "success"),
        ("Dispatch: MILP Optimal", "info"),
        ("Currency: INR (₹)", "warning"),
    ],
)

# 1. KPI SUMMARY ROW (Clean Horizontal Ribbon Strip)
render_section_header(
    title="Operational Performance Summary",
    subtitle=f"Aggregated performance metrics across {sidebar_params['sim_duration_hours']}-hour analysis window",
    badge_text="INDIAN MARKET ToD",
)

from dashboard.cache import get_cached_benchmark_comparison_data

comp_dict = get_cached_benchmark_comparison_data(
    duration_hours=sidebar_params["sim_duration_hours"],
    capacity_kwh=sidebar_params["capacity_kwh"],
    max_power_kw=sidebar_params["max_power_kw"],
    efficiency=sidebar_params["efficiency"],
    initial_soc=sidebar_params["initial_soc"],
)

render_stat_strip([
    {
        "label": "Optimization Net Bill",
        "val": format_inr(comp_dict["opt_total_cost"]),
        "sub": f"-{format_inr(comp_dict['savings_vs_rule_based_usd'])} vs Rule-Based",
        "color": "#10B981",
    },
    {
        "label": "Bill Reduction vs Grid",
        "val": f"{comp_dict['savings_vs_unmanaged_pct']:.1f}%",
        "sub": f"{format_inr(comp_dict['savings_vs_unmanaged_usd'])} saved vs Base",
        "color": "#F59E0B",
    },
    {
        "label": "Peak Demand Shaving",
        "val": f"{comp_dict['peak_demand_reduction_pct']:.1f}%",
        "sub": f"{comp_dict['opt_peak_grid_demand_kw']:.1f} kW Peak Intake",
        "color": "#38BDF8",
    },
    {
        "label": "Active Storage Capacity",
        "val": f"{sidebar_params['capacity_kwh']:.1f} Units",
        "sub": f"Initial SOC: {int(sidebar_params['initial_soc']*100)}%",
        "color": "var(--text-primary)",
    },
])

# 2. SYSTEM MODULE NAVIGATION
render_section_header(
    title="System Architecture & Analytics Modules",
    subtitle="Access specialized analytical and optimization modules via the left sidebar navigation",
)

c1, c2, c3 = st.columns(3)

with c1:
    render_html("""
    <div class="ems-panel" style="height: 100%;">
        <div class="ems-panel-header">
            <span class="ems-panel-title">Generation & Load Forecasting</span>
            <span class="ems-status-pill">CERC ALIGNED</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; margin-bottom: 10px;">
            Candidate architecture comparison (XGBoost, Random Forest, Ridge, Persistence) across Indian solar irradiance and diurnal demand profiles.
        </p>
        <div style="font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
            Pages: 2_Solar_Forecast &bull; 3_Load_Forecast
        </div>
    </div>
    """)

with c2:
    render_html("""
    <div class="ems-panel" style="height: 100%;">
        <div class="ems-panel-header">
            <span class="ems-panel-title">BESS Dynamics & Physics</span>
            <span class="ems-status-pill">BIS IS 16046</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; margin-bottom: 10px;">
            Electrochemical model enforcing 15%-95% safe SOC bounds, 0.5C converter limits, 90.25% roundtrip efficiency, and BIS safety norms.
        </p>
        <div style="font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
            Pages: 4_Battery_Status &bull; 5_Energy_Flow
        </div>
    </div>
    """)

with c3:
    render_html("""
    <div class="ems-panel" style="height: 100%;">
        <div class="ems-panel-header">
            <span class="ems-panel-title">Optimization & Benchmarks</span>
            <span class="ems-status-pill">MILP SOLVER</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; margin-bottom: 10px;">
            PuLP MILP solver for 24-hour State DISCOM ToD price arbitrage, strict CEA power conservation, and 3-way multi-strategy economic scorecards in ₹.
        </p>
        <div style="font-size: 0.72rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
            Pages: 6_Optimization_EMS &bull; 7_Analytics
        </div>
    </div>
    """)
