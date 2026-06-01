"""
Unit Tests for Salesforce Lead Data Generator.

This test suite programmatically validates the schema, persona-driven intent scores,
conversion ratios, and the behavior of both clean and DQ-injected generation modes.

Author: Senior Data Engineer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generators"))

import unittest
import numpy as np
import pandas as pd
from generators.generate_leads import SalesforceLeadGenerator


class TestSalesforceLeadGenerator(unittest.TestCase):
    """Test suite for the SalesforceLeadGenerator module."""

    @classmethod
    def setUpClass(cls):
        """Set up standard (DQ-injected) and clean lead datasets."""
        cls.num_records = 600
        cls.seed = 42
        
        # Standard generator with DQ anomalies
        cls.generator = SalesforceLeadGenerator(seed=cls.seed)
        cls.df_dq = cls.generator.generate_records(cls.num_records, inject_dq_errors=True)
        
        # Clean generator without DQ anomalies
        cls.df_clean = cls.generator.generate_records(cls.num_records, inject_dq_errors=False)

    def test_record_count(self):
        """Verify generated dataset contains exact requested count."""
        self.assertEqual(len(self.df_dq), self.num_records)
        self.assertEqual(len(self.df_clean), self.num_records)

    def test_schema_and_columns(self):
        """Verify all target Salesforce Lead schema columns are present and spelled correctly."""
        expected_columns = {
            "lead_id", "email", "first_name", "last_name", "title", "company", "job_persona", "job_level",
            "lead_status", "lead_source", "created_date", "mql_date",
            "mkto_lead_score", "is_converted", "converted_contact_id",
            "has_opted_out", "email_bounced", "phone", "industry", "true_entry_date"
        }
        actual_cols_dq = set(self.df_dq.columns) - {"_persona", "_archetype"}
        self.assertEqual(actual_cols_dq, expected_columns)

    def test_lead_id_format_and_uniqueness(self):
        """Verify lead_id follows Salesforce 18-character Lead format starting with '00Q'."""
        for df in [self.df_dq, self.df_clean]:
            ids = df["lead_id"]
            self.assertEqual(ids.nunique(), self.num_records)
            for lid in ids:
                self.assertEqual(len(lid), 18)
                self.assertTrue(lid.startswith("00Q"))
                self.assertTrue(lid.isalnum())

    def test_title_null_rate(self):
        """Verify title contains approximately 35% null values globally (within statistical tolerance)."""
        for df in [self.df_dq, self.df_clean]:
            null_rate = df["title"].isnull().mean()
            self.assertGreaterEqual(null_rate, 0.28)
            self.assertLessEqual(null_rate, 0.42)

    def test_persona_driven_scores_and_conversions(self):
        """Verify that high-priority security personas score higher and convert better than non-prospects."""
        df = self.df_clean
        
        # 1. Non-prospect conversion block
        competitors = df[df["_persona"] == "Competitor Employee"]
        vendors = df[df["_persona"] == "Vendor Employee"]
        self.assertTrue((competitors["is_converted"] == False).all())
        self.assertTrue((vendors["is_converted"] == False).all())
        
        # 2. Intent score mapping (CISOs & VPs score higher than Analysts & Competitors)
        cisos_vps = df[df["_persona"].isin(["CISO", "VP Security"])]
        analysts = df[df["_persona"] == "Security Analyst"]
        
        ciso_scores = pd.to_numeric(cisos_vps["mkto_lead_score"], errors="coerce").dropna()
        analyst_scores = pd.to_numeric(analysts["mkto_lead_score"], errors="coerce").dropna()
        comp_scores = pd.to_numeric(competitors["mkto_lead_score"], errors="coerce").dropna()

        self.assertGreater(ciso_scores.mean(), analyst_scores.mean())
        self.assertGreater(analyst_scores.mean(), comp_scores.mean())

        # 3. Conversion mapping
        self.assertGreater(cisos_vps["is_converted"].mean(), analysts["is_converted"].mean())

    def test_clean_mode_assertions(self):
        """Verify that clean generation mode (no DQ injection) has strict CRM data integrity."""
        df = self.df_clean
        
        # 1. Created Date format
        created_dates = df["created_date"]
        self.assertTrue(created_dates.notnull().all())
        for dt in created_dates:
            self.assertNotIn("/", dt)
            self.assertEqual(len(dt), 19)

        # 2. Converted Contact Linkage
        converted = df[df["is_converted"]]
        not_converted = df[~df["is_converted"]]
        
        # In clean mode, G's conversion is also clean, so all converted leads have contacts
        self.assertTrue(converted["converted_contact_id"].notnull().all())
        for cid in converted["converted_contact_id"]:
            self.assertEqual(len(cid), 18)
            self.assertTrue(cid.startswith("003"))

        self.assertTrue(not_converted["converted_contact_id"].isnull().all())

        # 3. MQL Date tracking
        mql_statuses = df["lead_status"].isin(["MQL", "SQL", "Converted"])
        mql_leads = df[mql_statuses]
        non_mql_leads = df[~mql_statuses]
        
        self.assertTrue(mql_leads["mql_date"].notnull().all())
        self.assertTrue(non_mql_leads["mql_date"].isnull().all())

        # 4. Score range constraints
        scores = df["mkto_lead_score"]
        self.assertTrue(scores.notnull().all())
        for s in scores:
            self.assertIsInstance(s, int)
            self.assertGreaterEqual(s, -25)
            self.assertLessEqual(s, 100)

        # 5. Strict Compliance Block
        compliance_block = df["has_opted_out"] | df["email_bounced"]
        violated_conversions = df[compliance_block & df["is_converted"]]
        self.assertEqual(len(violated_conversions), 0)

    def test_dq_mode_anomalies_presence(self):
        """Verify that standard (DQ-injected) generation mode contains realistic data discrepancies."""
        df = self.df_dq

        # 1. DQ-4: ETL bulk load dates (exactly 80% override)
        etl_timestamp = "2026-05-15 03:00:00"
        etl_count = (df["created_date"] == etl_timestamp).sum()
        self.assertEqual(etl_count, int(round(self.num_records * 0.80)))

        # 2. DQ-1: Converted contact ID synchronization failures (exactly 20% converted missing)
        converted_leads = df[df["is_converted"]]
        total_conv = len(converted_leads)
        broken_conv = converted_leads["converted_contact_id"].isnull().sum()
        expected_broken = int(round(total_conv * 0.20))
        self.assertEqual(broken_conv, expected_broken)

        # 3. DQ-2: Email Duplication (10% to 15% duplicates)
        duplicated_emails = df["email"].duplicated().sum()
        dup_pct = duplicated_emails / self.num_records * 100
        self.assertGreaterEqual(dup_pct, 10.0)
        self.assertLessEqual(dup_pct, 15.0)

        # 4. DQ-2: Specific clusters (2% high cardinality = Megacorp + HighIntent)
        megacorp_count = (df["email"] == "info@megacorp.com").sum()
        highintent_count = (df["email"] == "security@highintent.com").sum()
        self.assertEqual(megacorp_count, 6)
        self.assertEqual(highintent_count, 6)

        # 5. DQ-9: Compliance leakage conversions
        compliance_block = df["has_opted_out"] | df["email_bounced"]
        leakage = df[compliance_block & df["is_converted"]]
        self.assertGreater(len(leakage), 0)

        # 6. Job levels and personas population rate (around 60%)
        self.assertGreaterEqual(df["job_persona"].notnull().mean(), 0.50)
        self.assertLessEqual(df["job_persona"].notnull().mean(), 0.70)
        self.assertGreaterEqual(df["job_level"].notnull().mean(), 0.50)
        self.assertLessEqual(df["job_level"].notnull().mean(), 0.70)

        # 7. phone and industry completeness gaps (with statistical tolerance for random generation)
        self.assertGreaterEqual(df["phone"].isnull().mean(), 0.15)
        self.assertLessEqual(df["phone"].isnull().mean(), 0.35)
        self.assertGreaterEqual(df["industry"].isnull().mean(), 0.12)
        self.assertLessEqual(df["industry"].isnull().mean(), 0.28)

    def test_archetypes_injection(self):
        """Verify that all 8 deterministic archetypes are generated successfully in both datasets."""
        for df in [self.df_dq, self.df_clean]:
            for arch in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                row = df[df["_archetype"] == arch]
                self.assertEqual(len(row), 1)
                
                # Check specific attributes to confirm identities
                if arch == 'A':
                    self.assertEqual(row["first_name"].values[0], "Sarah")
                    self.assertEqual(row["job_level"].values[0], "VP")
                elif arch == 'E':
                    self.assertEqual(row["first_name"].values[0], "Craig")
                    self.assertEqual(row["company"].values[0], "Competitor Inc")
                    self.assertEqual(row["lead_status"].values[0], "Disqualified")
                elif arch == 'G' and df is self.df_dq:
                    # Broken conversion link in DQ mode
                    self.assertTrue(row["is_converted"].values[0])
                    self.assertTrue(pd.isnull(row["converted_contact_id"].values[0]))


if __name__ == "__main__":
    unittest.main()
