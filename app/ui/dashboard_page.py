"""
Dashboard Page
BLACKWOODS CRM
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import date
from app.dashboard.analytics import (
    get_dashboard_kpis, get_monthly_trend, get_status_distribution,
    get_company_pipeline, get_recruiter_performance, get_upcoming_90day_alerts,
    mark_all_notifications_read
)
from app.auth.auth import get_current_user
from app.utils.whatsapp import get_whatsapp_url


# ─────────────────────────────────────────────────
# CHART THEME
# ─────────────────────────────────────────────────

CHART_COLORS = ["#1C64F2", "#0E9F6E", "#FF8A4C", "#7E3AF2", "#F05252", "#3F83F8"]
CHART_LAYOUT = dict(
    font_family="Plus Jakarta Sans",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def kpi_card(icon: str, label: str, value, delta: str = "", variant: str = "blue", prefix: str = ""):
    """Render a styled KPI card."""
    value_str = f"{prefix}{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    delta_html = f'<div class="kpi-delta" style="color:#059669;">↑ {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="kpi-card kpi-{variant}">
        <div class="kpi-stripe"></div>
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value_str}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_dashboard():
    user = get_current_user()
    kpis = get_dashboard_kpis()

    # ── Page Header ──────────────────────────────
    first_name = user['full_name'].split()[0]
    today_str = date.today().strftime('%A, %B %d %Y')
    st.markdown(f"""
    <div class="page-title">📊Dashboard, {first_name}!</div>
    <div class="page-subtitle">Here is today's summary — {today_str}</div>
    """, unsafe_allow_html=True)

    # ── 90-Day Alert Banner ──────────────────────
    if kpis["alerts_90_day"] > 0:
        st.markdown(f"""
        <div class="alert-banner alert-warning">
            <span style="font-size:1.25rem;">🎯</span>
            <div>
                <strong>{kpis['alerts_90_day']} candidate(s)</strong> have completed 90 days and are eligible for payment collection.
                Immediate follow-up required.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── KPI Row 1 ────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("👥", "Total Candidates", kpis["total_candidates"], variant="blue")
    with c2:
        kpi_card("✅", "In Process", kpis["active_candidates"], variant="green")
    with c3:
        kpi_card("🏢", "Currently Working", kpis["joined_candidates"], variant="purple")
    with c4:
        kpi_card("🎯", "Payment Due", kpis["completed_90_days"], variant="orange")
    with c5:
        kpi_card("❌", "Dropped", kpis["drops"], variant="red")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI Row 2 ────────────────────────────────
    from app.auth.auth import is_admin
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if is_admin():
            kpi_card("💰", "Amount to Collect", kpis["pending_payment"], variant="orange", prefix="₹")
        else:
            kpi_card("📅", "Joined This Month", kpis["month_joins"], variant="blue")
    with c2:
        if is_admin():
            kpi_card("✅", "Amount Received", kpis["received_payment"], variant="green", prefix="₹")
        else:
            kpi_card("👥", "My Candidates", kpis["active_candidates"], variant="purple")
    with c3:
        kpi_card("📅", "Joined This Month", kpis["month_joins"], variant="blue")
    with c4:
        if is_admin():
            kpi_card("📈", "This Month Earnings", kpis["month_revenue"], variant="green", prefix="₹")
        else:
            kpi_card("✅", "Currently Working", kpis["joined_candidates"], variant="green")
    with c5:
        kpi_card("🔔", "New Alerts", kpis["unread_notifications"], variant="purple")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 1 ─────────────────────────────
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">📈 Monthly Joining & Revenue Trend</div>
        </div>
        """, unsafe_allow_html=True)

        trend_df = get_monthly_trend(12)
        if not trend_df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Bar(
                    x=trend_df["month"], y=trend_df["joins"],
                    name="Joins", marker_color="#1C64F2",
                    opacity=0.85, marker_line_width=0,
                ),
                secondary_y=False,
            )
            if is_admin():
                fig.add_trace(
                    go.Scatter(
                        x=trend_df["month"], y=trend_df["revenue"],
                        name="Revenue (₹)", mode="lines+markers",
                        line=dict(color="#0E9F6E", width=2.5),
                        marker=dict(size=7, color="#0E9F6E"),
                    ),
                    secondary_y=True,
                )
            fig.update_layout(
                **CHART_LAYOUT,
                height=300,
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor="#F3F4F6", title="Joins"),
                yaxis2=dict(showgrid=False, title="Revenue (₹)"),
                barmode="group",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available yet.")

    with col_right:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">🍩 Status Distribution</div>
        </div>
        """, unsafe_allow_html=True)

        status_df = get_status_distribution()
        if not status_df.empty:
            fig = px.pie(
                status_df, values="count", names="status",
                hole=0.55, color_discrete_sequence=CHART_COLORS,
            )
            fig.update_traces(
                textposition="outside", textinfo="label+percent",
                textfont_size=11,
            )
            fig.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 2 ─────────────────────────────
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">🏢 Company-wise Pipeline</div>
        </div>
        """, unsafe_allow_html=True)

        if not is_admin():
            st.info("ℹ️ Company financial data is visible to admins only.")
        else:
            company_df = get_company_pipeline()
            if not company_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=company_df["company"], x=company_df["pending_amount"],
                    name="Pending (₹)", orientation="h",
                    marker_color="#FF8A4C", marker_line_width=0,
                ))
                fig.add_trace(go.Bar(
                    y=company_df["company"], x=company_df["received_amount"],
                    name="Received (₹)", orientation="h",
                    marker_color="#0E9F6E", marker_line_width=0,
                ))
                fig.update_layout(
                    **CHART_LAYOUT,
                    height=300,
                    barmode="stack",
                    xaxis=dict(showgrid=True, gridcolor="#F3F4F6", tickprefix="₹"),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No company data available.")

    with col_right:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">🏆 Recruiter Performance</div>
        </div>
        """, unsafe_allow_html=True)

        rec_df = get_recruiter_performance()
        if not rec_df.empty:
            fig = px.bar(
                rec_df, x="recruiter", y=["joins", "drops"],
                barmode="group",
                color_discrete_map={"joins": "#1C64F2", "drops": "#F05252"},
                labels={"value": "Count", "variable": ""},
            )
            fig.update_layout(**CHART_LAYOUT, height=300,
                              xaxis=dict(showgrid=False, tickangle=-20),
                              yaxis=dict(showgrid=True, gridcolor="#F3F4F6"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recruiter data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 90-Day Approaching Alerts ─────────────────
    alerts = get_upcoming_90day_alerts()
    if alerts:
        st.markdown(f"""
        <div class="section-header">
            <div class="section-title">⏰ Approaching 90-Day Mark ({len(alerts)} candidates)</div>
        </div>
        """, unsafe_allow_html=True)

        for alert in alerts[:8]:
            urgency = "🔴" if alert["days_left"] <= 5 else ("🟡" if alert["days_left"] <= 10 else "🟢")
            wa_url = get_whatsapp_url(alert["phone"])
            st.markdown(f"""
            <div style="
                display:flex; align-items:center; justify-content:space-between;
                padding: 0.875rem 1.25rem;
                background: white;
                border: 1px solid #E5E7EB;
                border-left: 4px solid {'#EF4444' if alert['days_left'] <= 5 else '#F59E0B'};
                border-radius: 10px;
                margin-bottom: 0.5rem;
                box-shadow: 0 1px 3px rgba(0,0,0,.05);
            ">
                <div style="display:flex; align-items:center; gap:1rem;">
                    <div style="font-size:1.2rem;">{urgency}</div>
                    <div>
                        <div style="font-weight:700; color:#111928; font-size:0.9rem;">{alert['name']}</div>
                        <div style="color:#6B7280; font-size:0.78rem;">🏢 {alert['company']} &nbsp;|&nbsp; 📅 Joined: {alert['joining_date']} &nbsp;|&nbsp; ⏳ Day {alert['days_in']} of 90</div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:1rem;">
                    <div style="text-align:right;">
                        <div style="font-size:0.75rem; color:#6B7280;">Days Left</div>
                        <div style="font-size:1.1rem; font-weight:800; color:{'#EF4444' if alert['days_left'] <= 5 else '#1C64F2'};">{alert['days_left']}</div>
                    </div>
                    {f'<div style="text-align:right;"><div style="font-size:0.75rem; color:#6B7280;">Fee</div><div style="font-size:0.9rem; font-weight:700; color:#0E9F6E;">₹{alert["payment_amount"]:,.0f}</div></div>' if is_admin() else ''}
                    <a href="{wa_url}" target="_blank" class="wa-btn">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                        WhatsApp
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)