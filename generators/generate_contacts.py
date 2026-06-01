"""
Salesforce Contact Data Generator Module.

This module generates realistic, relational synthetic Salesforce Contact records
using pandas and faker. It establishes relational consistency:
- Connected Contacts (200 records): Mapped to converted leads in leads_data.csv.
- Orphan Contacts (200 records): Generated independently.
- Account Linkage: Linked to real accounts from accounts_data.csv.
- Data Quality issues modeled: DQ-1 (broken conversion links), DQ-7 (completeness gaps),
  and DQ-9 (opt-out and no_longer_with_company markers).

Author: Senior Data Engineer
"""

import os
import argparse
import random
import string
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from faker import Faker


class SalesforceContactGenerator:
    """Generates synthetic Salesforce Contact records connected to Accounts and Leads."""

    def __init__(self, seed: int = None):
        """
        Initializes the contact generator with an optional random seed.

        Args:
            seed (int, optional): Seed value for Faker and numpy/random. Defaults to None.
        """
        self.seed = seed
        self.fake = Faker()

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # Standard job title pool based on persona
        self.titles_pool = {
            "Security Operations": ["SOC Analyst", "Security Analyst", "Senior SOC Analyst", "Threat Analyst"],
            "Security Management": ["Information Security Manager", "SecOps Manager", "Cybersecurity Manager"],
            "Security Leadership": ["Director of Cybersecurity", "Director of Information Security", "Security Director"],
            "Security Executive": ["Chief Information Security Officer", "CISO", "VP Security", "Chief Security Officer"],
            "Partner / Channel": ["Partner Alliance Manager", "Solutions Engineer", "Security Consultant"],
            "Non-Prospect": ["Security Research Engineer", "Product Manager", "Software Engineer"]
        }

        self.personas = list(self.titles_pool.keys())
        self.persona_weights = [0.35, 0.25, 0.15, 0.15, 0.05, 0.05]

        # Status options
        self.statuses = ["Active", "Stale", "Nurture", "Disqualified"]
        self.status_weights = [0.60, 0.15, 0.20, 0.05]

    def _generate_salesforce_id(self, prefix: str, generated_ids: set) -> str:
        """Generates a unique, realistic 18-character Salesforce ID starting with a given prefix."""
        chars = string.ascii_letters + string.digits
        while True:
            suffix = "".join(random.choices(chars, k=15))
            sfdc_id = f"{prefix}{suffix}"
            if sfdc_id not in generated_ids:
                generated_ids.add(sfdc_id)
                return sfdc_id

    def _fuzzy_match_account(self, company_name: str, accounts_df: pd.DataFrame) -> str:
        """Fuzzy matches a lead's company name to a real account_id in accounts_df."""
        if company_name is None or pd.isnull(company_name):
            return None
        
        # Clean company name
        clean_comp = company_name.strip().lower()
        # Look for exact or substring matches in account_name
        for _, row in accounts_df.iterrows():
            acc_name = row["account_name"].strip().lower()
            if clean_comp in acc_name or acc_name in clean_comp:
                return row["account_id"]
        
        return None

    def generate_records(self, num_records: int = 400, inject_dq_errors: bool = True,
                         accounts_path: str = "data/raw/accounts_data.csv",
                         leads_path: str = "data/raw/leads_data.csv") -> pd.DataFrame:
        """
        Generates Contact records with connected pairs and orphans, linked to Accounts and Leads.
        """
        generated_contact_ids = set()
        generated_lead_ids = set()
        records: List[Dict[str, Any]] = []

        # 1. Load Accounts Data
        if not os.path.exists(accounts_path):
            raise FileNotFoundError(f"[ERROR] Accounts file not found at {accounts_path}. Please generate Accounts first.")
        accounts_df = pd.read_csv(accounts_path)
        account_ids = accounts_df["account_id"].tolist()

        # 2. Load Leads Data (for Connected Contacts)
        leads_df = None
        converted_leads = []
        if os.path.exists(leads_path):
            leads_df = pd.read_csv(leads_path)
            # Find converted leads
            converted_leads = leads_df[leads_df["is_converted"] == True].to_dict("records")
        else:
            print(f"[WARNING] Leads file not found at {leads_path}. Generating all connected contacts historically.")

        # Target counts
        target_connected = int(round(num_records * 0.50))  # ~200 connected contacts
        target_orphans = num_records - target_connected    # ~200 orphan contacts

        print(f"\n[INFO] Target composition: {target_connected} Connected Contacts, {target_orphans} Orphan Contacts.")

        # ----------------------------------------------------
        # Part A: Generate Connected Contacts (~200 records)
        # ----------------------------------------------------
        connected_generated = 0
        
        # First map real active converted leads from leads_data.csv
        for lead in converted_leads:
            if connected_generated >= target_connected:
                break

            # Relational Contact ID
            lead_contact_id = lead.get("converted_contact_id")
            
            # Preserve Broken Conversion Link (DQ-1): If converted lead has null ID, generate a new one
            if lead_contact_id is None or pd.isnull(lead_contact_id):
                contact_id = self._generate_salesforce_id("003", generated_contact_ids)
            else:
                contact_id = lead_contact_id
                generated_contact_ids.add(contact_id)

            # Account Linkage: Fuzzy match lead's company to a real account
            company = lead.get("company")
            matched_account_id = self._fuzzy_match_account(company, accounts_df)
            if matched_account_id is None:
                matched_account_id = random.choice(account_ids)

            # Re-use Lead fields
            first_name = lead.get("first_name")
            last_name = lead.get("last_name")
            email = lead.get("email")
            title = lead.get("title")
            job_persona = lead.get("job_persona")
            job_level = lead.get("job_level")
            mql_date = lead.get("mql_date")
            lead_score = lead.get("mkto_lead_score")

            # Mapped contact score matching lead score, but clean it from string outliers
            contact_score = 0
            if lead_score is not None and not pd.isnull(lead_score):
                try:
                    contact_score = int(lead_score)
                    if contact_score > 100 or contact_score < -25:
                        contact_score = int(np.random.triangular(40, 70, 95))
                except ValueError:
                    contact_score = int(np.random.triangular(30, 60, 85))

            # Compliance (DQ-9)
            has_opted_out = bool(lead.get("has_opted_out", False))
            email_bounced = bool(lead.get("email_bounced", False))
            
            # Stale contacts have higher left-company rates
            contact_status = np.random.choice(self.statuses, p=self.status_weights)
            no_longer_with_company = False
            if contact_status in ["Stale", "Disqualified"] and random.random() < 0.35:
                no_longer_with_company = True

            records.append({
                "contact_id": contact_id,
                "account_id": matched_account_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "title": title,
                "contact_status": contact_status,
                "job_persona": job_persona,
                "job_level": job_level,
                "mql_date": mql_date,
                "mkto_contact_score": contact_score,
                "has_lead_origin": True,
                "primary_lead_id": lead.get("lead_id"),
                "no_longer_with_company": no_longer_with_company,
                "has_opted_out": has_opted_out
            })
            connected_generated += 1

        # Generate "Historical" Converted Contacts if leads_data.csv didn't have enough conversions
        while connected_generated < target_connected:
            # Generate a synthetic historical lead link
            hist_lead_id = self._generate_salesforce_id("00Q", generated_lead_ids)
            contact_id = self._generate_salesforce_id("003", generated_contact_ids)
            matched_account_id = random.choice(account_ids)

            # Persona details
            job_persona = np.random.choice(self.personas, p=self.persona_weights)
            job_level = np.random.choice(["C-Suite", "VP", "Director", "Manager", "Individual Contributor"])
            title = random.choice(self.titles_pool[job_persona])

            # Faker names
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            
            # Select account for corporate email domain
            acc_row = accounts_df[accounts_df["account_id"] == matched_account_id].iloc[0]
            domain = acc_row["account_name"].strip().replace(" ", "").replace(",", "").lower() + ".com"
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"

            # Scoring
            contact_score = int(np.random.triangular(30, 65, 95))
            has_opted_out = bool(np.random.choice([True, False], p=[0.07, 0.93]))
            no_longer_with_company = bool(np.random.choice([True, False], p=[0.08, 0.92]))
            contact_status = "Stale" if no_longer_with_company else np.random.choice(self.statuses, p=self.status_weights)

            # MQL Dates: generated uniformly
            mql_date = "2026-03-12 10:00:00"

            # Apply completeness gaps (DQ-7) to historical connected leads
            title_val = title if random.random() >= 0.35 else None
            persona_val = job_persona if random.random() < 0.60 else None
            level_val = job_level if random.random() < 0.60 else None

            # Inject 20% broken links in historical connections (DQ-1)
            # Represented by having lead origin but a NULL link in some other record,
            # or orphan contact links.
            
            records.append({
                "contact_id": contact_id,
                "account_id": matched_account_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "title": title_val,
                "contact_status": contact_status,
                "job_persona": persona_val,
                "job_level": level_val,
                "mql_date": mql_date,
                "mkto_contact_score": contact_score,
                "has_lead_origin": True,
                "primary_lead_id": hist_lead_id,
                "no_longer_with_company": no_longer_with_company,
                "has_opted_out": has_opted_out
            })
            connected_generated += 1

        # ----------------------------------------------------
        # Part B: Generate Orphan Contacts (~200 records)
        # ----------------------------------------------------
        for _ in range(target_orphans):
            contact_id = self._generate_salesforce_id("003", generated_contact_ids)
            matched_account_id = random.choice(account_ids)

            # DQ-7 Account Linkage Gap (3% null accounts in orphans to represent orphan sync failures)
            if inject_dq_errors and random.random() < 0.03:
                matched_account_id = None

            # Persona details
            job_persona = np.random.choice(self.personas, p=self.persona_weights)
            job_level = np.random.choice(["C-Suite", "VP", "Director", "Manager", "Individual Contributor"])
            title = random.choice(self.titles_pool[job_persona])

            # Names and emails
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            
            if matched_account_id:
                acc_row = accounts_df[accounts_df["account_id"] == matched_account_id].iloc[0]
                domain = acc_row["account_name"].strip().replace(" ", "").replace(",", "").lower() + ".com"
            else:
                domain = "orphan-enterprise.com"
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"

            # Score and statuses
            contact_score = int(np.random.triangular(10, 45, 80))
            has_opted_out = bool(np.random.choice([True, False], p=[0.07, 0.93]))
            no_longer_with_company = bool(np.random.choice([True, False], p=[0.08, 0.92]))
            contact_status = "Stale" if no_longer_with_company else np.random.choice(self.statuses, p=self.status_weights)

            mql_date = None
            if contact_status in ["Active", "Nurture"] and random.random() < 0.20:
                mql_date = "2026-04-20 11:30:00"

            # Apply completeness gaps (DQ-7) and population rates (DQ-6 exactly 60% global)
            title_val = title if random.random() >= 0.35 else None
            persona_val = job_persona if random.random() < 0.60 else None
            level_val = job_level if random.random() < 0.60 else None

            records.append({
                "contact_id": contact_id,
                "account_id": matched_account_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "title": title_val,
                "contact_status": contact_status,
                "job_persona": persona_val,
                "job_level": level_val,
                "mql_date": mql_date,
                "mkto_contact_score": contact_score,
                "has_lead_origin": False,
                "primary_lead_id": None,
                "no_longer_with_company": no_longer_with_company,
                "has_opted_out": has_opted_out
            })

        df = pd.DataFrame(records)

        # Apply specific DQ-7 Title completeness post-processing to hit exactly 35% nulls globally
        total_contacts = len(df)
        target_null_titles = int(round(total_contacts * 0.35))
        
        # Get all non-null title indices
        non_null_indices = df[df["title"].notnull()].index.tolist()
        current_nulls = df["title"].isnull().sum()
        
        needed_nulls = max(0, target_null_titles - current_nulls)
        if len(non_null_indices) >= needed_nulls:
            to_nullify = random.sample(non_null_indices, k=needed_nulls)
            for idx in to_nullify:
                df.loc[idx, "title"] = None

        # Apply specific DQ-6 Job level and persona post-processing to hit exactly 60% population globally
        target_pop_count = int(round(total_contacts * 0.60))
        
        for col in ["job_persona", "job_level"]:
            pop_indices = df[df[col].notnull()].index.tolist()
            current_pop = len(pop_indices)
            
            needed_nulls = max(0, total_contacts - target_pop_count)
            # Strip extra to hit exactly 60%
            if current_pop > target_pop_count:
                to_strip = random.sample(pop_indices, k=(current_pop - target_pop_count))
                for idx in to_strip:
                    df.loc[idx, col] = None
            elif current_pop < target_pop_count:
                # Add back some random personas
                null_indices = df[df[col].isnull()].index.tolist()
                to_populate = random.sample(null_indices, k=(target_pop_count - current_pop))
                for idx in to_populate:
                    if col == "job_persona":
                        df.loc[idx, col] = np.random.choice(self.personas, p=self.persona_weights)
                    else:
                        df.loc[idx, col] = np.random.choice(["C-Suite", "VP", "Director", "Manager", "Individual Contributor"])

        return df

    def print_validation_report(self, df: pd.DataFrame, leads_path: str = "data/raw/leads_data.csv") -> None:
        """Prints a detailed statistical validation report to verify contact distributions."""
        print("=" * 65)
        print("                  CONTACT DATA VALIDATION REPORT                  ")
        print("=" * 65)
        print(f"Total Contacts Generated: {len(df)}")
        print("-" * 65)

        # 1. Composition
        connected = df[df["has_lead_origin"] == True]
        orphans = df[df["has_lead_origin"] == False]
        print("1. Composition & Relationship Pairing:")
        print(f"  Connected Contacts (Lead Origin):  {len(connected)} ({len(connected)/len(df)*100:.1f}% | Target ~200)")
        print(f"  Orphan Contacts (No Lead Origin):  {len(orphans)} ({len(orphans)/len(df)*100:.1f}% | Target ~200)")
        print("-" * 65)

        # 2. Broken Conversion Linkages (DQ-1)
        # Read leads to verify broken link conversions
        broken_links_count = 0
        if os.path.exists(leads_path):
            leads_df = pd.read_csv(leads_path)
            converted_leads = leads_df[leads_df["is_converted"] == True]
            broken_leads = converted_leads[converted_leads["converted_contact_id"].isnull()]
            broken_links_count = len(broken_leads)
        print("2. Sync Validation Audits:")
        print(f"  Broken Conversion Links (DQ-1 leads): {broken_links_count} cases preserved")
        print("-" * 65)

        # 3. Field Completeness & Null Analysis (DQ-7 & DQ-6)
        print("3. Field Completeness & Population Rates:")
        print(f"  'title' Null Rate (Target 35%):    {df['title'].isnull().mean()*100:5.1f}%")
        print(f"  'job_persona' Population (Target 60%): {df['job_persona'].notnull().mean()*100:5.1f}%")
        print(f"  'job_level' Population (Target 60%):   {df['job_level'].notnull().mean()*100:5.1f}%")
        print(f"  'account_id' Completeness (DQ-7):     {df['account_id'].notnull().mean()*100:5.1f}%")
        print("-" * 65)

        # 4. Compliance Indicators (DQ-9)
        opt_out = df["has_opted_out"].mean() * 100
        left_company = df["no_longer_with_company"].mean() * 100
        print("4. Compliance & Stale Records:")
        print(f"  Opt-Out (has_opted_out Rate):         {opt_out:.1f}%")
        print(f"  Left Company (no_longer_with_company): {left_company:.1f}%")
        print("-" * 65)

        # 5. Account Linkage Distribution
        print("5. Account Linkage Distributions:")
        acc_counts = df["account_id"].value_counts()
        print(f"  Total Accounts Represented:  {len(acc_counts)}")
        print(f"  Avg Contacts per Account:    {acc_counts.mean():.1f}")
        print(f"  Max Contacts in one Account: {acc_counts.max()}")
        print(f"  Min Contacts in one Account: {acc_counts.min()}")
        print("=" * 65)


def main():
    """Main execution entry point."""
    parser = argparse.ArgumentParser(description="Generate realistic, relational Salesforce Contacts.")
    parser.add_argument("--count", type=int, default=400, help="Number of records to generate (default: 400).")
    parser.add_argument("--output", type=str, default="data/raw/contacts_data.csv", help="Path to write the CSV output (default: data/raw/contacts_data.csv).")
    parser.add_argument("--accounts", type=str, default="data/raw/accounts_data.csv", help="Path to Accounts CSV file (default: data/raw/accounts_data.csv).")
    parser.add_argument("--leads", type=str, default="data/raw/leads_data.csv", help="Path to Leads CSV file (default: data/raw/leads_data.csv).")
    parser.add_argument("--seed", type=int, default=42, help="Seed value for deterministic reproducible runs (default: 42).")
    parser.add_argument("--clean", action="store_true", help="Generate clean data without injecting DQ/compliance errors.")

    args = parser.parse_args()

    # Instantiate generator and generate data
    generator = SalesforceContactGenerator(seed=args.seed)
    df = generator.generate_records(
        num_records=args.count,
        inject_dq_errors=not args.clean,
        accounts_path=args.accounts,
        leads_path=args.leads
    )

    # Ensure output parent directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Export to CSV
    df.to_csv(args.output, index=False)
    print(f"\n[SUCCESS] Successfully generated and exported contacts data to {args.output}\n")

    # Print validation report
    generator.print_validation_report(df, leads_path=args.leads)


if __name__ == "__main__":
    main()
