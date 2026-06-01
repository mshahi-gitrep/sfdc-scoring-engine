"""
Reviewer Playground Submodule for Streamlit Application.

Renders slider/checkbox controls to modify engagement and account assumptions,
running live sensitivity calculations to plot delta comparisons in real-time.

"""

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from app.utils import load_unified_data, simulate_readiness_score


def render_reviewer_playground():
    """Renders the Reviewer Playground Sensitivity page."""
    st.markdown("<h1 style='color: #1E90FF;'>🎯 Reviewer Playground (Sensitivity Analysis)</h1>", unsafe_allow_html=True)
    st.markdown("Modify assumptions (add campaign response history, toggle named accounts, alter intent) to see the readiness score and prioritization tier recalculate reactively.")
    st.markdown("---")

    # Load data
    df, _, _, _ = load_unified_data()

    # Determine default selected ID from session state, fallback to first in list
    default_id = st.session_state.get("selected_prospect_id", df["master_person_id"].iloc[0])
    
    if default_id not in df["master_person_id"].values:
        default_id = df["master_person_id"].iloc[0]

    # Prospect Selector
    prospects_list = {
        f"{row['master_person_id']} - {row['first_name']} {row['last_name']} (Original Score: {row['readiness_score']})": row["master_person_id"]
        for _, row in df.iterrows()
    }
    
    default_index = 0
    for idx, key in enumerate(prospects_list.keys()):
        if prospects_list[key] == default_id:
            default_index = idx
            break

    selected_key = st.selectbox("Select Opportunity to Simulate:", list(prospects_list.keys()), index=default_index)
    mpid = prospects_list[selected_key]

    # Save to session state so it persists
    st.session_state["selected_prospect_id"] = mpid

    # Fetch prospect data
    row = df[df["master_person_id"] == mpid].iloc[0]

    st.markdown("---")

    # ----------------------------------------------------
    # Page Columns: Left Controls vs. Right Output Simulation
    # ----------------------------------------------------
    col_left_ctrl, col_right_sim = st.columns([1, 1.2])

    with col_left_ctrl:
        st.subheader("Simulation Controls")
        st.markdown("Alter campaign response history and account-level contexts to recalculate priorities live:")

        st.markdown("### 1. Additional Campaign Engagement History")
        extra_webinars = st.slider("Add Webinar Responses (+70 pts value each)", 0, 10, 0, help="Simulate a prospect registering/attending a new webinar.")
        extra_events = st.slider("Add Event Responses (+100 pts value each)", 0, 5, 0, help="Simulate a prospect attending a premium event (e.g. VIP Diner).")

        st.markdown("### 2. Account-Level Prioritization Modifiers")
        
        # Check if prospect has an account
        has_account = pd.notnull(row["account_id"])
        
        if has_account:
            init_intent = float(row["intent_score"])
            init_named = bool(row["is_named_account"])
            
            intent_score_sim = st.slider("Alter Account Intent Score", 0.0, 100.0, init_intent, step=5.0)
            is_named_sim = st.checkbox("Toggle Strategic Named Account Tier", value=init_named)
        else:
            st.info("Prospect is an Orphan Lead (no account linkage). Account-level simulations are restricted.")
            intent_score_sim = 0.0
            is_named_sim = False

        st.markdown("---")
        st.info("💡 Adjust the sliders to see scores, bands, and explainability reasons recalibrate reactively on the right panel!")

    with col_right_sim:
        st.subheader("Simulated Opportunity Prioritization")

        # Compile modifications
        mods = {
            "extra_webinars": extra_webinars,
            "extra_events": extra_events,
            "intent_score": intent_score_sim,
            "is_named_account": is_named_sim
        }

        # Run sensitivity simulation
        sim_res = simulate_readiness_score(row, {}, mods)

        # ----------------------------------------------------
        # Score Delta Comparison
        # ----------------------------------------------------
        orig_score = float(row["readiness_score"])
        sim_score = float(sim_res["readiness_score"])
        score_delta = sim_score - orig_score

        col_orig, col_sim = st.columns(2)
        with col_orig:
            st.metric("Original Score", f"{orig_score:.1f}", help="Prioritization score from static database.")
        with col_sim:
            delta_str = f"+{score_delta:.1f}" if score_delta >= 0 else f"{score_delta:.1f}"
            st.metric(
                "Simulated Score", 
                f"{sim_score:.1f}", 
                delta=f"{delta_str} points",
                delta_color="normal" if score_delta >= 0 else "inverse"
            )

        # Priority Tiers & Bands comparisons
        orig_tier = row["priority_tier"]
        sim_tier = sim_res["priority_tier"]
        orig_band = row["readiness_band"]
        sim_band = sim_res["readiness_band"]

        st.markdown(f"**Priority Tier Calibration**: `{orig_tier} ({orig_band})` ➡️ `{sim_tier} ({sim_band})`")

        # ----------------------------------------------------
        # Side-by-Side Component Scores Visual Chart
        # ----------------------------------------------------
        # Get raw simulated breakdown
        sim_eng = sim_res["engagement_score"]
        sim_rec = sim_res["recency_score"]
        sim_prof = sim_res["profile_fit_score"]
        sim_acc = sim_res["account_score"]

        # Parse original breakdown
        orig_breakdown = json.loads(row["score_breakdown_json"])
        orig_eng = orig_breakdown["engagement"]
        orig_rec = orig_breakdown["recency"]
        orig_prof = orig_breakdown["profile"]
        orig_acc = orig_breakdown["account"]

        # Draw Side-by-Side Bar Chart using Plotly graph objects
        fig_sim = go.Figure(data=[
            go.Bar(
                name='Original Components',
                y=['Engagement', 'Recency', 'Profile Fit', 'Account Fit'],
                x=[orig_eng, orig_rec, orig_prof, orig_acc],
                orientation='h',
                marker_color='#ADD8E6'
            ),
            go.Bar(
                name='Simulated Components',
                y=['Engagement', 'Recency', 'Profile Fit', 'Account Fit'],
                x=[sim_eng, sim_rec, sim_prof, sim_acc],
                orientation='h',
                marker_color='#1E90FF'
            )
        ])
        
        fig_sim.update_layout(
            barmode='group',
            height=240,
            template="plotly_white",
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_sim, use_container_width=True)

        # ----------------------------------------------------
        # Updated Explainability Reasons panels
        # ----------------------------------------------------
        st.markdown("### Recalculated Explainability")
        
        col_pos_sim, col_neg_sim = st.columns(2)
        with col_pos_sim:
            st.markdown("<p style='color: #2E8B57; font-weight: bold;'>🟢 Simulated Positive Drivers</p>", unsafe_allow_html=True)
            positives = sim_res["top_positive_reasons"].split(", ")
            if positives and positives[0] != "None":
                for pos in positives:
                    st.markdown(f"✔️ **{pos}**")
            else:
                st.markdown("*No active positive drivers.*")

        with col_neg_sim:
            st.markdown("<p style='color: #DC143C; font-weight: bold;'>🔴 Simulated Negative Detractors</p>", unsafe_allow_html=True)
            negatives = sim_res["top_negative_reasons"].split(", ")
            if negatives and negatives[0] != "None":
                for neg in negatives:
                    st.markdown(f"⚠️ **{neg}**")
            else:
                st.markdown("*No active negative detractors.*")
