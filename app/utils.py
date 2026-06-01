"""
Utility Module for Streamlit Application.

This module centralizes data loading, Plotly telemetry charts construction, 
and the core Sensitivity Simulation Engine for the Reviewer Playground.

"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pipeline.stage04_agentic_explainer import SalesforceAgenticExplainer
from typing import Dict, List, Tuple, Any


@st.cache_data
def load_unified_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads and returns all processed and raw datasets cached for fast rendering."""
    master_persons_path = "data/processed/master_persons.csv"
    person_features_path = "data/processed/person_features.csv"
    person_scores_path = "data/processed/person_scores.csv"
    campaign_members_path = "data/raw/campaign_members_data.csv"
    entity_resolution_map_path = "data/processed/entity_resolution_map.csv"
    accounts_path = "data/raw/accounts_data.csv"

    # Fallback checking
    for path in [master_persons_path, person_features_path, person_scores_path, campaign_members_path, entity_resolution_map_path, accounts_path]:
        if not os.path.exists(path):
            st.error(f"[ERROR] Required dataset not found at: {path}. Please run pipeline stages first.")
            st.stop()

    master_df = pd.read_csv(master_persons_path)
    features_df = pd.read_csv(person_features_path)
    scores_df = pd.read_csv(person_scores_path)
    cm_df = pd.read_csv(campaign_members_path)
    accounts_df = pd.read_csv(accounts_path)
    entity_map_df = pd.read_csv(entity_resolution_map_path)
    recommendations_path = "data/processed/person_agent_recommendations.csv"

    # Auto-generate agentic recommendations if missing or stale
    if not os.path.exists(recommendations_path):
        st.info("Generating AI recommendation data for the first time...")
        SalesforceAgenticExplainer().calculate_recommendations()
    else:
        src_times = [os.path.getmtime(p) for p in [master_persons_path, person_scores_path, entity_resolution_map_path, campaign_members_path] if os.path.exists(p)]
        dest_time = os.path.getmtime(recommendations_path)
        if any(src_time > dest_time for src_time in src_times):
            st.info("Regenerating AI recommendation data because source datasets changed...")
            SalesforceAgenticExplainer().calculate_recommendations()

    recommendations_df = pd.read_csv(recommendations_path) if os.path.exists(recommendations_path) else pd.DataFrame()

    # Enrich raw CampaignMember data with master_person_id from entity resolution output
    if "entity_id" in cm_df.columns and "raw_entity_id" in entity_map_df.columns and "master_person_id" in entity_map_df.columns:
        map_dict = entity_map_df.set_index("raw_entity_id")["master_person_id"].to_dict()
        cm_df["master_person_id"] = cm_df["entity_id"].map(map_dict)
        cm_df = cm_df[cm_df["master_person_id"].notnull()].copy()

    # Compile a unified rich dataset by joining scores and features together
    # Drop duplicate name/title/eligibility/block columns before joining to prevent pandas suffix collisions (_x, _y)
    features_clean = features_df.drop(
        columns=[
            "first_name", "last_name", "title", "eligibility_status", "structural_block_flag"
        ], 
        errors="ignore"
    )
    
    unified_df = pd.merge(scores_df, features_clean, on="master_person_id", how="left")

    # Drop duplicate name/title/account columns from master_df before merging to prevent pandas suffix collisions
    master_clean = master_df.drop(
        columns=[
            "first_name", "last_name", "title", "account_id"
        ],
        errors="ignore"
    )
    
    unified_df = pd.merge(unified_df, master_clean, on="master_person_id", how="left")

    # Enrich with business-friendly account names when available
    if "account_id" in unified_df.columns and "account_id" in accounts_df.columns:
        unified_df = pd.merge(
            unified_df,
            accounts_df[["account_id", "account_name"]].drop_duplicates(subset=["account_id"]),
            on="account_id",
            how="left"
        )

    # Coalesce duplicate flag columns created by pandas suffixing from overlapping feature/master fields
    suffixed_cols = [c for c in unified_df.columns if c.endswith("_x") or c.endswith("_y")]
    base_names = set(c[:-2] for c in suffixed_cols)
    for base in base_names:
        x_col = f"{base}_x"
        y_col = f"{base}_y"
        if x_col in unified_df.columns and y_col in unified_df.columns:
            unified_df[base] = unified_df[x_col].combine_first(unified_df[y_col])
            unified_df = unified_df.drop(columns=[x_col, y_col])
        elif x_col in unified_df.columns and base not in unified_df.columns:
            unified_df = unified_df.rename(columns={x_col: base})
        elif y_col in unified_df.columns and base not in unified_df.columns:
            unified_df = unified_df.rename(columns={y_col: base})

    unified_df["dq_flag"] = (
        unified_df.get("missing_title_flag", False) |
        unified_df.get("duplicate_email_flag", False) |
        unified_df.get("missing_account_flag", False) |
        unified_df.get("opted_out_flag", False) |
        unified_df.get("bounced_or_left_company_flag", False) |
        unified_df.get("shared_mailbox_flag", False) |
        unified_df.get("broken_conversion_link_flag", False)
    )

    if not recommendations_df.empty:
        unified_df = pd.merge(unified_df, recommendations_df, on="master_person_id", how="left")
        unified_df["agentic_recommendation_available"] = unified_df["why_summary"].notnull()
    else:
        unified_df["agentic_recommendation_available"] = False

    return unified_df, cm_df, accounts_df, master_df


def simulate_readiness_score(original_row: pd.Series, acc_info: Dict[str, Any], mods: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sensitivity Simulation Engine.
    Takes a master person's original features and applies modifications live,
    recalculating all decomposed component scores, priority bands, and explainability reasons.
    """
    # ----------------------------------------------------
    # 1. Apply modifications to simulated features
    # ----------------------------------------------------
    # Base count modifications
    extra_webinars = int(mods.get("extra_webinars", 0))
    extra_events = int(mods.get("extra_events", 0))
    new_intent_score = float(mods.get("intent_score", original_row["intent_score"]))
    new_is_named = bool(mods.get("is_named_account", original_row["is_named_account"]))

    # Calculations
    total_responses = int(original_row["total_responses"]) + extra_webinars + extra_events
    webinar_attended = int(original_row["webinar_attended_count"]) + extra_webinars
    event_attended = int(original_row["event_attended_count"]) + extra_events
    content_response = int(original_row["content_response_count"])
    email_response = int(original_row["email_response_count"])
    
    total_memberships = int(original_row["total_campaign_memberships"]) + extra_webinars + extra_events
    automated_touches = int(original_row["automated_touch_count"])

    # If new webinar/event, update recency to 5.0 days (recent activity)
    days_since_last = float(original_row["days_since_last_response"])
    if extra_webinars > 0 or extra_events > 0:
        days_since_last = min(days_since_last, 5.0)

    # Recompute quality score
    raw_quality_sum = (
        (event_attended * 100) + 
        (webinar_attended * 70) + 
        (content_response * 50) + 
        (email_response * 20)
    )
    engagement_quality = float(raw_quality_sum / max(1, total_responses)) if total_responses > 0 else 0.0

    # Automation ratio
    automation_ratio = float(automated_touches / max(1, total_memberships))

    # Boost updates
    burst_flag = bool(original_row["engagement_burst_flag"])
    if (extra_webinars + extra_events) >= 3:
        burst_flag = True

    sustained_flag = bool(original_row["sustained_engagement_flag"])
    if total_responses >= 3 and days_since_last <= 30:
        sustained_flag = True

    # Account indicators
    is_icp = bool(original_row["is_icp_qualified"])
    
    # Calculate simulated buying committee strength
    acc_engaged_contacts = int(original_row["engaged_contacts_on_account"])
    # If the user changed their account status to named, and they were not previously, update engaged contacts
    if new_is_named and not original_row["is_named_account"]:
        acc_engaged_contacts = max(1, acc_engaged_contacts)
    
    buying_committee_size = 6 if new_is_named else 3
    committee_strength = (acc_engaged_contacts / buying_committee_size) * 100.0 if pd.notnull(original_row["account_id"]) else 0.0
    committee_strength = min(100.0, committee_strength)

    # ----------------------------------------------------
    # 2. Decomposed Component Scoring Formulas
    # ----------------------------------------------------
    # A. Engagement Score (0-45)
    quality_contrib = (engagement_quality / 100.0) * 20.0
    volume_contrib = min(25.0, total_responses * 5.0)
    eng_score = quality_contrib + volume_contrib
    if automation_ratio > 0.70:
        eng_score = max(0.0, eng_score - 15.0)
    eng_score = round(min(45.0, max(0.0, eng_score)), 2)

    # B. Recency Score (0-25)
    if days_since_last <= 7:
        rec_base = 20.0
    elif days_since_last <= 14:
        rec_base = 16.0
    elif days_since_last <= 30:
        rec_base = 12.0
    elif days_since_last <= 90:
        rec_base = 6.0
    else:
        rec_base = 0.0

    boost = 0.0
    if burst_flag:
        boost += 5.0
    if sustained_flag:
        boost += 3.0

    rec_score = rec_base + boost
    rec_score = round(min(25.0, max(0.0, rec_score)), 2)

    # C. Profile Score (0-20)
    seniority = float(original_row["seniority_score"])
    persona = float(original_row["persona_score"])
    completeness = float(original_row["profile_completeness_score"])

    seniority_contrib = (seniority / 100.0) * 8.0
    persona_contrib = (persona / 100.0) * 8.0
    completeness_contrib = (completeness / 100.0) * 4.0
    prof_score = round(min(20.0, max(0.0, seniority_contrib + persona_contrib + completeness_contrib)), 2)

    # D. Account Score (0-10)
    icp_contrib = 2.0 if is_icp else 0.0
    named_contrib = 3.0 if new_is_named else 0.0
    intent_contrib = (new_intent_score / 100.0) * 3.0
    strength_contrib = (committee_strength / 100.0) * 2.0
    acc_score = round(min(10.0, max(0.0, icp_contrib + named_contrib + intent_contrib + strength_contrib)), 2)

    # E. Final Readiness Score (0-100)
    readiness_score = float(round(eng_score + rec_score + prof_score + acc_score, 2))
    readiness_score = min(100.0, max(0.0, readiness_score))

    # Tiers and bands
    if readiness_score >= 80.0:
        priority_tier = "Hot"
        readiness_band = "Very High"
    elif readiness_score >= 60.0:
        priority_tier = "Warm"
        readiness_band = "High"
    elif readiness_score >= 40.0:
        priority_tier = "Monitor"
        readiness_band = "Medium"
    else:
        priority_tier = "Cold"
        readiness_band = "Low"

    # Explainability
    pos_reasons: List[str] = []
    neg_reasons: List[str] = []

    if total_responses >= 3:
        pos_reasons.append("High interaction volume (3+ responses)")
    if event_attended >= 1:
        pos_reasons.append("Attended premium Event campaign")
    if days_since_last <= 7:
        pos_reasons.append("Hot recency: engaged within past 7 days")
    if burst_flag:
        pos_reasons.append("Engagement surge detected in past 14 days")
    if seniority >= 70:
        pos_reasons.append("High-tier buying authority (Director/C-Suite)")
    if new_is_named:
        pos_reasons.append("Strategic Named Account profile match")
    if committee_strength >= 50:
        pos_reasons.append("Strong buying-committee activity at account")
    if completeness >= 85:
        pos_reasons.append("High profile completeness")

    if total_responses == 0:
        neg_reasons.append("Zero response history (passive sends only)")
    elif days_since_last >= 90:
        neg_reasons.append("Cold recency: no engagement in past 90 days")
    if automation_ratio > 0.70:
        neg_reasons.append("High automation inflation (DQ-8: >70% sends)")
    if seniority <= 25:
        neg_reasons.append("Individual contributor profile (low decision influence)")
    if bool(original_row.get("missing_title_flag", False)):
        neg_reasons.append("Data gap: missing title field")
    if bool(original_row.get("missing_account_flag", False)):
        neg_reasons.append("Data gap: missing account linkage (orphan)")
    if bool(original_row.get("duplicate_email_flag", False)):
        neg_reasons.append("Data quality risk: duplicate email address")
    if bool(original_row.get("shared_mailbox_flag", False)):
        neg_reasons.append("Data quality risk: shared general inbox address")

    top_pos = ", ".join(pos_reasons[:3]) if pos_reasons else "None"
    top_neg = ", ".join(neg_reasons[:3]) if neg_reasons else "None"

    return {
        "engagement_score": eng_score,
        "recency_score": rec_score,
        "profile_fit_score": prof_score,
        "account_score": acc_score,
        "readiness_score": readiness_score,
        "priority_tier": priority_tier,
        "readiness_band": readiness_band,
        "top_positive_reasons": top_pos,
        "top_negative_reasons": top_neg,
        "simulated_features": {
            "total_campaign_memberships": total_memberships,
            "total_responses": total_responses,
            "automated_touch_count": automated_touches,
            "automation_ratio": automation_ratio,
            "engagement_quality_score": engagement_quality,
            "buying_committee_strength": committee_strength,
            "days_since_last_response": days_since_last
        }
    }
