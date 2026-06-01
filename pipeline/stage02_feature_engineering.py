"""
Stage 02: Feature Engineering Pipeline Stage.

This module processes the resolved Master Persons and calculates behavioral, 
temporal, profile-fit, account-level, and data-quality features for every unique 
master_person_id. It incorporates three advanced business layers:
1. Risk Layer: risk_score and eligibility_status routing.
2. Engagement Quality Layer: engagement_quality_score (Event > Webinar > Content > Email).
3. Buying Committee Layer: buying_committee_strength based on engaged account contacts.

Outputs:
- data/processed/person_features.csv

Author: Senior Data Engineer
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple, Any


class SalesforceFeatureEngineer:
    """Engineers rich behavioral features and prioritization layers for Master Persons."""

    def __init__(self, master_persons_path: str = "data/processed/master_persons.csv",
                 resolver_map_path: str = "data/processed/entity_resolution_map.csv",
                 campaign_members_path: str = "data/raw/campaign_members_data.csv",
                 accounts_path: str = "data/raw/accounts_data.csv"):
        self.master_persons_path = master_persons_path
        self.resolver_map_path = resolver_map_path
        self.campaign_members_path = campaign_members_path
        self.accounts_path = accounts_path

        # Baseline date for recency calculations (evaluating as of May 30, 2026)
        self.baseline_date = pd.to_datetime("2026-05-30 23:59:59")

    def engineer_features(self) -> pd.DataFrame:
        """Processes all raw and resolved files to output the comprehensive features dataset."""
        # 1. Load Sourcing Files
        for path in [self.master_persons_path, self.resolver_map_path, self.campaign_members_path, self.accounts_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"[ERROR] Required pipeline file not found at: {path}")

        master_df = pd.read_csv(self.master_persons_path)
        map_df = pd.read_csv(self.resolver_map_path)
        cm_df = pd.read_csv(self.campaign_members_path)
        accounts_df = pd.read_csv(self.accounts_path)

        print(f"[INFO] Processing features for {len(master_df)} master persons...")

        # 2. Maps raw entity ID (Lead or Contact) to master_person_id
        map_dict = map_df.set_index("raw_entity_id")["master_person_id"].to_dict()

        # Map campaign member records to master_person_id
        cm_df["master_person_id"] = cm_df["entity_id"].map(map_dict)
        # Keep only memberships that successfully resolved to a master person
        cm_df = cm_df[cm_df["master_person_id"].notnull()].copy()

        # Parse CampaignMember dates
        cm_df["parsed_response_date"] = pd.to_datetime(cm_df["response_date"], errors="coerce")
        # Calculate days since response relative to baseline
        cm_df["days_since_response"] = (self.baseline_date - cm_df["parsed_response_date"]).dt.total_seconds() / (24 * 3600)
        # Bounded at 0.0 for any future dates
        cm_df.loc[cm_df["days_since_response"] < 0, "days_since_response"] = 0.0

        # pre-calculate automated campaign send indicators (DQ-8 Sent with no responses)
        cm_df["_is_automated_touch"] = (
            cm_df["campaign_type"].isin(["Email", "Advertisement", "Telemarketing"]) & 
            (~cm_df["is_responded"].astype(bool))
        )

        # ----------------------------------------------------
        # Part A: Pre-computing CampaignMember Features
        # ----------------------------------------------------
        person_cm_stats: Dict[str, Dict[str, Any]] = {}
        
        # Group CampaignMembers by master_person_id
        cm_groups = cm_df.groupby("master_person_id")
        for mpid, group in cm_groups:
            tot_memberships = len(group)
            
            # Engagement metrics
            responses_df = group[group["is_responded"].astype(bool)]
            total_responses = len(responses_df)
            real_engagement_count = total_responses
            
            automated_touch_count = group["_is_automated_touch"].sum()
            auto_ratio = automated_touch_count / tot_memberships if tot_memberships > 0 else 0.0

            # Channel response counts
            webinar_attended = responses_df[responses_df["campaign_type"] == "Webinar"].shape[0]
            event_attended = responses_df[responses_df["campaign_type"] == "Event"].shape[0]
            content_response = responses_df[responses_df["campaign_type"] == "Content Syndication"].shape[0]
            email_response = responses_df[responses_df["campaign_type"] == "Email"].shape[0]

            # Recency metrics
            last_resp_date = responses_df["response_date"].max() if total_responses > 0 else None
            min_days_since_resp = responses_df["days_since_response"].min() if total_responses > 0 else 180.0

            responses_7d = responses_df[responses_df["days_since_response"] <= 7].shape[0]
            responses_14d = responses_df[responses_df["days_since_response"] <= 14].shape[0]
            responses_30d = responses_df[responses_df["days_since_response"] <= 30].shape[0]
            responses_90d = responses_df[responses_df["days_since_response"] <= 90].shape[0]

            # Velocity metrics
            responses_31_60_days = responses_df[
                (responses_df["days_since_response"] > 30) & 
                (responses_df["days_since_response"] <= 60)
            ].shape[0]
            velocity_30d = responses_30d / max(1, responses_31_60_days)

            engagement_burst = responses_14d >= 3
            sustained_engagement = (responses_30d >= 1) and (responses_90d >= 3)

            # Store computed metrics
            person_cm_stats[mpid] = {
                "total_campaign_memberships": tot_memberships,
                "total_responses": total_responses,
                "real_engagement_count": real_engagement_count,
                "automated_touch_count": automated_touch_count,
                "automation_ratio": auto_ratio,
                "webinar_attended_count": webinar_attended,
                "event_attended_count": event_attended,
                "content_response_count": content_response,
                "email_response_count": email_response,
                "last_response_date": last_resp_date if pd.notnull(last_resp_date) else np.nan,
                "days_since_last_response": min_days_since_resp,
                "responses_7d": responses_7d,
                "responses_14d": responses_14d,
                "responses_30d": responses_30d,
                "responses_90d": responses_90d,
                "response_velocity_30d": velocity_30d,
                "engagement_burst_flag": engagement_burst,
                "sustained_engagement_flag": sustained_engagement
            }

        # ----------------------------------------------------
        # Part B: Pre-computing Account Context and Aggregates
        # ----------------------------------------------------
        acc_metadata = accounts_df.set_index("account_id").to_dict(orient="index")

        # Map master person to their total response count for account aggregation
        person_response_counts: Dict[str, int] = {}
        for mpid in master_df["master_person_id"]:
            person_response_counts[mpid] = person_cm_stats.get(mpid, {}).get("total_responses", 0)

        # Pre-compute account aggregate metrics across all master persons
        acc_groups = master_df.groupby("account_id")
        account_aggregates: Dict[str, Dict[str, Any]] = {}

        for acc_id, group in acc_groups:
            if pd.isnull(acc_id) or str(acc_id).strip() == "":
                continue

            person_ids = group["master_person_id"].tolist()
            
            # Account response count = sum of responses of all persons on this account
            tot_acc_responses = sum(person_response_counts.get(pid, 0) for pid in person_ids)
            
            # Engaged contacts count = count of persons with responses > 0 on this account
            engaged_cnts = sum(1 for pid in person_ids if person_response_counts.get(pid, 0) > 0)

            # Surges calculation (total responses on account in last 14 days)
            recent_acc_responses = 0
            surging_people_count = set()
            for pid in person_ids:
                stats = person_cm_stats.get(pid, {})
                if stats:
                    recent_acc_responses += stats.get("responses_14d", 0)
                    if stats.get("responses_14d", 0) > 0:
                        surging_people_count.add(pid)

            # Account Surge Flag is True if explicitly flagged in accounts,
            # OR if account-level responses in last 14 days >= 3 across at least 2 unique master persons
            raw_surge_flag = acc_metadata.get(acc_id, {}).get("intent_surge_flag", False)
            account_surge = bool(
                raw_surge_flag or 
                (recent_acc_responses >= 3 and len(surging_people_count) >= 2)
            )

            account_aggregates[acc_id] = {
                "account_response_count": tot_acc_responses,
                "engaged_contacts_on_account": engaged_cnts,
                "account_surge_flag": account_surge
            }

        # ----------------------------------------------------
        # Part C: Build Final Feature Database for Master Persons
        # ----------------------------------------------------
        features: List[Dict[str, Any]] = []

        # Load Leads and Contacts for bounce/left/opt-out status checking
        leads_df = pd.read_csv("data/raw/leads_data.csv")
        contacts_df = pd.read_csv("data/raw/contacts_data.csv")
        
        leads_opt_bounced = leads_df.set_index("lead_id")[["has_opted_out", "email_bounced"]].to_dict(orient="index")
        contacts_opt_left = contacts_df.set_index("contact_id")[["has_opted_out", "no_longer_with_company"]].to_dict(orient="index")

        for _, row in master_df.iterrows():
            mpid = row["master_person_id"]
            acc_id = row["account_id"]
            job_level = str(row["job_level"]).strip()
            job_persona = str(row["job_persona"]).strip()

            # Retrieve CampaignMember features (default if no history)
            cm_stats = person_cm_stats.get(mpid, {
                "total_campaign_memberships": 0,
                "total_responses": 0,
                "real_engagement_count": 0,
                "automated_touch_count": 0,
                "automation_ratio": 0.0,
                "webinar_attended_count": 0,
                "event_attended_count": 0,
                "content_response_count": 0,
                "email_response_count": 0,
                "last_response_date": np.nan,
                "days_since_last_response": 180.0,
                "responses_7d": 0,
                "responses_14d": 0,
                "responses_30d": 0,
                "responses_90d": 0,
                "response_velocity_30d": 0.0,
                "engagement_burst_flag": False,
                "sustained_engagement_flag": False
            })

            # Retrieve Account level features
            is_icp = False
            is_named = False
            intent_score = 0.0
            do_not_contact = False
            
            acc_resp_count = 0
            acc_engaged_contacts = 0
            acc_surge = False

            if pd.notnull(acc_id) and str(acc_id).strip() != "":
                acc_id_str = str(acc_id).strip()
                acc_info = acc_metadata.get(acc_id_str, {})
                
                is_icp = acc_info.get("is_icp_qualified", False)
                is_named = acc_info.get("is_named_account", False)
                intent_score = float(acc_info.get("intent_score", 0.0))
                do_not_contact = acc_info.get("do_not_contact", False)

                acc_aggs = account_aggregates.get(acc_id_str, {})
                acc_resp_count = acc_aggs.get("account_response_count", 0)
                acc_engaged_contacts = acc_aggs.get("engaged_contacts_on_account", 0)
                acc_surge = acc_aggs.get("account_surge_flag", False)

            # ----------------------------------------------------
            # 1. Profile Fit Calculations
            # ----------------------------------------------------
            # Seniority Score mapping (0-100)
            seniority_mapping = {
                "C-Suite": 100,
                "VP": 85,
                "Director": 70,
                "Manager": 50,
                "Individual Contributor": 25
            }
            seniority_score = seniority_mapping.get(job_level, 0)

            # Persona Score mapping (0-100)
            persona_mapping = {
                "Security Executive": 100,
                "Security Leadership": 85,
                "Security Management": 75,
                "Security Operations": 60
            }
            persona_score = persona_mapping.get(job_persona, 0)

            # Profile Completeness score (percentage of 7 key fields populated)
            key_fields = ["first_name", "last_name", "email", "title", "job_persona", "job_level", "account_id"]
            populated_count = sum(1 for f in key_fields if pd.notnull(row.get(f)) and str(row.get(f)).strip() != "")
            profile_completeness = (populated_count / len(key_fields)) * 100.0

            # Non-Prospect Flag (competitors, vendor noise, etc.)
            is_non_prospect = job_persona == "Non-Prospect" or str(row.get("normalized_email")).endswith("competitorsec.com")
            
            # ----------------------------------------------------
            # 2. Data Quality Flags Checks
            # ----------------------------------------------------
            missing_title = pd.isnull(row["title"]) or str(row["title"]).strip() == ""
            missing_account = pd.isnull(row["account_id"]) or str(row["account_id"]).strip() == ""

            # Check opt-out and bounce status from preferred entities
            opted_out = False
            bounced = False
            left_company = False

            pref_id = row["preferred_entity_id"]
            if row["preferred_entity_type"] == "Contact":
                c_info = contacts_opt_left.get(pref_id, {})
                opted_out = c_info.get("has_opted_out", False)
                left_company = c_info.get("no_longer_with_company", False)
            else:
                l_info = leads_opt_bounced.get(pref_id, {})
                opted_out = l_info.get("has_opted_out", False)
                bounced = l_info.get("email_bounced", False)

            bounced_or_left = bool(bounced or left_company)

            # Structural Block Flag (hard outreach block)
            structural_block = bool(
                do_not_contact or 
                opted_out or 
                bounced_or_left or 
                is_non_prospect
            )

            # ----------------------------------------------------
            # 3. Enhancement Layers (Risk, Quality, Committee)
            # ----------------------------------------------------
            # Risk Layer Calculation
            risk_score = 0
            if opted_out or bounced_or_left or do_not_contact:
                risk_score = 100
            else:
                if row["shared_mailbox_flag"] is True or str(row["shared_mailbox_flag"]).strip().lower() == "true":
                    risk_score += 40
                if row["duplicate_email_flag"] is True or str(row["duplicate_email_flag"]).strip().lower() == "true":
                    risk_score += 30
                if missing_title:
                    risk_score += 15
                if missing_account:
                    risk_score += 15
                risk_score = min(risk_score, 100)

            # Eligibility Status
            if structural_block:
                eligibility_status = "Blocked"
            elif risk_score >= 40:
                eligibility_status = "Restricted"
            else:
                eligibility_status = "Eligible"

            # Engagement Quality score (Event (100) > Webinar (70) > Content (50) > Email (20))
            tot_resp = cm_stats["total_responses"]
            raw_quality_sum = (
                (cm_stats["event_attended_count"] * 100) + 
                (cm_stats["webinar_attended_count"] * 70) + 
                (cm_stats["content_response_count"] * 50) + 
                (cm_stats["email_response_count"] * 20)
            )
            engagement_quality = float(raw_quality_sum / max(1, tot_resp)) if tot_resp > 0 else 0.0

            # Buying Committee Layer: buying_committee_strength
            # Estimate account's buying committee size dynamically based on Named Strategic tier
            buying_committee_size = 6 if is_named else 3
            committee_strength = (acc_engaged_contacts / buying_committee_size) * 100.0 if acc_id else 0.0
            committee_strength = float(min(100.0, committee_strength))

            # Compile all features
            features.append({
                "master_person_id": mpid,
                
                # 1. Engagement features
                "total_campaign_memberships": cm_stats["total_campaign_memberships"],
                "total_responses": tot_resp,
                "real_engagement_count": cm_stats["real_engagement_count"],
                "automated_touch_count": cm_stats["automated_touch_count"],
                "automation_ratio": cm_stats["automation_ratio"],
                "webinar_attended_count": cm_stats["webinar_attended_count"],
                "event_attended_count": cm_stats["event_attended_count"],
                "content_response_count": cm_stats["content_response_count"],
                "email_response_count": cm_stats["email_response_count"],
                
                # 2. Recency features
                "last_response_date": cm_stats["last_response_date"],
                "days_since_last_response": cm_stats["days_since_last_response"],
                "responses_7d": cm_stats["responses_7d"],
                "responses_14d": cm_stats["responses_14d"],
                "responses_30d": cm_stats["responses_30d"],
                "responses_90d": cm_stats["responses_90d"],
                
                # 3. Velocity features
                "response_velocity_30d": cm_stats["response_velocity_30d"],
                "engagement_burst_flag": cm_stats["engagement_burst_flag"],
                "sustained_engagement_flag": cm_stats["sustained_engagement_flag"],
                
                # 4. Profile features
                "seniority_score": seniority_score,
                "persona_score": persona_score,
                "profile_completeness_score": profile_completeness,
                "non_prospect_flag": is_non_prospect,
                
                # 5. Account features
                "account_id": acc_id if pd.notnull(acc_id) else np.nan,
                "is_icp_qualified": is_icp,
                "is_named_account": is_named,
                "intent_score": intent_score,
                "do_not_contact": do_not_contact,
                "account_response_count": acc_resp_count,
                "engaged_contacts_on_account": acc_engaged_contacts,
                "account_surge_flag": acc_surge,
                
                # 6. Data Quality features
                "duplicate_email_flag": row["duplicate_email_flag"],
                "shared_mailbox_flag": row["shared_mailbox_flag"],
                "broken_conversion_link_flag": row["broken_conversion_link_flag"],
                "missing_title_flag": missing_title,
                "missing_account_flag": missing_account,
                "opted_out_flag": opted_out,
                "bounced_or_left_company_flag": bounced_or_left,
                "structural_block_flag": structural_block,

                # 7. Enhancement Layers
                "risk_score": risk_score,
                "eligibility_status": eligibility_status,
                "engagement_quality_score": engagement_quality,
                "buying_committee_strength": committee_strength
            })

        person_features_df = pd.DataFrame(features)

        # Print stage 02 validation report
        self._print_validation_report(person_features_df)

        return person_features_df

    def _print_validation_report(self, df: pd.DataFrame):
        """Prints a detailed statistical validation report for engineered features."""
        print("=" * 70)
        print("                 STAGE 02: FEATURE ENGINEERING REPORT             ")
        print("=" * 70)
        print(f"Total Feature Rows Built:           {len(df)}")
        print(f"Average memberships Per Person:     {df['total_campaign_memberships'].mean():.2f}")
        print(f"Average Responses Per Person:       {df['total_responses'].mean():.2f}")
        print("-" * 70)
        print("Outreach Eligibility Telemetry:")
        elig_counts = df["eligibility_status"].value_counts()
        for status, count in elig_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {status:<22}: Count = {count:4d} ({pct:5.1f}%)")
        print("-" * 70)
        print("Data Quality completeness & Obstacles:")
        print(f"  Missing Title Flag Rate:          {df['missing_title_flag'].mean()*100:5.1f}%")
        print(f"  Missing Account Flag Rate:        {df['missing_account_flag'].mean()*100:5.1f}%")
        print(f"  Structural Hard Block Rate:       {df['structural_block_flag'].mean()*100:5.1f}%")
        print("-" * 70)
        print("Buying Committee & Quality Layers:")
        named_df = df[df["is_named_account"] == True]
        std_df = df[df["is_named_account"] == False]
        print(f"  Named Accounts Avg Strength:      {named_df['buying_committee_strength'].mean():.2f}%")
        print(f"  Standard Accounts Avg Strength:   {std_df['buying_committee_strength'].mean():.2f}%")
        print(f"  Average Engagement Quality:       {df['engagement_quality_score'].mean():.2f} pts")
        print("=" * 70)


def main():
    """Execution entry point."""
    resolver_map = "data/processed/entity_resolution_map.csv"
    master_persons = "data/processed/master_persons.csv"
    campaign_members = "data/raw/campaign_members_data.csv"
    accounts = "data/raw/accounts_data.csv"
    output_file = "data/processed/person_features.csv"

    # Instantiate feature engineer and execute
    engineer = SalesforceFeatureEngineer(
        master_persons_path=master_persons,
        resolver_map_path=resolver_map,
        campaign_members_path=campaign_members,
        accounts_path=accounts
    )
    features_df = engineer.engineer_features()

    # Save output features
    features_df.to_csv(output_file, index=False)
    print(f"\n[SUCCESS] Exported engineered features dataset to: {output_file}\n")


if __name__ == "__main__":
    main()
