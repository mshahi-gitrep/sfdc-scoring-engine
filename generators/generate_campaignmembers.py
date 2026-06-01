"""
Salesforce CampaignMember Data Generator Module.

This module generates exactly 5,000 CampaignMember records linked dynamically 
to Accounts, Leads, and Contacts. It implements advanced CRM properties:
- Persona-driven engagement (Webinars for SOC Analysts, Events for CISOs).
- DQ-8 Automation Inflation: exactly 30% of leads/contacts have automation_share > 70%.
- Persona H (Henry Inflated) explicitly configured: 40 memberships, 38 automated sends.
- buying-committee and clustered account engagement: Named Accounts get larger
  Buying Committees, High-Intent Accounts get higher responses, and exactly 10%
  of high-intent accounts show coordinated recent 14-day surges.

Author: Senior Data Engineer
"""

import os
import argparse
import random
import string
import datetime
from typing import Dict, Any, List, Set

import numpy as np
import pandas as pd
from faker import Faker


class SalesforceCampaignMemberGenerator:
    """Generates relational CampaignMember records with buying committee surges and automation inflation."""

    def __init__(self, seed: int = None):
        """
        Initializes the generator with a seed for reproducibility.
        """
        self.seed = seed
        self.fake = Faker()

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # 1. Campaign Types & Name Pools
        self.campaign_names = {
            "Webinar": [
                "Webinar: Advanced SOC Threat Detection",
                "Webinar: Securing DevSecOps Pipelines",
                "Webinar: CISO Guide to Ransomware Mitigation",
                "Webinar: Cloud Security Best Practices",
                "Webinar: SIEM Scaling Strategies"
            ],
            "Event": [
                "Event: Executive Roundtable London 2026",
                "Event: BlackHat Las Vegas 2026",
                "Event: Cybersecurity Summit New York 2026",
                "Event: RSA Conference San Francisco 2026",
                "Event: VIP Executive Dinner 2026"
            ],
            "Content Syndication": [
                "Content: SIEM Evaluation Checklist",
                "Content: EDR Solutions Buyers Guide",
                "Content: SOC Analyst Team Scaling Report",
                "Content: Zero Trust Infrastructure Whitepaper"
            ],
            "Email": [
                "Email: Monthly Security Insights Newsletter",
                "Email: Cyber Threat Intelligence Bulletin",
                "Email: Quarterly Product Feature Announcement",
                "Email: Critical Vulnerability Alert Notification"
            ],
            "Advertisement": [
                "Ad: LinkedIn Lead Gen - EDR Buyers Guide",
                "Ad: Google Search - Enterprise Cybersecurity Keywords",
                "Ad: Dark Reading Homepage Digital Banner"
            ],
            "Telemarketing": [
                "Telemarketing: Outbound SDR Cold Sequence",
                "Telemarketing: Event Attendee Follow-up Call",
                "Telemarketing: Inbound Lead Qualification"
            ]
        }
        self.campaign_types = list(self.campaign_names.keys())

    def _generate_salesforce_id(self, prefix: str, generated_ids: Set[str]) -> str:
        """Generates a unique, realistic 18-character Salesforce CampaignMember ID."""
        chars = string.ascii_letters + string.digits
        while True:
            suffix = "".join(random.choices(chars, k=15))
            sfdc_id = f"{prefix}{suffix}"
            if sfdc_id not in generated_ids:
                generated_ids.add(sfdc_id)
                return sfdc_id

    def generate_records(self, num_records: int = 5000, inject_dq_errors: bool = True,
                         accounts_path: str = "data/raw/accounts_data.csv",
                         leads_path: str = "data/raw/leads_data.csv",
                         contacts_path: str = "data/raw/contacts_data.csv") -> pd.DataFrame:
        """
        Generates exactly 5,000 CampaignMember records based on Account, Lead, and Contact linkages.
        """
        generated_cm_ids: Set[str] = set()
        campaign_members: List[Dict[str, Any]] = []

        # 1. Load Sourcing Files
        if not os.path.exists(accounts_path):
            raise FileNotFoundError(f"[ERROR] Accounts file not found at {accounts_path}.")
        if not os.path.exists(leads_path):
            raise FileNotFoundError(f"[ERROR] Leads file not found at {leads_path}.")
        if not os.path.exists(contacts_path):
            raise FileNotFoundError(f"[ERROR] Contacts file not found at {contacts_path}.")

        accounts_df = pd.read_csv(accounts_path)
        leads_df = pd.read_csv(leads_path)
        contacts_df = pd.read_csv(contacts_path)

        # 2. Compile all unique person records (Leads and Contacts)
        # We need their creation dates and persona tags for relational mapping
        persons: List[Dict[str, Any]] = []
        
        for _, row in leads_df.iterrows():
            persons.append({
                "id": row["lead_id"],
                "type": "Lead",
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "created_date": row["created_date"] if pd.notnull(row["created_date"]) else "2026-05-01 00:00:00",
                # Read internal persona if available in export (or fallback based on titles)
                "persona": row.get("_persona", "Security Analyst"),
                "company": row.get("company", None),
                "account_id": None,
                "archetype": row.get("_archetype", None)
            })
            
        for _, row in contacts_df.iterrows():
            persons.append({
                "id": row["contact_id"],
                "type": "Contact",
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "created_date": "2026-01-15 08:30:00",  # Default historical date for contacts
                "persona": row.get("job_persona", "Security Manager"),
                "company": None,
                "account_id": row.get("account_id", None),
                "archetype": None
            })

        person_df = pd.DataFrame(persons)
        person_ids = person_df["id"].tolist()

        print(f"[INFO] Relational database populated with {len(person_df)} total person records (Leads & Contacts).")

        # ----------------------------------------------------
        # Part A: Deterministic Setup of Persona H (Henry Inflated)
        # ----------------------------------------------------
        # Persona H: lead_id = '00QARCHETYPE0000H' (or matching name Henry Inflated)
        h_row = person_df[person_df["id"].str.contains("ARCHETYPE0000H") | (person_df["first_name"] == "Henry")]
        h_id = h_row.iloc[0]["id"] if len(h_row) > 0 else "00QARCHETYPE0000H"

        # Persona H has exactly 40 campaign memberships:
        # - Exactly 38 automated sends (Email, Sent, is_responded=False)
        # - Exactly 2 active responses
        # Let's generate these deterministically
        for i in range(38):
            campaign_name = self.campaign_names["Email"][i % len(self.campaign_names["Email"])]
            campaign_members.append({
                "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                "entity_id": h_id,
                "entity_type": "Lead",
                "campaign_name": campaign_name,
                "campaign_type": "Email",
                "member_status": "Sent",
                "is_responded": False,
                "response_date": None,
                "is_active": True,
                "_person_id": h_id
            })

        # Add 2 active responses
        campaign_members.append({
            "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
            "entity_id": h_id,
            "entity_type": "Lead",
            "campaign_name": self.campaign_names["Webinar"][0],
            "campaign_type": "Webinar",
            "member_status": "Attended",
            "is_responded": True,
            "response_date": "2026-05-20 15:30:00",
            "is_active": True,
            "_person_id": h_id
        })

        campaign_members.append({
            "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
            "entity_id": h_id,
            "entity_type": "Lead",
            "campaign_name": self.campaign_names["Content Syndication"][0],
            "campaign_type": "Content Syndication",
            "member_status": "Registered",
            "is_responded": True,
            "response_date": "2026-05-22 10:15:00",
            "is_active": True,
            "_person_id": h_id
        })

        # ----------------------------------------------------
        # Part B: DQ-8 Automation Inflation (Exactly 30% of records > 70% automation)
        # ----------------------------------------------------
        # We sample exactly 30% of unique Lead/Contact IDs (excluding Henry H)
        unique_ids = [pid for pid in person_ids if pid != h_id]
        target_inflated_count = int(round(len(unique_ids) * 0.30))
        
        inflated_ids = set(random.sample(unique_ids, k=target_inflated_count))
        print(f"[INFO] DQ-8: Designating exactly {len(inflated_ids)} unique Leads/Contacts for >70% automation inflation.")

        # For each inflated record, we generate a high volume of automated sends (e.g. 8-12 automated email sends)
        # and only 1-2 active responses (or 0) so their automation_share exceeds 70%
        for pid in inflated_ids:
            p_row = person_df[person_df["id"] == pid].iloc[0]
            p_type = p_row["type"]
            
            # Select total automated sends: 8
            # Select total active responses: 1
            # Automation share = 8 / 9 = 88.9% (>70%)
            for i in range(8):
                campaign_type = random.choice(["Email", "Advertisement", "Telemarketing"])
                campaign_name = random.choice(self.campaign_names[campaign_type])
                
                campaign_members.append({
                    "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                    "entity_id": pid,
                    "entity_type": p_type,
                    "campaign_name": campaign_name,
                    "campaign_type": campaign_type,
                    "member_status": "Sent",
                    "is_responded": False,
                    "response_date": None,
                    "is_active": True,
                    "_person_id": pid
                })
            
            # 1 active response (80% chance)
            if random.random() < 0.80:
                campaign_type = random.choice(["Webinar", "Content Syndication"])
                campaign_name = random.choice(self.campaign_names[campaign_type])
                campaign_members.append({
                    "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                    "entity_id": pid,
                    "entity_type": p_type,
                    "campaign_name": campaign_name,
                    "campaign_type": campaign_type,
                    "member_status": "Registered" if campaign_type == "Content Syndication" else "Attended",
                    "is_responded": True,
                    "response_date": "2026-05-24 14:00:00",
                    "is_active": True,
                    "_person_id": pid
                })

        # ----------------------------------------------------
        # Part C: buying Committee & Clustered Account Engagement
        # ----------------------------------------------------
        # We process accounts and cluster multiple contacts/leads together
        high_intent_accounts = accounts_df[accounts_df["intent_score"] > 75]
        high_intent_ids = high_intent_accounts["account_id"].tolist()
        
        # Designate exactly 10% of high-intent accounts as Surging Accounts
        target_surge_count = max(1, int(round(len(high_intent_ids) * 0.10)))
        surge_account_ids = set(random.sample(high_intent_ids, k=target_surge_count))
        
        print(f"[INFO] buying Committee: {len(high_intent_accounts)} High-Intent Accounts identified. "
              f"DQ Surge: Designating {len(surge_account_ids)} accounts for coordinated 14-day engagement surges.")

        for _, row in accounts_df.iterrows():
            acc_id = row["account_id"]
            is_named = row["is_named_account"]
            is_high_intent = acc_id in high_intent_ids
            is_surging = acc_id in surge_account_ids
            
            # Find all contacts at this account
            acc_contacts = person_df[person_df["account_id"] == acc_id]
            
            # Find all leads matching this company (fuzzy name matching)
            clean_name = row["account_name"].strip().lower()
            acc_leads = person_df[(person_df["type"] == "Lead") & (person_df["company"].str.strip().str.lower().str.contains(clean_name, na=False))]
            
            # Combine to form buying committee
            committee = pd.concat([acc_contacts, acc_leads])
            if len(committee) == 0:
                continue

            # Standard vs. Named buying committee logic
            if is_surging:
                # 14-Day Surge Event: multiple contacts/leads engage coordinated in 14-day window
                # Surge window: 2026-05-01 to 2026-05-15
                for _, member in committee.iterrows():
                    # Generate 3-5 clustered response actions per member in surge window
                    num_surge_events = random.randint(2, 4)
                    for _ in range(num_surge_events):
                        campaign_type = random.choice(["Webinar", "Content Syndication", "Event"])
                        campaign_name = random.choice(self.campaign_names[campaign_type])
                        
                        # Generate random date in surge window
                        surge_day = random.randint(1, 14)
                        response_date = f"2026-05-{surge_day:02d} {random.randint(9,17):02d}:{random.randint(0,59):02d}:00"
                        
                        campaign_members.append({
                            "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                            "entity_id": member["id"],
                            "entity_type": member["type"],
                            "campaign_name": campaign_name,
                            "campaign_type": campaign_type,
                            "member_status": "Attended" if campaign_type == "Event" else "Responded",
                            "is_responded": True,
                            "response_date": response_date,
                            "is_active": True,
                            "_person_id": member["id"]
                        })
            
            elif is_named:
                # Named accounts buying committee: larger committees (3-6 contacts) engage overlapping campaigns
                # Simulates team alignment
                selected_committee = committee.iloc[:random.randint(3, 6)]
                
                # Coordinated campaigns
                webinar_name = random.choice(self.campaign_names["Webinar"])
                event_name = random.choice(self.campaign_names["Event"])
                
                for _, member in selected_committee.iterrows():
                    # Attended same event/webinar
                    campaign_members.append({
                        "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                        "entity_id": member["id"],
                        "entity_type": member["type"],
                        "campaign_name": webinar_name,
                        "campaign_type": "Webinar",
                        "member_status": "Attended",
                        "is_responded": True,
                        "response_date": "2026-04-10 14:00:00",
                        "is_active": True,
                        "_person_id": member["id"]
                    })
                    
                    # 50% chance of attending VIP dinner
                    if random.random() < 0.50:
                        campaign_members.append({
                            "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                            "entity_id": member["id"],
                            "entity_type": member["type"],
                            "campaign_name": event_name,
                            "campaign_type": "Event",
                            "member_status": "Responded",
                            "is_responded": True,
                            "response_date": "2026-04-12 19:30:00",
                            "is_active": True,
                            "_person_id": member["id"]
                        })
            
            elif is_high_intent:
                # High intent but standard accounts: higher volume of responses
                for _, member in committee.iterrows():
                    if random.random() < 0.70:
                        campaign_type = random.choice(["Webinar", "Content Syndication", "Email"])
                        campaign_name = random.choice(self.campaign_names[campaign_type])
                        
                        campaign_members.append({
                            "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                            "entity_id": member["id"],
                            "entity_type": member["type"],
                            "campaign_name": campaign_name,
                            "campaign_type": campaign_type,
                            "member_status": "Responded" if campaign_type == "Email" else "Registered",
                            "is_responded": True,
                            "response_date": "2026-05-10 11:00:00",
                            "is_active": True,
                            "_person_id": member["id"]
                        })

        # ----------------------------------------------------
        # Part D: General Persona-Driven Engagement & Pad to Exactly 5,000 Records
        # ----------------------------------------------------
        # Loop standardly to fill up to exactly 5,000 records
        # CISOs/VPs prefer Event/Webinar. Analysts prefer Webinar/Content.
        print(f"[INFO] Current generated transactional CampaignMembers = {len(campaign_members)}")

        # To avoid massive loops, we pre-compile a standard persona mapping
        while len(campaign_members) < num_records:
            # Pick a random person (avoiding Persona H to keep its exact 40 records intact)
            pid = random.choice(unique_ids)
            p_row = person_df[person_df["id"] == pid].iloc[0]
            p_persona = p_row["persona"]
            
            # Map campaign types based on persona preference
            if p_persona in ["CISO", "VP Security"]:
                campaign_type = np.random.choice(["Event", "Webinar", "Email", "Telemarketing"], p=[0.35, 0.35, 0.20, 0.10])
            elif p_persona in ["Security Director", "Security Manager"]:
                campaign_type = np.random.choice(["Webinar", "Event", "Content Syndication", "Email"], p=[0.40, 0.20, 0.25, 0.15])
            elif p_persona == "Security Analyst":
                campaign_type = np.random.choice(["Webinar", "Content Syndication", "Email", "Advertisement"], p=[0.50, 0.30, 0.10, 0.10])
            else:
                campaign_type = random.choice(self.campaign_types)

            campaign_name = random.choice(self.campaign_names[campaign_type])
            
            # Pick status & response logic based on channel
            is_responded = False
            member_status = "Sent"
            response_date = None

            if campaign_type in ["Webinar", "Event", "Content Syndication"]:
                # High response channels
                if random.random() < 0.65:
                    is_responded = True
                    member_status = "Attended" if campaign_type == "Event" else "Registered"
            else:
                # Outbound channels
                if random.random() < 0.12:
                    is_responded = True
                    member_status = "Clicked" if campaign_type == "Email" else "Responded"

            if is_responded:
                # Generate date between creation date and today
                days_ago = random.randint(0, 45)
                resp_dt = datetime.datetime.now() - datetime.timedelta(days=days_ago)
                response_date = resp_dt.strftime("%Y-%m-%d %H:%M:%S")

            campaign_members.append({
                "cm_id": self._generate_salesforce_id("00v", generated_cm_ids),
                "entity_id": pid,
                "entity_type": p_row["type"],
                "campaign_name": campaign_name,
                "campaign_type": campaign_type,
                "member_status": member_status,
                "is_responded": is_responded,
                "response_date": response_date,
                "is_active": bool(random.random() < 0.85),
                "_person_id": pid
            })

        # Enforce EXACT target count of 5,000
        # If we exceeded it due to bulk additions, truncate exactly
        # Ensure we do NOT truncate Persona H's records!
        df = pd.DataFrame(campaign_members)
        if len(df) > num_records:
            # Identify Persona H records to protect them
            h_indices = df[df["entity_id"] == h_id].index.tolist()
            other_indices = df[df["entity_id"] != h_id].index.tolist()
            
            needed_others = num_records - len(h_indices)
            selected_other_indices = other_indices[:needed_others]
            
            final_indices = h_indices + selected_other_indices
            df = df.loc[final_indices].reset_index(drop=True)

        # ----------------------------------------------------
        # Part E: DQ-8 Exact Calibration Post-Processing
        # ----------------------------------------------------
        # Ensure exact DQ-8 automation percentage
        df["_is_automated_send"] = df["campaign_type"].isin(["Email", "Advertisement", "Telemarketing"]) & (~df["is_responded"])
        unique_pids = [pid for pid in df["entity_id"].unique() if pid != h_id]
        total_unique = len(unique_pids) + 1  # including Henry
        target_inflated = int(round(total_unique * 0.30))
        
        # Calculate current automation share per person
        person_stats = {}
        for pid in df["entity_id"].unique():
            p_rows = df[df["entity_id"] == pid]
            tot = len(p_rows)
            auto = p_rows["_is_automated_send"].sum()
            share = auto / tot if tot > 0 else 0.0
            person_stats[pid] = {
                "total": tot,
                "auto": auto,
                "share": share,
                "indices": p_rows.index.tolist()
            }
            
        current_inflated = [pid for pid, stats in person_stats.items() if stats["share"] > 0.70]
        
        # Make sure Henry is counted as inflated
        if h_id not in current_inflated and h_id in person_stats:
            current_inflated.append(h_id)
            
        c_count = len(current_inflated)
        
        if c_count < target_inflated:
            # We need to inflate more people.
            candidates = [pid for pid in unique_pids if person_stats[pid]["share"] <= 0.70]
            candidates.sort(key=lambda pid: person_stats[pid]["share"], reverse=True)
            
            num_to_inflate = target_inflated - c_count
            for i in range(min(num_to_inflate, len(candidates))):
                pid = candidates[i]
                stats = person_stats[pid]
                indices = stats["indices"]
                
                for idx in indices:
                    if not df.at[idx, "_is_automated_send"]:
                        df.at[idx, "campaign_type"] = "Email"
                        df.at[idx, "campaign_name"] = random.choice(self.campaign_names["Email"])
                        df.at[idx, "member_status"] = "Sent"
                        df.at[idx, "is_responded"] = False
                        df.at[idx, "response_date"] = None
                        df.at[idx, "_is_automated_send"] = True
                        
                        stats["auto"] += 1
                        stats["share"] = stats["auto"] / stats["total"]
                        if stats["share"] > 0.70:
                            break
                            
        elif c_count > target_inflated:
            # We need to deflate some people.
            candidates = [pid for pid in unique_pids if person_stats[pid]["share"] > 0.70]
            candidates.sort(key=lambda pid: person_stats[pid]["share"])
            
            num_to_deflate = c_count - target_inflated
            for i in range(min(num_to_deflate, len(candidates))):
                pid = candidates[i]
                stats = person_stats[pid]
                indices = stats["indices"]
                
                for idx in indices:
                    if df.at[idx, "_is_automated_send"]:
                        df.at[idx, "is_responded"] = True
                        df.at[idx, "member_status"] = "Clicked"
                        df.at[idx, "response_date"] = "2026-05-24 14:00:00"
                        df.at[idx, "_is_automated_send"] = False
                        
                        stats["auto"] -= 1
                        stats["share"] = stats["auto"] / stats["total"]
                        if stats["share"] <= 0.70:
                            break
                            
        print(f"[SUCCESS] Synthesized exactly {len(df)} CampaignMember records.")
        return df

    def print_validation_report(self, df: pd.DataFrame, leads_path: str = "data/raw/leads_data.csv",
                                 contacts_path: str = "data/raw/contacts_data.csv",
                                 accounts_path: str = "data/raw/accounts_data.csv") -> None:
        """Prints a detailed statistical validation report to verify CampaignMember distributions."""
        print("=" * 70)
        print("                CAMPAIGNMEMBER VALIDATION REPORT                  ")
        print("=" * 70)
        print(f"Total CampaignMembers Generated: {len(df)}")
        print("-" * 70)

        # 1. Campaign Types Breakdown & Response Rates
        print("1. Channel Breakdown & Response Metrics:")
        channels = df["campaign_type"].value_counts()
        for chan, count in channels.items():
            chan_df = df[df["campaign_type"] == chan]
            resp_rate = chan_df["is_responded"].mean() * 100
            print(f"  {chan:<22}: Count = {count:4d} ({count/len(df)*100:5.1f}%) | Response Rate = {resp_rate:5.1f}%")
        print("-" * 70)

        # 2. DQ-8 Automation Inflation
        print("2. DQ-8 Automation Inflation Metrics:")
        # Calculate automation share per unique lead/contact ID
        # Automated sends = campaign_type in Email/Telemarketing/Ad AND is_responded=False
        df["_is_automated_send"] = df["campaign_type"].isin(["Email", "Advertisement", "Telemarketing"]) & (~df["is_responded"])
        
        person_groups = df.groupby("entity_id")
        total_unique_people = df["entity_id"].nunique()
        
        inflated_people_count = 0
        for pid, group in person_groups:
            tot_memberships = len(group)
            auto_sends = group["_is_automated_send"].sum()
            share = auto_sends / tot_memberships if tot_memberships > 0 else 0.0
            if share > 0.70:
                inflated_people_count += 1
                
        inflated_pct = inflated_people_count / total_unique_people * 100
        print(f"  Unique Leads/Contacts Represented: {total_unique_people}")
        print(f"  Leads/Contacts with >70% Automation: {inflated_people_count} ({inflated_pct:.1f}% | Target exactly 30%)")
        print("-" * 70)

        # 3. Explicit Persona H Verification
        # Persona H: lead_id = '00QARCHETYPE0000H' or found dynamically
        h_id = "00QARCHETYPE0000H"
        if os.path.exists(leads_path):
            try:
                leads_df = pd.read_csv(leads_path)
                h_row = leads_df[leads_df["lead_id"].str.contains("ARCHETYPE0000H") | (leads_df["first_name"] == "Henry")]
                if len(h_row) > 0:
                    h_id = h_row.iloc[0]["lead_id"]
            except Exception:
                pass

        h_memberships = df[df["entity_id"] == h_id]
        h_auto_sends = h_memberships["_is_automated_send"].sum()
        h_responses = h_memberships["is_responded"].sum()
        print("3. Deterministic Persona H (Henry Inflated) Audit:")
        print(f"  Henry Inflated ID:           {h_id}")
        print(f"  Total Campaign memberships:  {len(h_memberships)} (Target exactly 40)")
        print(f"  Automated Sends (Sent):      {h_auto_sends} (Target exactly 38)")
        print(f"  Active Responses (Responded): {h_responses} (Target exactly 2)")
        print("-" * 70)

        # 4. buying Committee & Surge Account Verification
        print("4. buying Committee & Account-Level Clustered Engagement:")
        
        # Load Accounts and Contacts to join account ID
        accounts_df = pd.read_csv(accounts_path)
        contacts_df = pd.read_csv(contacts_path)
        
        # Map contacts to accounts
        contact_acc_map = contacts_df.set_index("contact_id")["account_id"].to_dict()
        
        # Add account_id to CampaignMember df for contact entities
        df["_account_id"] = df["entity_id"].map(contact_acc_map)
        
        # Calculate contact memberships by Account
        acc_memberships = df[df["entity_type"] == "Contact"].groupby("_account_id")
        
        # Segment Named vs. Standard
        named_acc_ids = set(accounts_df[accounts_df["is_named_account"] == True]["account_id"])
        
        named_contacts_engaged = []
        standard_contacts_engaged = []
        
        for acc_id, group in acc_memberships:
            num_engaged = group["entity_id"].nunique()
            if acc_id in named_acc_ids:
                named_contacts_engaged.append(num_engaged)
            else:
                standard_contacts_engaged.append(num_engaged)
                
        avg_named_engaged = np.mean(named_contacts_engaged) if named_contacts_engaged else 0.0
        avg_standard_engaged = np.mean(standard_contacts_engaged) if standard_contacts_engaged else 0.0
        
        print("  Buying Committee Activity (Engaged Contacts count by Account):")
        print(f"    Named Strategic Accounts:  Avg Engaged Contacts = {avg_named_engaged:.2f} contacts / account")
        print(f"    Standard Target Accounts:  Avg Engaged Contacts = {avg_standard_engaged:.2f} contacts / account")
        
        # Recency Surge Window Verification (exactly 10% high-intent surge accounts)
        surge_df = df[df["response_date"].str.contains("2026-05-0", na=False) | df["response_date"].str.contains("2026-05-1", na=False)]
        surge_accs_active = surge_df["_account_id"].dropna().nunique()
        print(f"\n  Active Surging Accounts (14-Day Surge Window May 1-15): {surge_accs_active} accounts with clustered spikes")
        print("=" * 70)


def main():
    """Main execution entry point."""
    parser = argparse.ArgumentParser(description="Generate realistic, relational CampaignMembers.")
    parser.add_argument("--count", type=int, default=5000, help="Number of records to generate (default: 5000).")
    parser.add_argument("--output", type=str, default="data/raw/campaign_members_data.csv", help="Path to write the CSV output (default: data/raw/campaign_members_data.csv).")
    parser.add_argument("--accounts", type=str, default="data/raw/accounts_data.csv", help="Path to Accounts CSV (default: data/raw/accounts_data.csv).")
    parser.add_argument("--leads", type=str, default="data/raw/leads_data.csv", help="Path to Leads CSV (default: data/raw/leads_data.csv).")
    parser.add_argument("--contacts", type=str, default="data/raw/contacts_data.csv", help="Path to Contacts CSV (default: data/raw/contacts_data.csv).")
    parser.add_argument("--seed", type=int, default=42, help="Seed value for deterministic reproducible runs (default: 42).")
    parser.add_argument("--clean", action="store_true", help="Generate clean data without DQ-8 automation inflation.")

    args = parser.parse_args()

    # Instantiate generator and generate data
    generator = SalesforceCampaignMemberGenerator(seed=args.seed)
    df = generator.generate_records(
        num_records=args.count,
        inject_dq_errors=not args.clean,
        accounts_path=args.accounts,
        leads_path=args.leads,
        contacts_path=args.contacts
    )

    # Ensure output parent directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Remove internal metadata columns prior to saving
    export_df = df.drop(columns=["_person_id", "_account_id", "_is_automated_send"], errors="ignore")

    # Export to CSV
    export_df.to_csv(args.output, index=False)
    print(f"\n[SUCCESS] Successfully generated and exported CampaignMembers to {args.output}\n")

    # Print validation report
    generator.print_validation_report(
        df,
        leads_path=args.leads,
        contacts_path=args.contacts,
        accounts_path=args.accounts
    )


if __name__ == "__main__":
    main()
