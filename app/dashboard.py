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
    st.markdown(
        "<div style='margin-bottom:32px;'>"
        "<h1 style='color:#3B82F6; margin:0 0 8px; font-size:2.4rem;'>Who Should We Call This Week?</h1>"
        "<p style='color:#94A3B8; margin:0; font-size:1.05rem; line-height:1.6;'>Executive insights into your most ready-to-engage prospects. This model analyzes all leads and contacts to surface the people most likely to engage with sales right now.</p>"
        "</div>",
        unsafe_allow_html=True
    )

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
    total_records = len(df)
    coverage_pct = round((total_records - needs_cleanup - blocked) / total_records * 100, 1) if total_records > 0 else 0

    st.markdown(
        "<div style='padding:24px; border-radius:16px; background:linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.05) 100%); border:1px solid rgba(59,130,246,0.2); margin-bottom:28px;'>"
        "<div style='display:flex; justify-content:space-between; align-items:center; gap:20px;'>"
        "<div>"
        "<h3 style='margin:0 0 8px; color:#F8FAFC;'>Ready-to-Call Rate</h3>"
        "<p style='margin:0; color:#94A3B8; font-size:0.95rem;'>Percentage of your database ready for outreach</p>"
        "</div>"
        "<div style='text-align:right;'>"
        f"<div style='font-size:2.8rem; font-weight:700; color:#3B82F6;'>{coverage_pct}%</div>"
        f"<div style='color:#94A3B8; font-size:0.9rem; margin-top:4px;'>{ready_now + high_priority:,} of {total_records:,} prospects</div>"
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(34,197,94,0.2);'>"
            "<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>"
            "<h3 style='margin:0; color:#F8FAFC;'>🔥 Priority</h3>"
            "<span style='background:rgba(34,197,94,0.1); color:#22C55E; padding:4px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>Ready Now</span>"
            "</div>"
            f"<p style='font-size:2.2rem; font-weight:700; margin:8px 0 0; color:#22C55E;'>{ready_now:,}</p>"
            "<p style='margin:8px 0 0; color:#94A3B8; font-size:0.9rem;'>Immediate outreach opportunities</p>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(59,130,246,0.2);'>"
            "<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>"
            "<h3 style='margin:0; color:#F8FAFC;'>⚡ Active</h3>"
            "<span style='background:rgba(59,130,246,0.1); color:#3B82F6; padding:4px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>High Priority</span>"
            "</div>"
            f"<p style='font-size:2.2rem; font-weight:700; margin:8px 0 0; color:#3B82F6;'>{high_priority:,}</p>"
            "<p style='margin:8px 0 0; color:#94A3B8; font-size:0.9rem;'>Strong outreach-ready prospects</p>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(245,158,11,0.2);'>"
            "<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>"
            "<h3 style='margin:0; color:#F8FAFC;'>📋 Cleanup</h3>"
            "<span style='background:rgba(245,158,11,0.1); color:#F59E0B; padding:4px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>Action</span>"
            "</div>"
            f"<p style='font-size:2.2rem; font-weight:700; margin:8px 0 0; color:#F59E0B;'>{needs_cleanup:,}</p>"
            "<p style='margin:8px 0 0; color:#94A3B8; font-size:0.9rem;'>Records with data issues</p>"
            "</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(239,68,68,0.2);'>"
            "<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>"
            "<h3 style='margin:0; color:#F8FAFC;'>🚫 Blocked</h3>"
            "<span style='background:rgba(239,68,68,0.1); color:#EF4444; padding:4px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>Hold</span>"
            "</div>"
            f"<p style='font-size:2.2rem; font-weight:700; margin:8px 0 0; color:#EF4444;'>{blocked:,}</p>"
            "<p style='margin:8px 0 0; color:#94A3B8; font-size:0.9rem;'>Not contactable this week</p>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("")
    st.markdown(
        "<div style='padding:24px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
        "<div style='display:flex; justify-content:space-between; align-items:center; gap:20px;'>"
        "<div>"
        "<h3 style='margin:0 0 8px; color:#F8FAFC; font-size:1.2rem;'>BDR Efficiency Multiplier</h3>"
        "<p style='margin:0; color:#94A3B8; font-size:0.95rem;'>Expected lift in quality conversations using readiness ranking vs random outreach</p>"
        "</div>"
        "<div style='text-align:right;'>"
        "<div style='font-size:3rem; font-weight:700; color:#3B82F6; line-height:1;'>3.5×</div>"
        "</div>"
        "</div>"
        "<div style='margin-top:20px; padding-top:20px; border-top:1px solid rgba(255,255,255,0.08);'>"
        "<div style='display:grid; grid-template-columns:1fr 1fr; gap:16px;'>"
        "<div style='padding:16px; border-radius:12px; background:#13203B;'>"
        "<div style='color:#94A3B8; font-size:0.9rem; margin-bottom:8px;'>Random Outreach</div>"
        "<div style='font-size:2rem; font-weight:700; color:#F8FAFC;'>2%</div>"
        "<div style='color:#94A3B8; font-size:0.8rem; margin-top:4px;'>Expected response rate</div>"
        "</div>"
        "<div style='padding:16px; border-radius:12px; background:#13203B;'>"
        "<div style='color:#94A3B8; font-size:0.9rem; margin-bottom:8px;'>Readiness Ranked</div>"
        "<div style='font-size:2rem; font-weight:700; color:#22C55E;'>7%</div>"
        "<div style='color:#94A3B8; font-size:0.8rem; margin-top:4px;'>Expected response rate</div>"
        "</div>"
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("")

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

    st.markdown(
        "<h2 style='color:#F8FAFC; margin-bottom:4px; font-size:1.3rem;'>Signal Analysis</h2>"
        "<p style='color:#94A3B8; margin:0 0 20px;'>Distribution of engagement signals and common blockers across your database</p>",
        unsafe_allow_html=True
    )

    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.markdown("<h4 style='color:#22C55E; margin-bottom:16px;'>✔️ Positive Engagement Signals</h4>", unsafe_allow_html=True)
        for name, count in signal_counts.items():
            st.markdown(_render_bar(name, count, signal_max), unsafe_allow_html=True)

    with col_right:
        st.markdown("<h4 style='color:#F59E0B; margin-bottom:16px;'>⚠️ Common Blockers</h4>", unsafe_allow_html=True)
        for name, count in blocker_counts.items():
            st.markdown(_render_bar(name, count, blocker_max), unsafe_allow_html=True)

    st.markdown("")
    st.markdown(
        "<h2 style='color:#F8FAFC; margin-bottom:4px; font-size:1.3rem;'>Top 10 Ready-To-Call Prospects</h2>"
        "<p style='color:#94A3B8; margin:0 0 20px;'>Highest readiness scores with clean data and clear engagement signals</p>",
        unsafe_allow_html=True
    )
    
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
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Name": st.column_config.TextColumn("Prospect", width="medium"),
            "Company": st.column_config.TextColumn("Company", width="medium"),
            "Readiness": st.column_config.NumberColumn("Score", format="%.1f", width="small"),
            "Reason": st.column_config.TextColumn("Primary Signal")
        }
    )
