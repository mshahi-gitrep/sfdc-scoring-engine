# Agent Decision Rules

This document describes the behavior of each decision agent in the Readiness Intelligence Platform, including responsibilities, decision criteria, and outputs.

## Data Quality Agent

### Responsibilities
- Detect data quality issues.
- Flag records for cleanup, restriction, or block.
- Surface data-quality explanations for scoring and recommendations.

### Decision Criteria
- Missing title, account linkage, or email.
- Duplicate email or shared mailbox.
- Opt-out or compliance flags.
- Automation share > 70%.

### Outputs
- `dq_flag`
- Data quality reason labels
- Eligibility state adjustments
- Recommendation adjustments

---

## Entity Resolution Agent

### Responsibilities
- Match leads, contacts, and accounts into unified identities.
- Resolve duplicates and consolidate signal history.
- Assign confidence scores to resolution results.

### Decision Criteria
- Direct conversion IDs.
- Email matches.
- Backlink recovery.
- Shared mailbox exclusions.
- Duplicate consolidation rules.

### Outputs
- Unified entity IDs
- Match confidence levels
- Resolved account linkages
- Consolidated engagement history

---

## Scoring Agent

### Responsibilities
- Calculate component scores.
- Apply penalties and explainability signals.
- Generate readiness bands and priority tiers.

### Decision Criteria
- Engagement quantity and quality.
- Recency of last response.
- Profile fit and completeness.
- Account fit and committee strength.
- Data quality penalties.

### Outputs
- Readiness score
- Readiness band
- Priority tier
- Top positive reasons
- Top negative reasons

---

## BDR Intelligence Agent

### Responsibilities
- Translate readiness and eligibility into outreach actions.
- Recommend operational next steps for sales teams.
- Surface guardrails for restricted or blocked records.

### Decision Criteria
- Readiness band (Hot/Warm/Monitor/Cold)
- Eligibility state (Eligible/Restricted/Blocked)
- Data quality flags
- Compliance signals

### Outputs
- Recommended action label
- Outreach urgency guidance
- Review or approval prompts for restricted records

---

## Governance Agent

### Responsibilities
- Ensure rule consistency across scoring, eligibility, and recommendations.
- Detect conflicts between readiness and eligibility.
- Maintain audit trails for decision logic.

### Decision Criteria
- Rule compliance checks
- Conflict detection between dimensions
- Explainability coverage
- Documentation alignment with code

### Outputs
- Governance summaries
- Rule validation reports
- Decision audit logs
