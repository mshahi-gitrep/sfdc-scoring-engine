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
    :root {
        --color-bg-primary: #07111F;
        --color-bg-secondary: #0E1728;
        --color-bg-tertiary: #13203B;
        --color-accent: #3B82F6;
        --color-accent-hover: #2563EB;
        --color-success: #22C55E;
        --color-warning: #F59E0B;
        --color-danger: #EF4444;
        --color-text-primary: #F8FAFC;
        --color-text-secondary: #94A3B8;
        --color-text-muted: #475569;
        --color-border: rgba(255,255,255,0.08);
        --color-border-strong: rgba(255,255,255,0.12);
        --spacing-xs: 8px;
        --spacing-sm: 12px;
        --spacing-md: 16px;
        --spacing-lg: 20px;
        --spacing-xl: 24px;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
        --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--color-bg-primary);
        color: var(--color-text-primary);
    }

    [data-testid="stSidebar"] {
        background: var(--color-bg-secondary);
        border-right: 1px solid var(--color-border);
    }

    .css-1d391kg, .css-1d391kg * {
        color: var(--color-text-primary);
    }

    .css-1d391kg h1 {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        color: var(--color-text-primary);
    }

    .css-1d391kg h2 {
        font-size: 1.6rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: var(--color-text-primary);
    }

    .css-1d391kg h3 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: var(--color-text-primary);
    }

    .css-1d391kg h4 {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--color-text-primary);
    }

    .css-1d391kg p {
        line-height: 1.6;
        color: var(--color-text-secondary);
    }

    .css-1d391kg hr {
        border-top: 1px solid var(--color-border);
        margin: 24px 0;
    }

    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        background-color: var(--color-accent);
        color: white;
        border: none;
        padding: 10px 20px;
    }

    .stButton>button:hover {
        background-color: var(--color-accent-hover);
    }

    .stAlert {
        border-radius: 12px;
        border-width: 1px;
    }

    .css-10trblm {
        background-color: var(--color-bg-secondary);
    }

    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: var(--color-text-primary);
    }

    [data-testid="stMetricLabel"] {
        color: var(--color-text-secondary);
    }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    .card {
        padding: 20px;
        border-radius: 16px;
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        transition: all 0.3s ease;
    }

    .card:hover {
        border-color: var(--color-accent);
        background: var(--color-bg-tertiary);
    }

    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .badge-success {
        background: rgba(34, 197, 94, 0.1);
        color: var(--color-success);
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.1);
        color: var(--color-warning);
    }

    .badge-danger {
        background: rgba(239, 68, 68, 0.1);
        color: var(--color-danger);
    }

    .badge-info {
        background: rgba(59, 130, 246, 0.1);
        color: var(--color-accent);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    "<div style='text-align:center; padding:24px 12px; border-bottom:1px solid rgba(255,255,255,0.08);'>"
    "<div style='font-size:1.4rem; font-weight:700; color:#3B82F6; margin-bottom:8px;'>🎯 Readiness Hub</div>"
    "<p style='font-size:0.85em; color:#94A3B8; margin:0; line-height:1.5;'>Sales readiness intelligence that powers qualified conversations</p>"
    "</div>",
    unsafe_allow_html=True
)

st.sidebar.markdown("")

page = st.sidebar.radio(
    "Navigate",
    [
        "Who Should We Call This Week?",
        "Opportunity Workbench",
        "Prospect Brief",
        "How The Readiness Model Works"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("")
st.sidebar.markdown(
    "<div style='padding:16px; border-radius:12px; background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2);'>"
    "<p style='font-size:0.75em; color:#94A3B8; text-align:center; margin:0;'>"
    "<strong style=\"color:#3B82F6;\">✓ Real-time</strong> • Deterministic • Fully auditable"
    "</p></div>",
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
