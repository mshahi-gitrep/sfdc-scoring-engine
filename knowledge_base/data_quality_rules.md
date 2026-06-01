# Data Quality Rules Catalog

This document catalogs every data quality rule used by the Readiness Intelligence Platform. Each rule is documented as a governance item for detection, impact, mitigation, and downstream score behavior.

## Rule ID: DQ-1
### Name
Broken Conversion Links

### Detection Logic
Lead is converted but converted_contact_id is NULL.

### Business Impact
Engagement history becomes fragmented and attribution is unreliable.

### Risk Level
High

### Mitigation
Recover linkage using:
- primary_lead_id
- email matching
- entity resolution graph

### Downstream Impact
Readiness score confidence reduced.

---

## Rule ID: DQ-2
### Name
Duplicate Email Address

### Detection Logic
Multiple contacts or leads share the same email address.

### Business Impact
Outreach may be sent to invalid or duplicate recipients and engagement signals may be double-counted.

### Risk Level
High

### Mitigation
Consolidate duplicates through entity resolution and apply a restricted status if ambiguity persists.

### Downstream Impact
Eligibility may be restricted; readiness remains visible but outreach recommendation is conservative.

---

## Rule ID: DQ-3
### Name
Shared General Mailbox

### Detection Logic
Email domain or address indicates shared inbox (e.g. info@, sales@, support@).

### Business Impact
Messages may not reach the intended decision-maker and response signals are noisy.

### Risk Level
Medium

### Mitigation
Flag as restricted and prioritize more direct contact methods.

### Downstream Impact
Readiness score may be fair, but outreach should be reviewed for validity.

---

## Rule ID: DQ-4
### Name
Missing Title Field

### Detection Logic
Contact or lead is missing a professional title.

### Business Impact
Buyer intent and decision authority are unclear.

### Risk Level
Medium

### Mitigation
Use role inference and cross-source matching to recover title when possible.

### Downstream Impact
Profile fit is reduced and recommendation is more cautious.

---

## Rule ID: DQ-5
### Name
Missing Account Linkage

### Detection Logic
Contact is not linked to an account record.

### Business Impact
Account fit and buying committee signals cannot be calculated.

### Risk Level
High

### Mitigation
Use account matching on company name, domain, and CRM lookup.

### Downstream Impact
Account fit defaults lower and eligibility can become restricted.

---

## Rule ID: DQ-6
### Name
Opted-Out Record

### Detection Logic
Record has do_not_contact or opt-out flag set.

### Business Impact
Outreach is prohibited for compliance reasons.

### Risk Level
Critical

### Mitigation
Mark status as Blocked and exclude from active outreach.

### Downstream Impact
Readiness is still measurable, but action is Do Not Call.

---

## Rule ID: DQ-7
### Name
Incomplete Profile

### Detection Logic
Essential fields such as name, title, email, or account are missing.

### Business Impact
Signal confidence drops and personalization is limited.

### Risk Level
Medium

### Mitigation
Enrich missing fields from alternate sources and avoid high-risk outreach.

### Downstream Impact
Profile fit decreases and recommended action becomes more conservative.

---

## Rule ID: DQ-8
### Name
Automation Share Inflation

### Detection Logic
Automated sends represent > 70% of total campaign memberships.

### Business Impact
Engagement appears stronger than legitimate activity.

### Risk Level
High

### Mitigation
Subtract 15 points from Engagement Score and highlight the automation risk.

### Downstream Impact
Readiness score is lowered; outreach recommendations are adjusted.

---

## Rule ID: DQ-9
### Name
Bounced or Left Company Email

### Detection Logic
Email bounce history or known departed employee address.

### Business Impact
Contact is not reachable and outreach is wasted.

### Risk Level
High

### Mitigation
Mark as restricted or blocked and attempt contact recovery via alternate address.

### Downstream Impact
Eligibility is reduced; readiness remains visible but action is conservative.

---

## Rule ID: DQ-10
### Name
Employee or Internal Contact

### Detection Logic
Record is identified as a current employee or internal stakeholder.

### Business Impact
Outreach should not be treated as external sales activity.

### Risk Level
Critical

### Mitigation
Block external outreach and route to internal engagement channels.

### Downstream Impact
Status is Blocked; readiness remains for internal insight only.

---

## Rule ID: DQ-11
### Name
Invalid Email Format

### Detection Logic
Email address fails syntax or domain validation.

### Business Impact
Messages will bounce or never arrive.

### Risk Level
Medium

### Mitigation
Clean the address or remove the contact from active outreach.

### Downstream Impact
Eligibility is restricted and profile quality is lowered.

---

## Rule ID: DQ-12
### Name
Incomplete Campaign History

### Detection Logic
Campaign membership events are missing key timestamp or response details.

### Business Impact
Engagement and recency calculations are unreliable.

### Risk Level
Medium

### Mitigation
Fill gaps from secondary campaign systems and treat the record with caution.

### Downstream Impact
Recency and engagement weights may be reduced and recommendation is more conservative.
