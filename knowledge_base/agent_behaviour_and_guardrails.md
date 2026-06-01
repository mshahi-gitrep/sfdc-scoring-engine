# Agent Behaviour and Guardrails

## System Principle

The platform uses agent-inspired modules to support decision-making, but core scoring and routing remain deterministic, auditable, and reproducible.

Agents are not allowed to invent facts. Every explanation must be grounded in one or more of:

- master_persons.csv
- entity_resolution_map.csv
- person_features.csv
- person_scores.csv
- campaign_members_data.csv
- accounts_data.csv
- documented business rules

If evidence is unavailable, the agent must explicitly say so.

---

# 1. Data Quality Agent

## Purpose

Detect CRM data quality issues that affect scoring confidence, outreach eligibility, or downstream interpretation.

## Inputs

- leads_data.csv
- contacts_data.csv
- accounts_data.csv
- campaign_members_data.csv
- master_persons.csv

## Core Skills

- Detect missing fields
- Detect duplicate emails
- Detect shared mailboxes
- Detect broken conversion links
- Detect opted-out or bounced records
- Detect automation-inflated engagement
- Detect missing account linkage
- Classify DQ severity

## Decision Rules

- If `title` is NULL → missing_title_flag = True
- If email appears across multiple records and is not shared mailbox → duplicate_email_flag = True
- If email prefix is info/sales/support/security/admin/contact → shared_mailbox_flag = True
- If Lead is converted and converted_contact_id is NULL → broken_conversion_link_flag = True
- If automation_ratio > 0.70 → automation_inflation_flag = True
- If has_opted_out = True or email_bounced = True or no_longer_with_company = True → outreach risk exists

## Guardrails

- Do not infer missing title from email or company name.
- Do not merge shared mailbox records based only on email.
- Do not treat all duplicates as bad; duplicates are flags, not automatic exclusions.
- Do not zero out readiness score because of DQ issues.
- Surface DQ issues separately from readiness.

## Allowed Outputs

- DQ flags
- risk_score
- eligibility_status input signals
- DQ explanation
- confidence notes

## Failure / Uncertainty Behavior

If required fields are missing, return:

"Data quality assessment is incomplete because required fields are unavailable."

## Example output

{
  "missing_title_flag": true,
  "duplicate_email_flag": false,
  "shared_mailbox_flag": false,
  "dq_severity": "medium",
  "confidence_note": "Email bounce history missing from contacts_data.csv"
}

---

# 2. Entity Resolution Agent

## Purpose

Unify Salesforce Leads and Contacts into a master person identity.

## Inputs

- leads_data.csv
- contacts_data.csv
- entity_resolution_map.csv
- master_persons.csv

## Core Skills

- Resolve direct Lead → Contact conversion links
- Recover broken conversion links
- Merge duplicate non-shared email records
- Protect shared mailbox records from unsafe merges
- Assign master_person_id
- Assign resolution confidence

## Decision Rules

- Direct converted_contact_id match → confidence 1.00
- Contact primary_lead_id backlink match → confidence 1.00
- Non-shared normalized email match → confidence 0.90
- Broken conversion + email fallback → confidence 0.85
- Shared mailbox email match alone → do not merge

## Guardrails

- Never merge shared mailbox records using email-only logic.
- Never merge records if both name and email conflict.
- Never assume a Lead and Contact are the same person without a defined rule.
- Always preserve source IDs for auditability.
- Always output resolution confidence.

## Allowed Outputs

- master_person_id
- source_entity_types
- resolution_confidence
- connected_pair_flag
- broken_conversion_recovery_flag

## Failure / Uncertainty Behavior

If resolution evidence is weak, keep records separate and mark low confidence rather than forcing a merge.

## Example output

{
  "master_person_id": "mp_000123",
  "source_entity_types": ["Lead","Contact"],
  "resolution_confidence": 0.85,
  "connected_pair_flag": true,
  "notes": "Recovered via email fallback; converted_contact_id missing"
}

---

# 3. Feature Engineering Agent

## Purpose

Convert resolved people, campaigns, accounts, and DQ signals into model-ready features.

## Inputs

- master_persons.csv
- entity_resolution_map.csv
- campaign_members_data.csv
- accounts_data.csv

## Core Skills

- Aggregate campaign engagement
- Calculate response counts
- Calculate automation ratio
- Calculate recency windows
- Calculate engagement velocity
- Calculate profile scores
- Calculate account-level buying committee features
- Calculate structural risk features

## Decision Rules

- Count only `is_responded = True` as real engagement.
- Count `Sent` with `is_responded = False` as passive / automated touch.
- Calculate days_since_last_response from baseline date.
- Use 7d, 14d, 30d, 90d response windows.
- Calculate buying committee strength from engaged people per account.
- Calculate profile completeness from key fields.

## Guardrails

- Do not use MQL status.
- Do not use Marketo score as a feature.
- Do not count passive email sends as buyer intent.
- Do not infer account intent if account_id is missing.
- Do not treat missing data as negative intent; flag it separately.

## Allowed Outputs

- person_features.csv
- engagement features
- recency features
- account features
- DQ features
- risk features

## Failure / Uncertainty Behavior

If campaign history is missing, set engagement features to zero and explain that no campaign evidence was available.

## Example output

{
  "person_id": "mp_000123",
  "engagement_7d": 2,
  "engagement_30d": 5,
  "automation_ratio": 0.12,
  "profile_completeness": 0.8,
  "buying_committee_strength": 3
}

---

# 4. Readiness Scoring Agent

## Purpose

Calculate a 0-100 readiness score using deterministic component scoring.

## Inputs

- person_features.csv
- scoring_rules.md

## Core Skills

- Score engagement
- Score recency
- Score profile fit
- Score account fit
- Apply automation penalty
- Produce score breakdown
- Assign priority tier
- Assign score percentile

## Decision Rules

Final score:

readiness_score =
engagement_score +
recency_score +
profile_fit_score +
account_score

Component weights:

- Engagement: 0-45
- Recency: 0-25
- Profile Fit: 0-20
- Account Fit: 0-10

Tier rules:

- Hot: 80-100
- Warm: 60-79
- Monitor: 40-59
- Cold: 0-39

## Guardrails

- Do not use MQL status.
- Do not use Marketo score.
- Do not let LLMs change numeric scores.
- Do not zero readiness because of compliance blocks.
- Every score must be decomposable.
- Every score must be reproducible.

## Allowed Outputs

- readiness_score
- component scores
- score_breakdown_json
- priority_tier
- readiness_band
- score_percentile

## Failure / Uncertainty Behavior

If required features are missing, score only available components and mark scoring confidence as reduced.

## Example output

{
  "person_id": "mp_000123",
  "readiness_score": 72,
  "components": {"engagement": 34, "recency": 20, "profile_fit": 12, "account_fit": 6},
  "priority_tier": "Warm",
  "scoring_confidence": "partial_features"
}

---

# 5. Eligibility & Compliance Agent

## Purpose

Determine whether outreach is allowed, restricted, or blocked.

## Inputs

- person_features.csv
- accounts_data.csv
- data_quality_rules.md
- eligibility_rules.md

## Core Skills

- Identify compliance blocks
- Identify opt-outs
- Identify bounced emails
- Identify no-longer-with-company records
- Identify non-prospect records
- Classify eligibility state
- Generate risk notes

## Decision Rules

Blocked if:

- has_opted_out = True
- do_not_contact = True
- no_longer_with_company = True
- non_prospect_flag = True

Restricted if:

- duplicate_email_flag = True
- shared_mailbox_flag = True
- missing critical contact fields
- broken conversion link exists

Eligible if:

- no blocking or restriction conditions apply

## Guardrails

- Eligibility must not modify readiness score.
- Do not recommend outreach for blocked records.
- Do not hide high readiness blocked records.
- Always explain why a record is blocked or restricted.

## Allowed Outputs

- eligibility_status
- risk_score
- risk_note
- outreach_allowed flag

## Failure / Uncertainty Behavior

If compliance data is incomplete, default to Restricted and recommend review.

## Example output

{
  "person_id": "mp_000123",
  "eligibility_status": "Restricted",
  "outreach_allowed": false,
  "risk_note": "Duplicate email across two active contacts; compliance review recommended"
}

---

# 6. BDR Intelligence Agent

## Purpose

Translate scores and features into actionable BDR-facing guidance.

## Inputs

- person_scores.csv
- person_features.csv
- campaign_members_data.csv
- entity_resolution_map.csv
- recommendation_rules.md

## Core Skills

- Explain why the record matters
- Explain where the signal came from
- Explain why now
- Recommend next action
- Generate talking points
- Generate risk note

## Decision Rules

Hot + Eligible:

"Contact within 24-48 hours."

Hot + Restricted:

"Review compliance before outreach."

Warm + Eligible:

"Add to SDR sequence."

Monitor:

"Keep in nurture and watch for additional engagement."

Cold:

"Do not prioritize now."

Blocked:

"Do not contact."

## Guardrails

- Do not invent campaign activity.
- Do not invent intent increases.
- Do not say "why now" unless recent evidence exists.
- Do not generate outreach recommendations for blocked records.
- Do not claim a person is evaluating unless supported by engagement signals.
- Use plain business language.
- Keep summaries grounded in actual features and timeline evidence.

## Allowed Outputs

- why_summary
- where_signal_summary
- why_now_summary
- recommended_action
- talking_points
- risk_note

## Failure / Uncertainty Behavior

If there is no recent activity, say:

"No material recent buying signal was detected. Current prioritization is based on historical profile and account context."

## Example output

{
  "person_id": "mp_000123",
  "why_summary": "Strong recent engagement with product webinar and two inbound replies.",
  "where_signal_summary": "Engagement aggregated from campaign_members_data.csv (webinar) and recent replied emails.",
  "why_now_summary": "Most recent reply was 3 days ago; engagement_7d = 2.",
  "recommended_action": "Contact within 24-48 hours",
  "talking_points": ["Mention webinar attendance","Reference recent reply about feature X"]
}

---

# 7. Governance & Monitoring Agent

## Purpose

Monitor data quality, scoring stability, pipeline health, and deployment readiness.

## Inputs

- test outputs
- pipeline logs
- person_scores.csv
- person_features.csv
- data quality metrics

## Core Skills

- Monitor test pass/fail status
- Monitor score distribution
- Monitor tier distribution
- Monitor DQ issue rates
- Monitor eligibility distribution
- Detect score drift
- Detect pipeline failures

## Decision Rules

Flag if:

- tests fail
- score distribution shifts materially
- Hot tier exceeds expected range
- blocked records increase unexpectedly
- missing account rate spikes
- pipeline output row counts change unexpectedly

## Guardrails

- Do not auto-change scoring rules.
- Do not suppress failed tests.
- Do not deploy if required files are missing.
- Always surface validation warnings.

## Allowed Outputs

- monitoring summary
- deployment readiness status
- issue list
- recommended remediation

## Failure / Uncertainty Behavior

If validation artifacts are missing, mark deployment readiness as incomplete.

## Example output

{
  "monitoring_summary": "Score distribution drift detected between weekly snapshot and current run.",
  "deployment_readiness": "incomplete",
  "issues": ["unit tests failing: stage02_feature_engineering.py","missing person_features.csv output"]
}

---

## Notes on Determinism and Auditability

- All agents must reference source files or documented rules for any factual statement.
- Agents may produce human-readable explanations, but numeric outputs and decisions remain deterministic and produced by reproducible code paths.
- Any recovered or transformed identifiers (e.g., `master_person_id`) must retain source mappings for audit.

---

## Appendix: Example agent interaction policy

- If an agent cannot find supporting evidence for a claim, it must respond: "Required evidence not available: [list of missing datasets/fields]."
- Agents should attach one or more source pointers (filename and field) for each factual claim or inference.
