"""
Unit Tests for Stage 01: Entity Resolution.

This test suite programmatically validates the graph-based entity resolution,
including direct conversion links, backlink recovery, fallback email matching,
shared mailbox exclusions, attribute survivorship, and deterministic formatting.

Author: Senior Data Engineer
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

# Ensure the workspace is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stage01_entity_resolution import SalesforceEntityResolver


class TestSalesforceEntityResolver(unittest.TestCase):
    """Test suite for the Stage 01 Entity Resolution module."""

    @classmethod
    def setUpClass(cls):
        """Set up standard paths and load processed outputs."""
        cls.leads_path = "data/raw/leads_data.csv"
        cls.contacts_path = "data/raw/contacts_data.csv"
        cls.master_persons_path = "data/processed/master_persons.csv"
        cls.resolution_map_path = "data/processed/entity_resolution_map.csv"

        # Instantiate resolver and process
        cls.resolver = SalesforceEntityResolver(leads_path=cls.leads_path, contacts_path=cls.contacts_path)
        cls.master_df, cls.map_df = cls.resolver.resolve_entities()

    def test_output_files_existence(self):
        """Verify that resolved master persons and mapping files exist on disk."""
        self.assertTrue(os.path.exists(self.master_persons_path))
        self.assertTrue(os.path.exists(self.resolution_map_path))

    def test_master_persons_schema(self):
        """Verify the required columns are present in the Master Persons output."""
        expected_columns = {
            "master_person_id", "preferred_entity_id", "preferred_entity_type",
            "lead_id", "contact_id", "email", "normalized_email", "account_id",
            "first_name", "last_name", "title", "job_persona", "job_level",
            "source_entity_types", "has_lead_record", "has_contact_record",
            "is_connected_pair", "broken_conversion_link_flag", "duplicate_email_flag",
            "shared_mailbox_flag", "entity_resolution_confidence"
        }
        actual_cols = set(self.master_df.columns)
        self.assertEqual(actual_cols, expected_columns)

    def test_deterministic_master_person_ids(self):
        """Verify master_person_id is deterministic and follows the format MP + 14 digits."""
        ids = self.master_df["master_person_id"]
        self.assertEqual(ids.nunique(), len(self.master_df))
        for mpid in ids:
            self.assertEqual(len(mpid), 16)
            self.assertTrue(mpid.startswith("MP"))
            suffix = mpid[2:]
            self.assertTrue(suffix.isdigit())

    def test_survivorship_priority_contact_over_lead(self):
        """Verify that when a Contact and a Lead are resolved together, Contact takes precedence."""
        connected_pairs = self.master_df[self.master_df["is_connected_pair"] & 
                                         self.master_df["has_lead_record"] & 
                                         self.master_df["has_contact_record"]]
        
        self.assertGreater(len(connected_pairs), 0)
        for _, row in connected_pairs.iterrows():
            self.assertEqual(row["preferred_entity_type"], "Contact")
            self.assertTrue(row["preferred_entity_id"].startswith("003"))

    def test_persona_g_broken_conversion_resolution(self):
        """Verify that the Persona G archetype (George Broken) is successfully resolved to a single Master Person."""
        leads_df = pd.read_csv(self.leads_path)
        g_lead = leads_df[leads_df["first_name"] == "George"]
        self.assertGreater(len(g_lead), 0, "George Broken record not found in leads_data.csv")
        g_lead_id = g_lead.iloc[0]["lead_id"]

        # In master_persons, find the record containing George's lead ID
        resolved_row = self.master_df[self.master_df["lead_id"].str.contains(g_lead_id, na=False)]
        self.assertEqual(len(resolved_row), 1, "George Broken's Lead should resolve to exactly one Master Person")
        
        # Verify both Lead and Contact records are mapped to this Master Person
        self.assertTrue(resolved_row["has_lead_record"].values[0])
        self.assertTrue(resolved_row["has_contact_record"].values[0])
        self.assertTrue(resolved_row["is_connected_pair"].values[0])
        self.assertTrue(resolved_row["broken_conversion_link_flag"].values[0])
        self.assertEqual(resolved_row["preferred_entity_type"].values[0], "Contact")

    def test_shared_mailboxes_exclusion(self):
        """Verify that entities with duplicate shared mailbox emails are NOT merged blindly."""
        # Find some shared mailbox group in Leads (e.g. security@highintent.com or info@megacorp.com)
        leads_df = pd.read_csv(self.leads_path)
        leads_df["_norm_email"] = leads_df["email"].str.strip().str.lower()
        
        # Filter for non-converted shared mailbox leads
        info_leads = leads_df[(leads_df["_norm_email"] == "info@megacorp.com") & (leads_df["is_converted"] == False)]
        if len(info_leads) > 1:
            lead_ids = info_leads["lead_id"].tolist()
            
            # Look up their resolved master persons
            mp_ids = []
            for lid in lead_ids:
                row = self.master_df[self.master_df["lead_id"].str.contains(lid, na=False)]
                if len(row) > 0:
                    mp_ids.append(row["master_person_id"].values[0])
            
            # Verify they are resolved to DIFFERENT master persons
            self.assertEqual(len(set(mp_ids)), len(mp_ids), 
                             "Unconnected leads sharing a general info@ mailbox must NOT be merged into a single master person")

    def test_duplicate_non_shared_email_merges(self):
        """Verify that duplicate normal (non-shared) emails are consolidated into a single master person."""
        # Find normal email duplication in Leads/Contacts
        leads_df = pd.read_csv(self.leads_path)
        leads_df["_norm_email"] = leads_df["email"].str.strip().str.lower()
        
        contacts_df = pd.read_csv(self.contacts_path)
        contacts_df["_norm_email"] = contacts_df["email"].str.strip().str.lower()

        # Find all emails and identify duplicates that are not shared mailboxes
        all_emails = pd.concat([leads_df["_norm_email"], contacts_df["_norm_email"]])
        email_counts = all_emails.value_counts()
        
        normal_duplicates = []
        shared_usernames = {"info", "sales", "security", "support", "admin", "marketing", "office", "contact", "jobs", "careers"}
        for email, count in email_counts.items():
            if count > 1 and pd.notnull(email) and "@" in email:
                username = email.split("@")[0]
                if username not in shared_usernames:
                    normal_duplicates.append(email)
                    break
        
        if normal_duplicates:
            dup_email = normal_duplicates[0]
            # Check resolved master persons with this email
            resolved_rows = self.master_df[self.master_df["normalized_email"] == dup_email]
            
            # Assert they are merged into exactly ONE master person record
            self.assertEqual(len(resolved_rows), 1, 
                             f"Entities sharing a normal duplicate email ({dup_email}) must be consolidated into a single master person.")
            self.assertTrue(resolved_rows["duplicate_email_flag"].values[0])


if __name__ == "__main__":
    unittest.main()
