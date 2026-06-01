"""
Readiness Command Center - Streamlit Root Entrypoint.

This script configures the executive sales readiness experience, the dark premium
theme, navigation, and routing for the main workflow pages.
"""

import sys
import os
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Readiness Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://www.example.com/help",
        "Report a bug": "https://www.example.com/feedback",
        "About": "Executive readiness workflow for outreach prioritization"
    }
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #07111F;
        color: #F8FAFC;
    }
    [data-testid="stSidebar"] {
        background: #0E1728;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .css-1d391kg, .css-1d391kg * {
        color: #F8FAFC;
    }
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3, .css-1d391kg h4 {
        color: #F8FAFC;
    }
    .css-1d391kg hr {
        border-top: 1px solid rgba(255,255,255,0.08);
    }
    .stButton>button {
        border-radius: 12px;
    }
    .stAlert {
        border-radius: 16px;
    }
    .css-10trblm {
        background-color: #0E1728;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    "<div style='text-align:center; padding:18px 8px;'>"
    "<h2 style='color:#3B82F6; margin-bottom:4px;'>Who Should We Call?</h2>"
    "<p style='font-size:0.9em; color:#94A3B8; margin:0;'>Executive command center for top outreach-ready opportunities</p>"
    "</div>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Who Should We Call This Week?",
        "Opportunity Workbench",
        "Prospect Brief",
        "How The Readiness Model Works"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size:0.8em; color:#94A3B8; text-align:center;'>"
    "Modern sales readiness workflow • Story-driven BDR decision support"
    "</div>",
    unsafe_allow_html=True
)

if page == "Who Should We Call This Week?":
    from app.dashboard import render_dashboard
    render_dashboard()
elif page == "Opportunity Workbench":
    from app.ranked_records import render_ranked_records
    render_ranked_records()
elif page == "Prospect Brief":
    from app.record_detail import render_record_detail
    render_record_detail()
elif page == "How The Readiness Model Works":
    from app.methodology import render_methodology
    render_methodology()
