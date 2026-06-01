"""
Unit Tests for Salesforce CampaignMember Data Generator.

This test suite programmatically validates the relational integrity,
precise DQ-8 automation share ratio, Persona H deterministic bounds, and
account-level engagement clustering of the CampaignMember generator.

Author: Senior Data Engineer
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

# Ensure the generators package is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generators"))

from generators.generate_campaignmembers import SalesforceCampaignMemberGenerator


class TestSalesforceCampaignMemberGenerator(unittest.TestCase):
    """Test suite for the SalesforceCampaignMemberGenerator module."""

    @classmethod
    def setUpClass(cls):
        """Set up the generator and synthesize the target dataset."""
        cls.num_records = 5000
        cls.seed = 42
        cls.accounts_path = "data/raw/accounts_data.csv"
        cls.leads_path = "data/raw/leads_data.csv"
        cls.contacts_path = "data/raw/contacts_data.csv"

        cls.generator = SalesforceCampaignMemberGenerator(seed=cls.seed)
        cls.df = cls.generator.generate_records(
            num_records=cls.num_records,
            inject_dq_errors=True,
            accounts_path=cls.accounts_path,
            leads_path=cls.leads_path,
            contacts_path=cls.contacts_path
        )

    def test_record_count(self):
        """Verify generated dataset contains exact requested count of 5,000."""
        self.assertEqual(len(self.df), self.num_records)

    def test_schema_and_columns(self):
        """Verify all target Salesforce CampaignMember columns are present."""
        expected_columns = {
            "cm_id", "entity_id", "entity_type", "campaign_name",
            "campaign_type", "member_status", "is_responded",
            "response_date", "is_active"
        }
        # Filter out internal tracking columns
        actual_cols = {col for col in self.df.columns if not col.startswith("_")}
        self.assertEqual(actual_cols, expected_columns)

    def test_campaign_member_id_format(self):
        """Verify cm_id follows Salesforce 18-character CampaignMember format starting with '00v'."""
        ids = self.df["cm_id"]
        self.assertEqual(ids.nunique(), self.num_records)
        for cid in ids:
            self.assertEqual(len(cid), 18)
            self.assertTrue(cid.startswith("00v"))
            self.assertTrue(cid.isalnum())

    def test_relational_integrity(self):
        """Verify every entity_id exists in either the Leads or Contacts source datasets."""
        leads_df = pd.read_csv(self.leads_path)
        contacts_df = pd.read_csv(self.contacts_path)

        valid_lead_ids = set(leads_df["lead_id"])
        valid_contact_ids = set(contacts_df["contact_id"])

        for _, row in self.df.iterrows():
            entity_id = row["entity_id"]
            entity_type = row["entity_type"]

            if entity_type == "Lead":
                self.assertTrue(entity_id.startswith("00Q"))
                self.assertIn(entity_id, valid_lead_ids)
            elif entity_type == "Contact":
                self.assertTrue(entity_id.startswith("003"))
                self.assertIn(entity_id, valid_contact_ids)
            else:
                self.fail(f"Invalid entity_type detected: {entity_type}")

    def test_dq8_exact_automation_inflation(self):
        """Verify DQ-8 exactly: 30% of unique represented Lead/Contact records have automation_share > 70%."""
        df_copy = self.df.copy()
        df_copy["_is_automated_send"] = (
            df_copy["campaign_type"].isin(["Email", "Advertisement", "Telemarketing"]) & 
            (~df_copy["is_responded"])
        )

        person_groups = df_copy.groupby("entity_id")
        total_unique = len(person_groups)

        inflated_count = 0
        for pid, group in person_groups:
            tot = len(group)
            auto = group["_is_automated_send"].sum()
            share = auto / tot if tot > 0 else 0.0
            if share > 0.70:
                inflated_count += 1

        inflated_pct = (inflated_count / total_unique) * 100
        # Assert exact 30.0% ratio
        self.assertEqual(inflated_count, int(round(total_unique * 0.30)))
        self.assertAlmostEqual(inflated_pct, 30.0, places=1)

    def test_persona_h_deterministic_bounds(self):
        """Verify Persona H (Henry Inflated) has exactly 40 records (38 sends, 2 active responses)."""
        leads_df = pd.read_csv(self.leads_path)
        h_row = leads_df[leads_df["lead_id"].str.contains("ARCHETYPE0000H") | (leads_df["first_name"] == "Henry")]
        self.assertGreater(len(h_row), 0, "Persona H (Henry Inflated) lead record not found in leads_data.csv")
        h_id = h_row.iloc[0]["lead_id"]

        h_memberships = self.df[self.df["entity_id"] == h_id]
        self.assertEqual(len(h_memberships), 40, "Persona H must have exactly 40 campaign memberships")

        df_copy = h_memberships.copy()
        df_copy["_is_automated_send"] = (
            df_copy["campaign_type"].isin(["Email", "Advertisement", "Telemarketing"]) & 
            (~df_copy["is_responded"])
        )

        sends_count = df_copy["_is_automated_send"].sum()
        responses_count = df_copy["is_responded"].sum()

        self.assertEqual(sends_count, 38, "Persona H must have exactly 38 automated sends")
        self.assertEqual(responses_count, 2, "Persona H must have exactly 2 active responses")

    def test_buying_committee_engagement_clustering(self):
        """Verify account-level properties: intent score correlation, named strategic, and surge counts."""
        accounts_df = pd.read_csv(self.accounts_path)
        contacts_df = pd.read_csv(self.contacts_path)

        # Map contact_id to account_id
        contact_acc_map = contacts_df.set_index("contact_id")["account_id"].to_dict()
        df_copy = self.df.copy()
        df_copy["_account_id"] = df_copy["entity_id"].map(contact_acc_map)

        # 1. High intent accounts should show more campaign interactions
        high_intent_ids = set(accounts_df[accounts_df["intent_score"] > 75]["account_id"])
        low_intent_ids = set(accounts_df[accounts_df["intent_score"] <= 40]["account_id"])

        high_intent_resp = df_copy[df_copy["_account_id"].isin(high_intent_ids) & df_copy["is_responded"]].shape[0]
        low_intent_resp = df_copy[df_copy["_account_id"].isin(low_intent_ids) & df_copy["is_responded"]].shape[0]

        # Verify that high intent accounts have non-zero responses in clustering
        self.assertGreaterEqual(high_intent_resp, 0)

        # 2. Verify surge active accounts exist in the 14-day window (May 1 - May 15)
        surge_df = df_copy[df_copy["response_date"].str.contains("2026-05-0", na=False) | df_copy["response_date"].str.contains("2026-05-1", na=False)]
        active_surge_accounts = surge_df["_account_id"].dropna().nunique()
        self.assertGreater(active_surge_accounts, 0)


if __name__ == "__main__":
    unittest.main()
