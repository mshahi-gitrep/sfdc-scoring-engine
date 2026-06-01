"""
Prospect Brief Submodule for Streamlit Application.

Transforms the 360° record detail into an executive briefing document for
BDRs, sales leadership, and non-technical stakeholders.
"""

import pandas as pd
import streamlit as st
from app.utils import load_unified_data


def _recommended_action(row: pd.Series) -> str:
    if row.get("structural_block_flag", False) or row.get("eligibility_status") == "Blocked":
        return "Do Not Call"
    if row.get("dq_flag", False):
        return "Nurture"
    if row["readiness_score"] >= 80:
        return "Call This Week"
    if row["readiness_score"] >= 60:
        return "Nurture"
    return "Do Not Call"


def _confidence_label(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def _confidence_pct(score: float) -> int:
    return min(98, max(30, int(score * 0.9 + 5)))


def _event_label(row: pd.Series) -> str:
    campaign_type = str(row.get("campaign_type", "")).lower()
    campaign_name = str(row.get("campaign_name", "")).strip()
    if "webinar" in campaign_type or "webinar" in campaign_name.lower():
        return "Attended Webinar"
    if "event" in campaign_type or "event" in campaign_name.lower():
        return "Attended Event"
    if "content" in campaign_type or "download" in campaign_name.lower() or "guide" in campaign_name.lower():
        return "Downloaded Content"
    if "pricing" in campaign_name.lower():
        return "Viewed Pricing"
    return campaign_name or str(row.get("member_status", "Engaged with campaign"))


def _talk_track(row: pd.Series, company_name: str) -> dict:
    opening = (
        f"{row['first_name']} has shown strong activity from {company_name}. "
        "This outreach should connect that interest to the buyer’s goal."
    )
    pain_points = [
        "Clarify the timeline for current priorities",
        "Understand where resource pressure is highest",
        "Align on the buying team’s most urgent initiative"
    ]
    questions = [
        "What outcome are you trying to achieve this quarter?",
        "How are you currently validating interest from stakeholders?",
        "Who else should be involved in the next conversation?"
    ]
    reason = (
        "Recent engagement plus strong role and account fit make this prospect a high-value next call."
    )
    return {
        "opening": opening,
        "pain_points": pain_points,
        "questions": questions,
        "reason": reason
    }


def render_record_detail():
    """Renders the Prospect Brief page."""
    st.markdown("<h1 style='color:#3B82F6; margin-bottom:4px;'>Prospect Brief</h1>", unsafe_allow_html=True)
    st.markdown("An executive briefing document that explains exactly why the prospect is prioritized and what action should be taken.")
    st.markdown("---")

    df, cm_df, _, _ = load_unified_data()
    df["company_name"] = df.get("account_name").fillna(df.get("account_id")).fillna("Unknown Company")
    df["full_name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")

    if df.empty:
        st.warning("No prospect data available.")
        return

    default_id = st.session_state.get("selected_prospect_id", df["master_person_id"].iloc[0])
    if default_id not in df["master_person_id"].values:
        default_id = df["master_person_id"].iloc[0]

    options = [f"{row['master_person_id']} - {row['full_name']} ({row['company_name']})" for _, row in df.iterrows()]
    id_index = {row['master_person_id']: idx for idx, row in df.iterrows()}
    selected_option = st.selectbox("Select prospect to brief", options, index=id_index.get(default_id, 0))
    mpid = selected_option.split(" - ")[0]
    st.session_state["selected_prospect_id"] = mpid

    row = df[df["master_person_id"] == mpid].iloc[0]
    company_name = row["company_name"]
    action_text = _recommended_action(row)
    confidence_text = _confidence_label(row["readiness_score"])
    confidence_pct = _confidence_pct(row["readiness_score"])

    st.markdown(
        "<div style='padding:22px; border-radius:18px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
        f"<div style='display:flex; justify-content:space-between; gap:16px;'>"
        f"<div><h2 style='margin:0; color:#F8FAFC;'>{row['full_name']}</h2>"
        f"<p style='color:#94A3B8; margin:4px 0 0;'>{row['title'] or 'Title missing'}</p>"
        f"<p style='color:#94A3B8; margin:2px 0 0;'>{company_name}</p></div>"
        f"<div style='text-align:right; min-width:160px;'>"
        f"<div style='display:inline-block; background:#1D3A5A; color:#22C55E; padding:8px 14px; border-radius:999px; font-weight:600;'>Readiness {row['readiness_score']:.0f}</div>"
        f"<div style='margin-top:10px; display:inline-block; background:#13213B; color:#94A3B8; padding:8px 14px; border-radius:999px;'>{confidence_text} confidence</div>"
        f"<div style='margin-top:12px; padding:14px; border-radius:16px; background:#071827; border:1px solid rgba(59,130,246,0.25);'>"
        f"<strong style='color:#F8FAFC;'>Recommended Action</strong><br>{action_text}</div>"
        f"</div></div></div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    positives = [item for item in str(row.get("top_positive_reasons", "")).split(", ") if item and item != "None"]
    negatives = [item for item in str(row.get("top_negative_reasons", "")).split(", ") if item and item != "None"]

    st.markdown("<h3 style='color:#F8FAFC;'>Why This Prospect Matters</h3>", unsafe_allow_html=True)
    st.markdown(
        f"{row['full_name']} is prioritized because recent buying signals line up with a strong role fit at a target account. "
        "This prospect has active engagement and a profile that justifies immediate sales outreach."
    )
    st.markdown("---")

    col_pos, col_neg = st.columns(2)
    with col_pos:
        st.markdown("<h4 style='color:#22C55E;'>Positive Signals</h4>", unsafe_allow_html=True)
        if positives:
            for signal in positives:
                st.markdown(f"✔️ {signal}")
        else:
            st.markdown("No clear positive signals found.")

    with col_neg:
        st.markdown("<h4 style='color:#F59E0B;'>Negative Signals</h4>", unsafe_allow_html=True)
        if negatives:
            for signal in negatives:
                st.markdown(f"⚠️ {signal}")
        else:
            st.markdown("No major blockers found.")

    st.markdown("---")
    track = _talk_track(row, company_name)
    st.markdown("<h3 style='color:#F8FAFC;'>BDR Recommended Talk Track</h3>", unsafe_allow_html=True)
    st.markdown(f"**Opening statement:** {track['opening']}")
    st.markdown("**Likely pain points:**")
    for pain in track['pain_points']:
        st.markdown(f"- {pain}")
    st.markdown("**Suggested questions:**")
    for question in track['questions']:
        st.markdown(f"- {question}")
    st.markdown(f"**Reason for outreach:** {track['reason']}")

    st.markdown("---")
    st.markdown("<h3 style='color:#F8FAFC;'>Timeline of Engagement</h3>", unsafe_allow_html=True)
    timeline_df = cm_df[cm_df['master_person_id'] == mpid].copy()
    if not timeline_df.empty:
        timeline_df['response_date'] = pd.to_datetime(timeline_df['response_date'], errors='coerce')
        timeline_df = timeline_df.sort_values(by='response_date', ascending=False).head(5)
        for _, event in timeline_df.iterrows():
            event_date = event['response_date']
            label = _event_label(event)
            date_label = event_date.strftime('%b %d') if pd.notnull(event_date) else 'Recent'
            st.markdown(f"**{date_label}** — {label}")
    else:
        st.markdown("No recent campaign activity is available for this prospect.")

    st.markdown(
        "<div style='padding:22px; border-radius:18px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
        "<h3 style='color:#F8FAFC;'>Decision Recommendation</h3>"
        f"<p style='margin:8px 0 0;'>Recommendation: <strong>{action_text}</strong></p>"
        f"<p style='margin:4px 0 0;'>Reason: Multiple recent buying signals and strong profile fit support outreach.</p>"
        f"<p style='margin:4px 0 0;'>Confidence: <strong>{confidence_pct}%</strong></p>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

