"""
BLACKWOODS CRM - Main Application Entry Point
"""

import streamlit as st
import os
import sys
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass
# ─────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────

st.set_page_config(
    page_title="BLACKWOODS CRM",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────
# LOGO LOADER
# ─────────────────────────────────────────────────

def get_logo_b64():
    try:
        with open("images/logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

# ─────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #3B82F6;
    --primary-dark: #2563EB;
    --primary-light: #1E3A5F;
    --accent: #10B981;
    --accent-light: #064E3B;
    --warning: #F59E0B;
    --warning-light: #78350F;
    --danger: #EF4444;
    --danger-light: #7F1D1D;
    --purple: #8B5CF6;
    --purple-light: #3B0764;
    --surface: #1E293B;
    --surface-2: #0F172A;
    --border: #334155;
    --text: #F1F5F9;
    --text-2: #CBD5E1;
    --text-3: #64748B;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.3), 0 1px 2px rgba(0,0,0,.2);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,.3), 0 2px 4px -1px rgba(0,0,0,.2);
    --radius: 12px;
    --radius-sm: 8px;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text);
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }

.main .block-container {
    padding: 0.5rem 2rem 2rem !important;
    max-width: 1600px !important;
}

/* KPI Cards */
.kpi-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow-sm);
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.kpi-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.kpi-card .kpi-icon {
    width: 48px; height: 48px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 0.875rem;
}
.kpi-card .kpi-value {
    font-size: 2rem; font-weight: 800;
    line-height: 1; color: #F1F5F9; margin-bottom: 0.25rem;
}
.kpi-card .kpi-label {
    font-size: 0.8rem; font-weight: 500;
    color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;
}
.kpi-card .kpi-stripe {
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: var(--radius) var(--radius) 0 0;
}
.kpi-blue .kpi-icon { background: #1E3A5F; }
.kpi-blue .kpi-stripe { background: #3B82F6; }
.kpi-green .kpi-icon { background: #064E3B; }
.kpi-green .kpi-stripe { background: #10B981; }
.kpi-orange .kpi-icon { background: #78350F; }
.kpi-orange .kpi-stripe { background: #F59E0B; }
.kpi-red .kpi-icon { background: #7F1D1D; }
.kpi-red .kpi-stripe { background: #EF4444; }
.kpi-purple .kpi-icon { background: #3B0764; }
.kpi-purple .kpi-stripe { background: #8B5CF6; }

/* Alert Banners */
.alert-banner {
    padding: 1rem 1.25rem; border-radius: var(--radius-sm);
    margin-bottom: 1rem; display: flex;
    align-items: flex-start; gap: 0.75rem; font-size: 0.875rem;
}
.alert-warning { background: #78350F; border-left: 4px solid #F59E0B; color: #FDE68A; }
.alert-danger  { background: #7F1D1D; border-left: 4px solid #EF4444; color: #FECACA; }
.alert-success { background: #064E3B; border-left: 4px solid #10B981; color: #6EE7B7; }
.alert-info    { background: #1E3A5F; border-left: 4px solid #3B82F6; color: #BFDBFE; }

/* Section Header */
.section-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.25rem; padding-bottom: 0.75rem;
    border-bottom: 1px solid #334155;
}
.section-title {
    font-size: 1.125rem; font-weight: 700;
    color: #F1F5F9; display: flex; align-items: center; gap: 0.5rem;
}

/* Badges */
.badge {
    display: inline-flex; align-items: center; padding: 0.2rem 0.6rem;
    border-radius: 999px; font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.04em;
}
.badge-blue   { background: #1E3A5F; color: #93C5FD; }
.badge-green  { background: #064E3B; color: #6EE7B7; }
.badge-orange { background: #78350F; color: #FCD34D; }
.badge-red    { background: #7F1D1D; color: #FCA5A5; }
.badge-gray   { background: #1E293B; color: #94A3B8; }
.badge-purple { background: #3B0764; color: #C4B5FD; }

/* WhatsApp Button */
.wa-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #25D366; color: white !important;
    padding: 0.4rem 0.875rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; text-decoration: none !important;
}
.wa-btn:hover { background: #128C7E; }

/* Notification Dot */
.notif-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #EF4444; border-radius: 50%; margin-left: 4px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #334155 !important;
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
}

/* Form */
[data-testid="stForm"] {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: var(--radius) !important;
    padding: 1.5rem !important;
}

/* Buttons */
.stButton button[kind="primary"] {
    background: #3B82F6 !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    color: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stButton button[kind="primary"]:hover { background: #2563EB !important; }
.stButton button[kind="secondary"] {
    border: 1px solid #334155 !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #1E293B !important;
    color: #CBD5E1 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px !important; background: #0F172A !important;
    padding: 4px !important; border-radius: var(--radius-sm) !important;
    border: 1px solid #334155 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important; font-weight: 500 !important;
    font-size: 0.85rem !important; padding: 0.45rem 1rem !important;
    color: #CBD5E1 !important;
}
.stTabs [aria-selected="true"] {
    background: #1E293B !important; color: #3B82F6 !important;
    font-weight: 600 !important;
}

/* Metric */
[data-testid="stMetric"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: var(--radius-sm);
    padding: 1rem 1.25rem;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* Page Title */
.page-title { font-size: 1.5rem; font-weight: 800; color: #F1F5F9; margin-bottom: 0.25rem; }
.page-subtitle { font-size: 0.875rem; color: #94A3B8; margin-bottom: 1.5rem; }
/* Input fields dark mode */
.stTextInput input {
    background: #0F172A !important;
    border: 1px solid #475569 !important;
    border-radius: var(--radius-sm) !important;
    color: #F1F5F9 !important;
}
.stTextInput input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.2) !important;
}
.stTextInput input::placeholder { color: #64748B !important; }

.stTextArea textarea {
    background: #0F172A !important;
    border: 1px solid #475569 !important;
    border-radius: var(--radius-sm) !important;
    color: #F1F5F9 !important;
}
.stTextArea textarea:focus {
    border-color: #3B82F6 !important;
}
.stTextArea textarea::placeholder { color: #64748B !important; }

.stNumberInput input {
    background: #0F172A !important;
    border: 1px solid #475569 !important;
    color: #F1F5F9 !important;
}

.stSelectbox > div > div {
    background: #0F172A !important;
    border: 1px solid #475569 !important;
    color: #F1F5F9 !important;
}

.stDateInput input {
    background: #0F172A !important;
    border: 1px solid #475569 !important;
    color: #F1F5F9 !important;
}

/* Expander dark */
.streamlit-expanderHeader {
    background: #1E293B !important;
    color: #F1F5F9 !important;
    border: 1px solid #334155 !important;
    border-radius: var(--radius-sm) !important;
}
.streamlit-expanderContent {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
}

/* Radio and checkbox */
.stRadio label { color: #CBD5E1 !important; }
.stCheckbox label { color: #CBD5E1 !important; }

/* Labels */
.stTextInput label, .stSelectbox label, 
.stTextArea label, .stNumberInput label,
.stDateInput label { color: #CBD5E1 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────

from app.auth.auth import init_session, is_authenticated, login, logout, is_admin, get_current_user
from app.ui.login_page import render_login
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
# SCHEDULER
# ─────────────────────────────────────────────────

if "scheduler_started" not in st.session_state:
    try:
        start_scheduler()
        st.session_state.scheduler_started = True
    except Exception:
        st.session_state.scheduler_started = False

# ─────────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────────

init_session()

# ─────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────

if not is_authenticated():
    render_login()
else:
    user = get_current_user()
    logo_b64 = get_logo_b64()

    # Role-based navigation
    if st.session_state.get("role") == "admin":
        pages = ["Dashboard", "Candidates", "Add Candidate",
                 "Recruiters", "Payments", "Companies",
                 "Notifications", "Smart Import", "Settings"]
        icons = {
            "Dashboard":     "🏠",
            "Candidates":    "👥",
            "Add Candidate": "➕",
            "Recruiters":    "💼",
            "Payments":      "💰",
            "Companies":     "🏢",
            "Notifications": "🔔",
            "Smart Import":  "📥",
            "Settings":      "⚙️",
        }
    else:
        pages = ["Dashboard", "Candidates", "Add Candidate",
                 "Companies", "Notifications", "Settings"]
        icons = {
            "Dashboard":     "🏠",
            "Candidates":    "👥",
            "Add Candidate": "➕",
            "Companies":     "🏢",
            "Notifications": "🔔",
            "Settings":      "⚙️",
        }

    current = st.session_state.get("current_page", "Dashboard")
    if current not in pages:
        current = "Dashboard"
        st.session_state.current_page = "Dashboard"

    # Top Navbar
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:40px; width:auto;">'
    else:
        logo_html = '<span style="color:white; font-size:1.5rem;">🎯</span>'

    st.markdown(f"""
    <div style="
        background: #0F172A;
        padding: 0.6rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -3rem -4rem 1rem -4rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        border-bottom: 1px solid #334155;
    ">
        <div style="display:flex; align-items:center; gap:0.75rem;">
            {logo_html}
            <span style="color:#F1F5F9; font-weight:800; font-size:1.1rem;">BLACKWOODS CRM</span>
        </div>
        <div style="color:#64748B; font-size:0.8rem;">
            👤 {user['full_name']} &nbsp;|&nbsp; {user['role'].title()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Buttons
    nav_cols = st.columns(len(pages))
    for idx, page in enumerate(pages):
        with nav_cols[idx]:
            is_active = current == page
            page_icon = icons.get(page, "📄")
            if st.button(
                f"{page_icon} {page}",
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_page = page
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Sign Out
    cols = st.columns(9)
    with cols[8]:
        if st.button("🚪 Sign Out", use_container_width=True):
            logout()

    st.markdown("---")

    # Page Renderer
    try:
        from app.ui.smart_import_page import render_smart_import_page
    except Exception as e:
        def render_smart_import_page():
            st.error(f"Smart Import failed to load: {e}")

    page_map = {
        "Dashboard":     render_dashboard,
        "Candidates":    render_candidates,
        "Add Candidate": render_add_candidate,
        "Recruiters":    render_recruiters,
        "Payments":      render_payments,
        "Companies":     render_companies,
        "Notifications": render_notifications,
        "Smart Import":  render_smart_import_page,
        "Settings":      render_settings,
    }

    renderer = page_map.get(current, render_dashboard)
    renderer()