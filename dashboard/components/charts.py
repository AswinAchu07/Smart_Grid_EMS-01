"""High-precision data visualizations for Smart Grid EMS analytics.
Tailored for the Indian energy sector with Indian Rupee (₹ INR) financial units,
DISCOM Time-of-Day (ToD) tariff curves, and high-legibility industrial layout.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Localized scale factors for Indian Market
INR_CONVERSION_RATE = 85.0
TOD_TARIFF_INR_SCALE = 34.3  # Scales 0.35/0.18/0.10 baseline to ~₹12.00/₹6.20/₹3.50 per Unit

# Disciplined Industrial Chart Canvas Theme
INDUSTRIAL_LAYOUT = dict(
    paper_bgcolor="#101726",
    plot_bgcolor="#101726",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color="#CBD5E1", size=11),
    xaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.05)",
        zerolinecolor="rgba(255, 255, 255, 0.08)",
        showgrid=True,
        tickfont=dict(size=10, color="#94A3B8", family="JetBrains Mono, monospace"),
        title_font=dict(size=11, color="#CBD5E1"),
    ),
    yaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.05)",
        zerolinecolor="rgba(255, 255, 255, 0.08)",
        showgrid=True,
        tickfont=dict(size=10, color="#94A3B8", family="JetBrains Mono, monospace"),
        title_font=dict(size=11, color="#CBD5E1"),
    ),
    hoverlabel=dict(
        bgcolor="#1E293B",
        font_size=11,
        font_family="JetBrains Mono, monospace",
        bordercolor="rgba(255, 255, 255, 0.15)",
    ),
    legend=dict(
        bgcolor="rgba(16, 23, 38, 0.9)",
        bordercolor="rgba(255, 255, 255, 0.08)",
        borderwidth=1,
        font=dict(color="#CBD5E1", size=10),
    ),
)


def plot_actual_vs_predicted(
    df: pd.DataFrame,
    actual_col: str,
    pred_col: str,
    title: str,
    y_label: str = "Power (kW)",
) -> go.Figure:
    """Comparative line chart displaying ground truth generation/demand vs ML forecast."""
    fig = go.Figure()
    
    x_axis = df["timestamp"] if "timestamp" in df.columns else (df["step"] if "step" in df.columns else df.index)
    
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=df[actual_col],
            mode="lines",
            name="Ground Truth (Actual)",
            line=dict(color="#38BDF8", width=2),
            hovertemplate="Actual: %{y:.2f} kW<extra></extra>",
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=df[pred_col],
            mode="lines",
            name="ML Model Prediction",
            line=dict(color="#F59E0B", width=2, dash="dash"),
            hovertemplate="Forecast: %{y:.2f} kW<extra></extra>",
        )
    )
    
    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Timeline"
    layout["yaxis_title"] = y_label
    layout["hovermode"] = "x unified"
    layout["margin"] = dict(l=45, r=25, t=45, b=35)
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    
    fig.update_layout(**layout)
    return fig


def plot_battery_soc(
    df: pd.DataFrame,
    min_soc: float = 0.15,
    max_soc: float = 0.95,
    soc_col: str = "soc",
    title: str = "BESS Battery State of Charge (SOC) Trajectory",
) -> go.Figure:
    """Plot battery state of charge trajectory with operational safety limits."""
    fig = go.Figure()
    
    col = soc_col if soc_col in df.columns else ("soc" if "soc" in df.columns else df.columns[0])
    y_vals = df[col] * 100.0 if df[col].max() <= 1.05 else df[col]
    x_axis = df["timestamp"] if "timestamp" in df.columns else list(range(len(df)))
    
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=y_vals,
            mode="lines",
            name="BESS SOC (%)",
            line=dict(color="#10B981", width=2),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.08)",
            hovertemplate="SOC: %{y:.1f}%<extra></extra>",
        )
    )
    
    fig.add_hline(
        y=max_soc * 100.0,
        line_dash="dot",
        line_color="#EF4444",
        line_width=1.2,
        annotation_text=f"Max Safe Limit ({int(max_soc*100)}%)",
        annotation_position="top right",
        annotation_font=dict(size=9, color="#EF4444", family="JetBrains Mono"),
    )
    fig.add_hline(
        y=min_soc * 100.0,
        line_dash="dot",
        line_color="#F97316",
        line_width=1.2,
        annotation_text=f"Min Safe Limit ({int(min_soc*100)}%)",
        annotation_position="bottom right",
        annotation_font=dict(size=9, color="#F97316", family="JetBrains Mono"),
    )
    
    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Timeline"
    layout["yaxis_title"] = "State of Charge (%)"
    layout["yaxis"] = dict(range=[0, 105], gridcolor="rgba(255, 255, 255, 0.05)")
    layout["hovermode"] = "x unified"
    layout["margin"] = dict(l=45, r=25, t=45, b=35)
    
    fig.update_layout(**layout)
    return fig


def plot_battery_soc_gauge(
    current_soc: float,
    min_soc: float = 0.15,
    max_soc: float = 0.95,
) -> go.Figure:
    """Industrial radial gauge chart displaying real-time battery state of charge."""
    val = current_soc * 100.0 if current_soc <= 1.0 else current_soc
    bar_color = "#10B981" if val >= 30 else ("#F59E0B" if val >= 20 else "#EF4444")
    
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Live BESS State of Charge", "font": {"size": 11, "color": "#94A3B8", "family": "Inter"}},
            number={"suffix": "%", "font": {"size": 26, "color": "#F0F4F8", "family": "JetBrains Mono"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.15)", "tickfont": {"size": 9, "color": "#94A3B8"}},
                "bar": {"color": bar_color, "thickness": 0.22},
                "bgcolor": "#151F32",
                "borderwidth": 1,
                "bordercolor": "rgba(255, 255, 255, 0.08)",
                "steps": [
                    {"range": [0, min_soc * 100], "color": "rgba(239, 68, 68, 0.12)"},
                    {"range": [min_soc * 100, max_soc * 100], "color": "rgba(16, 185, 129, 0.06)"},
                    {"range": [max_soc * 100, 100], "color": "rgba(239, 68, 68, 0.12)"},
                ],
                "threshold": {
                    "line": {"color": "#F0F4F8", "width": 2},
                    "thickness": 0.75,
                    "value": val,
                },
            },
        )
    )
    layout = {**INDUSTRIAL_LAYOUT}
    layout["margin"] = dict(l=25, r=25, t=35, b=25)
    fig.update_layout(**layout)
    return fig


plot_soc_trajectory = plot_battery_soc
plot_energy_balance_stacked = plot_actual_vs_predicted


def plot_energy_flow_stacked(df: pd.DataFrame, title: str = "Microgrid Power Balance & Load Fulfillment (kW)") -> go.Figure:
    """Stacked area chart displaying load supply decomposition."""
    fig = go.Figure()

    x_axis = df["timestamp"] if "timestamp" in df.columns else (df["step"] if "step" in df.columns else df.index)

    if "solar_to_load_kw" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["solar_to_load_kw"],
                name="Rooftop Solar PV Direct",
                mode="lines",
                stackgroup="load_supply",
                line=dict(color="#D97706", width=1),
                fillcolor="rgba(217, 119, 6, 0.50)",
                hovertemplate="Solar Direct: %{y:.2f} kW<extra></extra>",
            )
        )
    if "battery_to_load_kw" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["battery_to_load_kw"],
                name="BESS Battery Discharge",
                mode="lines",
                stackgroup="load_supply",
                line=dict(color="#059669", width=1),
                fillcolor="rgba(5, 150, 105, 0.50)",
                hovertemplate="Battery to Load: %{y:.2f} kW<extra></extra>",
            )
        )
    if "grid_import_kw" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["grid_import_kw"],
                name="DISCOM Grid Import",
                mode="lines",
                stackgroup="load_supply",
                line=dict(color="#E11D48", width=1),
                fillcolor="rgba(225, 29, 72, 0.50)",
                hovertemplate="DISCOM Import: %{y:.2f} kW<extra></extra>",
            )
        )

    if "load_kw" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["load_kw"],
                name="Total Facility Demand",
                mode="lines",
                line=dict(color="#F0F4F8", width=2),
                hovertemplate="Total Demand: %{y:.2f} kW<extra></extra>",
            )
        )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Timeline"
    layout["yaxis_title"] = "Power (kW / Units per Hour)"
    layout["hovermode"] = "x unified"
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    layout["margin"] = dict(l=45, r=25, t=45, b=35)

    fig.update_layout(**layout)
    return fig


def plot_energy_sankey(
    df_or_none=None,
    total_solar: float = 0.0,
    total_load: float = 0.0,
    solar_to_load: float = 0.0,
    solar_to_battery: float = 0.0,
    solar_to_grid: float = 0.0,
    battery_to_load: float = 0.0,
    grid_import: float = 0.0,
    grid_export: float = 0.0,
) -> go.Figure:
    """Generate industrial Sankey flow diagram tracing cumulative energy distribution in kWh (Units)."""
    if isinstance(df_or_none, pd.DataFrame):
        tot_s_load = df_or_none["solar_to_load_kw"].sum() if "solar_to_load_kw" in df_or_none.columns else 0.0
        tot_s_bat = df_or_none["solar_to_battery_kw"].sum() if "solar_to_battery_kw" in df_or_none.columns else 0.0
        tot_s_grid = df_or_none["solar_to_grid_kw"].sum() if "solar_to_grid_kw" in df_or_none.columns else 0.0
        tot_b_load = df_or_none["battery_to_load_kw"].sum() if "battery_to_load_kw" in df_or_none.columns else 0.0
        tot_g_import = df_or_none["grid_import_kw"].sum() if "grid_import_kw" in df_or_none.columns else 0.0
    else:
        tot_s_load = solar_to_load
        tot_s_bat = solar_to_battery
        tot_s_grid = solar_to_grid
        tot_b_load = battery_to_load
        tot_g_import = grid_import

    nodes = [
        "Rooftop Solar PV",              # 0
        "State DISCOM Grid Import",      # 1
        "BESS Battery Storage",          # 2
        "Facility C&I Load Demand",      # 3
        "DISCOM Feed-In Net Export",     # 4
    ]

    sources = [0, 0, 0, 1, 2]
    targets = [3, 2, 4, 3, 3]
    values = [
        max(0.1, round(tot_s_load, 1)),
        max(0.1, round(tot_s_bat, 1)),
        max(0.1, round(tot_s_grid, 1)),
        max(0.1, round(tot_g_import, 1)),
        max(0.1, round(tot_b_load, 1)),
    ]

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=16,
                    thickness=20,
                    line=dict(color="rgba(255, 255, 255, 0.12)", width=1),
                    label=nodes,
                    color=["#D97706", "#E11D48", "#059669", "#0284C7", "#64748B"],
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=[
                        "rgba(217, 119, 6, 0.25)",
                        "rgba(5, 150, 105, 0.25)",
                        "rgba(100, 116, 139, 0.25)",
                        "rgba(225, 29, 72, 0.25)",
                        "rgba(5, 150, 105, 0.25)",
                    ],
                ),
            )
        ]
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text="Aggregate Energy Flow Distribution (kWh / Units)",
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["margin"] = dict(l=35, r=35, t=45, b=35)
    fig.update_layout(**layout)
    return fig


def plot_strategy_cost_comparison(comp_dict: Dict[str, Any]) -> go.Figure:
    """Redesigned electricity operating cost chart comparing strategies with clear financial differences."""
    strategies = ["Unmanaged (No BESS)", "Rule-Based Heuristic", "Proposed MILP Optimization"]
    
    # Scale raw baseline costs to Indian Rupees (INR)
    unm_cost = comp_dict.get("unm_total_cost", 86.42) * INR_CONVERSION_RATE
    rb_cost = comp_dict.get("rb_total_cost", 58.15) * INR_CONVERSION_RATE
    opt_cost = comp_dict.get("opt_total_cost", 49.30) * INR_CONVERSION_RATE
    
    costs_inr = [unm_cost, rb_cost, opt_cost]
    colors = ["#F43F5E", "#F59E0B", "#10B981"]

    rb_pct = ((rb_cost - unm_cost) / unm_cost) * 100.0 if unm_cost > 0 else 0
    opt_pct = ((opt_cost - unm_cost) / unm_cost) * 100.0 if unm_cost > 0 else 0

    annotations_text = [
        f"₹{unm_cost:,.2f}<br><span style='font-size:9px;color:#94A3B8;'>Reference Baseline</span>",
        f"₹{rb_cost:,.2f}<br><span style='font-size:9px;color:#FBBF24;'>{rb_pct:.1f}% vs Base</span>",
        f"₹{opt_cost:,.2f}<br><span style='font-size:9px;color:#34D399;'>{opt_pct:.1f}% vs Base</span>",
    ]

    hover_text = [
        f"<b>Unmanaged (Reference)</b><br>Total Cost: ₹{unm_cost:,.2f}<br>Storage: 0 kWh<br>Baseline Grid Import",
        f"<b>Rule-Based Heuristic</b><br>Total Cost: ₹{rb_cost:,.2f}<br>Savings vs Base: ₹{unm_cost - rb_cost:,.2f} ({abs(rb_pct):.1f}%)<br>Greedy Solar Self-Consumption",
        f"<b>Proposed MILP Optimization</b><br>Total Cost: ₹{opt_cost:,.2f}<br>Savings vs Base: ₹{unm_cost - opt_cost:,.2f} ({abs(opt_pct):.1f}%)<br>Savings vs Heuristic: ₹{rb_cost - opt_cost:,.2f}<br>Time-of-Day Tariff Arbitrage",
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=strategies,
                y=costs_inr,
                marker=dict(
                    color=colors,
                    line=dict(color="rgba(255,255,255,0.12)", width=1),
                ),
                text=annotations_text,
                textposition="outside",
                textfont=dict(size=10, color="#F0F4F8", family="JetBrains Mono"),
                hovertext=hover_text,
                hoverinfo="text",
                width=0.45,
            )
        ]
    )

    # Add reference dashed line at Unmanaged level
    fig.add_hline(
        y=unm_cost,
        line_dash="dot",
        line_color="rgba(244, 63, 94, 0.4)",
        line_width=1,
        annotation_text="Base Expenditure",
        annotation_position="top left",
        annotation_font=dict(size=9, color="#F43F5E", family="Inter"),
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text="Electricity Operating Cost Benchmark (₹ INR) & Savings vs Reference",
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["yaxis_title"] = "Total Electricity Cost (₹ INR)"
    layout["yaxis"]["range"] = [0, max(costs_inr) * 1.25]
    layout["margin"] = dict(l=55, r=25, t=50, b=40)
    fig.update_layout(**layout)
    return fig


def plot_tou_price_arbitrage(df: pd.DataFrame, title: str = "24-Hour DISCOM Time-of-Day (ToD) Tariff vs Battery SOC") -> go.Figure:
    """Dual-axis plot showing DISCOM ToD tariff in ₹/Unit overlaid with battery SOC dispatch."""
    fig = go.Figure()

    if "price_per_kwh" in df.columns:
        inr_tariff = df["price_per_kwh"] * TOD_TARIFF_INR_SCALE
    else:
        inr_tariff = [7.50] * len(df)

    step_axis = df["step"] if "step" in df.columns else list(range(len(df)))

    fig.add_trace(
        go.Scatter(
            x=step_axis,
            y=inr_tariff,
            name="DISCOM ToD Tariff (₹/Unit)",
            mode="lines+markers",
            line=dict(color="#F43F5E", width=1.8, dash="dot"),
            yaxis="y2",
            hovertemplate="ToD Rate: ₹%{y:.2f} / Unit<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=step_axis,
            y=df["soc"] * 100.0 if "soc" in df.columns else [50.0] * len(df),
            name="Optimized BESS SOC (%)",
            mode="lines",
            line=dict(color="#10B981", width=2),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.08)",
            hovertemplate="Battery SOC: %{y:.1f}%<extra></extra>",
        )
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Hour of Day (00:00 - 23:00 IST)"
    layout["yaxis"] = dict(title="Battery SOC (%)", range=[0, 105], gridcolor="rgba(255, 255, 255, 0.05)")
    layout["yaxis2"] = dict(
        title="DISCOM Tariff (₹ / Unit)",
        overlaying="y",
        side="right",
        range=[0, 16],
        gridcolor="rgba(244, 63, 94, 0.08)",
    )
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    layout["margin"] = dict(l=45, r=50, t=45, b=35)

    fig.update_layout(**layout)
    return fig


def plot_model_residuals(y_true: np.ndarray, y_pred: np.ndarray, model_name: str) -> go.Figure:
    """Distribution histogram of forecasting residuals with target reference."""
    residuals = y_true - y_pred
    fig = go.Figure(
        data=[
            go.Histogram(
                x=residuals,
                nbinsx=35,
                marker=dict(color="#64748B", line=dict(color="rgba(255,255,255,0.08)", width=0.8)),
                opacity=0.85,
            )
        ]
    )
    fig.add_vline(x=0.0, line_dash="dash", line_color="#10B981", line_width=1.2, annotation_text="Zero Error (0 kW)", annotation_font=dict(size=9, color="#10B981"))

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=f"Residual Error Distribution ({model_name})",
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Forecast Residual (kW)"
    layout["yaxis_title"] = "Frequency Count"
    layout["margin"] = dict(l=45, r=25, t=45, b=35)
    fig.update_layout(**layout)
    return fig


def plot_feature_importances(feature_names: List[str], importances: List[float], title: str = "Feature Importance Attribution") -> go.Figure:
    """Horizontal bar chart displaying relative feature importances."""
    sorted_idx = np.argsort(importances)
    sorted_feats = [feature_names[i] for i in sorted_idx][-8:]
    sorted_scores = [importances[i] for i in sorted_idx][-8:]

    fig = go.Figure(
        data=[
            go.Bar(
                x=sorted_scores,
                y=sorted_feats,
                orientation="h",
                marker=dict(
                    color="#0284C7",
                    line=dict(color="rgba(255,255,255,0.08)", width=0.8),
                ),
            )
        ]
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Relative Importance Weight"
    layout["margin"] = dict(l=130, r=25, t=45, b=35)
    fig.update_layout(**layout)
    return fig


def plot_roi_payback_curve(years: int, pv_kw: float, bat_kwh: float, annual_savings_inr: float) -> go.Figure:
    """Projected multi-year cumulative cash flow and capital payback curve in Indian Rupees (₹ INR)."""
    pv_capex_inr = pv_kw * 48000.0
    bat_capex_inr = bat_kwh * 28000.0
    initial_investment_inr = pv_capex_inr + bat_capex_inr

    timeline = list(range(0, years + 1))
    cumulative_cash_flow = [-initial_investment_inr + (annual_savings_inr * y) for y in timeline]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timeline,
            y=cumulative_cash_flow,
            mode="lines+markers",
            name="Net Cumulative Cash Flow (₹)",
            line=dict(color="#10B981", width=2),
            marker=dict(size=5, color="#10B981"),
            hovertemplate="Year %{x}: ₹%{y:,.0f}<extra></extra>",
        )
    )

    fig.add_hline(
        y=0.0,
        line_dash="dash",
        line_color="#F59E0B",
        line_width=1.2,
        annotation_text="Breakeven Point",
        annotation_position="bottom right",
        annotation_font=dict(size=9, color="#F59E0B", family="Inter"),
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=f"Capital Payback Horizon ({pv_kw:.1f} kWp Solar + {bat_kwh:.1f} kWh BESS)",
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Project Timeline (Years)"
    layout["yaxis_title"] = "Cumulative Cash Flow (₹ INR)"
    layout["margin"] = dict(l=65, r=25, t=45, b=35)

    fig.update_layout(**layout)
    return fig


def plot_quantile_forecast_chart(
    df: pd.DataFrame,
    title: str,
    target_name: str = "Solar Power",
    y_label: str = "Power (kW)",
    theme_color: str = "#F59E0B",
) -> go.Figure:
    """Probabilistic confidence ribbon chart displaying P10 (floor), P50 (median), P90 (ceiling), and actuals."""
    fig = go.Figure()
    x_axis = df["timestamp"] if "timestamp" in df.columns else (df["step"] if "step" in df.columns else df.index)

    # 1. P90 Upper Bound (Transparent line for fill basis)
    if "p90" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["p90"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
                name="P90 (Upper 90%)",
            )
        )

    # 2. P10 Lower Bound with translucent shaded ribbon fill to P90
    if "p10" in df.columns:
        fill_color = "rgba(245, 158, 11, 0.18)" if theme_color == "#F59E0B" else "rgba(56, 189, 248, 0.18)"
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df["p10"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor=fill_color,
                name="80% Confidence Band (P10 - P90)",
                hovertemplate="P10 Floor: %{y:.2f} kW<extra></extra>",
            )
        )

    # 3. P50 Median Forecast Line
    p50_col = "p50" if "p50" in df.columns else "predicted"
    if p50_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df[p50_col],
                mode="lines",
                name="P50 Median Forecast",
                line=dict(color=theme_color, width=2.5),
                hovertemplate="P50 Forecast: %{y:.2f} kW<extra></extra>",
            )
        )

    # 4. Actual Observed Line
    actual_col = "actual" if "actual" in df.columns else "actual_value"
    if actual_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df[actual_col],
                mode="lines",
                name="Actual Ground Truth",
                line=dict(color="#10B981", width=2, dash="dot"),
                hovertemplate="Actual: %{y:.2f} kW<extra></extra>",
            )
        )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Timeline"
    layout["yaxis_title"] = y_label
    layout["margin"] = dict(l=55, r=25, t=45, b=35)
    layout["legend"] = dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(16, 23, 38, 0.8)",
    )

    fig.update_layout(**layout)
    return fig


def plot_shap_feature_importance(
    features_list: List[Dict[str, Any]],
    title: str = "SHAP Global Feature Importance (Mean |SHAP Value|)",
) -> go.Figure:
    """Horizontal bar chart ranking features by global SHAP impact."""
    df_shap = pd.DataFrame(features_list)
    if df_shap.empty or "feature" not in df_shap.columns or "importance" not in df_shap.columns:
        return go.Figure()

    df_shap = df_shap.sort_values(by="importance", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_shap["importance"],
            y=df_shap["feature"],
            orientation="h",
            marker=dict(
                color=df_shap["importance"],
                colorscale="Viridis",
                showscale=False,
            ),
            hovertemplate="<b>%{y}</b><br>Mean |SHAP|: %{x:.4f} kW<extra></extra>",
        )
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Mean Absolute SHAP Value (|ΔkW|)"
    layout["margin"] = dict(l=140, r=25, t=45, b=35)

    fig.update_layout(**layout)
    return fig


def plot_shap_local_waterfall(
    attributions: List[Dict[str, Any]],
    base_value: float,
    predicted_value: float,
    title: str = "SHAP Local Prediction Decomposition",
) -> go.Figure:
    """Diverging horizontal bar chart displaying directional feature impacts for a specific sample."""
    df_loc = pd.DataFrame(attributions)
    if df_loc.empty:
        return go.Figure()

    df_loc = df_loc.sort_values(by="shap_value", ascending=True)
    colors = ["#10B981" if s >= 0 else "#EF4444" for s in df_loc["shap_value"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_loc["shap_value"],
            y=[f"{row['feature']} (= {row['value']:.2f})" for _, row in df_loc.iterrows()],
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="<b>%{y}</b><br>Impact: %{x:+.3f} kW<extra></extra>",
        )
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=f"{title} (Base: {base_value:.2f} kW → Forecast: {predicted_value:.2f} kW)",
        font=dict(size=11, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "SHAP Impact on Forecast (kW)"
    layout["margin"] = dict(l=170, r=25, t=45, b=35)

    fig.update_layout(**layout)
    return fig


def plot_battery_degradation_cycles(
    dod_histogram: Dict[str, float],
    title: str = "ASTM E1049-85 Rainflow Cycle Distribution",
) -> go.Figure:
    """Bar chart displaying Rainflow cycle counts across Depth-of-Discharge (DOD) stress bins."""
    bins = list(dod_histogram.keys())
    counts = list(dod_histogram.values())

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=bins,
            y=counts,
            marker=dict(
                color=["#10B981", "#34D399", "#FBBF24", "#F59E0B", "#EF4444"],
            ),
            hovertemplate="<b>DOD Bin: %{x}</b><br>Rainflow Cycles: %{y:.1f}<extra></extra>",
        )
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=title,
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Depth of Discharge (DOD) Range"
    layout["yaxis_title"] = "Extracted Cycles"
    layout["margin"] = dict(l=55, r=25, t=45, b=35)

    fig.update_layout(**layout)
    return fig


def plot_soh_retention_gauge(soh: float, rul_years: float = 15.0) -> go.Figure:
    """Industrial radial gauge displaying battery State of Health (SOH) and Remaining Useful Life."""
    soh_pct = float(soh * 100.0)

    color = "#10B981" if soh_pct >= 90.0 else ("#F59E0B" if soh_pct >= 80.0 else "#EF4444")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=soh_pct,
            number={"suffix": "%", "font": {"size": 24, "color": color, "family": "JetBrains Mono"}},
            title={"text": f"State of Health (SOH)<br><span style='font-size:0.7em;color:#94A3B8'>RUL: ~{rul_years:.1f} Yrs</span>", "font": {"size": 11, "color": "#CBD5E1", "family": "Inter"}},
            gauge={
                "axis": {"range": [60, 100], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.2)", "tickfont": {"size": 9, "color": "#94A3B8"}},
                "bar": {"color": color, "thickness": 0.22},
                "bgcolor": "rgba(255,255,255,0.04)",
                "borderwidth": 1,
                "bordercolor": "rgba(255,255,255,0.08)",
                "steps": [
                    {"range": [60, 80], "color": "rgba(239, 68, 68, 0.25)"},
                    {"range": [80, 90], "color": "rgba(245, 158, 11, 0.2)"},
                    {"range": [90, 100], "color": "rgba(16, 185, 129, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": "#EF4444", "width": 2},
                    "thickness": 0.75,
                    "value": 80.0,
                },
            },
        )
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["margin"] = dict(l=25, r=25, t=35, b=25)
    layout["height"] = 190
    fig.update_layout(**layout)
    return fig


def plot_live_weather_solar_curve(
    hourly_data: Dict[str, Any],
    city_name: str = "Global Coordinates",
) -> go.Figure:
    """Dual-axis line chart comparing live global solar irradiance (GHI) and estimated PV generation."""
    times = hourly_data.get("time", [])
    ghis = hourly_data.get("ghi_w_m2", [])
    pvs = hourly_data.get("estimated_solar_kw", [])
    temps = hourly_data.get("temperature_c", [])

    fig = go.Figure()

    # Solar PV Power Line (Primary Y-axis)
    fig.add_trace(
        go.Scatter(
            x=times,
            y=pvs,
            mode="lines",
            name="Physical PV Generation (kW)",
            line=dict(color="#F59E0B", width=2.5),
            hovertemplate="%{x}<br>PV Power: <b>%{y:.2f} kW</b><extra></extra>",
        )
    )

    # GHI Irradiance Area (Secondary Y-axis)
    fig.add_trace(
        go.Scatter(
            x=times,
            y=ghis,
            mode="lines",
            name="Global Irradiance (GHI W/m²)",
            line=dict(color="#38BDF8", width=1.5, dash="dot"),
            yaxis="y2",
            hovertemplate="%{x}<br>GHI: <b>%{y:.1f} W/m²</b><extra></extra>",
        )
    )

    layout = {**INDUSTRIAL_LAYOUT}
    layout["title"] = dict(
        text=f"Live Solar PV Feed ({city_name}) - Open-Meteo High-Resolution Model",
        font=dict(size=12, color="#F0F4F8", family="Inter"),
        x=0.01,
        y=0.96,
    )
    layout["xaxis_title"] = "Timestamp"
    layout["yaxis_title"] = "PV Power Output (kW)"
    layout["yaxis2"] = dict(
        title=dict(text="GHI Irradiance (W/m²)", font=dict(color="#38BDF8", size=10)),
        tickfont=dict(color="#38BDF8", size=9),
        overlaying="y",
        side="right",
        showgrid=False,
    )
    layout["margin"] = dict(l=55, r=55, t=45, b=35)
    layout["legend"] = dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(16, 23, 38, 0.8)",
    )

    fig.update_layout(**layout)
    return fig

