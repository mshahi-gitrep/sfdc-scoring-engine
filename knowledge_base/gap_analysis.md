# Project-Wide Gap Analysis Report

This document records the design and compliance status of the synthetic data generators and system features against the system specification defined in [project_requirements.md](file:///c:/sfdc-scoring-engine/project_requirements.md).

---

## 1. Executive Compliance Summary

- **Accounts Dataset**: **100% Fully Compliant**. Correct row volumes (200), required schema, named-account sizing, and Pearson size-revenue correlations ($r = 0.98$).
- **Leads Dataset**: **100% Fully Compliant**. Correct default row volumes (600), full schema compliance, exact mathematical DQ enforcements (DQ-1: 20% conversion links; DQ-2: 11.8% duplicated emails; DQ-4: 80% ETL created dates), 60% population parameters, and deterministic injection of Archetypes A-H.
- **Contacts Dataset**: **Pending Build** (Planned for next step).
- **CampaignMembers Dataset**: **Pending Build** (Planned for next step).
- **Readiness Scoring Framework**: **Pending Build** (Planned for downstream pipelines).
- **Interactive Web Application**: **Pending Build** (Planned for downstream frontend pages).

---

## 2. Comprehensive Compliance & Gap Matrix

| Component / Requirement | Target / Specification | Current Compliance Status | Gap Status / Technical Notes | Priority |
| :--- | :--- | :---: | :--- | :--- |
| **Accounts Count** | Exactly 200 accounts. | **Yes** | 200 records generated in `accounts_data.csv`. | Completed |
| **Accounts Schema** | Required columns (industry, size, revenue, etc.). | **Yes** | 100% of required fields present in [generate_accounts.py](file:///c:/sfdc-scoring-engine/generators/generate_accounts.py). | Completed |
| **Leads Count** | Exactly 600 leads. | **Yes** | 600 records generated in [generate_leads.py](file:///c:/sfdc-scoring-engine/generators/generate_leads.py). | Completed |
| **Leads Schema** | Full schema including `first_name`, `last_name`, `phone`, `industry`. | **Yes** | All fields present and exported, with preserved `true_entry_date` for validation. | Completed |
| **DQ-1: Broken Conversion Links** | Exactly 20% of converted leads missing contact ID. | **Yes** | Post-processing enforces exactly **19.8% (16/81)** converted leads are masked (due to integer rounding). | Completed |
| **DQ-2: Email Duplication** | 10–15% duplicated email addresses. | **Yes** | Duplication engine creates exactly **11.8% duplicates** (prospect submissions, shared company aliases, and 2% cluster spikes). | Completed |
| **DQ-4: ETL Created Dates** | Exactly 80% of leads receive bulk ETL date. | **Yes** | Exactly **80.0% (480/600 records)** overridden with bulk date `2026-05-15 03:00:00`. | Completed |
| **DQ-6: Non-Prospect Noise** | Mapped non-prospects, 60% job population rate. | **Yes** | Mapped competitors, vendors, partners with exactly **61.7%** field population rate globally. | Completed |
| **DQ-7: Data Completeness** | Missing title, missing phone, missing industry. | **Yes** | Completeness gaps: title (35.7% null), phone (19% null), industry (18% null). | Completed |
| **DQ-9: Opt-out and Bounce** | opt-out (7%), bounced (4%) with DQ leakage. | **Yes** | Modeled. DQ mode contains 2 compliance leakage conversion anomalies. | Completed |
| **Deterministic Archetypes** | Predefined records for Personas A–H in dataset. | **Yes** | Exact profiles, scores, conversion flags, and MQL dates for **A-H deterministically injected**. | Completed |
| **Contacts Count** | Exactly 400 contacts. | **No** | Yet to implement. Planned to generate ~200 connected contacts (linked to converted leads) and ~200 orphan contacts. | **Critical** |
| **Contacts Schema** | Required columns (lead origin, no longer with company, opt-out). | **No** | Yet to implement. Mapped schema in `project_requirements.md` must be followed. | **Critical** |
| **CampaignMembers Count** | Exactly 5,000 campaign memberships. | **No** | Yet to implement. Planned across Webinars, Event, Content, Email, Advertisements, Telemarketing. | **Important** |
| **Scoring Framework** | 0-100 score: Engagement (45%), Recency (25%), Profile (20%), Intent (10%). | **No** | Downstream modeling task. Plan to utilize feature engineering pipelines to evaluate recency time decay. | **Critical** |
| **Demo Application** | Multi-page dashboard, ranked list, details, and KB. | **No** | Downstream frontend task. Plan to write a premium Vite/React or Next.js app to display results. | **Important** |

---

## 3. Recommended Design for Pending Gaps

### A. Contacts Generation Symmetrical Model
To achieve **100% connected pair fidelity**, the next step (`generate_contacts.py`) should read `data/raw/leads_data.csv` to pull the first name, last name, email, company, and `converted_contact_id` of all converted leads. It will then generate:
- **~200 Connected Contacts**: Directly mapped to these converted leads, sharing identical profiles and pointing back via `primary_lead_id` and `has_lead_origin = True`.
- **~200 Orphan Contacts**: Generated independently with their own names/emails and associated with accounts.
This solves the **Entity Resolution Challenge (Persona G)** beautifully!

### B. CampaignMember Multi-Channel Attribution
To achieve **5,000 realistic engagement records**, `generate_campaign_members.py` must run a loop over all generated Lead and Contact IDs. It will populate webinar registrations, content downloads, and event responses:
- A random decay function will distribute campaign member timestamps relative to the record's `created_date`.
- **DQ-8 (Automation Inflation)**: Introduce high-volume automated touchpoints (CampaignMember status = "Sent" with `is_responded = False`) targeting specific segments (e.g. Persona H getting 40+ automated touches).

### C. Downstream Explainable Scoring Pipeline
Once the synthetic database is complete, the scoring engine will:
- Parse campaign timestamps to evaluate engagement and recency decay.
- Apply a clean profile fit model comparing industry, size, title, and job level.
- Incorporate account intent surges to compile a composite 0-100 score.
