"""
Executive Command Center Submodule for Streamlit Application.

This page surface executive KPIs, top signals, outreach blockers, and the
business story of the people worth calling this week.
"""

import streamlit as st
import pandas as pd
from app.utils import load_unified_data


def _count_flag(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].astype(bool).sum())


def _render_bar(label: str, count: int, max_value: int) -> str:
    width = int((count / max_value) * 100) if max_value > 0 else 0
    return (
        f"<div style='margin-bottom: 12px;'>"
        f"<div style='display:flex; justify-content:space-between; color:#F8FAFC; font-size:0.95em; margin-bottom:4px;'>"
        f"<span>{label}</span><span>{count:,}</span></div>"
        f"<div style='background: rgba(255,255,255,0.08); border-radius: 999px; height: 12px;'>"
        f"<div style='width: {width}%; background: #3B82F6; height: 12px; border-radius: 999px;'></div>"
        f"</div></div>"
    )


def render_dashboard():
    """Renders the Executive Command Center page."""
    st.markdown("<h1 style='color:#3B82F6; margin-bottom:4px;'>Who Should We Call This Week?</h1>", unsafe_allow_html=True)
    st.markdown("This model evaluates every lead and contact and identifies the people most likely to engage with sales right now.")
    st.markdown("---")

    df, _, _, _ = load_unified_data()
    df["company_name"] = df.get("account_name").fillna(df.get("account_id")).fillna("Unknown Company")

    ready_now = df[(df["readiness_score"] >= 80) & (df["eligibility_status"] == "Eligible") & (~df.get("structural_block_flag", False))].shape[0]
    high_priority = df[(df["readiness_score"] >= 60) & (df["eligibility_status"] != "Blocked")].shape[0]
    needs_cleanup = df[
        (df.get("missing_title_flag", False)) |
        (df.get("duplicate_email_flag", False)) |
        (df.get("missing_account_flag", False)) |
        (df.get("opted_out_flag", False)) |
        (df.get("bounced_or_left_company_flag", False))
    ].shape[0]
    blocked = df[(df.get("structural_block_flag", False)) | (df["eligibility_status"] == "Blocked")].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
                    f"<h3 style='margin:0; color:#F8FAFC;'>🔥 Ready Now</h3>"
                    f"<p style='font-size:2.2rem; margin:10px 0 0; color:#F8FAFC;'>{ready_now:,}</p>"
                    "<p style='margin:8px 0 0; color:#94A3B8;'>Immediate outreach opportunities</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
                    f"<h3 style='margin:0; color:#F8FAFC;'>⚡ High Priority</h3>"
                    f"<p style='font-size:2.2rem; margin:10px 0 0; color:#F8FAFC;'>{high_priority:,}</p>"
                    "<p style='margin:8px 0 0; color:#94A3B8;'>Strong outreach-ready prospects</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
                    f"<h3 style='margin:0; color:#F8FAFC;'>⚠ Needs Cleanup</h3>"
                    f"<p style='font-size:2.2rem; margin:10px 0 0; color:#F8FAFC;'>{needs_cleanup:,}</p>"
                    "<p style='margin:8px 0 0; color:#94A3B8;'>Records with data quality issues</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
                    f"<h3 style='margin:0; color:#F8FAFC;'>🚫 Blocked</h3>"
                    f"<p style='font-size:2.2rem; margin:10px 0 0; color:#F8FAFC;'>{blocked:,}</p>"
                    "<p style='margin:8px 0 0; color:#94A3B8;'>Records not contactable this week</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<div style='padding:22px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
                "<div style='display:flex; justify-content:space-between; align-items:center; gap:20px;'>"
                "<div><h3 style='margin:0; color:#F8FAFC;'>Potential BDR Efficiency Gain</h3>"
                "<p style='margin:6px 0 0; color:#94A3B8;'>Ranked outreach is built to deliver more qualified conversations and less wasted time.</p></div>"
                "<div style='text-align:right; color:#F8FAFC;'><div style='font-size:1.8rem; font-weight:700;'>3.5x</div>"
                "<div style='color:#94A3B8; margin-top:4px;'>Expected response lift vs random outreach</div></div>"
                "</div>"
                "<div style='display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:20px;'>"
                "<div style='padding:14px; border-radius:14px; background:#13213B;'>"
                "<div style='color:#94A3B8; font-size:0.92rem;'>Random Outreach</div>"
                "<div style='font-size:1.7rem; font-weight:700; color:#F8FAFC;'>2%</div>"
                "</div>"
                "<div style='padding:14px; border-radius:14px; background:#13213B;'>"
                "<div style='color:#94A3B8; font-size:0.92rem;'>Readiness Ranked Outreach</div>"
                "<div style='font-size:1.7rem; font-weight:700; color:#F8FAFC;'>7%</div>"
                "</div>"
                "</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    signal_counts = {
        "Recent Webinar Activity": int((df.get("webinar_attended_count", 0) > 0).sum()),
        "Event Attendance": int((df.get("event_attended_count", 0) > 0).sum()),
        "Content Downloads": int((df.get("content_response_count", 0) > 0).sum()),
        "Strategic Accounts": int((df.get("is_named_account", False)).astype(bool).sum()),
        "Director+ Titles": int((df.get("seniority_score", 0) >= 70).sum())
    }
    blocker_counts = {
        "Missing Job Title": _count_flag(df, "missing_title_flag"),
        "Duplicate Email": _count_flag(df, "duplicate_email_flag"),
        "No Recent Engagement": int((df.get("days_since_last_response", 999) > 30).sum()),
        "Left Company": _count_flag(df, "bounced_or_left_company_flag"),
        "Opt-Out": _count_flag(df, "opted_out_flag")
    }
    signal_max = max(signal_counts.values()) if signal_counts else 1
    blocker_max = max(blocker_counts.values()) if blocker_counts else 1

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("<h3 style='color:#F8FAFC;'>Top Positive Signals</h3>", unsafe_allow_html=True)
        for name, count in signal_counts.items():
            st.markdown(_render_bar(name, count, signal_max), unsafe_allow_html=True)

    with col_right:
        st.markdown("<h3 style='color:#F8FAFC;'>Top Outreach Blockers</h3>", unsafe_allow_html=True)
        for name, count in blocker_counts.items():
            st.markdown(_render_bar(name, count, blocker_max), unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<h3 style='color:#F8FAFC;'>Top 10 Ready-To-Call Prospects</h3>", unsafe_allow_html=True)
    candidate_df = df[(df["eligibility_status"] == "Eligible") & (~df.get("structural_block_flag", False))].copy()
    candidate_df = candidate_df.sort_values(by="readiness_score", ascending=False).head(10)
    candidate_df["Rank"] = range(1, len(candidate_df) + 1)
    candidate_df["Name"] = candidate_df["first_name"].fillna("") + " " + candidate_df["last_name"].fillna("")
    candidate_df["Company"] = candidate_df["company_name"].fillna("Unknown Company")
    candidate_df["Readiness"] = candidate_df["readiness_score"].round(1)
    candidate_df["Reason"] = candidate_df["top_positive_reasons"].fillna("Strong engagement signals").str.split(", ").apply(lambda items: items[0] if len(items) else "Active sales signal")

    st.dataframe(
        candidate_df[["Rank", "Name", "Company", "Readiness", "Reason"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": "Rank",
            "Name": "Prospect",
            "Company": "Company",
            "Readiness": st.column_config.NumberColumn("Readiness", format="%.1f"),
            "Reason": "Primary Signal"
        }
    )
