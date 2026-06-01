# Eligibility Rules

This document defines the eligibility states and the rules that determine whether a prospect is eligible, restricted, or blocked.

## Eligibility States

- Eligible
- Restricted
- Blocked

Readiness and Eligibility are independent. A record can be highly ready but still restricted or blocked for compliance or data-quality reasons.

---

## Blocked Rules

A record is Blocked when any of the following conditions are true:

- `do_not_contact = True`
- competitor affiliation is detected
- current employee or internal contact
- compliance block applies

### Business Outcome
Blocked records are not reachable for outreach. They are retained for reporting but excluded from active sequences.

---

## Restricted Rules

A record is Restricted when data or contact quality issues introduce uncertainty. In the current implementation, this is triggered when the record's risk score reaches 40 or higher based on one or more of the following conditions:

- duplicate email detected
- shared mailbox detected
- missing title
- missing account linkage

### Business Outcome
Restricted records remain visible in the pipeline, but outreach recommendations are conservative and require review before action.

---

## Eligible Rules

A record is Eligible when:

- no Blocked condition exists
- key contact fields are present
- email/contact is valid
- account linkage is established or recoverable

### Business Outcome
Eligible records may be prioritized for outreach based on readiness score.

---

## Rule Independence

Readiness measures how likely a prospect is to engage. Eligibility determines whether outreach should be executed. These two dimensions must remain separate to preserve explainability and governance.
