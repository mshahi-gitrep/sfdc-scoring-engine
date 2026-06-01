# Lessons Learned

This document captures discovery findings, surprises, design tradeoffs, and future enhancements for the Readiness Intelligence Platform.

## Discovery Findings

- High-touch events are far more predictive than email sends.
- Data quality issues frequently drive false-positive outreach recommendations.
- Eligibility rules must be separated from readiness scoring to preserve trust.

---

## Surprising Observations

- Many highly scored records still require review due to shared mailbox or duplicate contact risks.
- A strong account signal can mask poor individual profile data if not governed carefully.
- Automated campaign volume can inflate engagement without improving true outreach readiness.

---

## Design Tradeoffs

- Chose deterministic scoring over probabilistic models for explainability.
- Allowed readiness to remain visible for blocked records to support operational awareness.
- Kept account fit lower-weighted to prevent account status from overwhelming individual readiness.

---

## Future Enhancements

- Add a decision audit layer that logs every scoring and recommendation path.
- Build a rule editor UI for non-technical governance reviewers.
- Add lineage tracing for every data-quality and entity-resolution decision.

---

## What Would Be Done Differently in Production

- Standardize all rule IDs and documentation before the first release.
- Deploy a dedicated data-quality monitoring pipeline with alerting.
- Add machine-readable rule metadata for downstream agentic workflows.
