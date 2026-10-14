"""High-precision industrial telemetry card renderers and page header components.
Customized for the Indian Smart Grid and Renewable Energy market (CEA / DISCOM / CERC standards).
Provides high contrast, tabular figures, Indian Rupee (₹) financial formatting, and clean semantic structure.
"""

from typing import Optional, List, Tuple, Dict, Any
import os
import streamlit as st

# Exchange rate / localized scale factor for converting baseline energy costs to Indian Rupees (INR)
INR_EXCHANGE_RATE = 85.0


def render_html(html_str: str):
    """Safely render HTML/SVG in Streamlit without markdown interpreting lines as code blocks."""
    clean_lines = [line.strip() for line in html_str.strip().splitlines() if line.strip()]
    clean_html = "\n".join(clean_lines)
    if hasattr(st, "html"):
        st.html(clean_html)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)


def render_sidebar_html(html_str: str):
    """Safely render HTML in Streamlit sidebar without markdown code block interpretation."""
    clean_lines = [line.strip() for line in html_str.strip().splitlines() if line.strip()]
    clean_html = "\n".join(clean_lines)
    if hasattr(st.sidebar, "html"):
        st.sidebar.html(clean_html)
    else:
        st.sidebar.markdown(clean_html, unsafe_allow_html=True)


def format_inr(value_usd_or_inr: float, is_already_inr: bool = False) -> str:
    """Format numerical cost into Indian Rupees (₹) with clean, standard Indian numbering."""
    val = value_usd_or_inr if is_already_inr else value_usd_or_inr * INR_EXCHANGE_RATE
    abs_val = abs(val)
    prefix = "-" if val < 0 else ""
    
    if abs_val >= 10000000:
        return f"{prefix}₹{abs_val / 10000000:.2f} Cr"
    elif abs_val >= 100000:
        return f"{prefix}₹{abs_val / 100000:.2f} Lakh"
    elif abs_val >= 1000:
        return f"{prefix}₹{abs_val:,.2f}"
    else:
        return f"{prefix}₹{abs_val:.2f}"


def render_kpi_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
    card_type: str = "default",
    icon: Optional[str] = None,
    subtitle: Optional[str] = None,
):
    """Render an engineering-grade KPI metric card without visual clutter."""
    # Dot indicator for domain context
    dot_color = "var(--text-tertiary)"
    if card_type == "solar":
        dot_color = "var(--color-solar-bright)"
    elif card_type in ("battery", "opt", "ai"):
        dot_color = "var(--color-battery-bright)"
    elif card_type == "load":
        dot_color = "var(--color-load-bright)"
    elif card_type == "grid":
        dot_color = "var(--color-grid-bright)"

    delta_class = "ems-delta-neutral"
    if delta:
        if delta_color == "normal":
            delta_class = "ems-delta-pos"
        elif delta_color in ("inverse", "neg", "alert"):
            delta_class = "ems-delta-neg"
        elif delta_color == "cyan":
            delta_class = "ems-delta-neutral"

    delta_html = f'<span class="ems-kpi-delta {delta_class}">{delta}</span>' if delta else ""
    sub_html = f'<span style="color: var(--text-muted); font-size: 0.70rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{subtitle}</span>' if subtitle else ""

    footer_html = ""
    if delta or subtitle:
        footer_html = f"""
        <div class="ems-kpi-footer">
            {delta_html}
            {sub_html}
        </div>
        """

    card_html = f"""
    <div class="ems-kpi-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="ems-kpi-label">{title}</span>
            <span style="width: 5px; height: 5px; border-radius: 50%; background-color: {dot_color}; flex-shrink: 0;"></span>
        </div>
        <div class="ems-kpi-value">{value}</div>
        {footer_html}
    </div>
    """
    render_html(card_html)


def render_strategy_comparison_cards(
    unm_cost_inr: str,
    unm_peak_kw: float,
    unm_grid_import_kwh: float,
    unm_self_consumption_pct: float,
    rb_cost_inr: str,
    rb_savings_inr: str,
    rb_savings_pct: float,
    rb_peak_kw: float,
    rb_grid_import_kwh: float,
    rb_self_consumption_pct: float,
    opt_cost_inr: str,
    opt_savings_vs_unm_inr: str,
    opt_savings_vs_unm_pct: float,
    opt_savings_vs_rb_inr: str,
    opt_peak_kw: float,
    opt_grid_import_kwh: float,
    opt_self_consumption_pct: float,
):
    """Render the 3-way strategy comparison hero section with disciplined layout and clear visual hierarchy."""
    html = f"""
    <div class="strategy-grid">
        <!-- 1. Unmanaged Baseline -->
        <div class="strategy-card">
            <div class="strategy-card-header">
                <span class="strategy-name">Unmanaged Microgrid</span>
                <span class="strategy-tag strategy-tag-base">Reference Base</span>
            </div>
            <div class="strategy-cost-block">
                <div class="strategy-cost-label">Total Electricity Bill</div>
                <div class="strategy-cost-figure" style="color: #F87171;">{unm_cost_inr}</div>
            </div>
            <div class="strategy-savings-block">
                <span style="color: var(--text-muted); font-size: 0.72rem;">Baseline benchmark (grid import with zero storage)</span>
            </div>
            <table class="strategy-specs-table">
                <tbody>
                    <tr>
                        <td>Peak Grid Demand</td>
                        <td class="spec-val">{unm_peak_kw:.2f} kW</td>
                    </tr>
                    <tr>
                        <td>Grid Import Intake</td>
                        <td class="spec-val">{unm_grid_import_kwh:,.1f} Units</td>
                    </tr>
                    <tr>
                        <td>Solar Self-Consumption</td>
                        <td class="spec-val">{unm_self_consumption_pct:.1f}%</td>
                    </tr>
                    <tr>
                        <td>Dispatch Intelligence</td>
                        <td class="spec-val" style="color: var(--text-muted);">None (Direct Flow)</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 2. Rule-Based Heuristic -->
        <div class="strategy-card">
            <div class="strategy-card-header">
                <span class="strategy-name">Rule-Based Heuristic</span>
                <span class="strategy-tag strategy-tag-heuristic">Heuristic Baseline</span>
            </div>
            <div class="strategy-cost-block">
                <div class="strategy-cost-label">Total Electricity Bill</div>
                <div class="strategy-cost-figure" style="color: #FBBF24;">{rb_cost_inr}</div>
            </div>
            <div class="strategy-savings-block strategy-savings-heuristic">
                <span style="color: var(--text-secondary); font-size: 0.72rem;">Saved <span class="strategy-savings-val" style="color: #FBBF24;">{rb_savings_inr}</span> (-{rb_savings_pct:.1f}% vs Base)</span>
            </div>
            <table class="strategy-specs-table">
                <tbody>
                    <tr>
                        <td>Peak Grid Demand</td>
                        <td class="spec-val">{rb_peak_kw:.2f} kW</td>
                    </tr>
                    <tr>
                        <td>Grid Import Intake</td>
                        <td class="spec-val">{rb_grid_import_kwh:,.1f} Units</td>
                    </tr>
                    <tr>
                        <td>Solar Self-Consumption</td>
                        <td class="spec-val">{rb_self_consumption_pct:.1f}%</td>
                    </tr>
                    <tr>
                        <td>Dispatch Intelligence</td>
                        <td class="spec-val" style="color: #FBBF24;">Greedy Self-Use</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 3. Proposed MILP Optimization -->
        <div class="strategy-card strategy-card-highlight">
            <div class="strategy-card-header">
                <span class="strategy-name">MILP Optimization</span>
                <span class="strategy-tag strategy-tag-optimal">Proposed System</span>
            </div>
            <div class="strategy-cost-block">
                <div class="strategy-cost-label">Total Electricity Bill</div>
                <div class="strategy-cost-figure" style="color: #34D399;">{opt_cost_inr}</div>
            </div>
            <div class="strategy-savings-block strategy-savings-optimal">
                <span style="color: var(--text-secondary); font-size: 0.72rem;">Saved <span class="strategy-savings-val" style="color: #34D399;">{opt_savings_vs_unm_inr}</span> (-{opt_savings_vs_unm_pct:.1f}% vs Base &bull; -{opt_savings_vs_rb_inr} vs Heuristic)</span>
            </div>
            <table class="strategy-specs-table">
                <tbody>
                    <tr>
                        <td>Peak Grid Demand</td>
                        <td class="spec-val" style="color: #34D399;">{opt_peak_kw:.2f} kW</td>
                    </tr>
                    <tr>
                        <td>Grid Import Intake</td>
                        <td class="spec-val">{opt_grid_import_kwh:,.1f} Units</td>
                    </tr>
                    <tr>
                        <td>Solar Self-Consumption</td>
                        <td class="spec-val" style="color: #34D399;">{opt_self_consumption_pct:.1f}%</td>
                    </tr>
                    <tr>
                        <td>Dispatch Intelligence</td>
                        <td class="spec-val" style="color: #34D399;">ToD Tariff Arbitrage</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """
    render_html(html)


def render_stat_strip(items: List[Dict[str, Any]]):
    """Render a horizontal strip ribbon of engineering metrics (non-card layout)."""
    blocks = []
    for item in items:
        label = item.get("label", "")
        val = item.get("val", "")
        sub = item.get("sub", "")
        color = item.get("color", "var(--text-primary)")
        sub_html = f'<span class="ems-stat-sub">{sub}</span>' if sub else ""
        blocks.append(f"""
        <div class="ems-stat-item">
            <span class="ems-stat-label">{label}</span>
            <span class="ems-stat-val" style="color: {color};">{val}</span>
            {sub_html}
        </div>
        """)
    html = f'<div class="ems-stat-strip">{"".join(blocks)}</div>'
    render_html(html)


def render_section_header(
    title: str,
    subtitle: Optional[str] = None,
    badge_text: Optional[str] = None,
    icon: Optional[str] = None,
):
    """Render a crisp, structured section divider with optional metadata."""
    badge_html = f'<span class="ems-status-pill">{badge_text}</span>' if badge_text else ""
    sub_html = f'<div class="ems-section-meta">{subtitle}</div>' if subtitle else ""

    header_html = f"""
    <div class="ems-section">
        <div class="ems-section-title">
            <span>{title}</span>
            {badge_html}
        </div>
        {sub_html}
    </div>
    """
    render_html(header_html)


def render_top_navigation():
    """Render a compact horizontal quick-navigation bar so all pages are always accessible,
    especially when the left sidebar is collapsed."""
    try:
        cols = st.columns(8)
        pages = [
            ("Home.py", "Home", "⚡"),
            ("pages/1_Overview.py", "Overview", "🏛️"),
            ("pages/2_Solar_Forecast.py", "Solar", "☀️"),
            ("pages/3_Load_Forecast.py", "Demand", "💡"),
            ("pages/4_Battery_Status.py", "Battery", "🔋"),
            ("pages/5_Energy_Flow.py", "Flow", "🔄"),
            ("pages/6_Optimization_EMS.py", "Dispatch", "🎯"),
            ("pages/7_Analytics_and_Comparison.py", "Analytics", "📈"),
        ]
        for i, (path, label, icon) in enumerate(pages):
            with cols[i]:
                try:
                    st.page_link(path, label=label, icon=icon, use_container_width=True)
                except Exception:
                    try:
                        st.page_link(f"dashboard/{path}", label=label, icon=icon, use_container_width=True)
                    except Exception:
                        pass
    except Exception:
        pass




def render_page_header(
    title: str,
    subtitle: str,
    badges: Optional[List[Tuple[str, str]]] = None,
    show_nav: bool = True,
):
    """Render a standardized executive page header with telemetry status badges and quick navigation."""
    badges_html = ""
    if badges:
        items = []
        for text, variant in badges:
            dot_class = "ems-dot-active"
            if variant in ("warning", "warn"):
                dot_class = "ems-dot-warn"
            elif variant in ("info", "load"):
                dot_class = "ems-dot-info"
            elif variant in ("neutral", "slate"):
                dot_class = "ems-dot-muted"
            items.append(f'<span class="ems-status-pill"><span class="ems-status-dot {dot_class}"></span>{text}</span>')
        badges_html = f'<div class="ems-status-strip">{"".join(items)}</div>'

    header_html = f"""
    <div class="ems-header">
        <div>
            <h1 class="ems-header-title">{title}</h1>
            <p class="ems-header-subtitle">{subtitle}</p>
        </div>
        {badges_html}
    </div>
    """
    render_html(header_html)
    if show_nav:
        render_top_navigation()


_CACHED_CUSTOM_CSS: Optional[str] = None


def inject_custom_css():
    """Inject custom industrial product styles into current Streamlit page."""
    global _CACHED_CUSTOM_CSS
    if _CACHED_CUSTOM_CSS is None:
        css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles", "custom.css")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                _CACHED_CUSTOM_CSS = f.read()
        else:
            _CACHED_CUSTOM_CSS = ""
    if _CACHED_CUSTOM_CSS:
        render_html(f"<style>{_CACHED_CUSTOM_CSS}</style>")
