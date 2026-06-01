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

    left_col, right_col = st.columns([2.2, 1])
    with left_col:
        st.markdown(f"**{len(filtered_df):,} prioritized opportunities found.**")
        display_df = filtered_df[["Rank", "full_name", "company_name", "readiness_score", "Recommended Action", "Primary Reason"]].copy()
        display_df.columns = ["Rank", "Person", "Company", "Readiness", "Recommended Action", "Primary Reason"]
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

    with right_col:
        st.markdown("<div style='padding:18px; border-radius:16px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
                    "<h3 style='color:#F8FAFC; margin-top:0;'>Why This Person Is Prioritized</h3>"
                    "</div>", unsafe_allow_html=True)

        if filtered_df.empty:
            st.info("No opportunities match the current filters. Broaden the selection to see recommended prospects.")
            return

        first_id = filtered_df["master_person_id"].iloc[0]
        selected_id = st.session_state.get("selected_prospect_id", first_id)
        if selected_id not in filtered_df["master_person_id"].values:
            selected_id = first_id
        options = [f"{row['Rank']}. {row['full_name']} — {row['company_name']}" for _, row in filtered_df.iterrows()]
        selected_index = int(filtered_df[filtered_df["master_person_id"] == selected_id].index[0])
        selected_option = st.selectbox("Select prospect", options, index=selected_index)
        selected_id = filtered_df.iloc[selected_index]["master_person_id"]
        st.session_state["selected_prospect_id"] = selected_id

        selected_row = filtered_df[filtered_df["master_person_id"] == selected_id].iloc[0]
        st.markdown(f"<h2 style='color:#F8FAFC; margin:0;'>{selected_row['full_name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94A3B8; margin-top:4px;'>{selected_row['company_name']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:12px 0 4px;'><strong>Recommended Action:</strong> {selected_row['Recommended Action']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:4px 0 4px;'><strong>Confidence:</strong> {selected_row['Confidence']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:4px 0 4px;'><strong>Primary Reason:</strong> {selected_row['Primary Reason']}</p>", unsafe_allow_html=True)
        if selected_row.get("agentic_recommendation_available"):
            st.markdown(f"<p style='margin:4px 0 4px;'><strong>Why summary:</strong> {selected_row.get('why_summary', 'N/A')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin:4px 0 4px;'><strong>Why now:</strong> {selected_row.get('why_now_summary', 'N/A')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin:4px 0 4px;'><strong>Signal source:</strong> {selected_row.get('where_signal_summary', 'N/A')}</p>", unsafe_allow_html=True)
            if selected_row.get('risk_note'):
                st.markdown(f"<p style='margin:4px 0 4px;'><strong>Risk note:</strong> {selected_row.get('risk_note')}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-top:1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
        st.markdown("<p style='margin:0 0 8px; color:#94A3B8;'>Key signals for this prospect are summarized below.</p>", unsafe_allow_html=True)
        st.markdown(f"- Readiness score: <strong>{selected_row['readiness_score']:.1f}</strong> / 100", unsafe_allow_html=True)
        st.markdown(f"- Recent activity: <strong>{int(selected_row.get('days_since_last_response', 0))} days</strong> since last response", unsafe_allow_html=True)
        st.markdown(f"- Account fit: <strong>{'Strategic' if selected_row.get('is_named_account', False) else 'Standard'}</strong>", unsafe_allow_html=True)
        if selected_row.get("dq_flag"):
            st.markdown(f"- Data quality note: <span style='color:#F59E0B;'>Needs cleanup</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"- Data quality note: <span style='color:#22C55E;'>Clean profile</span>", unsafe_allow_html=True)
        st.markdown("---")
        if selected_row.get("top_positive_reasons"):
            for reason in str(selected_row["top_positive_reasons"]).split(", "):
                if reason and reason != "None":
                    st.markdown(f"✔️ {reason}")
        if selected_row.get("top_negative_reasons"):
            for reason in str(selected_row["top_negative_reasons"]).split(", "):
                if reason and reason != "None":
                    st.markdown(f"⚠️ {reason}")
