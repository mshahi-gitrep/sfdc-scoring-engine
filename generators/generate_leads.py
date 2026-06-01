"""
Salesforce Lead Data Generator Module (generators package).

This module generates realistic, highly correlated, and persona-driven synthetic 
Salesforce Lead records using pandas and faker. It simulates complex CRM dynamics:
- Persona distribution driving engagement, conversion rates, and lead scores.
- Messy company names representing raw inbound web/form capture quality.
- Deliberate injection of real-world Data Quality (DQ) anomalies (DQ-1, DQ-2, DQ-4, DQ-6, DQ-7, DQ-9).
- Explicit injection of 8 deterministic archetype personas (A-H).

"""

import os
import argparse
import random
import string
import datetime
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from faker import Faker


class SalesforceLeadGenerator:
    """Generates synthetic, persona-driven Salesforce Lead records with realistic noise."""

    def __init__(self, seed: int = None):
        """
        Initializes the lead generator with an optional random seed for reproducibility.

        Args:
            seed (int, optional): Seed value for Faker and numpy/random. Defaults to None.
        """
        self.seed = seed
        self.fake = Faker()
        
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # 1. Persona definitions and their target weights (must sum to 1.0)
        self.persona_weights = {
            "Security Analyst": 0.30,
            "Security Manager": 0.25,
            "Security Director": 0.15,
            "VP Security": 0.10,
            "CISO": 0.05,
            "Competitor Employee": 0.05,
            "Vendor Employee": 0.05,
            "Partner Contact": 0.05
        }
        self.personas = list(self.persona_weights.keys())
        self.weights = list(self.persona_weights.values())

        # 2. Map personas to standard Salesforce Job Levels and Job Personas
        self.persona_mapping = {
            "Security Analyst": ("Security Operations", "Individual Contributor"),
            "Security Manager": ("Security Management", "Manager"),
            "Security Director": ("Security Leadership", "Director"),
            "VP Security": ("Security Executive", "VP"),
            "CISO": ("Security Executive", "C-Suite"),
            "Competitor Employee": ("Non-Prospect", "Individual Contributor"),
            "Vendor Employee": ("Non-Prospect", "Manager"),
            "Partner Contact": ("Partner / Channel", "Manager")
        }

        # 3. Mapped title generation libraries per persona
        self.titles_pool = {
            "Security Analyst": [
                "Security Analyst", "Senior Security Analyst", "SOC Analyst", 
                "Cyber Security Analyst", "Information Security Analyst", "Threat Intelligence Analyst"
            ],
            "Security Manager": [
                "Security Operations Manager", "Information Security Manager", 
                "Cyber Security Manager", "IT Security Manager", "SecOps Manager"
            ],
            "Security Director": [
                "Director of Information Security", "Director of Cybersecurity", 
                "Director Security Operations", "Information Security Director"
            ],
            "VP Security": [
                "VP of Information Security", "Vice President Security", 
                "VP Cybersecurity", "Vice President Information Security"
            ],
            "CISO": [
                "Chief Information Security Officer", "CISO", "Chief Security Officer", "VP & CISO"
            ],
            "Competitor Employee": [
                "Security Engineer", "Product Manager", "Security Researcher", "Developer"
            ],
            "Vendor Employee": [
                "Account Executive", "Recruiter", "Customer Success Manager", "Sales Engineer"
            ],
            "Partner Contact": [
                "Partner Alliance Manager", "Solutions Engineer", "Security Consultant"
            ]
        }

        # 4. Target lead source options
        self.sources = ["Webinar", "Direct Inbound", "Paid Search", "Enterprise Event", "Executive Dinner", "Cold Outreach", "Referral"]
        
        # 5. Core industries for completeness gaps
        self.industries = ["Technology", "Cybersecurity", "Finance", "Energy", "Healthcare", "Manufacturing", "Retail", "Education"]

    def _generate_salesforce_id(self, prefix: str, generated_ids: set) -> str:
        """Generates a unique, realistic 18-character Salesforce ID starting with a given prefix."""
        chars = string.ascii_letters + string.digits
        while True:
            suffix = "".join(random.choices(chars, k=15))
            sfdc_id = f"{prefix}{suffix}"
            if sfdc_id not in generated_ids:
                generated_ids.add(sfdc_id)
                return sfdc_id

    def _make_company_name_messy(self, company_name: str) -> str:
        """Applies realistic human data-entry noise to a clean company name."""
        noise_roll = random.random()
        if noise_roll < 0.08:
            return company_name.lower()
        elif noise_roll < 0.15:
            return company_name.upper()
        elif noise_roll < 0.35:
            for suffix in [" Inc.", " Inc", " LLC", " Group", " Corp.", " Corp", " and Sons"]:
                if company_name.endswith(suffix):
                    company_name = company_name[:-len(suffix)]
                    break
            return company_name
        elif noise_roll < 0.40:
            if len(company_name) > 4:
                idx = random.randint(1, len(company_name) - 2)
                company_name = company_name[:idx] + company_name[idx+1] + company_name[idx] + company_name[idx+2:]
            return company_name
        elif noise_roll < 0.45:
            return company_name + "  "
        return company_name

    def _inject_deterministic_archetypes(self, generated_lead_ids: set, generated_contact_ids: set) -> List[Dict[str, Any]]:
        """Injects the exactly 8 required deterministic archetype personas (A-H) from PROJECT_REQUIREMENTS.md."""
        archetypes = []
        
        # Archetype A
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "sarah.security@strategiccorp.com",
            "first_name": "Sarah",
            "last_name": "Security",
            "title": "VP of Information Security",
            "company": "Strategic Enterprise Corp",
            "job_persona": "Security Executive",
            "job_level": "VP",
            "lead_status": "SQL",
            "lead_source": "Enterprise Event",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 85,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-019-2831",
            "industry": "Technology",
            "true_entry_date": "2026-05-10 14:32:00",
            "created_date": "2026-05-10 14:32:00",
            "mql_date": "2026-05-12 09:12:00",  # Added MQL Date for SQL lead
            "_persona": "VP Security",
            "_archetype": "A"
        })

        # Archetype B
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "robert.stale@dormantbusiness.com",
            "first_name": "Robert",
            "last_name": "Stale",
            "title": "VP Security",
            "company": "Dormant Business Inc",
            "job_persona": "Security Executive",
            "job_level": "VP",
            "lead_status": "Open",
            "lead_source": "Cold Outreach",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 20,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-021-9988",
            "industry": "Manufacturing",
            "true_entry_date": "2025-11-15 09:15:00",  # 6+ months ago
            "created_date": "2025-11-15 09:15:00",
            "mql_date": None,
            "_persona": "VP Security",
            "_archetype": "B"
        })

        # Archetype C
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "alex.analyst@activeoperations.com",
            "first_name": "Alex",
            "last_name": "Analyst",
            "title": "SOC Analyst",
            "company": "Active Operations Ltd",
            "job_persona": "Security Operations",
            "job_level": "Individual Contributor",
            "lead_status": "MQL",
            "lead_source": "Webinar",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 70,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-045-6677",
            "industry": "Cybersecurity",
            "true_entry_date": "2026-05-25 16:45:00",
            "created_date": "2026-05-25 16:45:00",
            "mql_date": "2026-05-26 10:30:00",  # Added MQL Date for MQL lead
            "_persona": "Security Analyst",
            "_archetype": "C"
        })

        # Archetype D
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "charles.ciso@megaenterprise.com",
            "first_name": "Charles",
            "last_name": "Ciso",
            "title": "Chief Information Security Officer",
            "company": "Mega Enterprise Corp",
            "job_persona": "Security Executive",
            "job_level": "C-Suite",
            "lead_status": "Nurture",
            "lead_source": "Purchased List",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 10,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-099-1234",
            "industry": "Finance",
            "true_entry_date": "2026-05-01 08:00:00",
            "created_date": "2026-05-01 08:00:00",
            "mql_date": None,
            "_persona": "CISO",
            "_archetype": "D"
        })

        # Archetype E
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "craig.competitor@competitorsec.com",
            "first_name": "Craig",
            "last_name": "Competitor",
            "title": "Security Research Engineer",
            "company": "Competitor Inc",
            "job_persona": "Non-Prospect",
            "job_level": "Individual Contributor",
            "lead_status": "Disqualified",
            "lead_source": "Webinar",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 5,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-001-9999",
            "industry": "Technology",
            "true_entry_date": "2026-05-28 11:20:00",
            "created_date": "2026-05-28 11:20:00",
            "mql_date": None,
            "_persona": "Competitor Employee",
            "_archetype": "E"
        })

        # Archetype F
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "fiona.optout@standardbusiness.com",
            "first_name": "Fiona",
            "last_name": "Optout",
            "title": "Cybersecurity Manager",
            "company": "Standard Business Inc",
            "job_persona": "Security Management",
            "job_level": "Manager",
            "lead_status": "Open",
            "lead_source": "Webinar",
            "has_opted_out": True,
            "email_bounced": False,
            "mkto_lead_score": 65,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-055-7766",
            "industry": "Retail",
            "true_entry_date": "2026-05-29 15:10:00",
            "created_date": "2026-05-29 15:10:00",
            "mql_date": None,
            "_persona": "Security Manager",
            "_archetype": "F"
        })

        # Archetype G (Broken Conversion Link Case)
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "george.broken@megaenterprise.com",
            "first_name": "George",
            "last_name": "Broken",
            "title": "Director of Cybersecurity",
            "company": "Mega Enterprise Corp",
            "job_persona": "Security Leadership",
            "job_level": "Director",
            "lead_status": "Converted",
            "lead_source": "Enterprise Event",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 75,
            "is_converted": True,
            "converted_contact_id": None,  # Forced DQ-1 converted but broken link
            "phone": "555-077-4433",
            "industry": "Finance",
            "true_entry_date": "2026-04-12 10:05:00",
            "created_date": "2026-04-12 10:05:00",
            "mql_date": "2026-04-15 14:22:00",  # Added MQL Date for Converted lead
            "_persona": "Security Director",
            "_archetype": "G"
        })

        # Archetype H
        archetypes.append({
            "lead_id": self._generate_salesforce_id("00Q", generated_lead_ids),
            "email": "henry.inflated@standardbusiness.com",
            "first_name": "Henry",
            "last_name": "Inflated",
            "title": "SOC Analyst",
            "company": "Standard Business Inc",
            "job_persona": "Security Operations",
            "job_level": "Individual Contributor",
            "lead_status": "Open",
            "lead_source": "Cold Outreach",
            "has_opted_out": False,
            "email_bounced": False,
            "mkto_lead_score": 95,
            "is_converted": False,
            "converted_contact_id": None,
            "phone": "555-088-2211",
            "industry": "Education",
            "true_entry_date": "2026-05-18 13:50:00",
            "created_date": "2026-05-18 13:50:00",
            "mql_date": None,
            "_persona": "Security Analyst",
            "_archetype": "H"
        })

        return archetypes

    def generate_records(self, num_records: int = 600, inject_dq_errors: bool = True) -> pd.DataFrame:
        """
        Generates a list of Lead records driven by personas, including DQ anomalies and explicit archetypes.

        Args:
            num_records (int): Total leads to generate. Defaults to 600.
            inject_dq_errors (bool): If True, will inject real-world Data Quality violations.

        Returns:
            pd.DataFrame: Pandas DataFrame containing the generated Leads.
        """
        generated_lead_ids = set()
        generated_contact_ids = set()
        
        # 1. Inject exactly 8 deterministic archetypes first
        records = self._inject_deterministic_archetypes(generated_lead_ids, generated_contact_ids)
        
        # Remaining counts to generate
        rem_count = num_records - len(records)
        
        # Reference time range for random creation dates: last 180 days
        end_date = datetime.datetime.now()
        
        for _ in range(rem_count):
            # Select Persona
            persona = np.random.choice(self.personas, p=self.weights)
            job_persona_val, job_level_val = self.persona_mapping[persona]

            lead_id = self._generate_salesforce_id("00Q", generated_lead_ids)

            # Title: 35% null globally
            title = None
            if random.random() >= 0.35:
                title = random.choice(self.titles_pool[persona])

            # Messy Company Name
            company = self._make_company_name_messy(self.fake.company())

            # E-mail generation
            clean_company = company.strip().replace(" ", "").replace(",", "").lower()
            if not clean_company:
                clean_company = "enterprise"
            
            if persona == "Competitor Employee":
                domain = "competitorsec.com"
            elif persona == "Vendor Employee":
                domain = "vendorsystems.com"
            elif persona == "Partner Contact":
                domain = "partnerconsulting.com"
            else:
                domain = f"{clean_company}.com"
                if random.random() < 0.10:
                    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com"])

            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"

            # Job Persona & Job Level (Reduced to exactly 60% population)
            job_persona = job_persona_val if random.random() < 0.60 else None
            job_level = job_level_val if random.random() < 0.60 else None

            # Sourcing attribution weights
            if persona in ["CISO", "VP Security"]:
                source_weights = [0.10, 0.15, 0.10, 0.25, 0.30, 0.05, 0.05]
            elif persona in ["Security Director", "Security Manager"]:
                source_weights = [0.25, 0.20, 0.20, 0.20, 0.05, 0.05, 0.05]
            elif persona == "Security Analyst":
                source_weights = [0.45, 0.20, 0.20, 0.05, 0.00, 0.08, 0.02]
            else:
                source_weights = [0.35, 0.15, 0.25, 0.05, 0.00, 0.20, 0.00]
            lead_source = np.random.choice(self.sources, p=source_weights)

            # Phone (Completeness gap: 25% null)
            phone = None
            if random.random() >= 0.25:
                phone = self.fake.phone_number()

            # Industry (Completeness gap: 20% null)
            industry = None
            if random.random() >= 0.20:
                # Align standard prospects with target lists, others random
                if persona in ["CISO", "VP Security", "Security Director", "Security Manager", "Security Analyst"]:
                    industry = np.random.choice(["Cybersecurity", "Technology", "Finance"], p=[0.50, 0.30, 0.20])
                else:
                    industry = np.random.choice(self.industries)

            # Opt-out & bounce rates
            has_opted_out = bool(np.random.choice([True, False], p=[0.07, 0.93]))
            email_bounced = bool(np.random.choice([True, False], p=[0.04, 0.96]))

            # Marketo Lead Score base score
            if persona in ["CISO", "VP Security"]:
                score = int(np.random.triangular(65, 88, 100))
            elif persona in ["Security Director", "Security Manager"]:
                score = int(np.random.triangular(45, 70, 95))
            elif persona == "Security Analyst":
                score = int(np.random.triangular(15, 40, 75))
            elif persona in ["Competitor Employee", "Vendor Employee"]:
                score = int(np.random.triangular(-20, -5, 10))
            else:
                score = int(np.random.triangular(20, 45, 70))

            # Conversion Rates
            is_converted = False
            conversion_bypass_compliance = False
            
            can_convert = not (has_opted_out or email_bounced)
            if inject_dq_errors and (has_opted_out or email_bounced) and random.random() < 0.20:
                can_convert = True
                conversion_bypass_compliance = True

            if can_convert:
                if persona in ["CISO", "VP Security"]:
                    is_converted = bool(np.random.choice([True, False], p=[0.35, 0.65]))
                elif persona in ["Security Director", "Security Manager"]:
                    is_converted = bool(np.random.choice([True, False], p=[0.22, 0.78]))
                elif persona == "Security Analyst":
                    is_converted = bool(np.random.choice([True, False], p=[0.08, 0.92]))
                elif persona == "Partner Contact":
                    is_converted = bool(np.random.choice([True, False], p=[0.05, 0.95]))

            if is_converted:
                lead_status = "Converted"
            elif persona in ["Competitor Employee", "Vendor Employee"]:
                lead_status = np.random.choice(["Disqualified", "Nurture"], p=[0.85, 0.15])
            else:
                lead_status = np.random.choice(["Open", "Working", "MQL", "SQL", "Nurture"], p=[0.20, 0.40, 0.20, 0.10, 0.10])

            # Dates: Generate a true entry date in last 180 days
            days_ago = random.randint(0, 180)
            true_dt = end_date - datetime.timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            true_entry_date_str = true_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Standard MQL Date
            mql_date_str = None
            if lead_status in ["MQL", "SQL", "Converted"]:
                mql_days = random.randint(0, 20)
                mql_dt = true_dt + datetime.timedelta(days=mql_days, hours=random.randint(0, 12))
                if mql_dt > end_date:
                    mql_dt = end_date
                mql_date_str = mql_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Converted Contact ID
            converted_contact_id = None
            if is_converted:
                converted_contact_id = self._generate_salesforce_id("003", generated_contact_ids)

            # Injected anomalies for DQ-3, DQ-5
            if inject_dq_errors:
                # DQ-3: MQL Date milestone anomalies
                if lead_status in ["MQL", "SQL", "Converted"]:
                    if random.random() < 0.05:
                        mql_date_str = None
                else:
                    if random.random() < 0.02:
                        err_dt = true_dt + datetime.timedelta(days=2)
                        mql_date_str = err_dt.strftime("%Y-%m-%d %H:%M:%S")

                # DQ-5: Marketo Score missing or out of bounds
                dq5_roll = random.random()
                if dq5_roll < 0.03:
                    score_val = None
                elif dq5_roll < 0.04:
                    score_val = 9999
                elif dq5_roll < 0.05:
                    score_val = "N/A"
                else:
                    score_val = score
            else:
                score_val = score

            if not inject_dq_errors or not conversion_bypass_compliance:
                if (has_opted_out or email_bounced) and is_converted:
                    is_converted = False
                    lead_status = "Disqualified"
                    converted_contact_id = None

            records.append({
                "lead_id": lead_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "title": title,
                "company": company,
                "job_persona": job_persona,
                "job_level": job_level,
                "lead_status": lead_status,
                "lead_source": lead_source,
                "created_date": true_entry_date_str,  # Will be overridden by DQ-4 bulk timestamps
                "mql_date": mql_date_str,
                "mkto_lead_score": score_val,
                "is_converted": is_converted,
                "converted_contact_id": converted_contact_id,
                "has_opted_out": has_opted_out,
                "email_bounced": email_bounced,
                "phone": phone,
                "industry": industry,
                "true_entry_date": true_entry_date_str,  # Preserved internally for validation
                "_persona": persona,
                "_archetype": None
            })

        df = pd.DataFrame(records)

        # ----------------------------------------------------
        # DQ-1: broken links (exactly 20% of converted leads)
        # ----------------------------------------------------
        if inject_dq_errors:
            # Get indices of all converted leads
            converted_indices = df[df["is_converted"]].index.tolist()
            # Archetype G is pre-configured as a broken conversion link. Let's handle the rest dynamically
            non_arch_converted_indices = [idx for idx in converted_indices if df.loc[idx, "_archetype"] != 'G']
            
            # Target count: exactly 20% of all converted leads must be NULL
            total_converted = len(converted_indices)
            target_broken_count = int(round(total_converted * 0.20))
            
            # Since Archetype G is already broken, we need to break (target_broken_count - 1) more records
            additional_to_break = max(0, target_broken_count - 1)
            
            if len(non_arch_converted_indices) >= additional_to_break:
                broken_choices = random.sample(non_arch_converted_indices, k=additional_to_break)
                for idx in broken_choices:
                    df.loc[idx, "converted_contact_id"] = None
            else:
                # Fail-safe backup
                for idx in non_arch_converted_indices:
                    df.loc[idx, "converted_contact_id"] = None
        else:
            # Clean mode: Fix Archetype G broken link to be clean
            g_idx = df[df["_archetype"] == 'G'].index
            if len(g_idx) > 0:
                df.loc[g_idx[0], "converted_contact_id"] = self._generate_salesforce_id("003", generated_contact_ids)

        # ----------------------------------------------------
        # DQ-4: ETL bulk load created dates (exactly 80% override)
        # ----------------------------------------------------
        if inject_dq_errors:
            etl_timestamp = "2026-05-15 03:00:00"
            # Target: exactly 80% of leads receive this timestamp
            total_leads = len(df)
            target_etl_count = int(round(total_leads * 0.80))
            
            # Randomly select exactly 80% of rows (keeping archetypes' true_entry_date intact if they aren't sampled,
            # or include them. We just select randomly across all indices)
            all_indices = list(range(total_leads))
            etl_indices = random.sample(all_indices, k=target_etl_count)
            
            for idx in etl_indices:
                df.loc[idx, "created_date"] = etl_timestamp

        # ----------------------------------------------------
        # DQ-2: Email Duplication (10-15% target duplicate emails)
        # ----------------------------------------------------
        if inject_dq_errors:
            # We want to achieve exactly e.g. 12% duplicated email addresses in the final dataset.
            # 12% of 600 records = 72 records with duplicated emails.
            # Let's create duplicates post-generation by selecting clean records and overriding their emails.
            # Total unique emails should be around 530, duplicates around 70.
            
            # Identify indices to duplicate
            # Avoid changing the 8 core archetypes to preserve their clean setups
            duplicatable_indices = df[df["_archetype"].isnull()].index.tolist()
            
            # 1. 2% High-Cardinality Clusters (exactly 2 clusters of 6 records each = 12 duplicate records)
            # We will pick 2 random target emails and apply them to 5 other records each
            if len(duplicatable_indices) >= 12:
                # Cluster 1: security@highintent.com
                cluster1_target_email = "security@highintent.com"
                cluster1_indices = duplicatable_indices[:6]
                for idx in cluster1_indices:
                    df.loc[idx, "email"] = cluster1_target_email
                
                # Cluster 2: info@megacorp.com
                cluster2_target_email = "info@megacorp.com"
                cluster2_indices = duplicatable_indices[6:12]
                for idx in cluster2_indices:
                    df.loc[idx, "email"] = cluster2_target_email
                
                # Remove them from our remaining duplicatable pool
                duplicatable_indices = duplicatable_indices[12:]

            # 2. Shared Mailboxes (e.g. info@, sales@, security@ on existing domains)
            # Pick 20 records and update their emails to be shared company aliases
            if len(duplicatable_indices) >= 20:
                shared_choices = duplicatable_indices[:20]
                for idx in shared_choices:
                    curr_email = df.loc[idx, "email"]
                    if "@" in curr_email:
                        domain = curr_email.split("@")[1]
                        prefix = random.choice(["info", "sales", "security"])
                        df.loc[idx, "email"] = f"{prefix}@{domain}"
                
                duplicatable_indices = duplicatable_indices[20:]

            # 3. Duplicate Prospects (Same name and email, simulating double form submissions)
            # Pick 60 base records, duplicate them (same email, first_name, last_name)
            # To simulate submission time lag, keep the duplicated emails and names, but different status/created_date
            if len(duplicatable_indices) >= 120:
                # We take 60 pairs (60 source rows, 60 target rows)
                source_rows = duplicatable_indices[:60]
                target_rows = duplicatable_indices[60:120]
                
                for src_idx, tgt_idx in zip(source_rows, target_rows):
                    df.loc[tgt_idx, "email"] = df.loc[src_idx, "email"]
                    df.loc[tgt_idx, "first_name"] = df.loc[src_idx, "first_name"]
                    df.loc[tgt_idx, "last_name"] = df.loc[src_idx, "last_name"]
                    # Add different dates or statuses to represent dirty duplicates
                    df.loc[tgt_idx, "lead_status"] = np.random.choice(["Open", "Working", "Nurture"])

        return df

    def print_validation_report(self, df: pd.DataFrame) -> None:
        """Prints a detailed statistical validation report to verify lead distributions."""
        print("=" * 65)
        print("                   LEAD DATA VALIDATION REPORT                    ")
        print("=" * 65)
        print(f"Total Leads Generated: {len(df)}")
        print("-" * 65)

        # 1. Persona Distribution
        print("1. Target Persona Distributions:")
        counts = df["_persona"].value_counts()
        for persona, count in counts.items():
            pct = count / len(df) * 100
            target_pct = self.persona_weights[persona] * 100
            print(f"  {persona:<20}: {count:3d} ({pct:5.1f}%) | Target: {target_pct:4.1f}%")
        print("-" * 65)

        # 2. Score Metrics by Persona
        print("2. Score Metrics by Persona:")
        score_series = pd.to_numeric(df["mkto_lead_score"], errors="coerce")
        for persona in self.personas:
            p_scores = score_series[df["_persona"] == persona].dropna()
            avg = p_scores.mean() if len(p_scores) > 0 else float('nan')
            med = p_scores.median() if len(p_scores) > 0 else float('nan')
            print(f"  {persona:<20}: Mean Score = {avg:5.1f} | Median Score = {med:5.1f}")
        print("-" * 65)

        # 3. Conversion Rates
        print("3. Conversion Rates by Persona:")
        for persona in self.personas:
            p_df = df[df["_persona"] == persona]
            conv_pct = p_df["is_converted"].mean() * 100
            print(f"  {persona:<20}: Converted Rate = {conv_pct:5.1f}%")
        print("-" * 65)

        # 4. Field Completeness & Null Analysis
        print("4. Field Completeness & Null Analysis:")
        print(f"  'title' Null Rate (Target 35%):    {df['title'].isnull().mean()*100:5.1f}%")
        print(f"  'job_persona' Population Rate (Target 60%): {df['job_persona'].notnull().mean()*100:5.1f}%")
        print(f"  'job_level' Population Rate (Target 60%):   {df['job_level'].notnull().mean()*100:5.1f}%")
        print(f"  'phone' Population Rate (Target 75%):       {df['phone'].notnull().mean()*100:5.1f}%")
        print(f"  'industry' Population Rate (Target 80%):    {df['industry'].notnull().mean()*100:5.1f}%")
        print("-" * 65)

        # 5. Data Quality (DQ) Anomalies Count
        print("5. Injected Data Quality (DQ) Anomalies:")
        
        # DQ-1 Converted Contact ID
        converted_leads = df[df["is_converted"]]
        total_conv = len(converted_leads)
        dq1_broken = converted_leads["converted_contact_id"].isnull().sum()
        dq1_pct = (dq1_broken / total_conv * 100) if total_conv > 0 else 0.0
        print(f"  DQ-1 (Broken conversion links):   Null Contact IDs = {dq1_broken} / {total_conv} Converted ({dq1_pct:.1f}% | Target 20%)")

        # DQ-2 Email Duplication
        duplicate_emails = df["email"].duplicated().sum()
        dup_pct = duplicate_emails / len(df) * 100
        # High-cardinality clusters
        high_card_megacorp = (df["email"] == "info@megacorp.com").sum()
        high_card_highintent = (df["email"] == "security@highintent.com").sum()
        print(f"  DQ-2 (Email duplications):         Total Duplicated Emails = {duplicate_emails} ({dup_pct:.1f}% | Target 10-15%)")
        print(f"                                     Cluster Megacorp Size = {high_card_megacorp} | Cluster HighIntent Size = {high_card_highintent}")

        # DQ-4 ETL Dominated dates
        etl_count = (df["created_date"] == "2026-05-15 03:00:00").sum()
        etl_pct = etl_count / len(df) * 100
        print(f"  DQ-4 (ETL-dominated dates):        Bulk ETL override = {etl_count} ({etl_pct:.1f}% | Target 80%)")

        # DQ-9 Compliance leakage
        opt_or_bounce = df["has_opted_out"] | df["email_bounced"]
        dq9_compliance_leak = df[opt_or_bounce & df["is_converted"]]
        print(f"  DQ-9 (Compliance leakages):        Opted-out/Bounced Leads that Converted = {len(dq9_compliance_leak)}")

        # 6. Archetypes Verification
        print("-" * 65)
        print("6. Deterministic Archetypes Injection Verification:")
        for arch in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            row = df[df["_archetype"] == arch]
            if len(row) > 0:
                name = f"{row['first_name'].values[0]} {row['last_name'].values[0]}"
                score_val = row['mkto_lead_score'].values[0]
                status = row['lead_status'].values[0]
                conv = row['is_converted'].values[0]
                contact_id = row['converted_contact_id'].values[0]
                print(f"  Persona {arch}: {name:<15} | Score: {score_val:<4} | Status: {status:<11} | Converted: {conv!s:<5} | Contact ID: {contact_id}")
        print("=" * 65)


def main():
    """Main execution entry point."""
    parser = argparse.ArgumentParser(description="Generate realistic, persona-driven Salesforce Leads.")
    parser.add_argument("--count", type=int, default=600, help="Number of records to generate (default: 600).")
    parser.add_argument("--output", type=str, default="data/raw/leads_data.csv", help="Path to write the CSV output (default: data/raw/leads_data.csv).")
    parser.add_argument("--seed", type=int, default=42, help="Seed value for deterministic reproducible runs (default: 42).")
    parser.add_argument("--clean", action="store_true", help="Generate clean data without injecting DQ/compliance errors.")

    args = parser.parse_args()

    # Instantiate generator and generate data
    generator = SalesforceLeadGenerator(seed=args.seed)
    df = generator.generate_records(args.count, inject_dq_errors=not args.clean)

    # Ensure output parent directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Remove internal metadata columns prior to saving
    export_df = df.drop(columns=["_persona", "_archetype"])

    # Export to CSV
    export_df.to_csv(args.output, index=False)
    print(f"\n[SUCCESS] Successfully generated and exported lead data to {args.output}\n")

    # Print summary reports using the internal dataframe with metadata
    generator.print_validation_report(df)


if __name__ == "__main__":
    main()
