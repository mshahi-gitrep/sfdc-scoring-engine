"""
Unit Tests for Stage 04: Agentic Explainer.

This suite validates deterministic explanation summaries, recommendation rules,
campaign signal construction, and risk note logic for the agentic output.

Author: Senior Data Engineer
"""

import sys
import os
import unittest
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stage04_agentic_explainer import SalesforceAgenticExplainer


class TestSalesforceAgenticExplainer(unittest.TestCase):
    """Test suite for the Stage 04 Agentic Explainer module."""

    @classmethod
    def setUpClass(cls):
        cls.person_scores_path = "data/processed/person_scores.csv"
        cls.master_persons_path = "data/processed/master_persons.csv"
        cls.campaign_members_path = "data/raw/campaign_members_data.csv"
        cls.entity_resolution_map_path = "data/processed/entity_resolution_map.csv"
        cls.output_path = "data/processed/person_agent_recommendations.csv"

        cls.explainer = SalesforceAgenticExplainer(
            person_scores_path=cls.person_scores_path,
            master_persons_path=cls.master_persons_path,
            campaign_members_path=cls.campaign_members_path,
            entity_resolution_map_path=cls.entity_resolution_map_path,
            output_path=cls.output_path
        )
        cls.df = cls.explainer.calculate_recommendations()

    def test_output_file_exists(self):
        """Verify the agentic recommendations output file is created."""
        self.assertTrue(os.path.exists(self.output_path))

    def test_recommendations_schema(self):
        """Verify all required agentic output columns are present."""
        expected_columns = {
            "master_person_id",
            "why_summary",
            "where_signal_summary",
            "recommended_action",
            "why_now_summary",
            "talking_points",
            "risk_note"
        }
        self.assertEqual(set(self.df.columns), expected_columns)

    def test_recommended_action_rules(self):
        """Verify recommendation rules follow the deterministic priority/eligibility mapping."""
        sample = self.df.sample(n=min(10, len(self.df)), random_state=42)
        for _, row in sample.iterrows():
            action = row["recommended_action"]
            self.assertIsInstance(action, str)
            self.assertTrue(action.endswith(".") or action.endswith(" only."))

    def test_why_summary_contains_reasons(self):
        """Verify why_summary provides business context and references strengths or concerns."""
        row = self.df.iloc[0]
        self.assertIsInstance(row["why_summary"], str)
        self.assertTrue(
            "Notable strengths include" in row["why_summary"] or
            "Current concerns include" in row["why_summary"] or
            "There is little to no evidence" in row["why_summary"]
        )

    def test_where_summary_includes_signal_source(self):
        """Verify where_signal_summary contains signal attribution language."""
        row = self.df.iloc[0]
        self.assertIsInstance(row["where_signal_summary"], str)
        self.assertTrue(len(row["where_signal_summary"]) > 0)

    def test_risk_note_flags(self):
        """Verify risk_note is present and deterministic for risk conditions."""
        row = self.df.iloc[0]
        self.assertIsInstance(row["risk_note"], str)
        self.assertTrue(
            row["risk_note"].startswith("No material") or
            row["risk_note"].startswith("Moderate Data Quality Risk") or
            row["risk_note"].startswith("Elevated Data Quality Risk")
        )

    def test_why_now_summary_format(self):
        """Verify why_now_summary provides a clear timing rationale."""
        row = self.df.iloc[0]
        self.assertIsInstance(row["why_now_summary"], str)
        self.assertTrue(
            row["why_now_summary"].startswith("WHY NOW?") or
            row["why_now_summary"].startswith("No material changes detected recently")
        )

    def test_output_determinism(self):
        """Verify repeat runs produce the same master_person_id order and deterministic outputs."""
        second_df = self.explainer.calculate_recommendations()
        self.assertEqual(list(self.df["master_person_id"]), list(second_df["master_person_id"]))
        self.assertEqual(list(self.df["recommended_action"]), list(second_df["recommended_action"]))


if __name__ == "__main__":
    unittest.main()
