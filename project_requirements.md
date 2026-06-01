# CRM Readiness Intelligence Platform - Project Requirements

## 1. Project Goal

Build an explainable Salesforce Lead and Contact prioritization system that produces a readiness score (0-100) for every person record and surfaces the results through an interactive web application.

The system should simulate a realistic enterprise Salesforce environment, including data quality issues, engagement history, account enrichment, and lifecycle complexity.

---

# 2. Business Problem

Current state:

* Sales Development Representatives (BDRs) are overwhelmed by millions of Lead and Contact records.
* Existing prioritization relies on Marketo MQL status.
* MQL is generated using a behavioral threshold.
* Many MQLs are stale.
* Many high-intent prospects never become MQLs.
* BDR trust in existing scoring is low.

Objective:

Replace MQL-based prioritization with an explainable readiness scoring framework.

---

# 3. Core Design Principles

## Principle 1 - Explainability First

Every score must be decomposable.

A reviewer must understand:

* Why a record scored highly
* Why a record scored poorly
* Which factors contributed

No black-box scoring.

---

## Principle 2 - Readiness Is Not Eligibility

Readiness and outreach eligibility are independent dimensions.

Examples:

* Highly engaged competitor employee
* Opted-out prospect with recent event attendance
* High-intent account under compliance restriction

These should be flagged separately rather than hidden through score manipulation.

---

## Principle 3 - Recency Matters More Than Historical Depth

Recent engagement should carry more weight than old engagement.

Example:

* 3 webinar attendances this month > 20 engagements two years ago

Time decay should be used.

---

## Principle 4 - Leads And Contacts Must Be Treated Fairly

Leads:

* Newer
* Sparser
* Less enriched

Contacts:

* Richer
* Older
* More account context

The scoring system should avoid systematically favoring Contacts.

---

## Principle 5 - Layered Architecture

Pipeline should be modular and inspectable.

Pipeline:

Raw Data
→ Cleaning
→ Entity Resolution
→ Feature Engineering
→ Component Scoring
→ Final Readiness
→ Explanations

Each stage should be independently testable.

---

# 4. Dataset Requirements

## Accounts

Target Count: 200

Required Fields:

* account_id
* account_name
* industry
* employee_count
* annual_revenue
* country
* is_icp_qualified
* is_named_account
* intent_score
* do_not_contact

Recommended Enhancements:

* account_created_date
* buying_committee_size
* named_account_tier
* intent_surge_flag

---

## Leads

Target Count: 600

Required Fields:

* lead_id
* email
* first_name
* last_name
* title
* company
* lead_status
* lead_source
* job_persona
* job_level
* created_date
* mql_date
* mkto_lead_score
* is_converted
* converted_contact_id
* has_opted_out
* email_bounced

---

## Contacts

Target Count: 400

Composition:

* ~200 connected contacts
* ~200 orphan contacts

Required Fields:

* contact_id
* account_id
* email
* first_name
* last_name
* title
* contact_status
* job_persona
* job_level
* mql_date
* mkto_contact_score
* has_lead_origin
* primary_lead_id
* no_longer_with_company
* has_opted_out

---

## CampaignMembers

Target Count: 5000

Required Fields:

* cm_id
* entity_id
* entity_type
* campaign_name
* campaign_type
* member_status
* is_responded
* response_date
* is_active

Campaign Types:

* Webinar
* Event
* Content Syndication
* Email
* Advertisement
* Telemarketing

---

# 5. Required Data Quality Issues

The dataset must simulate at least these 8 issues.

## DQ-1

Broken Lead Conversion Links

Target:

20% of converted leads

Behavior:

is_converted = True
converted_contact_id = NULL

---

## DQ-2

Email Duplication

Target:

10-15% duplicated emails

Include:

* shared mailboxes
* duplicate prospects
* high-cardinality clusters

---

## DQ-4

ETL-Dominated Created Dates

Target:

80% of Leads
34% of Contacts

Behavior:

created_date reflects ETL load date instead of true entry date

---

## DQ-6

Non-Prospect Contamination

Examples:

* Competitors
* Vendors
* Partners

job_persona populated approximately 60%

---

## DQ-7

Data Completeness Gaps

Examples:

* Missing title
* Missing industry
* Missing phone
* Missing account linkage

---

## DQ-8

Automation Inflated Engagement

Examples:

CampaignMember status = Sent

Many campaign records with no real response.

---

## DQ-9

Opt-Out And Bounce Records

Examples:

* has_opted_out
* email_bounced
* no_longer_with_company

---

## DQ-10

Disqualification History Loss

Behavior:

Re-MQL process clears historical DQ indicators.

---

# 6. Required Personas

Must explicitly generate these archetypes.

## Persona A

VP Security

Named Account

3 webinar attendances this month

Expected Tier:

Top

---

## Persona B

VP Security

No engagement in 6+ months

Expected Tier:

Medium / Low

---

## Persona C

Junior Analyst

15 responses in 30 days

Expected Tier:

Medium / High

---

## Persona D

CISO

Purchased list

No engagement

Expected Tier:

Low

---

## Persona E

Competitor Employee

High engagement

Expected Outcome:

Flagged

---

## Persona F

Opted-out record with recent event attendance

Expected Outcome:

Edge Case

---

## Persona G

Converted lead with broken conversion link

Expected Outcome:

Entity Resolution Challenge

---

## Persona H

Contact with 40 campaign memberships and 95% automation

Expected Outcome:

Automation Inflation Case

---

# 7. Scoring Model Requirements

Output:

0-100 readiness score

Required Components:

1. Engagement Score
2. Recency Score
3. Profile Fit Score
4. Account Intent Score

Recommended Weighting:

* Engagement = 45%
* Recency = 25%
* Profile Fit = 20%
* Account Intent = 10%

Must Not Use:

* Current MQL status
* Marketo score directly
* Existing readiness indicators

---

# 8. Readiness Tiers

Example:

80-100 = High Priority

60-79 = Medium Priority

0-59 = Low Priority

Final thresholds may be adjusted after score calibration.

---

# 9. Demo Application Requirements

Pages:

## Dashboard

* Readiness distribution
* Tier counts
* DQ issue counts

## Ranked Records

* Sort by score
* Filter by tier
* Filter by entity type

## Record Details

* Profile
* Engagement history
* Score breakdown
* DQ flags
* Recommendations

## Methodology

* Scoring explanation
* Design decisions
* Tradeoffs

## Knowledge Base

* Discovery notes
* DQ catalog
* Lessons learned

---

# 10. Interview Story

Key message:

This project is not a lead scoring model.

It is an explainable readiness intelligence platform built on realistic Salesforce data, designed to improve prioritization while explicitly accounting for data quality, entity differences, engagement recency, and operational trust.
