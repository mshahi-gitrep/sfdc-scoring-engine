# Entity Resolution Rules

This document defines how the platform consolidates leads, contacts, and accounts into unified entities and assigns confidence to match decisions.

## Core Principles

- Prefer deterministic matches over heuristics.
- Preserve original source traceability.
- Exclude shared mailboxes and duplicate garbage from identity merges.
- Annotate confidence levels for every resolved relationship.

---

## Direct Conversion Matching

### Rule
Match a converted lead to its destination contact or account using `converted_contact_id` and `converted_account_id`.

### Confidence
High when IDs are present and valid.

### Business Impact
Maintains accurate engagement history and avoids splitting a buyer profile.

---

## Backlink Recovery

### Rule
When direct conversion IDs are missing, recover relationships using backlink fields such as `primary_lead_id` or historical conversion references.

### Confidence
Medium to high depending on cross-source support.

### Business Impact
Reduces orphaned records and improves account-level scoring.

---

## Email Matching

### Rule
Match records by normalized email address when unique and not shared.

### Confidence
High for direct email matches; reduced if the domain is shared or generic.

### Business Impact
Supports identity unification across CRM, marketing, and event systems.

---

## Shared Mailbox Exclusions

### Rule
Exclude generic addresses such as `info@`, `support@`, and other shared inboxes from deterministic merges.

### Confidence
Low for shared inbox matches.

### Business Impact
Prevents false consolidation and avoids incorrect outreach targets.

---

## Duplicate Consolidation

### Rule
When multiple records represent the same person, consolidate by choosing the highest-quality, most recent data source and preserving alternate identifiers.

### Confidence
Medium to high depending on the number of matching signals.

### Business Impact
Reduces duplicate noise and centralizes readiness signals for the true buying entity.

---

## Confidence Levels

- High: Direct ID match or unique email match with strong account linkage.
- Medium: Multiple supporting attributes without direct conversion reference.
- Low: Soft matches, partial text similarity, or generic domain overlap.
