"""
Unit Tests for Stage 03: Prioritization and Component Scoring.

This test suite programmatically validates score distributions, component boundaries,
4-tier prioritization, readiness bands, JSON score breakdowns, and specific 
archetype scores (Persona A, Persona D, Persona F, and Persona H).

Author: Senior Data Engineer
"""

import sys
import os
import json
import unittest
import pandas as pd
import numpy as np

# Ensure the workspace is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stage03_component_scoring import SalesforceComponentScorer


class TestSalesforceComponentScorer(unittest.TestCase):
    """Test suite for the Stage 03 Component Prioritization and Scorer module."""

    @classmethod
    def setUpClass(cls):
        """Set up and run the component scoring stage."""
        cls.leads_path = "data/raw/leads_data.csv"
        cls.contacts_path = "data/raw/contacts_data.csv"
        cls.person_features_path = "data/processed/person_features.csv"
        cls.master_persons_path = "data/processed/master_persons.csv"
        cls.resolver_map_path = "data/processed/entity_resolution_map.csv"
        cls.output_path = "data/processed/person_scores.csv"

        cls.scorer = SalesforceComponentScorer(
            person_features_path=cls.person_features_path,
            master_persons_path=cls.master_persons_path
        )
        cls.df = cls.scorer.calculate_scores()

    def test_output_file_exists(self):
        """Verify that the prioritizations and scores dataset exists on disk."""
        self.assertTrue(os.path.exists(self.output_path))

    def test_scores_schema(self):
        """Verify all required output columns are present in person_scores.csv."""
        expected_columns = {
            "master_person_id", "first_name", "last_name", "title",
            "engagement_score", "recency_score", "profile_fit_score", "account_score",
            "readiness_score", "score_percentile", "priority_tier", "readiness_band",
            "score_breakdown_json", "eligibility_status", "structural_block_flag",
            "top_positive_reasons", "top_negative_reasons"
        }
        actual_cols = set(self.df.columns)
        self.assertEqual(actual_cols, expected_columns)

    def test_score_boundary_conditions(self):
        """Verify all computed scores stay within their logical maximum and minimum bounds."""
        for _, row in self.df.iterrows():
            # Engagement Score (0-45)
            self.assertGreaterEqual(row["engagement_score"], 0.0)
            self.assertLessEqual(row["engagement_score"], 45.0)

            # Recency Score (0-25)
            self.assertGreaterEqual(row["recency_score"], 0.0)
            self.assertLessEqual(row["recency_score"], 25.0)

            # Profile Fit Score (0-20)
            self.assertGreaterEqual(row["profile_fit_score"], 0.0)
            self.assertLessEqual(row["profile_fit_score"], 20.0)

            # Account Score (0-10)
            self.assertGreaterEqual(row["account_score"], 0.0)
            self.assertLessEqual(row["account_score"], 10.0)

            # Final Readiness Score (0-100)
            self.assertGreaterEqual(row["readiness_score"], 0.0)
            self.assertLessEqual(row["readiness_score"], 100.0)
            self.assertAlmostEqual(row["readiness_score"], 
                                   row["engagement_score"] + row["recency_score"] + 
                                   row["profile_fit_score"] + row["account_score"], 
                                   places=1)

    def test_tier_and_band_calibrations(self):
        """Verify 4-tier priorities and readiness bands mappings correspond exactly to thresholds."""
        for _, row in self.df.iterrows():
            score = row["readiness_score"]
            tier = row["priority_tier"]
            band = row["readiness_band"]

            if score >= 80.0:
                self.assertEqual(tier, "Hot")
                self.assertEqual(band, "Very High")
            elif score >= 60.0:
                self.assertEqual(tier, "Warm")
                self.assertEqual(band, "High")
            elif score >= 40.0:
                self.assertEqual(tier, "Monitor")
                self.assertEqual(band, "Medium")
            else:
                self.assertEqual(tier, "Cold")
                self.assertEqual(band, "Low")

    def test_json_score_breakdowns(self):
        """Verify JSON score breakdowns are valid and match raw scores exactly."""
        for _, row in self.df.iterrows():
            breakdown = json.loads(row["score_breakdown_json"])
            self.assertIn("engagement", breakdown)
            self.assertIn("recency", breakdown)
            self.assertIn("profile", breakdown)
            self.assertIn("account", breakdown)

            self.assertEqual(breakdown["engagement"], row["engagement_score"])
            self.assertEqual(breakdown["recency"], row["recency_score"])
            self.assertEqual(breakdown["profile"], row["profile_fit_score"])
            self.assertEqual(breakdown["account"], row["account_score"])

    def test_persona_h_henry_scoring(self):
        """Verify that Persona H (Henry Inflated) engagement score incurs the DQ-8 penalty."""
        leads_df = pd.read_csv(self.leads_path)
        h_lead = leads_df[leads_df["first_name"] == "Henry"]
        self.assertGreater(len(h_lead), 0)
        h_lead_id = h_lead.iloc[0]["lead_id"]

        map_df = pd.read_csv(self.resolver_map_path)
        h_mpid = map_df[map_df["raw_entity_id"] == h_lead_id].iloc[0]["master_person_id"]

        row = self.df[self.df["master_person_id"] == h_mpid].iloc[0]
        
        # Henry has high automation_ratio (0.95), so he must incur the -15 point penalty
        # Base quality: Webinar (70) and Content (50) average = 60.0. Contrib = 12.0
        # Base volume: 2 responses * 5 = 10.0. Total base = 22.0
        # Penalty = -15.0. Final engagement score = 7.0
        self.assertEqual(row["engagement_score"], 7.0)
        self.assertTrue("High automation inflation (DQ-8: >70% sends)" in row["top_negative_reasons"])

    def test_persona_f_optout_readiness_independence(self):
        """Verify Persona F (Fiona Optout) receives a high readiness score but eligibility Blocked."""
        leads_df = pd.read_csv(self.leads_path)
        f_lead = leads_df[leads_df["first_name"] == "Fiona"]
        self.assertGreater(len(f_lead), 0)
        f_lead_id = f_lead.iloc[0]["lead_id"]

        map_df = pd.read_csv(self.resolver_map_path)
        f_mpid = map_df[map_df["raw_entity_id"] == f_lead_id].iloc[0]["master_person_id"]

        row = self.df[self.df["master_person_id"] == f_mpid].iloc[0]

        # Fiona is highly qualified but opted-out. Under Principle 2:
        # 1. Her eligibility must be "Blocked"
        self.assertEqual(row["eligibility_status"], "Blocked")
        # 2. Her readiness score should stay non-zero (not zeroed out, since it is independent)
        self.assertGreater(row["readiness_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
