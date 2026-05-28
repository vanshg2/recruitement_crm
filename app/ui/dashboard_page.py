"""
Dashboard Page
Recruitment CRM
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import date
from app.auth.auth import is_admin, get_current_user
from app.dashboard.analytics import (
    get_dashboard_kpis, get_monthly_trend, get_status_distribution,
    get_company_pipeline, get_recruiter_performance, get_upcoming_90day_alerts,
)
from app.utils.whatsapp import get_whatsapp_url

CHART_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4"]
CHART_LAYOUT = dict(
    font_family="Plus Jakarta Sans",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
    font=dict(color="#CBD5E1"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def kpi_card(icon, label, value, variant="blue", prefix=""):
    value_str = f"{prefix}{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    st.markdown(f"""
    <div class="kpi-card kpi-{variant}">
        <div class="kpi-stripe"></div>
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value_str}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_dashboard():
    user = get_current_user()
    kpis = get_dashboard_kpis()
    admin = is_admin()

    first_name = user['full_name'].split()[0]
    today_str = date.today().strftime('%A, %B %d %Y')

    st.markdown(f"""
    <div class="page-title">👋 Welcome, {first_name}!</div>
    <div class="page-subtitle">Here is today's summary — {today_str}</div>
    """, unsafe_allow_html=True)

    # 90-Day Alert Banner
    if kpis["alerts_90_day"] > 0 and admin:
        st.markdown(f"""
        <div class="alert-banner alert-warning">
            <span style="font-size:1.25rem;">🎯</span>
            <div>
                <strong>{kpis['alerts_90_day']} candidate(s)</strong> have completed 90 days.
                Follow up with the company to collect payment!
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── KPI Row 1 — Candidate Stats (visible to all) ──
    st.markdown("**📊 Candidate Overview**")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("👥", "Total Candidates", kpis["total_candidates"], variant="blue")
    with c2:
        kpi_card("⏳", "In Process", kpis["active_candidates"], variant="purple")
    with c3:
        kpi_card("🏢", "Currently Working", kpis["joined_candidates"], variant="green")
    with c4:
        kpi_card("❌", "Not Joined", kpis["drops"], variant="red")
    with c5:
        kpi_card("📅", "Joined This Month", kpis["month_joins"], variant="blue")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI Row 2 — Financial Stats (Admin only) ──
    if admin:
        st.markdown("**💰 Financial Overview**")
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            kpi_card("💰", "Amount to Collect", kpis["pending_payment"], variant="orange", prefix="₹")
        with f2:
            kpi_card("✅", "Amount Received", kpis["received_payment"], variant="green", prefix="₹")
        with f3:
            kpi_card("📈", "This Month Earnings", kpis["month_revenue"], variant="green", prefix="₹")
        with f4:
            kpi_card("🎯", "Payment Due (90 Days)", kpis["completed_90_days"], variant="orange")
        with f5:
            kpi_card("🔔", "Unread Alerts", kpis["unread_notifications"], variant="purple")
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 1 ──
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">📈 Monthly Joining Trend</div>
        </div>
        """, unsafe_allow_html=True)

        trend_df = get_monthly_trend(12)
        if not trend_df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Bar(x=trend_df["month"], y=trend_df["joins"],
                       name="Joins", marker_color="#3B82F6",
                       opacity=0.85, marker_line_width=0),
                secondary_y=False,
            )
            if admin:
                fig.add_trace(
                    go.Scatter(x=trend_df["month"], y=trend_df["revenue"],
                               name="Revenue (₹)", mode="lines+markers",
                               line=dict(color="#10B981", width=2.5),
                               marker=dict(size=7, color="#10B981")),
                    secondary_y=True,
                )
            fig.update_layout(
                **CHART_LAYOUT, height=300,
                xaxis=dict(showgrid=False, tickangle=-30, color="#94A3B8"),
                yaxis=dict(showgrid=True, gridcolor="#1E293B", title="Joins", color="#94A3B8"),
                yaxis2=dict(showgrid=False, title="Revenue (₹)" if admin else "", color="#94A3B8"),
                barmode="group",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available yet.")

    with col_right:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">🍩 Candidate Status</div>
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
                textfont_size=10,
            )
            fig.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 2 ──
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("""
        <div class="section-header">
            <div class="section-title">🏢 Company-wise Placements</div>
        </div>
        """, unsafe_allow_html=True)

        if not admin:
            st.info("Company financial data is visible to admins only.")
        else:
            company_df = get_company_pipeline()
            if not company_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=company_df["company"], x=company_df["pending_amount"],
                    name="Pending (₹)", orientation="h",
                    marker_color="#F59E0B", marker_line_width=0,
                ))
                fig.add_trace(go.Bar(
                    y=company_df["company"], x=company_df["received_amount"],
                    name="Received (₹)", orientation="h",
                    marker_color="#10B981", marker_line_width=0,
                ))
                fig.update_layout(
                    **CHART_LAYOUT, height=300, barmode="stack",
                    xaxis=dict(showgrid=True, gridcolor="#1E293B", tickprefix="₹", color="#94A3B8"),
                    yaxis=dict(showgrid=False, color="#94A3B8"),
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
                color_discrete_map={"joins": "#3B82F6", "drops": "#EF4444"},
                labels={"value": "Count", "variable": ""},
            )
            fig.update_layout(
                **CHART_LAYOUT, height=300,
                xaxis=dict(showgrid=False, tickangle=-20, color="#94A3B8"),
                yaxis=dict(showgrid=True, gridcolor="#1E293B", color="#94A3B8"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recruiter data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 90-Day Approaching Alerts ──
    if admin:
        alerts = get_upcoming_90day_alerts()
        if alerts:
            st.markdown(f"""
            <div class="section-header">
                <div class="section-title">⏰ Approaching 90 Days — {len(alerts)} Candidates</div>
            </div>
            """, unsafe_allow_html=True)

            for alert in alerts[:8]:
                urgency = "🔴" if alert["days_left"] <= 5 else ("🟡" if alert["days_left"] <= 10 else "🟢")
                border = "#EF4444" if alert["days_left"] <= 5 else "#F59E0B"
                wa_url = get_whatsapp_url(alert["phone"])

                col_info, col_action = st.columns([5, 1])
                with col_info:
                    st.markdown(f"""
                    <div style="
                        background:#1E293B;
                        border:1px solid #334155;
                        border-left:4px solid {border};
                        border-radius:10px;
                        padding:0.875rem 1.25rem;
                        margin-bottom:0.5rem;
                    ">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="display:flex;align-items:center;gap:0.75rem;">
                                <span style="font-size:1.2rem;">{urgency}</span>
                                <div>
                                    <div style="font-weight:700;color:#F1F5F9;font-size:0.9rem;">{alert['name']}</div>
                                    <div style="color:#64748B;font-size:0.78rem;">
                                        🏢 {alert['company']} &nbsp;|&nbsp;
                                        📅 Joined: {alert['joining_date']} &nbsp;|&nbsp;
                                        ⏳ Day {alert['days_in']} of 90
                                    </div>
                                </div>
                            </div>
                            <div style="display:flex;gap:1.5rem;align-items:center;">
                                <div style="text-align:right;">
                                    <div style="font-size:0.72rem;color:#64748B;">Days Left</div>
                                    <div style="font-size:1.2rem;font-weight:800;color:{border};">{alert['days_left']}</div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-size:0.72rem;color:#64748B;">Fee</div>
                                    <div style="font-size:0.9rem;font-weight:700;color:#10B981;">₹{alert['payment_amount']:,.0f}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_action:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        f'<a href="{wa_url}" target="_blank" style="display:flex;justify-content:center;'
                        f'background:#25D366;color:white;padding:0.4rem 0.6rem;border-radius:8px;'
                        f'font-size:0.8rem;font-weight:600;text-decoration:none;">💬 WA</a>',
                        unsafe_allow_html=True
                    )