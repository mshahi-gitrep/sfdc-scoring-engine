# SFDC Scoring Engine - Architecture Documentation

Complete end-to-end architecture diagrams and reference documentation for the **CRM Readiness Intelligence Platform**.

---

## 📦 What's Included

This documentation package contains **4 comprehensive architecture documents** with **20+ detailed diagrams**, **40+ reference tables**, and **15+ code examples**.

### Documents

1. **INDEX.md** ← **START HERE**
   - Navigation guide
   - Quick links by task & audience
   - Learning paths

2. **ARCHITECTURE.md** (30 KB)
   - System overview
   - Data layer & pipeline
   - UI & design principles
   - Technology stack

3. **COMPONENT_DIAGRAMS.md** (31 KB)
   - Detailed scoring logic
   - Component calculations
   - Data models
   - Workflows

4. **DEPLOYMENT_INTEGRATION.md** (33 KB)
   - Production deployment
   - System integration
   - REST API reference
   - Monitoring & operations

---

## 🎯 Quick Start

### Choose Your Path

**I want to understand the project:**
→ Start with [INDEX.md](./INDEX.md), then read ARCHITECTURE.md §1-4

**I want to set up production:**
→ Read [DEPLOYMENT_INTEGRATION.md](./DEPLOYMENT_INTEGRATION.md) §1-2

**I want to understand scoring:**
→ Read [COMPONENT_DIAGRAMS.md](./COMPONENT_DIAGRAMS.md) §1-6

**I need to integrate with Salesforce:**
→ Read [DEPLOYMENT_INTEGRATION.md](./DEPLOYMENT_INTEGRATION.md) §3.1

**I need to debug or optimize:**
→ Read [COMPONENT_DIAGRAMS.md](./COMPONENT_DIAGRAMS.md) (detailed logic)

---

## 🏗️ System Architecture at a Glance

```
RAW DATA → PIPELINE (4 Stages) → SCORES (0-100) → UI DASHBOARD
   ↓                ↓                    ↓            ↓
 1000+          Entity→Features→    Components→    4 Pages      Analytics
 Records        Scoring→Explain     4 Tiers      Workbench
```

### The 4 Pipeline Stages

| Stage | Purpose | Key Output |
|-------|---------|-----------|
| **01** | Link & deduplicate records | Resolved entities with DQ flags |
| **02** | Extract & normalize features | Engagement, recency, profile data |
| **03** | Calculate 4 scoring components | Engagement, Recency, Profile Fit, Account Intent |
| **04** | Generate explanations | Natural language narratives & recommendations |

### Final Readiness Score

```
FINAL SCORE = (E×0.45) + (R×0.25) + (P×0.20) + (A×0.10)

Where:
  E = Engagement (0-100)   - Recent activity & diversity
  R = Recency (0-100)      - Time freshness (exponential decay)
  P = Profile Fit (0-100)  - Job persona & seniority match
  A = Account Intent (0-100) - Account buying signals

Result: 0-100 score → Tier Assignment
  80-100: High Priority ⭐  (10-15%)
  60-79:  Medium Priority 🟡 (25-35%)
  0-59:   Low Priority 🔵   (50-65%)
```

---

## 📊 Key Diagrams

### 1. End-to-End Data Flow
See: **ARCHITECTURE.md §6.1**

Raw Data → Stage 01 → Stage 02 → Stage 03 → Stage 04 → UI/Export

### 2. Scoring Component Details
See: **COMPONENT_DIAGRAMS.md §2-6**

Shows logic for each of 4 scoring components with calculation steps and examples.

### 3. Production Architecture
See: **DEPLOYMENT_INTEGRATION.md §2.1**

Full stack with Salesforce, databases, APIs, monitoring, and user layer.

### 4. UI Page Structure
See: **COMPONENT_DIAGRAMS.md §8**

4 pages: Who Should We Call This Week?, Opportunity Workbench, Prospect Brief, How The Readiness Model Works

### 5. Integration Patterns
See: **DEPLOYMENT_INTEGRATION.md §3**

How to connect with Salesforce, CRM systems, analytics platforms, and APIs.

---

## 🚀 Getting Started

### For Developers

1. **Understand the system:**
   ```
   Read: ARCHITECTURE.md (§1-4)
   Time: ~15 minutes
   ```

2. **Learn scoring logic:**
   ```
   Read: COMPONENT_DIAGRAMS.md (§1-6)
   Time: ~20 minutes
   ```

3. **Run locally:**
   ```
   python -m pipeline.stage01_entity_resolution
   python -m pipeline.stage02_feature_engineering
   python -m pipeline.stage03_component_scoring
   streamlit run streamlit_app.py  # View UI
   ```

4. **Understand code:**
   ```
   pipeline/stage01_entity_resolution.py
   pipeline/stage02_feature_engineering.py
   pipeline/stage03_component_scoring.py
   pipeline/stage04_agentic_explainer.py
   ```

### For Operations

1. **Choose deployment model:**
   - Batch (nightly scoring)
   - Interactive (dashboard only)
   - Hybrid (batch + live dashboard)
   
   See: DEPLOYMENT_INTEGRATION.md §1

2. **Set up monitoring:**
   - Pipeline health dashboard
   - API performance dashboard
   - Business metrics dashboard
   
   See: DEPLOYMENT_INTEGRATION.md §5

3. **Configure Salesforce integration:**
   - Daily extract
   - Nightly scoring
   - Write-back via Bulk API
   
   See: DEPLOYMENT_INTEGRATION.md §3.1

---

## 📖 Table of Contents

### ARCHITECTURE.md
- §1: System Overview
- §2: Data Layer
- §3: Pipeline Layer (4 Stages)
- §4: Scoring Architecture
- §5: User Interface Layer
- §6: Data Flow Diagram
- §7: File Organization
- §8: Technology Stack
- §9: Key Design Principles
- §10: Quality Assurance
- §11: Deployment Architecture
- §12: Extension Points
- §13: References & Glossary

### COMPONENT_DIAGRAMS.md
- §1: Pipeline Architecture
- §2: Engagement Scoring
- §3: Recency Scoring
- §4: Profile Fit Scoring
- §5: Account Intent Scoring
- §6: Final Score Combination
- §7: Tier Assignment
- §8: UI Component Diagram
- §9: Data Model Diagram
- §10: Workflow Diagrams
- §11: Error Handling & Validation

### DEPLOYMENT_INTEGRATION.md
- §1: Deployment Architecture (3 Models)
- §2: Full Production Stack
- §3: Integration Points (SFDC, CRM, Analytics)
- §4: REST API Reference
- §5: Monitoring & Operations
- §6: Disaster Recovery
- §7: Performance Tuning

### INDEX.md
- Navigation by task
- Navigation by audience
- Key diagrams
- Key concepts
- Performance targets
- Integration points
- Testing & validation
- Getting started checklist
- Learning paths

---

## 🔑 Key Concepts

### Scoring Components

| Component | Weight | Calculation | Examples |
|-----------|--------|-------------|----------|
| Engagement | 45% | Recent activity × time decay + historical | 5 webinars in 30d → High |
| Recency | 25% | exp(-decay_rate × days_elapsed) | Last touch 5 days ago → 97 |
| Profile Fit | 20% | Job persona + seniority + ICP + completeness | VP at ICP account → 90 |
| Account Intent | 10% | Account signal + buying committee + momentum | Named account + growth → 75 |

### Data Quality Issues

The system handles 10 realistic data quality challenges:

| Issue | Type | Example |
|-------|------|---------|
| DQ-1 | Broken Links | is_converted=True but no converted_contact_id |
| DQ-2 | Email Duplication | Multiple records with same email |
| DQ-4 | ETL Domination | created_date reflects bulk load, not true entry |
| DQ-6 | Non-Prospects | Competitors/vendors in prospect lists |
| DQ-7 | Completeness | Missing title, industry, account linkage |
| DQ-8 | Automation | "Sent" emails ≠ real engagement |
| DQ-9 | Opt-out/Bounce | Stale records still in active lists |
| DQ-10 | Disqualification Loss | Re-MQL clears historical DQ flags |

See more in: ARCHITECTURE.md §2.2

---

## 📊 Performance Characteristics

| Operation | Input | Duration | Notes |
|-----------|-------|----------|-------|
| Entity Resolution | 1000 | 5-10 sec | Linking + dedup |
| Feature Engineering | 1000 | 3-5 sec | Engagement agg |
| Component Scoring | 1000 | 2-3 sec | 4 components |
| Explanation Gen | 1000 | 10-15 sec | LLM-dependent |
| **Full Pipeline** | **1000** | **25-35 sec** | End-to-end |

---

## 🔌 Integration Points

### Inbound
- Salesforce (Accounts, Leads, Contacts, Campaigns)
- Marketo (optional enrichment)
- Custom data sources

### Outbound
- Salesforce (Bulk API write-back)
- BigQuery / Snowflake / Redshift
- HubSpot / Pipedrive / Copper
- REST API
- CSV Export
- Webhooks & notifications

See: DEPLOYMENT_INTEGRATION.md §3

---

## 📈 Business Impact

### Expected Results

- **Coverage:** 90%+ of addressable prospect universe scored
- **Quality:** 100% explainable scores (no black boxes)
- **Fairness:** Leads and Contacts scored comparably
- **Recency:** Recent engagement prioritized (30-day boost)
- **Actionability:** Scores drive next steps (outreach recommendations)

### Scoring Distribution

```
High Priority (80-100):   ⭐⭐⭐⭐⭐  10-15%  Immediate action
Medium Priority (60-79):  🟡🟡🟡🟡🟡  25-35%  Build pipeline
Low Priority (0-59):      🔵🔵🔵🔵🔵  50-65%  Long-tail nurture
```

---

## 🧪 Validation

### Test Coverage

- **Unit tests:** Entity resolution, feature engineering, scoring, explanation
- **Integration tests:** Full pipeline end-to-end, data persistence, UI rendering
- **Persona tests:** 8 explicit personas validated (High, Low, Medium, Edge Cases)

### Validation Checkpoints

Each pipeline stage validates:
- Data types & ranges
- Score boundaries [0-100]
- No missing values
- Correct tier assignment
- Explanation quality

See: ARCHITECTURE.md §10 & COMPONENT_DIAGRAMS.md §11

---

## 📞 Support

**For questions about:**

| Topic | See |
|-------|-----|
| Project overview | ARCHITECTURE.md §1-3 |
| Scoring logic | COMPONENT_DIAGRAMS.md §2-6 |
| Deployment | DEPLOYMENT_INTEGRATION.md §1-2 |
| Integration | DEPLOYMENT_INTEGRATION.md §3 |
| Troubleshooting | DEPLOYMENT_INTEGRATION.md §6 |
| Optimization | DEPLOYMENT_INTEGRATION.md §7 |

---

## 📋 Checklist: Before You Start

- [ ] Read INDEX.md (choose your learning path)
- [ ] Read ARCHITECTURE.md §1 (business context)
- [ ] Read relevant component sections
- [ ] Review data model (COMPONENT_DIAGRAMS.md §9)
- [ ] Understand deployment model needed
- [ ] Review integration requirements
- [ ] Set up monitoring (if production)
- [ ] Plan for disaster recovery (if production)

---

## 📅 Document Info

**Created:** 2026-05-31  
**Version:** 1.0 (Complete)  
**Total Size:** ~95 KB (4 documents)  
**Diagrams:** 20+ ASCII art diagrams  
**Tables:** 40+ reference tables  
**Code Examples:** 15+ pseudocode & API examples

---

## 🎓 Learning Resources

For structured learning, see: **INDEX.md - Learning Path**

Includes paths for:
- Understanding the business problem
- Learning how scoring works
- Setting up deployments
- Monitoring & operations
- Debugging & optimization

---

**Next Steps:**
1. Open [INDEX.md](./INDEX.md) for navigation
2. Follow your learning path
3. Refer back to specific sections as needed
4. Refer to actual code in `/pipeline/` directory

**Questions?** All documentation is cross-referenced. Use the table of contents or search for your topic.
