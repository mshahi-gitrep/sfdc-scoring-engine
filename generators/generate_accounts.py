"""
Salesforce Account Data Generator Module.

This module generates realistic, highly correlated synthetic Salesforce Account records
using pandas and faker. It enforces industrial data correlations:
- Named accounts (strategic accounts) have higher employee counts and annual revenues.
- Annual revenue is strongly correlated with employee count, with realistic industry modifiers.
- Ideal Customer Profile (ICP) qualified accounts are more likely to have high intent scores.
- Intent scores are generated using non-uniform triangular distributions.

"""

import os
import argparse
import random
import string
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from faker import Faker


class SalesforceAccountGenerator:
    """Generates synthetic, highly correlated Salesforce Account records."""

    def __init__(self, seed: int = None):
        """
        Initializes the generator with an optional random seed for reproducibility.

        Args:
            seed (int, optional): The seed to use for Faker and numpy/random. Defaults to None.
        """
        self.seed = seed
        self.fake = Faker()
        
        # Configure seeds for all random number generators to ensure reproducibility
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        # Core industry definitions and their average revenue multipliers
        self.industry_multipliers = {
            "Technology": 1.5,
            "Cybersecurity": 1.6,
            "Finance": 1.8,
            "Energy": 2.0,
            "Healthcare": 1.2,
            "Manufacturing": 0.8,
            "Retail": 0.6,
            "Education": 0.5
        }
        
        # Standard industry weights for generation
        self.industries = list(self.industry_multipliers.keys())
        self.industry_weights = [0.22, 0.15, 0.18, 0.08, 0.15, 0.12, 0.06, 0.04]

        # Target countries and weights
        self.countries = ["United States", "United Kingdom", "Canada", "Germany", "France", "Japan"]
        self.country_weights = [0.55, 0.15, 0.10, 0.08, 0.07, 0.05]

    def _generate_salesforce_id(self, generated_ids: set) -> str:
        """
        Generates a unique, realistic 18-character Salesforce Account ID.
        Salesforce Account IDs start with '001'.

        Args:
            generated_ids (set): A set of already generated IDs to ensure uniqueness.

        Returns:
            str: A unique 18-character Salesforce-like ID.
        """
        chars = string.ascii_letters + string.digits
        while True:
            # Generate the 15-character suffix and convert to uppercase for standard SFDC aesthetic
            suffix = "".join(random.choices(chars, k=15))
            sfdc_id = f"001{suffix}"
            if sfdc_id not in generated_ids:
                generated_ids.add(sfdc_id)
                return sfdc_id

    def generate_records(self, num_records: int = 200) -> pd.DataFrame:
        """
        Generates a DataFrame containing the specified number of Salesforce Account records.

        Args:
            num_records (int): Number of account records to generate. Defaults to 200.

        Returns:
            pd.DataFrame: A pandas DataFrame containing realistic, correlated account data.
        """
        generated_ids = set()
        records: List[Dict[str, Any]] = []

        for _ in range(num_records):
            # 1. Basic Fields
            account_id = self._generate_salesforce_id(generated_ids)
            account_name = self.fake.company()
            industry = np.random.choice(self.industries, p=self.industry_weights)
            country = np.random.choice(self.countries, p=self.country_weights)

            # 2. Named Account Determination (Strategic Enterprise Accounts)
            # Roughly 15% of accounts are designated as strategic Named Accounts
            is_named_account = bool(np.random.choice([True, False], p=[0.15, 0.85]))

            # 3. Correlated Employee Count
            # Normal accounts are primarily SMB to Mid-Market (log-normal distribution)
            # Named accounts are large enterprises (log-normal with a much higher mean)
            if is_named_account:
                # Named accounts: typical range 1,000 to 100,000+
                emp_count = int(np.random.lognormal(mean=np.log(4500), sigma=1.0))
                emp_count = max(1000, min(emp_count, 120000))
            else:
                # Standard accounts: typical range 10 to 1,500
                emp_count = int(np.random.lognormal(mean=np.log(120), sigma=0.9))
                emp_count = max(5, min(emp_count, 1500))

            # 4. Correlated Annual Revenue
            # Heavily correlated with employee count:
            # Revenue = Employee Count * Base Revenue per Employee * Industry Multiplier * Multiplicative Noise
            base_rev_per_emp = 220000  # $220k base revenue per employee
            multiplier = self.industry_multipliers[industry]
            noise = np.random.uniform(0.75, 1.25)
            
            annual_revenue = float(emp_count * base_rev_per_emp * multiplier * noise)
            
            # Format to a realistic float value (round to nearest hundred or thousand)
            annual_revenue = round(annual_revenue, -3)

            # 5. Ideal Customer Profile (ICP) Qualification
            # ICP logic: US/UK/Canada-based technology, finance, or cybersecurity companies with >= 100 employees
            is_icp_qualified = (
                country in ["United States", "United Kingdom", "Canada"]
                and industry in ["Technology", "Cybersecurity", "Finance"]
                and emp_count >= 100
            )

            # 6. Correlated Intent Score
            # Intent score is non-uniform (1-100).
            # ICP qualified accounts are more likely to have higher intent (skewed higher).
            # Non-ICP accounts are skewed lower.
            if is_icp_qualified:
                # Skewed towards 80-100
                intent_score = int(np.random.triangular(45, 88, 100))
            else:
                # Skewed towards 20-50
                intent_score = int(np.random.triangular(5, 30, 85))

            # 7. Do Not Contact (standard compliance flag)
            # Low probability (e.g. 5% chance of Opt-Out)
            do_not_contact = bool(np.random.choice([True, False], p=[0.05, 0.95]))

            records.append({
                "account_id": account_id,
                "account_name": account_name,
                "industry": industry,
                "employee_count": emp_count,
                "annual_revenue": annual_revenue,
                "country": country,
                "is_icp_qualified": is_icp_qualified,
                "is_named_account": is_named_account,
                "intent_score": intent_score,
                "do_not_contact": do_not_contact
            })

        return pd.DataFrame(records)

    def print_validation_report(self, df: pd.DataFrame) -> None:
        """
        Prints a detailed statistical validation report to verify data correlations.

        Args:
            df (pd.DataFrame): The generated account records DataFrame.
        """
        print("=" * 60)
        print("                 DATA VALIDATION REPORT                  ")
        print("=" * 60)
        print(f"Total Records Generated: {len(df)}")
        print("-" * 60)

        # 1. Named Accounts validation
        named_df = df[df["is_named_account"]]
        non_named_df = df[~df["is_named_account"]]
        
        print("Strategic Segment Analysis (Named vs. Non-Named Accounts):")
        print(f"  Named Accounts:     Count = {len(named_df):3d} | Avg Employees = {named_df['employee_count'].mean():,.1f} | Avg Revenue = ${named_df['annual_revenue'].mean():,.2f}")
        print(f"  Standard Accounts:  Count = {len(non_named_df):3d} | Avg Employees = {non_named_df['employee_count'].mean():,.1f} | Avg Revenue = ${non_named_df['annual_revenue'].mean():,.2f}")
        print("-" * 60)

        # 2. Correlation validation
        correlation = df["employee_count"].corr(df["annual_revenue"])
        print(f"Core Correlation Metrics:")
        print(f"  Employee Count to Annual Revenue Correlation (Pearson r): {correlation:.4f}")
        print("-" * 60)

        # 3. ICP to Intent validation
        icp_df = df[df["is_icp_qualified"]]
        non_icp_df = df[~df["is_icp_qualified"]]
        
        print("ICP & Engagement Analysis (ICP vs. Non-ICP Accounts):")
        print(f"  ICP-Qualified:      Count = {len(icp_df):3d} | Avg Intent Score = {icp_df['intent_score'].mean():.1f} | Median Intent = {icp_df['intent_score'].median():.1f}")
        print(f"  Non-ICP Qualified:  Count = {len(non_icp_df):3d} | Avg Intent Score = {non_icp_df['intent_score'].mean():.1f} | Median Intent = {non_icp_df['intent_score'].median():.1f}")
        print("-" * 60)

        # 4. Industry distributions
        print("Industry Account Breakdown:")
        ind_counts = df["industry"].value_counts()
        for ind, count in ind_counts.items():
            print(f"  {ind:<20} : {count:3d} ({count/len(df)*100:.1f}%)")
        print("-" * 60)

        # 5. Do Not Contact Opt-outs
        opt_out_pct = df["do_not_contact"].mean() * 100
        print(f"Compliance Metrics:")
        print(f"  Do Not Contact (Opt-Out Rate): {opt_out_pct:.1f}%")
        print("=" * 60)


def main():
    """Main execution entry point."""
    parser = argparse.ArgumentParser(description="Generate realistic, correlated Salesforce Accounts.")
    parser.add_argument("--count", type=int, default=200, help="Number of records to generate (default: 200).")
    parser.add_argument("--output", type=str, default="data/raw/accounts_data.csv", help="Path to write the CSV output (default: data/raw/accounts_data.csv).")
    parser.add_argument("--seed", type=int, default=42, help="Seed value for deterministic reproducible runs (default: 42).")
    
    args = parser.parse_args()

    # Instantiate generator and generate data
    generator = SalesforceAccountGenerator(seed=args.seed)
    df = generator.generate_records(args.count)

    # Ensure the parent directory for the output file exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to CSV
    df.to_csv(args.output, index=False)
    print(f"\n[SUCCESS] Successfully generated and exported data to {args.output}\n")

    # Print summary reports
    generator.print_validation_report(df)


if __name__ == "__main__":
    main()
