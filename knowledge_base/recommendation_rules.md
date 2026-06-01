# Recommendation Rules

This document captures the action logic used by the Readiness Intelligence Platform to convert readiness and eligibility signals into BDR recommendations.

## Recommendation Actions

- Call within 24–48 hours
- Review compliance before outreach
- Add to SDR sequence
- Keep in nurture
- Do not prioritize
- No outreach

---

## Hot + Eligible

### Condition
- Readiness band: Hot
- Eligibility state: Eligible

### Action
Call within 24–48 hours.

### Rationale
High readiness and clear eligibility justify rapid outreach.

---

## Hot + Restricted

### Condition
- Readiness band: Hot
- Eligibility state: Restricted

### Action
Review compliance before outreach.

### Rationale
The record is promising, but quality or contact risk requires human review. In many cases, restricted records should be held for nurture and cleanup instead of immediate dialing.

---

## Warm + Eligible

### Condition
- Readiness band: Warm
- Eligibility state: Eligible

### Action
Add to SDR sequence.

### Rationale
Solid readiness signals support nurturing without immediate escalation.

---

## Monitor

### Condition
- Readiness band: Monitor

### Action
Keep in nurture.

### Rationale
The prospect is worth tracking, but not urgent.

---

## Cold

### Condition
- Readiness band: Cold

### Action
Do not prioritize.

### Rationale
Low readiness means investment should be deprioritized.

---

## Blocked

### Condition
- Eligibility state: Blocked

### Action
No outreach.

### Rationale
Compliance or internal-policy constraints prohibit contact.
