"""
Methodology Submodule for Streamlit Application.

This page is an appendix that explains the readiness model in a concise,
business-friendly way.
"""

import streamlit as st


def render_methodology():
    """Renders the How The Readiness Model Works page."""
    st.markdown("<h1 style='color:#3B82F6; margin-bottom:4px;'>How The Readiness Model Works</h1>", unsafe_allow_html=True)
    st.markdown("This appendix explains the business logic behind readiness scoring without technical detail.")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            "<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
            "<h2 style='margin:0; color:#F8FAFC;'>40%</h2>"
            "<p style='margin:6px 0 0; color:#94A3B8;'>Engagement</p>"
            "<p style='margin:10px 0 0; color:#F8FAFC;'>Recent events, webinars, and content interactions.</p>"
            "</div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
            "<h2 style='margin:0; color:#F8FAFC;'>25%</h2>"
            "<p style='margin:6px 0 0; color:#94A3B8;'>Recency</p>"
            "<p style='margin:10px 0 0; color:#F8FAFC;'>How recent the last interaction was.</p>"
            "</div>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            "<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
            "<h2 style='margin:0; color:#F8FAFC;'>20%</h2>"
            "<p style='margin:6px 0 0; color:#94A3B8;'>Profile Fit</p>"
            "<p style='margin:10px 0 0; color:#F8FAFC;'>Role, seniority, and buyer influence fit.</p>"
            "</div>",
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            "<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
            "<h2 style='margin:0; color:#F8FAFC;'>15%</h2>"
            "<p style='margin:6px 0 0; color:#94A3B8;'>Account Fit</p>"
            "<p style='margin:10px 0 0; color:#F8FAFC;'>Target account alignment and buying committee signals.</p>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("<h3 style='color:#F8FAFC;'>Data Quality Adjustments</h3>", unsafe_allow_html=True)
    st.markdown(
        "- Missing title or account linkage reduces outreach confidence.\n"
        "- Duplicate email or shared inbox risk can delay outreach.\n"
        "- Opt-outs and former employees are held as blocked for compliance.\n"
        "- Readiness signals remain visible even when a record is temporarily blocked."
    )

    st.markdown("---")
    st.markdown("<h3 style='color:#F8FAFC;'>Why this is an appendix</h3>", unsafe_allow_html=True)
    st.markdown(
        "This page is designed for reviewers who want transparency. "
        "The primary user experience is about who to call, why they matter, and what to say."
    )
