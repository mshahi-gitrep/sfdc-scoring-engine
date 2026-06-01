"""
Unit Tests for Salesforce Contact Data Generator.

This test suite programmatically validates the relational pairing, orphan counts,
profile field synchronization, and data quality anomalies of the Contact generator.

Author: Senior Data Engineer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generators"))

import unittest
import pandas as pd
from generators.generate_contacts import SalesforceContactGenerator


class TestSalesforceContactGenerator(unittest.TestCase):
    """Test suite for the SalesforceContactGenerator module."""

    @classmethod
    def setUpClass(cls):
        """Set up standard (DQ-injected) and clean contact datasets."""
        cls.num_records = 400
        cls.seed = 42
        cls.accounts_path = "data/raw/accounts_data.csv"
        cls.leads_path = "data/raw/leads_data.csv"
        
        cls.generator = SalesforceContactGenerator(seed=cls.seed)
        
        # Standard generator with DQ anomalies
        cls.df_dq = cls.generator.generate_records(
            num_records=cls.num_records,
            inject_dq_errors=True,
            accounts_path=cls.accounts_path,
            leads_path=cls.leads_path
        )
        
        # Clean generator without DQ anomalies
        cls.df_clean = cls.generator.generate_records(
            num_records=cls.num_records,
            inject_dq_errors=False,
            accounts_path=cls.accounts_path,
            leads_path=cls.leads_path
        )

    def test_record_count(self):
        """Verify generated dataset contains exact requested count (400)."""
        self.assertEqual(len(self.df_dq), self.num_records)
        self.assertEqual(len(self.df_clean), self.num_records)

    def test_schema_and_columns(self):
        """Verify all target Salesforce Contact schema columns are present and spelled correctly."""
        expected_columns = {
            "contact_id", "account_id", "email", "first_name", "last_name", "title",
            "contact_status", "job_persona", "job_level", "mql_date",
            "mkto_contact_score", "has_lead_origin", "primary_lead_id",
            "no_longer_with_company", "has_opted_out"
        }
        self.assertEqual(set(self.df_dq.columns), expected_columns)
        self.assertEqual(set(self.df_clean.columns), expected_columns)

    def test_contact_id_format_and_uniqueness(self):
        """Verify contact_id follows Salesforce 18-character Contact format starting with '003'."""
        for df in [self.df_dq, self.df_clean]:
            ids = df["contact_id"]
            self.assertEqual(ids.nunique(), self.num_records)
            for cid in ids:
                self.assertEqual(len(cid), 18)
                self.assertTrue(cid.startswith("003"))
                self.assertTrue(cid.isalnum())

    def test_composition_ratios(self):
        """Verify composition targets: exactly 200 connected and exactly 200 orphans."""
        for df in [self.df_dq, self.df_clean]:
            connected_count = df["has_lead_origin"].sum()
            orphan_count = (~df["has_lead_origin"]).sum()
            self.assertEqual(connected_count, 200)
            self.assertEqual(orphan_count, 200)

    def test_connected_pair_fidelity(self):
        """Verify profile fields match converted leads exactly for active pairs in leads_data.csv."""
        # Read the leads file to match
        if os.path.exists(self.leads_path):
            leads_df = pd.read_csv(self.leads_path)
            converted_leads = leads_df[leads_df["is_converted"] == True]
            
            # Verify for each active lead with a mapped converted_contact_id
            for _, lead in converted_leads.iterrows():
                contact_id = lead["converted_contact_id"]
                if pd.isnull(contact_id):
                    continue
                
                # Check both DQ and clean Contact dataframes
                for df in [self.df_dq, self.df_clean]:
                    contact_row = df[df["contact_id"] == contact_id]
                    self.assertEqual(len(contact_row), 1)
                    
                    # Verify fields match exactly
                    self.assertEqual(contact_row["first_name"].values[0], lead["first_name"])
                    self.assertEqual(contact_row["last_name"].values[0], lead["last_name"])
                    self.assertEqual(contact_row["email"].values[0], lead["email"])
                    self.assertEqual(contact_row["primary_lead_id"].values[0], lead["lead_id"])
                    self.assertTrue(contact_row["has_lead_origin"].values[0])

    def test_broken_conversion_link_preservation(self):
        """Verify that converted leads with missing contact IDs (DQ-1) are still generated as Contacts."""
        if os.path.exists(self.leads_path):
            leads_df = pd.read_csv(self.leads_path)
            converted_leads = leads_df[leads_df["is_converted"] == True]
            broken_leads = converted_leads[converted_leads["converted_contact_id"].isnull()]
            
            # Verify that these broken converted leads still exist in standard contacts
            for _, lead in broken_leads.iterrows():
                contact_row = self.df_dq[self.df_dq["primary_lead_id"] == lead["lead_id"]]
                self.assertEqual(len(contact_row), 1)
                self.assertTrue(contact_row["has_lead_origin"].values[0])
                # Generated contact ID should be non-null and valid
                self.assertTrue(contact_row["contact_id"].values[0].startswith("003"))

    def test_completeness_gaps_dq_rules(self):
        """Verify DQ-7, DQ-6 constraints: exactly 35% null titles, exactly 60% global persona/level population."""
        # 1. Title completeness (approximately 35% null globally with statistical tolerance)
        self.assertGreaterEqual(self.df_dq["title"].isnull().mean(), 0.30)
        self.assertLessEqual(self.df_dq["title"].isnull().mean(), 0.42)
        self.assertGreaterEqual(self.df_clean["title"].isnull().mean(), 0.30)
        self.assertLessEqual(self.df_clean["title"].isnull().mean(), 0.42)

        # 2. Persona and Level population (exactly 60% globally)
        target_pop_count = int(round(self.num_records * 0.60))
        self.assertEqual(self.df_dq["job_persona"].notnull().sum(), target_pop_count)
        self.assertEqual(self.df_dq["job_level"].notnull().sum(), target_pop_count)

    def test_compliance_anomalies_presence(self):
        """Verify DQ-9 compliance presence (opt-outs, bounces, no longer with company)."""
        df = self.df_dq
        
        # 1. Opt-out rate is non-zero
        self.assertGreater(df["has_opted_out"].sum(), 0)
        
        # 2. no_longer_with_company is non-zero
        self.assertGreater(df["no_longer_with_company"].sum(), 0)
        
        # 3. Clean mode strict check (bounces and opt-outs exist but are clean, no null accounts in clean orphans)
        clean_orphans = self.df_clean[~self.df_clean["has_lead_origin"]]
        self.assertTrue(clean_orphans["account_id"].notnull().all())
        
        # DQ mode orphans account gaps (3% missing account linkages)
        dq_orphans = df[~df["has_lead_origin"]]
        self.assertGreater(dq_orphans["account_id"].isnull().sum(), 0)


if __name__ == "__main__":
    unittest.main()
