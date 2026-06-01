# Readiness Scoring Rules

This document defines every scoring decision used by the Readiness Intelligence Platform. It is the source of truth for how readiness is computed, decomposed, and explained.

## Final Score

**Readiness Score (0-100)** =

- Engagement Score (0-45)
- Recency Score (0-25)
- Profile Fit Score (0-20)
- Account Fit Score (0-10)

Each component is additive and independently explainable.

---

## Engagement Rules

Engagement score is built from two sub-components:

- Engagement quality contribution (0-20)
- Response volume contribution (0-25)

Quality is calculated using response channel weights:
- Event response = 100
- Webinar response = 70
- Content response = 50
- Email response = 20

The engagement quality score is the average weight of all responses, then scaled to 0-20. The response volume contribution is `min(25, total_responses * 5)`.

This design ensures high-touch interactions are rewarded and low-value email sends do not inflate readiness.

---

## DQ-8 Automation Penalty

If automation share > 70%, subtract 15 points from Engagement Score.

This penalty captures inflated engagement from automated touch volume and prevents artificial score boosting.

---

## Recency Rules

Recency measures the freshness of the last meaningful response.

- Last Response ≤ 7 days: +20
- Last Response ≤ 14 days: +16
- Last Response ≤ 30 days: +12
- Last Response ≤ 90 days: +6
- Last Response > 90 days: 0

Velocity and burst boosts:
- Burst or strong 30-day velocity: +5
- Sustained engagement: +3

Recency is capped at 25 points to keep freshness calibrated.

---

## Profile Fit Rules

Profile fit is composed of:
- Seniority contribution: up to 8 points
- Persona contribution: up to 8 points
- Profile completeness contribution: up to 4 points

Profile fit is determined by seniority, job persona alignment, and the completeness of key profile fields.

---

## Account Fit Rules

Account fit captures strategic account alignment and buying committee activity:
- Named Strategic Account match: +3
- ICP qualification: +2
- Intent score: up to +3
- Committee strength: up to +2

Account fit is intentionally smaller in weight, ensuring account context supports outreach rather than dominating it.

---

## Explainability

Every score component maps to observable signals. The platform exposes top positive reasons and top negative reasons for each record to make scoring auditable.
