"""
Prospect Brief Submodule for Streamlit Application.

Transforms the 360° record detail into an executive briefing document for
BDRs, sales leadership, and non-technical stakeholders.
"""

import ast
import pandas as pd
import streamlit as st
from app.utils import load_unified_data


def _normalize_talking_points(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if value.startswith("[") and value.endswith("]"):
            try:
                return list(ast.literal_eval(value))
            except Exception:
                return [value]
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [value]
    return []


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
    st.markdown(
        "<div style='margin-bottom:28px;'>"
        "<h1 style='color:#3B82F6; margin:0 0 8px; font-size:2.4rem;'>Prospect Brief</h1>"
        "<p style='color:#94A3B8; margin:0; font-size:1.05rem;'>A complete briefing document that explains exactly why this prospect is ready and what to say.</p>"
        "</div>",
        unsafe_allow_html=True
    )

    df, cm_df, _, _ = load_unified_data()
    df["company_name"] = df.get("account_name").fillna(df.get("account_id")).fillna("Unknown Company")
    df["full_name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")

    if df.empty:
        st.warning("No prospect data available.")
        return

    default_id = st.session_state.get("selected_prospect_id", df["master_person_id"].iloc[0])
    if default_id not in df["master_person_id"].values:
        default_id = df["master_person_id"].iloc[0]

    options = [f"{row['full_name']} at {row['company_name']}" for _, row in df.iterrows()]
    id_index = {row['master_person_id']: idx for idx, row in df.iterrows()}
    selected_option = st.selectbox("Select a prospect", options, index=id_index.get(default_id, 0), label_visibility="collapsed")
    selected_idx = options.index(selected_option)
    mpid = df.iloc[selected_idx]['master_person_id']
    st.session_state["selected_prospect_id"] = mpid

    row = df[df["master_person_id"] == mpid].iloc[0]
    company_name = row["company_name"]
    action_text = row.get("recommended_action") if row.get("agentic_recommendation_available") else _recommended_action(row)
    confidence_text = _confidence_label(row["readiness_score"])
    confidence_pct = _confidence_pct(row["readiness_score"])

    st.markdown(
        "<div style='padding:28px; border-radius:18px; background:linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.05) 100%); border:1px solid rgba(59,130,246,0.2); margin-bottom:28px;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:flex-start; gap:20px;'>"
        f"<div style='flex:1;'>"
        f"<h2 style='margin:0 0 4px; color:#F8FAFC; font-size:1.8rem;'>{row['full_name']}</h2>"
        f"<p style='color:#94A3B8; margin:0; font-size:1rem;'>{row['title'] or 'Title not provided'}</p>"
        f"<p style='color:#3B82F6; margin:8px 0 0; font-weight:600;'>{company_name}</p>"
        f"</div>"
        f"<div style='text-align:right;'>"
        f"<div style='background:rgba(34,197,94,0.15); color:#22C55E; padding:10px 16px; border-radius:10px; font-weight:700; margin-bottom:8px; font-size:1.1rem;'>Readiness {row['readiness_score']:.0f} / 100</div>"
        f"<div style='background:rgba(59,130,246,0.15); color:#3B82F6; padding:8px 14px; border-radius:10px; font-weight:600; font-size:0.9rem;'>{confidence_text} Confidence</div>"
        f"</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='padding:24px; border-radius:16px; background:#0E1728; border:1px solid rgba(34,197,94,0.2); margin-bottom:28px;'>"
        f"<h3 style='margin:0 0 12px; color:#22C55E; font-size:1.2rem;'>✓ Recommended Action</h3>"
        f"<p style='margin:0; color:#F8FAFC; font-size:1.05rem; font-weight:600;'>{action_text}</p>"
        "</div>",
        unsafe_allow_html=True
    )

    positives = [item for item in str(row.get("top_positive_reasons", "")).split(", ") if item and item != "None"]
    negatives = [item for item in str(row.get("top_negative_reasons", "")).split(", ") if item and item != "None"]

    col_pos, col_neg = st.columns(2, gap="medium")
    
    with col_pos:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(34,197,94,0.2);'>"
            "<h4 style='color:#22C55E; margin:0 0 12px;'>✔️ Positive Signals</h4>",
            unsafe_allow_html=True
        )
        if positives:
            for signal in positives:
                st.markdown(f"→ {signal}")
        else:
            st.markdown("<p style='color:#94A3B8;'>No clear signals</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_neg:
        st.markdown(
            "<div style='padding:20px; border-radius:14px; background:#0E1728; border:1px solid rgba(245,158,11,0.2);'>"
            "<h4 style='color:#F59E0B; margin:0 0 12px;'>⚠️ Concerns</h4>",
            unsafe_allow_html=True
        )
        if negatives:
            for signal in negatives:
                st.markdown(f"→ {signal}")
        else:
            st.markdown("<p style='color:#94A3B8;'>No major blockers</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    if row.get("agentic_recommendation_available"):
        st.markdown(
            "<div style='padding:24px; border-radius:16px; background:#0E1728; border:1px solid rgba(59,130,246,0.2); margin-bottom:28px;'>"
            "<h3 style='color:#3B82F6; margin:0 0 16px; font-size:1.2rem;'>🤖 AI Insights</h3>",
            unsafe_allow_html=True
        )
        st.markdown(f"**Why they're ready:** {row.get('why_summary', 'No summary available.')}")
        st.markdown(f"**Why now:** {row.get('why_now_summary', 'No recent evidence summary available.')}")
        st.markdown(f"**How we know:** {row.get('where_signal_summary', 'No campaign signal summary available.')}")
        if row.get("risk_note"):
            st.markdown(f"**⚠️ Important:** {row.get('risk_note')}")
        talking_points = _normalize_talking_points(row.get("talking_points", ""))
        if talking_points:
            st.markdown("**Conversation starters:**")
            for point in talking_points:
                st.markdown(f"→ {point}")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        track = _talk_track(row, company_name)
        st.markdown(
            "<div style='padding:24px; border-radius:16px; background:#0E1728; border:1px solid rgba(59,130,246,0.2); margin-bottom:28px;'>"
            "<h3 style='color:#3B82F6; margin:0 0 16px; font-size:1.2rem;'>💬 Suggested Talk Track</h3>",
            unsafe_allow_html=True
        )
        st.markdown(f"**Opening:** {track['opening']}")
        st.markdown("**Likely pain points they're facing:**")
        for pain in track['pain_points']:
            st.markdown(f"→ {pain}")
        st.markdown("**Questions to ask:**")
        for question in track['questions']:
            st.markdown(f"→ {question}")
        st.markdown(f"**Why reach out now:** {track['reason']}")
        st.markdown("</div>", unsafe_allow_html=True)

    timeline_df = cm_df[cm_df['master_person_id'] == mpid].copy()
    if not timeline_df.empty:
        st.markdown(
            "<h3 style='color:#F8FAFC; margin-bottom:16px; font-size:1.2rem;'>📅 Recent Engagement Timeline</h3>",
            unsafe_allow_html=True
        )
        timeline_df['response_date'] = pd.to_datetime(timeline_df['response_date'], errors='coerce')
        timeline_df = timeline_df.sort_values(by='response_date', ascending=False).head(5)
        for _, event in timeline_df.iterrows():
            event_date = event['response_date']
            label = _event_label(event)
            date_label = event_date.strftime('%b %d, %Y') if pd.notnull(event_date) else 'Recent'
            st.markdown(f"**{date_label}** — {label}")
    else:
        st.markdown(
            "<div style='padding:16px; border-radius:12px; background:#0E1728; border:1px solid rgba(255,255,255,0.08);'>"
            "<p style='color:#94A3B8; margin:0;'>No campaign activity yet for this prospect</p>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("")
    st.markdown(
        "<div style='padding:24px; border-radius:16px; background:linear-gradient(135deg, rgba(34,197,94,0.1) 0%, rgba(34,197,94,0.05) 100%); border:1px solid rgba(34,197,94,0.2);'>"
        "<h3 style='color:#22C55E; margin:0 0 12px; font-size:1.1rem;'>✓ Ready to Reach Out</h3>"
        f"<p style='margin:0; color:#94A3B8; line-height:1.6;'>"
        f"This prospect combines multiple engagement signals with a strong profile fit. "
        f"The <strong>{confidence_pct}% confidence</strong> score reflects readiness to engage. "
        f"Recommend: <strong>{action_text}</strong>"
        "</p>"
        "</div>",
        unsafe_allow_html=True
    )
