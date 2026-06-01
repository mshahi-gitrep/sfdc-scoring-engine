"""
Opportunity Workbench Submodule for Streamlit Application.

This page is the primary operating screen for reviewing prioritized opportunities,
selecting prospects, and understanding the best next action.
"""

import streamlit as st
import pandas as pd
from app.utils import load_unified_data


def _recommended_action(row: pd.Series) -> str:
    if row.get("structural_block_flag", False) or row.get("eligibility_status") == "Blocked":
        return "Do Not Call"
    if row.get("dq_flag", False):
        return "Nurture"
    if row["readiness_score"] >= 80:
        return "Call Today"
    if row["readiness_score"] >= 60:
        return "Nurture"
    return "Do Not Call"


def _confidence_label(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def _primary_reason(row: pd.Series) -> str:
    if row.get("agentic_recommendation_available"):
        summary = str(row.get("why_summary", "")).split(".")[0]
        return summary if summary else "Strong readiness signal"
    
    negative_reasons = [r for r in str(row.get("top_negative_reasons", "")).split(", ") if r and r != "None"]
    if row.get("dq_flag") and negative_reasons:
        return negative_reasons[0]

    positive_reasons = [r for r in str(row.get("top_positive_reasons", "")).split(", ") if r and r != "None"]
    return positive_reasons[0] if positive_reasons else "Strong readiness signal"


def render_ranked_records():
    """Renders the Opportunity Workbench page."""
    st.markdown(
        "<div style='margin-bottom:28px;'>"
        "<h1 style='color:#3B82F6; margin:0 0 8px; font-size:2.4rem;'>Opportunity Workbench</h1>"
        "<p style='color:#94A3B8; margin:0; font-size:1.05rem; line-height:1.6;'>Deep-dive view of prioritized opportunities. Filter by readiness level, account, seniority, and engagement to build your daily outreach list.</p>"
        "</div>",
        unsafe_allow_html=True
    )

    df, _, _, _ = load_unified_data()
    df["company_name"] = df.get("account_name").fillna(df.get("account_id")).fillna("Unknown Company")
    df["full_name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")
    df["dq_flag"] = (
        df.get("missing_title_flag", False) |
        df.get("duplicate_email_flag", False) |
        df.get("missing_account_flag", False) |
        df.get("opted_out_flag", False) |
        df.get("bounced_or_left_company_flag", False) |
        df.get("shared_mailbox_flag", False) |
        df.get("broken_conversion_link_flag", False)
    )

    st.markdown(
        "<h3 style='color:#F8FAFC; margin:24px 0 16px; font-size:1.1rem;'>Filters</h3>",
        unsafe_allow_html=True
    )

    col_search, col_readiness, col_account, col_seniority = st.columns(4)
    with col_search:
        search_query = st.text_input("Search", "", placeholder="Name or company...", help="Name, email, or account match.")
    with col_readiness:
        readiness_filter = st.selectbox("Readiness", ["All", "Call Today", "Nurture", "Do Not Call"], index=0, label_visibility="collapsed")
    with col_account:
        account_filter = st.selectbox("Account", ["All", "Strategic Accounts only", "Standard accounts only"], index=0, label_visibility="collapsed")
    with col_seniority:
        seniority_filter = st.selectbox("Seniority", ["All", "Director+", "Manager / Mid", "Individual Contributor"], index=0, label_visibility="collapsed")

    col_activity, col_quality = st.columns(2)
    with col_activity:
        recent_activity = st.selectbox("Recent Activity", ["All", "Last 7 days", "Last 30 days", "Older than 30 days"], index=0, label_visibility="collapsed")
    with col_quality:
        data_quality = st.selectbox("Data Quality", ["All", "Clean", "Needs Cleanup", "Blocked"], index=0, label_visibility="collapsed")

    filtered_df = df.copy()
    if search_query:
        query = search_query.lower().strip()
        filtered_df = filtered_df[filtered_df["full_name"].str.lower().str.contains(query, na=False) |
                                  filtered_df["email"].fillna("").str.lower().str.contains(query, na=False) |
                                  filtered_df["company_name"].fillna("").str.lower().str.contains(query, na=False)]

    if readiness_filter != "All":
        filtered_df["recommended_action"] = filtered_df.apply(_recommended_action, axis=1)
        filtered_df = filtered_df[filtered_df["recommended_action"] == readiness_filter]

    if account_filter == "Strategic Accounts only":
        filtered_df = filtered_df[filtered_df.get("is_named_account", False) == True]
    elif account_filter == "Standard accounts only":
        filtered_df = filtered_df[filtered_df.get("is_named_account", False) == False]

    if seniority_filter == "Director+":
        filtered_df = filtered_df[filtered_df.get("seniority_score", 0) >= 70]
    elif seniority_filter == "Manager / Mid":
        filtered_df = filtered_df[(filtered_df.get("seniority_score", 0) >= 40) & (filtered_df.get("seniority_score", 0) < 70)]
    elif seniority_filter == "Individual Contributor":
        filtered_df = filtered_df[filtered_df.get("seniority_score", 0) < 40]

    if recent_activity == "Last 7 days":
        filtered_df = filtered_df[filtered_df.get("days_since_last_response", 999) <= 7]
    elif recent_activity == "Last 30 days":
        filtered_df = filtered_df[filtered_df.get("days_since_last_response", 999) <= 30]
    elif recent_activity == "Older than 30 days":
        filtered_df = filtered_df[filtered_df.get("days_since_last_response", 0) > 30]

    if data_quality == "Clean":
        filtered_df = filtered_df[~filtered_df["dq_flag"] & (filtered_df.get("eligibility_status") != "Blocked")]
    elif data_quality == "Needs Cleanup":
        filtered_df = filtered_df[filtered_df["dq_flag"] & (filtered_df.get("eligibility_status") != "Blocked")]
    elif data_quality == "Blocked":
        filtered_df = filtered_df[filtered_df.get("eligibility_status") == "Blocked"]

    filtered_df = filtered_df.sort_values(by="readiness_score", ascending=False).reset_index(drop=True)
    filtered_df["Rank"] = filtered_df.index + 1
    filtered_df["Recommended Action"] = filtered_df.apply(lambda row: row.get("recommended_action") if row.get("agentic_recommendation_available") else _recommended_action(row), axis=1)
    filtered_df["Confidence"] = filtered_df["readiness_score"].apply(_confidence_label)
    filtered_df["Primary Reason"] = filtered_df.apply(_primary_reason, axis=1)

    if filtered_df.empty:
        st.info("No opportunities match the current filters. Broaden the selection to see recommended prospects.")
        return

    left_col, right_col = st.columns([2.2, 1.8])
    
    # LEFT COLUMN: Interactive table with row selection
    with left_col:
        st.markdown(
            f"<h3 style='color:#F8FAFC; margin:24px 0 16px;'>{len(filtered_df):,} Opportunities Found</h3>"
            "<p style='color:#94A3B8; margin:-12px 0 16px; font-size:0.95rem;'>Click a row below to view full details →</p>",
            unsafe_allow_html=True
        )
        display_df = filtered_df[["Rank", "full_name", "company_name", "readiness_score", "Recommended Action", "Primary Reason"]].copy()
        display_df.columns = ["Rank", "Person", "Company", "Readiness", "Action", "Primary Signal"]
        
        # Create a simple selection mechanism using row index
        selection = st.selectbox(
            "Select prospect from table",
            range(len(display_df)),
            format_func=lambda i: f"{display_df.iloc[i]['Rank']}. {display_df.iloc[i]['Person']} — {display_df.iloc[i]['Company']}",
            label_visibility="collapsed",
            key="prospect_selection"
        )
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Person": st.column_config.TextColumn("Person", width="medium"),
                "Company": st.column_config.TextColumn("Company", width="medium"),
                "Readiness": st.column_config.NumberColumn("Score", format="%.1f", width="small"),
                "Action": st.column_config.TextColumn("Action", width="medium"),
                "Primary Signal": st.column_config.TextColumn("Signal")
            }
        )

    # RIGHT COLUMN: Dynamic detail panel
    with right_col:
        st.markdown(
            "<h3 style='color:#F8FAFC; margin:24px 0 16px;'>📋 Prospect Details</h3>",
            unsafe_allow_html=True
        )
        
        selected_row = filtered_df.iloc[selection]
        st.session_state["selected_prospect_id"] = selected_row["master_person_id"]
        
        st.markdown(
            f"<h2 style='color:#F8FAFC; margin:0 0 4px; font-size:1.4rem;'>{selected_row['full_name']}</h2>"
            f"<p style='color:#3B82F6; margin:0 0 12px; font-weight:600;'>{selected_row['company_name']}</p>",
            unsafe_allow_html=True
        )
        
        st.markdown(
            f"<div style='padding:16px; border-radius:12px; background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.2); margin-bottom:12px;'>"
            f"<p style='margin:0; color:#94A3B8; font-size:0.85rem;'>Readiness Score</p>"
            f"<p style='margin:4px 0 0; color:#22C55E; font-weight:700; font-size:1.3rem;'>{selected_row['readiness_score']:.1f} / 100</p>"
            "</div>",
            unsafe_allow_html=True
        )
        
        st.markdown(f"**Recommended:** {selected_row['Recommended Action']}")
        st.markdown(f"**Confidence:** {selected_row['Confidence']}")
        
        if selected_row.get("agentic_recommendation_available"):
            st.markdown("---")
            st.markdown("<h4 style='color:#3B82F6; margin:12px 0 8px;'>🤖 AI Insights</h4>", unsafe_allow_html=True)
            st.markdown(f"**Why:** {selected_row.get('why_summary', 'N/A')}")
            st.markdown(f"**Now:** {selected_row.get('why_now_summary', 'N/A')}")
            st.markdown(f"**Signal:** {selected_row.get('where_signal_summary', 'N/A')}")
            if selected_row.get('risk_note'):
                st.markdown(f"**⚠️ Risk:** {selected_row.get('risk_note')}")
        
        st.markdown("---")
        st.markdown("<h4 style='color:#F8FAFC; margin:12px 0 8px;'>Key Signals</h4>", unsafe_allow_html=True)
        st.markdown(f"- **Activity:** {int(selected_row.get('days_since_last_response', 0))} days")
        st.markdown(f"- **Type:** {'Strategic' if selected_row.get('is_named_account', False) else 'Standard'}")
        st.markdown(f"- **Quality:** {'<span style=\"color:#F59E0B;\">⚠️ Cleanup</span>' if selected_row.get('dq_flag') else '<span style=\"color:#22C55E;\">✓ Clean</span>'}", unsafe_allow_html=True)
        
        if selected_row.get("top_positive_reasons"):
            st.markdown("**Strengths:**")
            for reason in str(selected_row["top_positive_reasons"]).split(", "):
                if reason and reason != "None":
                    st.markdown(f"  ✔️ {reason}")
        
        if selected_row.get("top_negative_reasons"):
            st.markdown("**Concerns:**")
            for reason in str(selected_row["top_negative_reasons"]).split(", "):
                if reason and reason != "None":
                    st.markdown(f"  ⚠️ {reason}")
