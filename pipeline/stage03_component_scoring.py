"""
Stage 03: Component Prioritization and Scoring Pipeline Stage.

This module ingests engineered features and calculates logical component scores:
1. engagement_score (0-45)
2. recency_score (0-25)
3. profile_fit_score (0-20)
4. account_score (0-10)

Final Readiness Score = Engagement + Recency + Profile + Account (0-100).
It applies outreach-eligibility independence and outputs rich explanations, 
percentile rankings, four-tier priorities, readiness bands, and JSON score breakdowns.

Outputs:
- data/processed/person_scores.csv

Author: Senior Data Engineer
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple, Any


class SalesforceComponentScorer:
    """Prioritizes and scores Master Persons using explainable multi-component logic."""

    def __init__(self, person_features_path: str = "data/processed/person_features.csv",
                 master_persons_path: str = "data/processed/master_persons.csv"):
        self.person_features_path = person_features_path
        self.master_persons_path = master_persons_path

    def calculate_scores(self) -> pd.DataFrame:
        """Calculates logical prioritization scores and engineering prioritizations."""
        # 1. Load Datasets
        if not os.path.exists(self.person_features_path):
            raise FileNotFoundError(f"[ERROR] Features file not found at: {self.person_features_path}")
        if not os.path.exists(self.master_persons_path):
            raise FileNotFoundError(f"[ERROR] Master Persons file not found at: {self.master_persons_path}")

        features_df = pd.read_csv(self.person_features_path)
        master_df = pd.read_csv(self.master_persons_path)

        # Merge names/titles context for explainability report
        context_df = master_df[["master_person_id", "first_name", "last_name", "title"]].copy()
        df = pd.merge(features_df, context_df, on="master_person_id", how="left")

        print(f"[INFO] Ingesting features for {len(df)} master persons...")

        scored_records: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            mpid = row["master_person_id"]

            # ----------------------------------------------------
            # 1. Engagement Score (0-45)
            # ----------------------------------------------------
            quality_score = float(row.get("engagement_quality_score", 0.0))
            total_responses = int(row.get("total_responses", 0))
            automation_ratio = float(row.get("automation_ratio", 0.0))

            # Quality Contribution: up to 20 pts
            quality_contrib = (quality_score / 100.0) * 20.0
            # Volume Contribution: up to 25 pts (5 responses maxes it out)
            volume_contrib = min(25.0, total_responses * 5.0)

            eng_score = quality_contrib + volume_contrib
            
            # DQ-8 Automation Penalty (deduct 15 pts if ratio > 70%)
            if automation_ratio > 0.70:
                eng_score = max(0.0, eng_score - 15.0)
            
            eng_score = float(round(min(45.0, max(0.0, eng_score)), 2))

            # ----------------------------------------------------
            # 2. Recency Score (0-25)
            # ----------------------------------------------------
            days_since_last = float(row.get("days_since_last_response", 180.0))
            burst_flag = bool(row.get("engagement_burst_flag", False))
            velocity_30d = float(row.get("response_velocity_30d", 0.0))
            sustained_flag = bool(row.get("sustained_engagement_flag", False))

            # Base Recency Time Decay (up to 20 pts)
            if days_since_last <= 7:
                rec_base = 20.0
            elif days_since_last <= 14:
                rec_base = 16.0
            elif days_since_last <= 30:
                rec_base = 12.0
            elif days_since_last <= 90:
                rec_base = 6.0
            else:
                rec_base = 0.0

            # Velocity & Burst Boosts (up to 5 pts)
            boost = 0.0
            if burst_flag or velocity_30d > 1.5:
                boost += 5.0
            if sustained_flag:
                boost += 3.0

            rec_score = rec_base + boost
            rec_score = float(round(min(25.0, max(0.0, rec_score)), 2))

            # ----------------------------------------------------
            # 3. Profile Fit Score (0-20)
            # ----------------------------------------------------
            seniority = float(row.get("seniority_score", 0.0))
            persona = float(row.get("persona_score", 0.0))
            completeness = float(row.get("profile_completeness_score", 0.0))

            seniority_contrib = (seniority / 100.0) * 8.0
            persona_contrib = (persona / 100.0) * 8.0
            completeness_contrib = (completeness / 100.0) * 4.0

            prof_score = seniority_contrib + persona_contrib + completeness_contrib
            prof_score = float(round(min(20.0, max(0.0, prof_score)), 2))

            # ----------------------------------------------------
            # 4. Account Intent Score (0-10)
            # ----------------------------------------------------
            is_icp = bool(row.get("is_icp_qualified", False))
            is_named = bool(row.get("is_named_account", False))
            intent = float(row.get("intent_score", 0.0))
            strength = float(row.get("buying_committee_strength", 0.0))

            icp_contrib = 2.0 if is_icp else 0.0
            named_contrib = 3.0 if is_named else 0.0
            intent_contrib = (intent / 100.0) * 3.0
            strength_contrib = (strength / 100.0) * 2.0

            acc_score = icp_contrib + named_contrib + intent_contrib + strength_contrib
            acc_score = float(round(min(10.0, max(0.0, acc_score)), 2))

            # ----------------------------------------------------
            # 5. Final Readiness Score (0-100) & Enhancements
            # ----------------------------------------------------
            # Strictly independent of eligibility status flags (structural block)
            readiness_score = float(round(eng_score + rec_score + prof_score + acc_score, 2))
            readiness_score = min(100.0, max(0.0, readiness_score))

            # priority_tier and readiness_band mapping (Enhancements 1 & 2)
            if readiness_score >= 80.0:
                priority_tier = "Hot"
                readiness_band = "Very High"
            elif readiness_score >= 60.0:
                priority_tier = "Warm"
                readiness_band = "High"
            elif readiness_score >= 40.0:
                priority_tier = "Monitor"
                readiness_band = "Medium"
            else:
                priority_tier = "Cold"
                readiness_band = "Low"

            # Score Breakdown JSON dictionary (Enhancement 3)
            breakdown_dict = {
                "engagement": eng_score,
                "recency": rec_score,
                "profile": prof_score,
                "account": acc_score
            }
            score_breakdown_json = json.dumps(breakdown_dict)

            # ----------------------------------------------------
            # 6. Explainability Engine: Reasons
            # ----------------------------------------------------
            pos_reasons: List[str] = []
            neg_reasons: List[str] = []

            # Positive logic
            if total_responses >= 3:
                pos_reasons.append("High interaction volume (3+ responses)")
            if int(row.get("event_attended_count", 0)) >= 1:
                pos_reasons.append("Attended premium Event campaign")
            if days_since_last <= 7:
                pos_reasons.append("Hot recency: engaged within past 7 days")
            if burst_flag:
                pos_reasons.append("Engagement surge detected in past 14 days")
            if seniority >= 70:
                pos_reasons.append("High-tier buying authority (Director/C-Suite)")
            if is_named:
                pos_reasons.append("Strategic Named Account profile match")
            if strength >= 50:
                pos_reasons.append("Strong buying-committee activity at account")
            if completeness >= 85:
                pos_reasons.append("High profile completeness")

            # Negative logic
            if total_responses == 0:
                neg_reasons.append("Zero response history (passive sends only)")
            elif days_since_last >= 90:
                neg_reasons.append("Cold recency: no engagement in past 90 days")
            if automation_ratio > 0.70:
                neg_reasons.append("High automation inflation (DQ-8: >70% sends)")
            if seniority <= 25:
                neg_reasons.append("Individual contributor profile (low decision influence)")
            if bool(row.get("missing_title_flag", False)):
                neg_reasons.append("Data gap: missing title field")
            if bool(row.get("missing_account_flag", False)):
                neg_reasons.append("Data gap: missing account linkage (orphan)")
            if bool(row.get("duplicate_email_flag", False)):
                neg_reasons.append("Data quality risk: duplicate email address")
            if bool(row.get("shared_mailbox_flag", False)):
                neg_reasons.append("Data quality risk: shared general inbox address")

            # Format list string as comma-separated or dynamic indicators
            top_pos = ", ".join(pos_reasons[:3]) if pos_reasons else "None"
            top_neg = ", ".join(neg_reasons[:3]) if neg_reasons else "None"

            scored_records.append({
                "master_person_id": mpid,
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "title": row["title"],
                "engagement_score": eng_score,
                "recency_score": rec_score,
                "profile_fit_score": prof_score,
                "account_score": acc_score,
                "readiness_score": readiness_score,
                "priority_tier": priority_tier,
                "readiness_band": readiness_band,
                "score_breakdown_json": score_breakdown_json,
                "eligibility_status": row["eligibility_status"],
                "structural_block_flag": row["structural_block_flag"],
                "top_positive_reasons": top_pos,
                "top_negative_reasons": top_neg
            })

        scored_df = pd.DataFrame(scored_records)

        # ----------------------------------------------------
        # 7. Percentile Rank Calculation (0-100 relative to resolved cohort)
        # ----------------------------------------------------
        scored_df["score_percentile"] = float(0.0)
        # Handle rankings
        scored_df["score_percentile"] = float(0.0)
        ranks = scored_df["readiness_score"].rank(pct=True, method="min") * 100.0
        scored_df["score_percentile"] = ranks.round(2)

        # Reorder columns standardly
        cols_order = [
            "master_person_id", "first_name", "last_name", "title",
            "engagement_score", "recency_score", "profile_fit_score", "account_score",
            "readiness_score", "score_percentile", "priority_tier", "readiness_band",
            "score_breakdown_json", "eligibility_status", "structural_block_flag",
            "top_positive_reasons", "top_negative_reasons"
        ]
        scored_df = scored_df[cols_order]

        # Print validation report & matrixes
        self._print_validation_report(scored_df)

        return scored_df

    def _print_validation_report(self, df: pd.DataFrame):
        """Dumps analytical score distribution metrics, matrices, and tables."""
        print("=" * 70)
        print("                 STAGE 03: PRIORITIZATION & SCORING REPORT         ")
        print("=" * 70)
        
        # 1. Distributions stats
        print("1. Readiness Score cohort Distributions:")
        print(f"  Total Master Persons scored:      {len(df)}")
        print(f"  Average Readiness Score:          {df['readiness_score'].mean():.2f}")
        print(f"  Standard Deviation:               {df['readiness_score'].std():.2f}")
        print(f"  Minimum Score:                    {df['readiness_score'].min():.2f}")
        print(f"  Median Score (50%):               {df['readiness_score'].median():.2f}")
        print(f"  Maximum Score:                    {df['readiness_score'].max():.2f}")
        print("-" * 70)

        # 2. Priority Tiers & bands
        print("2. Priority Tiers & Readiness bands Breakdown:")
        tier_counts = df["priority_tier"].value_counts()
        for tier in ["Hot", "Warm", "Monitor", "Cold"]:
            count = tier_counts.get(tier, 0)
            pct = (count / len(df)) * 100
            print(f"  {tier:<10} Tier ({df[df['priority_tier']==tier]['readiness_band'].iloc[0] if count>0 else 'Low'}): Count = {count:4d} ({pct:5.1f}%)")
        print("-" * 70)

        # 3. Readiness vs Eligibility Cross-Matrix (Principle 2 Check)
        print("3. Readiness Tiers vs Outreach Eligibility Matrix (Principle 2):")
        matrix = pd.crosstab(df["priority_tier"], df["eligibility_status"])
        # Reindex to force clean sorting
        matrix = matrix.reindex(index=["Hot", "Warm", "Monitor", "Cold"], 
                                columns=["Eligible", "Restricted", "Blocked"], 
                                fill_value=0)
        
        print(matrix.to_string())
        print("-" * 70)

        # 4. Top 10 Highest Readiness Records Table
        print("4. Top 10 Highest Readiness records (Hot Opportunities):")
        top_10 = df.sort_values(by="readiness_score", ascending=False).head(10)
        
        print(f"{'ID':<16} | {'Name':<22} | {'Score':<5} | {'Status':<10} | {'Positive Explanation':<30}")
        print("-" * 95)
        for _, row in top_10.iterrows():
            name = f"{row['first_name']} {row['last_name']}"
            pos_reasons = row["top_positive_reasons"]
            pos_short = pos_reasons[:28] + "..." if len(pos_reasons) > 28 else pos_reasons
            print(f"{row['master_person_id']:<16} | {name:<22} | {row['readiness_score']:<5.1f} | {row['eligibility_status']:<10} | {pos_short:<30}")
        print("=" * 70)


def main():
    """Execution entry point."""
    features_csv = "data/processed/person_features.csv"
    master_persons_csv = "data/processed/master_persons.csv"
    output_file = "data/processed/person_scores.csv"

    # Instantiate scorer and execute
    scorer = SalesforceComponentScorer(
        person_features_path=features_csv,
        master_persons_path=master_persons_csv
    )
    scores_df = scorer.calculate_scores()

    # Save to outputs
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    scores_df.to_csv(output_file, index=False)
    print(f"\n[SUCCESS] Exported prioritization scores database to: {output_file}\n")


if __name__ == "__main__":
    main()
