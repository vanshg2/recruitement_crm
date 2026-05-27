"""
RecruitPro CRM - Main Application Entry Point
"""

import streamlit as st
import os
import sys
from streamlit_option_menu import option_menu
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────────
# PAGE CONFIG (must be first Streamlit call)
# ─────────────────────────────────────────────────

st.set_page_config(
    page_title="RecruitPro CRM",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root Variables ── */
:root {
    --primary: #1C64F2;
    --primary-dark: #1A56DB;
    --primary-light: #EBF2FF;
    --accent: #0E9F6E;
    --accent-light: #DEF7EC;
    --warning: #FF8A4C;
    --warning-light: #FFF3E0;
    --danger: #F05252;
    --danger-light: #FDE8E8;
    --purple: #7E3AF2;
    --purple-light: #EDEBFE;
    --surface: #FFFFFF;
    --surface-2: #F9FAFB;
    --border: #E5E7EB;
    --text: #111928;
    --text-2: #4B5563;
    --text-3: #9CA3AF;
    --sidebar-bg: #0F172A;
    --sidebar-text: #CBD5E1;
    --sidebar-active: #1C64F2;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,.08), 0 2px 4px -1px rgba(0,0,0,.04);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,.08), 0 4px 6px -2px rgba(0,0,0,.03);
    --radius: 12px;
    --radius-sm: 8px;
    --radius-lg: 16px;
}

/* ── Base Reset ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text);
}

/* ── Hide Streamlit Branding ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }

/* ── Main Content Area ── */
.main .block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1600px !important;
}

/* ── Sidebar Styling ── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * {
    color: var(--sidebar-text) !important;
}
[data-testid="stSidebar"] .stButton button {
    background: transparent !important;
    border: none !important;
    color: var(--sidebar-text) !important;
    text-align: left !important;
    width: 100% !important;
    padding: 0.6rem 1rem !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    margin: 1px 0 !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #fff !important;
}

/* ── KPI Card ── */
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow-sm);
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.kpi-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}
.kpi-card .kpi-icon {
    width: 48px; height: 48px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 0.875rem;
}
.kpi-card .kpi-value {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.kpi-card .kpi-label {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-2);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kpi-card .kpi-delta {
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    gap: 3px;
}
.kpi-card .kpi-stripe {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: var(--radius) var(--radius) 0 0;
}

/* Colored KPI variants */
.kpi-blue .kpi-icon { background: var(--primary-light); }
.kpi-blue .kpi-stripe { background: var(--primary); }
.kpi-green .kpi-icon { background: var(--accent-light); }
.kpi-green .kpi-stripe { background: var(--accent); }
.kpi-orange .kpi-icon { background: var(--warning-light); }
.kpi-orange .kpi-stripe { background: var(--warning); }
.kpi-red .kpi-icon { background: var(--danger-light); }
.kpi-red .kpi-stripe { background: var(--danger); }
.kpi-purple .kpi-icon { background: var(--purple-light); }
.kpi-purple .kpi-stripe { background: var(--purple); }

/* ── Alert Banners ── */
.alert-banner {
    padding: 1rem 1.25rem;
    border-radius: var(--radius-sm);
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    font-size: 0.875rem;
}
.alert-warning {
    background: var(--warning-light);
    border-left: 4px solid var(--warning);
    color: #7C3D12;
}
.alert-danger {
    background: var(--danger-light);
    border-left: 4px solid var(--danger);
    color: #771D1D;
}
.alert-success {
    background: var(--accent-light);
    border-left: 4px solid var(--accent);
    color: #014737;
}
.alert-info {
    background: var(--primary-light);
    border-left: 4px solid var(--primary);
    color: #1E3A8A;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
}
.section-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Badge ── */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.badge-blue   { background: var(--primary-light); color: var(--primary-dark); }
.badge-green  { background: var(--accent-light); color: #065F46; }
.badge-orange { background: var(--warning-light); color: #92400E; }
.badge-red    { background: var(--danger-light); color: #991B1B; }
.badge-gray   { background: #F3F4F6; color: #4B5563; }
.badge-purple { background: var(--purple-light); color: #5521B5; }

/* ── WhatsApp Button ── */
.wa-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #25D366; color: white !important;
    padding: 0.4rem 0.875rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600;
    text-decoration: none !important;
    transition: background 0.2s ease;
}
.wa-btn:hover { background: #128C7E; }

/* ── Notification Dot ── */
.notif-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--danger);
    border-radius: 50%;
    margin-left: 4px;
}

/* ── Timeline ── */
.timeline-item {
    display: flex; gap: 1rem;
    padding: 0.75rem 0;
    border-left: 2px solid var(--border);
    padding-left: 1.25rem;
    margin-left: 0.5rem;
    position: relative;
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: -5px; top: 1.1rem;
    width: 8px; height: 8px;
    background: var(--primary);
    border-radius: 50%;
    border: 2px solid white;
}
.timeline-date {
    font-size: 0.75rem;
    color: var(--text-3);
    white-space: nowrap;
    min-width: 120px;
    font-family: 'JetBrains Mono', monospace;
}
.timeline-content .title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text);
}
.timeline-content .desc {
    font-size: 0.8rem;
    color: var(--text-2);
    margin-top: 2px;
}

/* ── Dataframe Styling ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
}

/* ── Form Styling ── */
[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.5rem !important;
}

/* ── Input Styling ── */
.stTextInput input, .stSelectbox select, .stNumberInput input, .stTextArea textarea {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.875rem !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(28, 100, 242, 0.1) !important;
}

/* ── Button Overrides ── */
.stButton button[kind="primary"] {
    background: var(--primary) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    padding: 0.5rem 1.25rem !important;
    transition: background 0.2s ease !important;
}
.stButton button[kind="primary"]:hover {
    background: var(--primary-dark) !important;
}
.stButton button[kind="secondary"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: var(--surface) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px !important;
    background: var(--surface-2) !important;
    padding: 4px !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 1rem !important;
    color: var(--text-2) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--primary) !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1rem 1.25rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-3); }

/* ── Page Title ── */
.page-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.page-subtitle {
    font-size: 0.875rem;
    color: var(--text-2);
    margin-bottom: 1.5rem;
}

/* ── Login Card ── */
.login-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# IMPORTS AFTER CSS
# ─────────────────────────────────────────────────

from app.auth.auth import init_session, is_authenticated, login, logout, is_admin
from app.ui.login_page import render_login
from app.ui.sidebar import render_sidebar
from app.ui.dashboard_page import render_dashboard
from app.ui.candidates_page import render_candidates
from app.ui.add_candidate_page import render_add_candidate
from app.ui.recruiters_page import render_recruiters
from app.ui.payments_page import render_payments
from app.ui.companies_page import render_companies
from app.ui.notifications_page import render_notifications
from app.ui.settings_page import render_settings
from app.utils.scheduler import start_scheduler


# ─────────────────────────────────────────────────
# SCHEDULER INIT (once per session)
# ─────────────────────────────────────────────────

if "scheduler_started" not in st.session_state:
    try:
        start_scheduler()
        st.session_state.scheduler_started = True
    except Exception:
        st.session_state.scheduler_started = False


# ─────────────────────────────────────────────────
# SESSION INIT
# ─────────────────────────────────────────────────

init_session()

# ─────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────

if not is_authenticated():
    render_login()
else:
    # Render sidebar + get current page
    page = render_sidebar()

    # Route to correct page
    page_map = {
        "Dashboard":       render_dashboard,
        "Candidates":      render_candidates,
        "Add Candidate":   render_add_candidate,
        "Recruiters":      render_recruiters,
        "Payments":        render_payments,
        "Companies":       render_companies,
        "Notifications":   render_notifications,
        "Settings":        render_settings,
    }

    renderer = page_map.get(page, render_dashboard)
    renderer()
