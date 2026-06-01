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
    st.markdown("<h1 style='color:#3B82F6; margin-bottom:4px;'>Opportunity Workbench</h1>", unsafe_allow_html=True)
    st.markdown("Prioritized outreach recommendations ranked by business readiness.")
    st.markdown("---")

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

    col_search, col_readiness, col_account, col_seniority = st.columns(4)
    with col_search:
        search_query = st.text_input("Search prospect", "", help="Name, email, or account match.")
    with col_readiness:
        readiness_filter = st.selectbox("Readiness", ["All", "Call Today", "Nurture", "Do Not Call"], index=0)
    with col_account:
        account_filter = st.selectbox("Account", ["All", "Strategic Accounts only", "Standard accounts only"], index=0)
    with col_seniority:
        seniority_filter = st.selectbox("Seniority", ["All", "Director+", "Manager / Mid", "Individual Contributor"], index=0)

    col_activity, col_quality = st.columns(2)
    with col_activity:
        recent_activity = st.selectbox("Recent Activity", ["All", "Last 7 days", "Last 30 days", "Older than 30 days"], index=0)
    with col_quality:
        data_quality = st.selectbox("Data Quality", ["All", "Clean", "Needs Cleanup", "Blocked"], index=0)

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
        st.markdown(f"**{len(filtered_df):,} prioritized opportunities found.** Click any row to view details →")
        display_df = filtered_df[["Rank", "full_name", "company_name", "readiness_score", "Recommended Action", "Primary Reason"]].copy()
        display_df.columns = ["Rank", "Person", "Company", "Readiness", "Recommended Action", "Primary Reason"]
        
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
                "Readiness": st.column_config.NumberColumn("Readiness", format="%.1f"),
                "Recommended Action": st.column_config.TextColumn("Recommended Action"),
                "Primary Reason": st.column_config.TextColumn("Primary Reason")
            }
        )

    # RIGHT COLUMN: Dynamic detail panel
    with right_col:
        st.markdown("<h3 style='color:#F8FAFC;'>📋 Prospect Details</h3>", unsafe_allow_html=True)
        
        selected_row = filtered_df.iloc[selection]
        st.session_state["selected_prospect_id"] = selected_row["master_person_id"]
        
        st.markdown(f"<h2 style='color:#F8FAFC; margin:0;'>{selected_row['full_name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94A3B8; margin-top:4px;'>{selected_row['company_name']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:12px 0 4px;'><strong>Readiness:</strong> {selected_row['readiness_score']:.1f} / 100</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:4px 0 4px;'><strong>Action:</strong> {selected_row['Recommended Action']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:4px 0 4px;'><strong>Confidence:</strong> {selected_row['Confidence']}</p>", unsafe_allow_html=True)
        
        if selected_row.get("agentic_recommendation_available"):
            st.markdown("---")
            st.markdown("<h4 style='color:#F8FAFC;'>🤖 AI Insights</h4>", unsafe_allow_html=True)
            st.markdown(f"**Why:** {selected_row.get('why_summary', 'N/A')}")
            st.markdown(f"**Why now:** {selected_row.get('why_now_summary', 'N/A')}")
            st.markdown(f"**Signal source:** {selected_row.get('where_signal_summary', 'N/A')}")
            if selected_row.get('risk_note'):
                st.markdown(f"**⚠️ Risk:** {selected_row.get('risk_note')}")
        
        st.markdown("---")
        st.markdown("<h4 style='color:#F8FAFC;'>📊 Key Signals</h4>", unsafe_allow_html=True)
        st.markdown(f"- **Activity:** {int(selected_row.get('days_since_last_response', 0))} days since last response")
        st.markdown(f"- **Account:** {'Strategic' if selected_row.get('is_named_account', False) else 'Standard'}")
        st.markdown(f"- **Data quality:** {'<span style=\"color:#F59E0B;\">⚠️ Needs cleanup</span>' if selected_row.get('dq_flag') else '<span style=\"color:#22C55E;\">✓ Clean</span>'}", unsafe_allow_html=True)
        
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
