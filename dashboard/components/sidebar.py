"""Global sidebar controls and system configuration for Streamlit.
Tailored for the Indian Smart Grid market (CEA / State DISCOM / CERC Time-of-Day tariffs).
"""

from typing import Dict, Any
import streamlit as st
from dashboard.components.metrics_cards import render_sidebar_html


def render_sidebar_controls() -> Dict[str, Any]:
    """Render structured industrial sidebar controls and return configuration dictionary."""
    render_sidebar_html("""
    <div class="sidebar-brand-lockup">
        <div class="sidebar-brand-name">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 2px; background: #10B981;"></span>
            SmartGrid Bharat EMS
        </div>
        <div class="sidebar-brand-sub">
            Microgrid Operations & Dispatch Console
        </div>
        <div class="sidebar-status-pill">
            <span style="width: 5px; height: 5px; border-radius: 50%; background-color: #10B981;"></span>
            Grid: 50.02 Hz &bull; CERC DSM OK
        </div>
    </div>
    """)

    render_sidebar_html('<div class="sidebar-section-divider">Operating Scenario</div>')
    scenario_preset = st.sidebar.selectbox(
        "Operating Scenario",
        options=[
            "National Grid Benchmark (Standard ToD)",
            "North India Summer Heatwave (High Solar & AC Load)",
            "Monsoon Low-Irradiance & High Humidity (Mumbai/Kerala)",
            "Winter Morning Smog & Ag-Pumping (NCR/Punjab)",
            "State DISCOM High-ToD Peak Arbitrage (MSEDCL/BESCOM)",
            "DISCOM Scheduled Load-Shedding (Islanding Backup)",
        ],
        index=0,
        label_visibility="collapsed",
    )

    # Apply presets defaults
    preset_cap = 10.0
    preset_soc = 50
    preset_pwr = 5.0
    preset_dur = 168

    if "Summer Heatwave" in scenario_preset:
        preset_cap = 15.0
        preset_soc = 40
        preset_pwr = 7.5
        preset_dur = 72
    elif "Monsoon" in scenario_preset:
        preset_cap = 10.0
        preset_soc = 80
        preset_pwr = 5.0
        preset_dur = 72
    elif "High-ToD" in scenario_preset:
        preset_cap = 20.0
        preset_soc = 90
        preset_pwr = 10.0
        preset_dur = 24
    elif "Load-Shedding" in scenario_preset:
        preset_cap = 12.0
        preset_soc = 95
        preset_pwr = 6.0
        preset_dur = 48

    render_sidebar_html('<div class="sidebar-section-divider">BESS Storage Hardware</div>')
    capacity_kwh = st.sidebar.slider(
        "BESS Capacity (kWh / Units)",
        min_value=2.0,
        max_value=50.0,
        value=preset_cap,
        step=1.0,
        help="Total nameplate battery storage capacity in kWh (Units).",
    )
    initial_soc = st.sidebar.slider(
        "Initial State of Charge (%)",
        min_value=15,
        max_value=95,
        value=preset_soc,
        step=5,
        help="Initial battery energy level (15% to 95% safe operating window).",
    ) / 100.0
    max_power_kw = st.sidebar.slider(
        "Hybrid PCU Power Limit (kW)",
        min_value=1.0,
        max_value=25.0,
        value=preset_pwr,
        step=0.5,
        help="Maximum symmetric continuous charge/discharge power of the solar-battery inverter.",
    )

    render_sidebar_html('<div class="sidebar-section-divider">Simulation Horizon</div>')
    sim_duration = st.sidebar.selectbox(
        "Dispatch Horizon",
        options=[24, 48, 72, 168, 720],
        format_func=lambda x: f"{x} Hours ({x//24} Day{'s' if x//24 > 1 else ''})",
        index=3 if preset_dur == 168 else (0 if preset_dur == 24 else (1 if preset_dur == 48 else 2)),
    )

    # Active DISCOM Tariff Summary Box
    render_sidebar_html("""
    <div style="margin-top: 14px; padding: 10px 12px; background: var(--surface-base); border: 1px solid var(--border-subtle); border-radius: 4px;">
        <div style="font-size: 0.6875rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;">
            State DISCOM ToD Tariffs
        </div>
        <div style="display: flex; flex-direction: column; gap: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.70rem;">
            <div style="display: flex; justify-content: space-between; padding-bottom: 3px; border-bottom: 1px solid rgba(255,255,255,0.04);">
                <span style="color: #94A3B8;">Peak (18-22h)</span>
                <span style="color: #F87171; font-weight: 600;">₹12.00 / Unit</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding-bottom: 3px; border-bottom: 1px solid rgba(255,255,255,0.04);">
                <span style="color: #94A3B8;">Normal (06-18h)</span>
                <span style="color: #38BDF8; font-weight: 600;">₹7.50 / Unit</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding-bottom: 3px; border-bottom: 1px solid rgba(255,255,255,0.04);">
                <span style="color: #94A3B8;">Night (22-06h)</span>
                <span style="color: #34D399; font-weight: 600;">₹4.50 / Unit</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #94A3B8;">Solar Export</span>
                <span style="color: #FBBF24; font-weight: 600;">₹3.50 / Unit</span>
            </div>
        </div>
    </div>
    """)

    return {
        "capacity_kwh": capacity_kwh,
        "initial_soc": initial_soc,
        "min_soc": 0.15,
        "max_soc": 0.95,
        "max_power_kw": max_power_kw,
        "efficiency": 0.95,
        "sim_duration_hours": sim_duration,
        "scenario_preset": scenario_preset,
    }
