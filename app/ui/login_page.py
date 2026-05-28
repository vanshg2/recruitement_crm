"""
Login Page UI
Recruitment CRM
"""

import streamlit as st


def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; margin-bottom: 2rem;">
            <div style="font-size:1.8rem; font-weight:900; color:#3B82F6;
                        text-align:center; letter-spacing:0.05em;
                        margin-bottom:0.5rem;">Recruitment CRM</div>
            <p style="color:#64748B; font-size:0.875rem;
                      margin:0.4rem 0 0; font-weight:500;">
                Recruitment Management System
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Sign in to your account**")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please enter username and password")
                else:
                    with st.spinner("Signing in..."):
                        from app.auth.auth import login
                        success, msg = login(username, password)
                    if success:
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem;
                    color:#9CA3AF; font-size:0.75rem;">
            © 2025 Recruitment CRM. All rights reserved.
        </div>
        """, unsafe_allow_html=True)
