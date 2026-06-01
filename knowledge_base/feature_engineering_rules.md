# Feature Engineering Rules

This document captures how raw CRM and campaign data are transformed into analytical features for readiness scoring.

## Engagement Count

### Rule
Count meaningful interactions from campaign membership and response history.

### Sources
- Event attendance
- Webinar participation
- Content downloads
- Form submissions
- Email responses

### Business Impact
High-touch engagement earns more score weight than volume-only signals.

---

## Engagement Quality

### Rule
Score interactions by quality category rather than treating all contacts equally.

### Categories
- Executive events and dinners
- Webinars
- Content downloads
- Form submissions
- Email sends

### Business Impact
Preserves signal quality and avoids inflated readiness from broad email sends.

---

## Buying Committee Size

### Rule
Measure the number of engaged contacts at the same account to infer team-level momentum.

### Business Impact
Accounts with multiple engaged participants are more likely to be in-market.

---

## Intent Score Normalization

### Rule
Normalize account intent signals to a standard scale before combining with other fit features.

### Business Impact
Prevents intent from overpowering other readiness components while preserving account context.

---

## Account Fit

### Rule
Combine named account status, ICP match, and committee strength into a compact fit score.

### Business Impact
Ensures account context supports, but does not dominate, individual readiness.

---

## Profile Completeness

### Rule
Compute completeness from presence of title, name, email, account linkage, and seniority fields.

### Business Impact
Incomplete profiles reduce confidence and increase recommendation caution.

---

## Automation Share

### Rule
Calculate the ratio of automated sends to total campaign memberships.

### Business Impact
High automation share triggers DQ-8 and penalizes engagement score.

---

## Campaign Velocity

### Rule
Detect recent surges in engagement over a short window (e.g., 14 days).

### Business Impact
Supports hot recency detection and identifies momentum-driven prospects.

---

## Recency Calculations

### Rule
Measure days since last valid response and bucket into recency score bands.

### Business Impact
Freshness is a key predictor for immediate outreach readiness.
