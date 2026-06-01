# Architecture Overview

This document describes the architecture of the Readiness Intelligence Platform and how its core components work together.

## High-Level Architecture

The platform is composed of:

- Data ingestion and entity resolution
- Feature engineering
- Component scoring
- Explainability and recommendation generation
- Streamlit-based operational interface

These layers are designed for separation of concerns, auditability, and governance.

---

## Data Flow

1. Raw source records are ingested from leads, contacts, accounts, and campaign memberships.
2. Entity resolution unifies duplicate and converted records.
3. Feature engineering creates readiness predictors such as engagement quality, recency, profile fit, and account fit.
4. Scoring computes a final readiness score and extracts positive/negative explanations.
5. Recommendation logic maps readiness and eligibility to business actions.
6. The Streamlit app exposes dashboards, ranked records, prospect briefs, and methodology documentation.

---

## Core Components

### Entity Resolution
- Matches direct conversions, email identities, and account relationships.
- Excludes shared mailboxes and ambiguous duplicates.

### Feature Engineering
- Builds signals for engagement, recency, intent, account fit, and profile completeness.
- Calculates automation share and campaign velocity.

### Scoring Engine
- Generates a decomposable readiness score with component weights.
- Applies data quality penalties and confidence labels.

### Eligibility & Recommendation
- Keeps eligibility separate from readiness.
- Produces action guidance for Hot, Warm, Monitor, Cold, Restricted, and Blocked records.

---

## Governance & Explainability

- Every rule is documented in the knowledge base.
- Top positive and negative reasons are stored with each record.
- Data quality and eligibility notes are surfaced alongside recommendations.

---

## Goal

The architecture is designed so a reviewer can understand every decision without reading the code. Documentation and rule metadata serve as the production-grade governance layer for future agentic workflows.
