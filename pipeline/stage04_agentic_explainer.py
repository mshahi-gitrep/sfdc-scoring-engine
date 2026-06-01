"""
Stage 04: Agentic Explanation and Recommendation Layer.

This module generates deterministic, explainable BDR recommendations for each
resolved master person. It ingests prioritization scores, master person context,
raw campaign membership activity, and entity resolution mappings to produce a
lightweight reasoning layer without external APIs or LLM dependencies.

Outputs:
- data/processed/person_agent_recommendations.csv

Author: Senior Data Engineer
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd


class SalesforceAgenticExplainer:
    """Produces deterministic agentic summaries and recommendations."""

    def __init__(
        self,
        person_scores_path: str = "data/processed/person_scores.csv",
        master_persons_path: str = "data/processed/master_persons.csv",
        campaign_members_path: str = "data/raw/campaign_members_data.csv",
        entity_resolution_map_path: str = "data/processed/entity_resolution_map.csv",
        output_path: str = "data/processed/person_agent_recommendations.csv"
    ):
        self.person_scores_path = person_scores_path
        self.master_persons_path = master_persons_path
        self.campaign_members_path = campaign_members_path
        self.entity_resolution_map_path = entity_resolution_map_path
        self.output_path = output_path

    def calculate_recommendations(self) -> pd.DataFrame:
        """Generates the agentic recommendations dataset and writes it to CSV."""
        for path in [
            self.person_scores_path,
            self.master_persons_path,
            self.campaign_members_path,
            self.entity_resolution_map_path
        ]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"[ERROR] Required input file not found at: {path}")

        scores_df = pd.read_csv(self.person_scores_path)
        master_df = pd.read_csv(self.master_persons_path)
        cm_raw_df = pd.read_csv(self.campaign_members_path)
        map_df = pd.read_csv(self.entity_resolution_map_path)

        # Enrich raw CampaignMember rows with master_person_id where possible
        if "entity_id" in cm_raw_df.columns and "raw_entity_id" in map_df.columns:
            mapping = map_df.set_index("raw_entity_id")["master_person_id"].to_dict()
            cm_raw_df["master_person_id"] = cm_raw_df["entity_id"].map(mapping)

        # normalize dates
        if "response_date" in cm_raw_df.columns:
            cm_raw_df["response_date"] = pd.to_datetime(cm_raw_df["response_date"], errors="coerce")

        campaign_groups = {
            mpid: group
            for mpid, group in cm_raw_df.groupby("master_person_id")
            if mpid is not None and pd.notnull(mpid)
        }

        person_map = master_df.set_index("master_person_id").to_dict(orient="index")

        recommendations: List[Dict[str, Any]] = []
        for _, row in scores_df.iterrows():
            mpid = row["master_person_id"]
            master_info = person_map.get(mpid, {})
            campaign_history = campaign_groups.get(mpid, pd.DataFrame())

            why_summary = self._build_why_summary(row, campaign_history)
            where_summary = self._build_where_signal_summary(row, campaign_history)
            recommended_action = self._build_recommended_action(row)
            talking_points = self._build_talking_points(row, master_info, campaign_history)
            why_now = self._build_why_now_summary(row, campaign_history)
            risk_note = self._build_risk_note(row)

            recommendations.append({
                "master_person_id": mpid,
                "why_summary": why_summary,
                "where_signal_summary": where_summary,
                "recommended_action": recommended_action,
                "why_now_summary": why_now,
                "talking_points": talking_points,
                "risk_note": risk_note
            })

        rec_df = pd.DataFrame(recommendations)
        rec_df.to_csv(self.output_path, index=False)
        self._print_validation_report(rec_df)
        return rec_df

    def _build_why_summary(self, row: pd.Series, campaign_history: pd.DataFrame) -> str:
        tier = str(row.get("priority_tier", "Cold"))
        eligibility = str(row.get("eligibility_status", "Eligible"))
        positives = self._split_reason_text(row.get("top_positive_reasons", "None"))
        negatives = self._split_reason_text(row.get("top_negative_reasons", "None"))
        automation_ratio = float(row.get("automation_ratio", 0.0))
        total_responses = int(row.get("total_responses", 0))
        days_since_last = float(row.get("days_since_last_response", 180.0))
        is_named = bool(row.get("is_named_account", False))
        strength = float(row.get("buying_committee_strength", 0.0))

        descriptions: List[str] = []

        if tier == "Hot":
            descriptions.append("This prospect is currently a high-priority opportunity with strong account fit and active buying signals.")
        elif tier == "Warm":
            descriptions.append("This prospect is showing promising momentum and deserves structured outreach to capture interest.")
        elif tier == "Monitor":
            descriptions.append("This prospect is worth keeping warm while we wait for a clearer engagement signal.")
        else:
            descriptions.append("This prospect has profile strength, but engagement is currently limited and it is not ready for immediate BDR pursuit.")

        if is_named or strength >= 50:
            descriptions.append("The account appears to be strategically aligned with a strong buying committee.")

        if total_responses == 0:
            descriptions.append("There is little to no evidence of proactive buyer interest today.")
        elif automation_ratio > 0.70 and total_responses < int(row.get("total_campaign_memberships", 0) * 0.4):
            descriptions.append("Most recorded activity is passive marketing touches rather than voluntary buyer responses.")
        elif days_since_last <= 14:
            descriptions.append("Recent activity suggests a fresh engagement window and should be acted on quickly.")
        elif days_since_last <= 30:
            descriptions.append("The most recent engagement is within the past month, so the prospect is still in a reasonably current evaluation timeframe.")

        if positives:
            descriptions.append("Notable strengths include " + ", ".join(positives) + ".")
        if negatives:
            descriptions.append("Current concerns include " + ", ".join(negatives) + ".")

        confidence = "high confidence" if tier == "Hot" and eligibility == "Eligible" else (
            "moderate confidence" if tier in ["Warm", "Monitor"] else "lower confidence"
        )
        descriptions.append(f"Overall outreach readiness is at {confidence}, grounded in the available profile, engagement, and compliance signals.")

        return " ".join(descriptions)

    def _build_where_signal_summary(self, row: pd.Series, campaign_history: pd.DataFrame) -> str:
        if campaign_history.empty:
            return "No campaign history is available; the record is currently qualified more by profile than recent buyer activity."

        type_counts = {}
        if "campaign_type" in campaign_history.columns:
            type_counts = campaign_history["campaign_type"].fillna("Unknown").value_counts().to_dict()

        event_count = int(type_counts.get("Event", 0))
        webinar_count = int(type_counts.get("Webinar", 0))
        content_count = int(type_counts.get("Content Syndication", 0))
        email_count = int(type_counts.get("Email", 0))

        recent_date = None
        if "response_date" in campaign_history.columns:
            recent_date = campaign_history["response_date"].max()

        active_signals = []
        if webinar_count:
            active_signals.append(f"webinar attendance ({webinar_count})")
        if event_count:
            active_signals.append(f"event participation ({event_count})")
        if content_count:
            active_signals.append(f"content engagement ({content_count})")
        if email_count:
            active_signals.append(f"email engagement ({email_count})")

        if not active_signals:
            return (
                "The engagement history is currently dominated by passive marketing touches. "
                "No substantive buyer-initiated webinar, event, content, or form interaction was observed in the evaluation window."
            )

        recency_phrase = "No dated activity is available"
        if pd.notnull(recent_date):
            recency_phrase = f"The latest known interaction occurred on {recent_date.date()}."

        signal_phrase = ", ".join(active_signals)
        if len(active_signals) == 1:
            signal_phrase = active_signals[0]

        return (
            f"The record shows active engagement through {signal_phrase}. {recency_phrase} "
            f"These signals support the current prioritization and indicate buyer interest rather than purely passive outreach." 
        ).strip()

    def _build_recommended_action(self, row: pd.Series) -> str:
        tier = str(row.get("priority_tier", "Cold"))
        eligibility = str(row.get("eligibility_status", "Eligible"))
        blocked = bool(row.get("structural_block_flag", False)) or eligibility == "Blocked"

        if blocked:
            return "Do not contact this prospect now; retain the intelligence for account planning, qualification, and future outreach windows."
        if tier == "Hot" and eligibility == "Eligible":
            return "Prioritize outreach in the next 24-48 hours and personalize the message using the recent engagement signals."
        if tier == "Hot" and eligibility == "Restricted":
            return "This prospect has strong buying signals, but outreach restrictions apply. Resolve compliance issues before planning contact."
        if tier == "Warm" and eligibility == "Eligible":
            return "Add this prospect to a targeted outbound sequence and monitor fresh activity for escalation signals."
        if tier == "Monitor":
            return "Keep the prospect in nurture and watch for a new engagement trigger before applying direct BDR effort."
        if tier == "Cold":
            return "Hold off on active outreach; revisit once stronger engagement or profile fit emerges."
        return "Keep under observation and re-evaluate when new evidence arrives."

    def _build_talking_points(
        self,
        row: pd.Series,
        master_info: Dict[str, Any],
        campaign_history: pd.DataFrame
    ) -> str:
        points: List[str] = []
        first_name = master_info.get("first_name") or "the prospect"
        title = master_info.get("title")

        if title and title != title:  # handle nan
            title = None

        if title:
            points.append(f"Reference the prospect's role as {title}.")
        elif first_name:
            points.append(f"Open with {first_name}'s recent engagement patterns.")

        content_references: List[str] = []
        email_references: List[str] = []
        event_references: List[str] = []
        webinar_references: List[str] = []

        if not campaign_history.empty:
            if "campaign_name" in campaign_history.columns:
                for _, cm in campaign_history.iterrows():
                    campaign_name = str(cm.get("campaign_name", "")).strip()
                    campaign_type = str(cm.get("campaign_type", "")).strip()
                    responded = bool(cm.get("is_responded", False))
                    if campaign_type == "Webinar":
                        webinar_references.append(campaign_name or "webinar activity")
                    elif campaign_type == "Event":
                        event_references.append(campaign_name or "event activity")
                    elif campaign_type in ["Content Syndication", "Content"]:
                        content_references.append(campaign_name or "content engagement")
                    elif campaign_type == "Email":
                        email_references.append(campaign_name or "email outreach")

        if webinar_references:
            points.append(f"Reference webinar participation such as {webinar_references[0]}.")
        if event_references:
            points.append(f"Reference event attendance such as {event_references[0]}.")
        if content_references:
            points.append(f"Highlight interest in content like {content_references[0]}.")
        if email_references and not content_references and not event_references and not webinar_references:
            points.append("Note that recent email campaigns were delivered with limited response, so the next step should be consultative.")

        if float(row.get("automation_ratio", 0.0)) > 0.70:
            points.append("Be mindful of automation inflation when interpreting engagement volume.")
        if bool(row.get("missing_title_flag", False)):
            points.append("Confirm the prospect's title to improve message relevance.")

        if not points:
            points.append("Focus on the recent signals and next best step.")

        # Return a concise set of talking points, up to 4 sentences.
        return " ".join(points[:4])

    def _build_why_now_summary(self, row: pd.Series, campaign_history: pd.DataFrame) -> str:
        events: List[str] = []
        recent_date = None
        if not campaign_history.empty and "response_date" in campaign_history.columns:
            recent_date = campaign_history["response_date"].max()

        has_recent_response = False
        has_webinar = False
        has_event = False
        has_content = False
        passive_only = False

        if not campaign_history.empty:
            recent_responses = campaign_history[campaign_history["is_responded"] == True]
            has_recent_response = not recent_responses.empty and pd.notnull(recent_date)
            has_webinar = any(campaign_history["campaign_type"].fillna("") == "Webinar")
            has_event = any(campaign_history["campaign_type"].fillna("") == "Event")
            has_content = any(campaign_history["campaign_type"].fillna("").isin(["Content Syndication", "Content"]))
            passive_only = not has_recent_response and bool(campaign_history["campaign_type"].fillna("Email").eq("Email").all())

        if has_recent_response and recent_date is not None and pd.notnull(recent_date):
            days_ago = (pd.Timestamp.now().normalize() - recent_date.normalize()).days
            if days_ago <= 14:
                events.append("Recent interaction within the last two weeks.")
            elif days_ago <= 30:
                events.append("Interaction occurred within the past 30 days.")

        if has_webinar and recent_date is not None and pd.notnull(recent_date):
            recent_webinars = campaign_history[campaign_history["campaign_type"].fillna("") == "Webinar"]
            if not recent_webinars.empty:
                valid_webinars = recent_webinars[pd.notnull(recent_webinars["response_date"])]
                latest_webinar = (
                    valid_webinars.loc[valid_webinars["response_date"].idxmax()]
                    if not valid_webinars.empty
                    else recent_webinars.iloc[0]
                )
                webinar_name = str(latest_webinar.get("campaign_name", "webinar")).strip()
                events.append(f"Attended {webinar_name} recently.")

        if has_event and recent_date is not None and pd.notnull(recent_date):
            recent_events = campaign_history[campaign_history["campaign_type"].fillna("") == "Event"]
            if not recent_events.empty:
                valid_events = recent_events[pd.notnull(recent_events["response_date"])]
                latest_event = (
                    valid_events.loc[valid_events["response_date"].idxmax()]
                    if not valid_events.empty
                    else recent_events.iloc[0]
                )
                event_name = str(latest_event.get("campaign_name", "an event")).strip()
                events.append(f"Attended {event_name} recently.")

        if has_content:
            recent_content = campaign_history[campaign_history["campaign_type"].fillna("").isin(["Content Syndication", "Content"])]
            if not recent_content.empty:
                if "response_date" in recent_content.columns:
                    valid_content = recent_content[pd.notnull(recent_content["response_date"])]
                    latest_content = (
                        valid_content.loc[valid_content["response_date"].idxmax()]
                        if not valid_content.empty
                        else recent_content.iloc[0]
                    )
                else:
                    latest_content = recent_content.iloc[0]
                content_name = str(latest_content.get("campaign_name", "content asset")).strip()
                events.append(f"Downloaded or engaged with content such as {content_name}.")

        if bool(row.get("engagement_burst_flag", False)):
            events.append("Second campaign response within 14 days.")

        if float(row.get("buying_committee_strength", 0.0)) >= 50.0:
            events.append("Account buying committee activity increased.")

        automation_ratio = float(row.get("automation_ratio", 0.0))
        if automation_ratio > 0.70:
            events.append("Automation inflation detected (>70% passive sends).")

        if not has_recent_response:
            events.append("No validated engagement during the last 90 days.")
        if not has_webinar and not has_event and not has_content:
            events.append("No webinar, event, or content response activity.")
        if passive_only:
            events.append("Current activity consists primarily of passive marketing sends.")

        if not events:
            return "WHY NOW?\n↑ No material changes detected recently. Current prioritization is driven by historical profile and engagement signals."

        unique_events = []
        for event in events:
            if event not in unique_events:
                unique_events.append(event)
        events = unique_events[:5]

        if not has_recent_response and automation_ratio <= 0.70:
            events.append("Readiness remains unchanged due to lack of meaningful buying signals.")
        elif has_recent_response:
            events.append("Readiness is elevated based on recent buyer activity.")

        return "\n".join(["WHY NOW?", *[f"↑ {event}" for event in events]])

    def _build_risk_note(self, row: pd.Series) -> str:
        issues: List[str] = []
        if bool(row.get("missing_title_flag", False)):
            issues.append("Missing title reduces persona confidence.")
        if float(row.get("automation_ratio", 0.0)) > 0.70:
            issues.append("Automation inflation detected (>70% passive marketing touches).")
        if bool(row.get("duplicate_email_flag", False)):
            issues.append("Duplicate email address reduces contact reliability.")
        if bool(row.get("shared_mailbox_flag", False)):
            issues.append("Shared mailbox address raises deliverability uncertainty.")
        if bool(row.get("bounced_or_left_company_flag", False)):
            issues.append("Contact appears bounced or departed, which increases risk.")

        compliance_restriction = str(row.get("eligibility_status", "Eligible")) == "Blocked" or bool(row.get("structural_block_flag", False))
        compliance_line = "No compliance restrictions currently present." if not compliance_restriction else "Compliance or structural outreach restrictions are present."

        if not issues and not compliance_restriction:
            return "No material data quality or compliance risks present."

        severity = "Moderate" if len(issues) <= 2 else "Elevated"
        header = f"{severity} Data Quality Risk"
        return "\n".join([header, *issues, compliance_line])

    def _split_reason_text(self, reason_text: str) -> List[str]:
        if not isinstance(reason_text, str):
            return []
        normalized = reason_text.strip()
        if not normalized or normalized == "None":
            return []
        return [part.strip() for part in normalized.split(",") if part.strip()]

    def _print_validation_report(self, df: pd.DataFrame):
        record_count = len(df)
        action_counts = df["recommended_action"].value_counts().to_dict()
        risk_counts = df["risk_note"].str.contains("Risk flags detected").sum()

        print(f"[INFO] Generated agentic recommendations for {record_count} master records.")
        print(f"[INFO] Recommended action distribution: {json.dumps(action_counts)}")
        print(f"[INFO] Records with risk notes: {risk_counts}")
