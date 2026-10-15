"""Overview & System Architecture Page.
Presents the technical architecture, mathematical formulation, hardware constraints,
and State DISCOM Time-of-Day (ToD) tariff schedules of the SmartGrid Bharat EMS.
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
from dashboard.components.sidebar import render_sidebar_controls
from dashboard.components.metrics_cards import (
    render_section_header,
    render_page_header,
    inject_custom_css,
    render_html,
)

st.set_page_config(
    page_title="Architecture & Specs - SmartGrid Bharat",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()
params = render_sidebar_controls()

# Page Header
render_page_header(
    title="Platform Architecture & Engineering Specifications",
    subtitle="Technical breakdown of microgrid telemetry pipeline, electrochemical physical limits, and CEA-compliant dispatch formulation.",
    badges=[
        ("Grid: CEA 415V 50 Hz", "info"),
        ("Storage: BIS IS 16046 LiFePO4", "success"),
        ("Degradation: ASTM E1049-85 Rainflow", "success"),
        ("Weather: Live Open-Meteo API", "info"),
        ("AI: Quantile P10-P90 & SHAP XAI", "warning"),
    ],
)


# 1. SEQUENTIAL ARCHITECTURE PIPELINE
render_section_header(
    title="Four-Tier Engineering Architecture Pipeline",
    subtitle="Sequential data and physical control flow aligned with Indian Smart Grid standards",
    badge_text="DATA & CONTROL FLOW",
)

render_html("""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 16px;">
    <!-- Tier 1 -->
    <div class="ems-panel" style="margin-bottom: 0;">
        <div style="font-size: 0.70rem; color: #D97706; font-family: 'JetBrains Mono', monospace; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">
            Tier 01 &bull; Telemetry Ingestion
        </div>
        <div style="font-size: 0.84rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
            Feature Ingestion & Partitioning
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.45;">
            Ingests 8,760 hours of microgrid telemetry reflecting Indian solar irradiance profiles and diurnal commercial load patterns.
        </div>
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-subtle); font-size: 0.70rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
            &bull; Sine/Cosine cyclical temporal lags<br>
            &bull; Chronological 70/15/15 train/val/test<br>
            &bull; Zero lookahead data leakage check
        </div>
    </div>

    <!-- Tier 2 -->
    <div class="ems-panel" style="margin-bottom: 0;">
        <div style="font-size: 0.70rem; color: #0284C7; font-family: 'JetBrains Mono', monospace; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">
            Tier 02 &bull; Predictive Forecasting
        </div>
        <div style="font-size: 0.84rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
            Machine Learning Inference
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.45;">
            Evaluates 4 candidate forecasters over 12h–72h rolling horizons with strict physical zero-nighttime solar clamping.
        </div>
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-subtle); font-size: 0.70rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
            &bull; XGBoost, Random Forest, Ridge, Base<br>
            &bull; Evaluation: MAE, RMSE, MAPE, R²<br>
            &bull; Edge inference latency &lt; 15ms
        </div>
    </div>

    <!-- Tier 3 -->
    <div class="ems-panel" style="margin-bottom: 0;">
        <div style="font-size: 0.70rem; color: #059669; font-family: 'JetBrains Mono', monospace; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">
            Tier 03 &bull; Physical Modeling
        </div>
        <div style="font-size: 0.84rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
            Electrochemical BESS Physics
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.45;">
            Physics model enforcing 15%–95% safe SOC bounds, 90.25% roundtrip efficiency, and 0.5C symmetric converter limits.
        </div>
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-subtle); font-size: 0.70rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
            &bull; BIS IS 16046 LiFePO4 chemistry<br>
            &bull; Mutual exclusivity: No simultaneous chg/dis<br>
            &bull; Degradation wear penalty: ₹0.40/Unit
        </div>
    </div>

    <!-- Tier 4 -->
    <div class="ems-panel" style="margin-bottom: 0;">
        <div style="font-size: 0.70rem; color: #10B981; font-family: 'JetBrains Mono', monospace; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">
            Tier 04 &bull; Economic Optimization
        </div>
        <div style="font-size: 0.84rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
            PuLP MILP ToD Arbitrage
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.45;">
            Mixed-Integer Linear Program minimizing net utility billing through overnight charging and peak evening discharge.
        </div>
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-subtle); font-size: 0.70rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; line-height: 1.5;">
            &bull; State DISCOM ToD rate differential<br>
            &bull; Verified Sources = Sinks (±10⁻⁵ kW)<br>
            &bull; Heuristic fallback on infeasibility
        </div>
    </div>
</div>
""")

# 2. HARDWARE SPECIFICATIONS & TARIFF TABLES
render_section_header(
    title="Microgrid Asset Specifications & State DISCOM Tariff Schedule",
    subtitle="Hardware nameplate ratings and commercial Time-of-Day (ToD) tariff structure",
)

s1, s2 = st.columns(2)

with s1:
    render_html("""
    <div class="ems-panel">
        <div class="ems-panel-title" style="margin-bottom: 12px;">Microgrid Asset Specifications (CEA Standards)</div>
        <table class="ems-table">
            <thead>
                <tr>
                    <th>Asset Parameter</th>
                    <th>Technical Specification</th>
                    <th style="text-align: right;">Rating / Unit</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Solar PV Nameplate</td>
                    <td>MNRE ALMM Approved Mono PERC Array</td>
                    <td class="value-cell" style="color: #F59E0B;">6.0 kWp</td>
                </tr>
                <tr>
                    <td>Storage Chemistry</td>
                    <td>Lithium Iron Phosphate (BIS IS 16046)</td>
                    <td class="value-cell" style="color: #10B981;">LiFePO4 LFP</td>
                </tr>
                <tr>
                    <td>Battery Capacity (Total / Active)</td>
                    <td>10.0 kWh nominal / 8.0 kWh active window</td>
                    <td class="value-cell">10.0 / 8.0 Units</td>
                </tr>
                <tr>
                    <td>Safe SOC Operating Window</td>
                    <td>80% Maximum Depth of Discharge (DOD)</td>
                    <td class="value-cell">15% &ndash; 95%</td>
                </tr>
                <tr>
                    <td>Bi-Directional PCU Inverter</td>
                    <td>Symmetric 0.5C Hybrid (IS 16221 / IEC 62109)</td>
                    <td class="value-cell">5.0 kW (415V 3-Ph)</td>
                </tr>
                <tr>
                    <td>Roundtrip Efficiency</td>
                    <td>&eta;<sub>chg</sub> &times; &eta;<sub>dis</sub> (0.95 &times; 0.95)</td>
                    <td class="value-cell" style="color: #38BDF8;">90.25%</td>
                </tr>
                <tr>
                    <td>Grid Nominal Frequency</td>
                    <td>Indian National Grid Band (49.95 - 50.05 Hz)</td>
                    <td class="value-cell">50.0 Hz</td>
                </tr>
            </tbody>
        </table>
    </div>
    """)

with s2:
    render_html("""
    <div class="ems-panel">
        <div class="ems-panel-title" style="margin-bottom: 12px;">State DISCOM Time-of-Day (ToD) Tariff Schedule</div>
        <table class="ems-table">
            <thead>
                <tr>
                    <th>Tariff Tier</th>
                    <th>Time Window (IST)</th>
                    <th style="text-align: right;">Rate (₹ / Unit)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="color: #F87171; font-weight: 500;">Evening Peak ToD</td>
                    <td>18:00 &ndash; 22:00 Daily (High Surcharge)</td>
                    <td class="value-cell" style="color: #F87171;">₹12.00 / Unit</td>
                </tr>
                <tr>
                    <td style="color: #38BDF8; font-weight: 500;">Normal Daytime</td>
                    <td>06:00 &ndash; 18:00 (Standard Commercial)</td>
                    <td class="value-cell" style="color: #38BDF8;">₹7.50 / Unit</td>
                </tr>
                <tr>
                    <td style="color: #34D399; font-weight: 500;">Off-Peak Night ToD</td>
                    <td>22:00 &ndash; 06:00 (Overnight Rebate)</td>
                    <td class="value-cell" style="color: #34D399;">₹4.50 / Unit</td>
                </tr>
                <tr>
                    <td style="color: #FBBF24; font-weight: 500;">Solar Net Metering Export</td>
                    <td>DISCOM Average Power Purchase Cost (APPC)</td>
                    <td class="value-cell" style="color: #FBBF24;">₹3.50 / Unit</td>
                </tr>
                <tr>
                    <td>BESS Cycling Degradation</td>
                    <td>Throughput cell wear cost penalty</td>
                    <td class="value-cell" style="color: #CBD5E1;">₹0.40 / Unit</td>
                </tr>
                <tr>
                    <td>Unmanaged Flat Base Rate</td>
                    <td>Reference non-ToD industrial tariff</td>
                    <td class="value-cell">₹8.50 / Unit</td>
                </tr>
            </tbody>
        </table>
    </div>
    """)

# 3. MATHEMATICAL DISPATCH FORMULATION
render_section_header(
    title="Mathematical Formulation & Operational Constraints",
    subtitle="Mixed-Integer Linear Programming objective and physical nodal conservation laws",
)

st.latex(r"""
\min \quad \sum_{t=1}^{T} \Big( c_{\text{import}}(t) \cdot P_{\text{import}}(t) - c_{\text{export}}(t) \cdot P_{\text{export}}(t) + c_{\text{deg}} \cdot P_{\text{dis}}(t) \Big) \Delta t
""")

st.latex(r"""
\text{subject to: } \quad P_{\text{pv}}(t) + P_{\text{dis}}(t) + P_{\text{import}}(t) = P_{\text{load}}(t) + P_{\text{chg}}(t) + P_{\text{export}}(t) \quad \forall t \in \{1,\dots,T\}
""")

st.latex(r"""
\text{SOC}(t+1) = \text{SOC}(t) + \left( \frac{\eta_{\text{chg}} \cdot P_{\text{chg}}(t) - \frac{1}{\eta_{\text{dis}}} P_{\text{dis}}(t)}{E_{\text{nom}}} \right) \Delta t, \quad 0.15 \le \text{SOC}(t) \le 0.95
""")
