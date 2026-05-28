"""
Login Page UI
CRM
"""

import streamlit as st
import base64
import os




def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        logo_b64 = get_logo_b64()

        # Logo / Brand
        if logo_b64:
            logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:80px; width:auto; display:block; margin:0 auto 1rem;">'
        else:
            logo_html = '<div style="font-size:3rem; text-align:center; margin-bottom:1rem;">🎯</div>'

        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 2rem;">
            {logo_html}
            <h1 style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 1.75rem;
                font-weight: 800;
                color: #F1F5F9;
                margin: 0.75rem 0 0;
                letter-spacing: -0.02em;
            ">CRM</h1>
            <p style="
                color: #64748B;
                font-size: 0.875rem;
                margin: 0.4rem 0 0;
                font-weight: 500;
            ">Recruitment Management System</p>
        </div>
        """, unsafe_allow_html=True)

        # Login Form
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
        <div style="text-align:center; margin-top: 1.5rem; color: #9CA3AF; font-size: 0.75rem;">
            © 2024 CRM. All rights reserved.
        </div>
        """, unsafe_allow_html=True)