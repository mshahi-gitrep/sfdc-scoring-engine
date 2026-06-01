"""
Methodology Submodule for Streamlit Application.

This page is an appendix that explains the readiness model in a concise,
business-friendly way.
"""

import streamlit as st


def render_methodology():
    """Renders the How The Readiness Model Works page."""
    st.markdown(
        "<div style='margin-bottom:32px;'>"
        "<h1 style='color:#3B82F6; margin:0 0 8px; font-size:2.4rem;'>How The Readiness Model Works</h1>"
        "<p style='color:#94A3B8; margin:0; font-size:1.05rem; line-height:1.6;'>This appendix explains the business logic behind readiness scoring in a way that's transparent and auditable.</p>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='padding:24px; border-radius:16px; background:linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.05) 100%); border:1px solid rgba(59,130,246,0.2); margin-bottom:28px;'>"
        "<h3 style='margin:0 0 12px; color:#F8FAFC;'>Readiness Score Formula</h3>"
        "<p style='margin:0; color:#94A3B8; font-size:0.95rem;'>Readiness = (Engagement × 0.40) + (Recency × 0.25) + (Profile Fit × 0.20) + (Account Fit × 0.15)</p>"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.markdown(
            "<div style='padding:22px; border-radius:14px; background:#0E1728; border:1px solid rgba(59,130,246,0.2);'>"
            "<div style='display:flex; align-items:flex-start; gap:10px; margin-bottom:14px;'>"
            "<span style='font-size:2rem;'>🎯</span>"
            "<div>"
            "<h4 style='margin:0; color:#F8FAFC;'>Engagement</h4>"
            "<p style='margin:4px 0 0; color:#94A3B8; font-size:0.85rem;'>Recent activity signal weight</p>"
            "</div>"
            "</div>"
            "<p style='font-size:2rem; font-weight:700; margin:12px 0; color:#3B82F6;'>40%</p>"
            "<ul style='margin:0; padding-left:20px; color:#94A3B8; font-size:0.9rem;'>"
            "<li>Webinar attendance</li>"
            "<li>Event participation</li>"
            "<li>Content downloads</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            "<div style='padding:22px; border-radius:14px; background:#0E1728; border:1px solid rgba(59,130,246,0.2);'>"
            "<div style='display:flex; align-items:flex-start; gap:10px; margin-bottom:14px;'>"
            "<span style='font-size:2rem;'>⏱️</span>"
            "<div>"
            "<h4 style='margin:0; color:#F8FAFC;'>Recency</h4>"
            "<p style='margin:4px 0 0; color:#94A3B8; font-size:0.85rem;'>Timeliness weight</p>"
            "</div>"
            "</div>"
            "<p style='font-size:2rem; font-weight:700; margin:12px 0; color:#3B82F6;'>25%</p>"
            "<ul style='margin:0; padding-left:20px; color:#94A3B8; font-size:0.9rem;'>"
            "<li>Days since interaction</li>"
            "<li>Engagement window</li>"
            "<li>Momentum signal</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            "<div style='padding:22px; border-radius:14px; background:#0E1728; border:1px solid rgba(59,130,246,0.2);'>"
            "<div style='display:flex; align-items:flex-start; gap:10px; margin-bottom:14px;'>"
            "<span style='font-size:2rem;'>👤</span>"
            "<div>"
            "<h4 style='margin:0; color:#F8FAFC;'>Profile Fit</h4>"
            "<p style='margin:4px 0 0; color:#94A3B8; font-size:0.85rem;'>Buyer profile weight</p>"
            "</div>"
            "</div>"
            "<p style='font-size:2rem; font-weight:700; margin:12px 0; color:#3B82F6;'>20%</p>"
            "<ul style='margin:0; padding-left:20px; color:#94A3B8; font-size:0.9rem;'>"
            "<li>Job title match</li>"
            "<li>Seniority level</li>"
            "<li>Buyer influence</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            "<div style='padding:22px; border-radius:14px; background:#0E1728; border:1px solid rgba(59,130,246,0.2);'>"
            "<div style='display:flex; align-items:flex-start; gap:10px; margin-bottom:14px;'>"
            "<span style='font-size:2rem;'>🏢</span>"
            "<div>"
            "<h4 style='margin:0; color:#F8FAFC;'>Account Fit</h4>"
            "<p style='margin:4px 0 0; color:#94A3B8; font-size:0.85rem;'>Account targeting weight</p>"
            "</div>"
            "</div>"
            "<p style='font-size:2rem; font-weight:700; margin:12px 0; color:#3B82F6;'>15%</p>"
            "<ul style='margin:0; padding-left:20px; color:#94A3B8; font-size:0.9rem;'>"
            "<li>Strategic accounts</li>"
            "<li>Buying committee</li>"
            "<li>Account fit score</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("")
    st.markdown(
        "<h2 style='color:#F8FAFC; margin-bottom:4px; font-size:1.3rem;'>Data Quality Rules</h2>"
        "<p style='color:#94A3B8; margin:0 0 20px;'>Records are automatically adjusted or blocked based on data integrity</p>",
        unsafe_allow_html=True
    )

    col_dq1, col_dq2 = st.columns(2, gap="large")
    
    with col_dq1:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(245,158,11,0.2);'>"
            "<h4 style='color:#F59E0B; margin:0 0 12px;'>⚠️ Data Quality Flags</h4>"
            "<ul style='margin:0; padding-left:20px; color:#94A3B8;'>"
            "<li>Missing title → Reduced confidence</li>"
            "<li>Duplicate email → Delayed outreach</li>"
            "<li>Missing account linkage → Lower fit score</li>"
            "<li>Shared mailbox risk → Manual review</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col_dq2:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(239,68,68,0.2);'>"
            "<h4 style='color:#EF4444; margin:0 0 12px;'>🚫 Compliance Blocks</h4>"
            "<ul style='margin:0; padding-left:20px; color:#94A3B8;'>"
            "<li>Opt-out → Do not contact</li>"
            "<li>Bounced email → Do not contact</li>"
            "<li>Former employee → Do not contact</li>"
            "<li>Compliance hold → No outreach</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("")
    st.markdown(
        "<h2 style='color:#F8FAFC; margin-bottom:4px; font-size:1.3rem;'>AI-Powered Insights</h2>"
        "<p style='color:#94A3B8; margin:0 0 20px;'>Deterministic agents explain the 'why' behind every recommendation</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(34,197,94,0.2);'>"
        "<h4 style='color:#22C55E; margin:0 0 12px;'>✓ Guardrails Principle</h4>"
        "<ul style='margin:0; padding-left:20px; color:#94A3B8; font-size:0.95rem;'>"
        "<li><strong>Deterministic:</strong> All decisions follow documented decision rules, never invented facts</li>"
        "<li><strong>Auditable:</strong> Every recommendation references source data and business logic</li>"
        "<li><strong>Reproducible:</strong> Run the model twice, get the same results</li>"
        "<li><strong>Human-in-the-loop:</strong> Scores are visible but interpretation is always human-guided</li>"
        "<li><strong>Compliance-first:</strong> Records marked as blocked are never recommended for outreach</li>"
        "</ul>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("")
    st.markdown(
        "<div style='padding:20px; border-radius:14px; background:linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.05) 100%); border:1px solid rgba(59,130,246,0.2);'>"
        "<h3 style='margin:0 0 12px; color:#F8FAFC;'>Why This Design Matters</h3>"
        "<p style='margin:0; color:#94A3B8; line-height:1.6;'>"
        "The primary user experience is about <strong>who to call</strong>, <strong>why they matter</strong>, and <strong>what to say</strong>. "
        "This methodology page exists for reviewers who need transparency about how the model works and confidence that it follows consistent, "
        "business-aligned decision rules."
        "</p>"
        "</div>",
        unsafe_allow_html=True
    )

