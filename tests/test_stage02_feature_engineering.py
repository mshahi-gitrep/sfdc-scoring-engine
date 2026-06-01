"""
Unit Tests for Stage 02: Feature Engineering.

This test suite validates the correctness of all engineered feature categories,
including behavioral counts, recency decay, velocity flags, profile mappings,
and our three new advanced layers (Risk, Quality, and Buying Committee Strength).

Author: Senior Data Engineer
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

# Ensure the workspace is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stage02_feature_engineering import SalesforceFeatureEngineer


class TestSalesforceFeatureEngineer(unittest.TestCase):
    """Test suite for the Stage 02 Feature Engineering module."""

    @classmethod
    def setUpClass(cls):
        """Set up and run the feature engineering stage."""
        cls.leads_path = "data/raw/leads_data.csv"
        cls.contacts_path = "data/raw/contacts_data.csv"
        cls.campaign_members_path = "data/raw/campaign_members_data.csv"
        cls.accounts_path = "data/raw/accounts_data.csv"
        cls.master_persons_path = "data/processed/master_persons.csv"
        cls.resolver_map_path = "data/processed/entity_resolution_map.csv"
        cls.output_path = "data/processed/person_features.csv"

        cls.engineer = SalesforceFeatureEngineer(
            master_persons_path=cls.master_persons_path,
            resolver_map_path=cls.resolver_map_path,
            campaign_members_path=cls.campaign_members_path,
            accounts_path=cls.accounts_path
        )
        cls.df = cls.engineer.engineer_features()

    def test_output_file_exists(self):
        """Verify that the engineered features dataset exists on disk."""
        self.assertTrue(os.path.exists(self.output_path))

    def test_features_schema(self):
        """Verify all required output columns are present in person_features.csv."""
        expected_columns = {
            "master_person_id", "total_campaign_memberships", "total_responses",
            "real_engagement_count", "automated_touch_count", "automation_ratio",
            "webinar_attended_count", "event_attended_count", "content_response_count",
            "email_response_count", "last_response_date", "days_since_last_response",
            "responses_7d", "responses_14d", "responses_30d", "responses_90d",
            "response_velocity_30d", "engagement_burst_flag", "sustained_engagement_flag",
            "seniority_score", "persona_score", "profile_completeness_score",
            "non_prospect_flag", "account_id", "is_icp_qualified", "is_named_account",
            "intent_score", "do_not_contact", "account_response_count",
            "engaged_contacts_on_account", "account_surge_flag", "duplicate_email_flag",
            "shared_mailbox_flag", "broken_conversion_link_flag", "missing_title_flag",
            "missing_account_flag", "opted_out_flag", "bounced_or_left_company_flag",
            "structural_block_flag", "risk_score", "eligibility_status",
            "engagement_quality_score", "buying_committee_strength"
        }
        actual_cols = set(self.df.columns)
        self.assertEqual(actual_cols, expected_columns)

    def test_persona_h_henry_features(self):
        """Verify that Persona H (Henry Inflated) features are exactly mapped and calibrated."""
        # Find Henry in Leads
        leads_df = pd.read_csv(self.leads_path)
        h_lead = leads_df[leads_df["first_name"] == "Henry"]
        self.assertGreater(len(h_lead), 0, "Henry Inflated lead not found in leads_data.csv")
        h_lead_id = h_lead.iloc[0]["lead_id"]

        # Find resolved Master Person ID from resolver map
        map_df = pd.read_csv(self.resolver_map_path)
        h_map = map_df[map_df["raw_entity_id"] == h_lead_id]
        self.assertEqual(len(h_map), 1)
        h_mpid = h_map.iloc[0]["master_person_id"]

        # Pull Henry's features
        h_features = self.df[self.df["master_person_id"] == h_mpid]
        self.assertEqual(len(h_features), 1)
        
        row = h_features.iloc[0]
        
        # Verify core counts
        self.assertEqual(row["total_campaign_memberships"], 40)
        self.assertEqual(row["total_responses"], 2)
        self.assertEqual(row["automated_touch_count"], 38)
        self.assertAlmostEqual(row["automation_ratio"], 0.95, places=2)

        # Verify Quality Layer: Webinar (70) and Content (50)
        # Average quality = (70 + 50) / 2 = 60.0
        self.assertEqual(row["engagement_quality_score"], 60.0)

    def test_risk_layer_and_eligibility(self):
        """Verify Risk Score calculations and Eligibility Routing states."""
        # 1. Check a hard blocked CISO or opted-out prospect
        blocked_df = self.df[self.df["structural_block_flag"] == True]
        for _, row in blocked_df.iterrows():
            self.assertEqual(row["eligibility_status"], "Blocked")
            if row["opted_out_flag"] or row["bounced_or_left_company_flag"] or row["do_not_contact"]:
                self.assertEqual(row["risk_score"], 100)

        # 2. Check general mailbox / shared box risk
        shared_mailbox_df = self.df[(self.df["shared_mailbox_flag"] == True) & 
                                    (self.df["structural_block_flag"] == False)]
        for _, row in shared_mailbox_df.iterrows():
            self.assertGreaterEqual(row["risk_score"], 40)
            self.assertEqual(row["eligibility_status"], "Restricted")

    def test_buying_committee_strength_and_surges(self):
        """Verify Account Aggregations and Buying Committee Strength metrics."""
        # Check active accounts
        acc_df = self.df[self.df["account_id"].notnull()]
        self.assertGreater(len(acc_df), 0)

        # Verify Named Account committee size and strength calculations
        named_accounts = acc_df[acc_df["is_named_account"] == True]
        for _, row in named_accounts.iterrows():
            expected_strength = (row["engaged_contacts_on_account"] / 6.0) * 100.0
            expected_strength = min(100.0, expected_strength)
            self.assertAlmostEqual(row["buying_committee_strength"], expected_strength, places=2)

        standard_accounts = acc_df[acc_df["is_named_account"] == False]
        for _, row in standard_accounts.iterrows():
            expected_strength = (row["engaged_contacts_on_account"] / 3.0) * 100.0
            expected_strength = min(100.0, expected_strength)
            self.assertAlmostEqual(row["buying_committee_strength"], expected_strength, places=2)


if __name__ == "__main__":
    unittest.main()
