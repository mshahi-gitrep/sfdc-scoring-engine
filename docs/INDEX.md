# SFDC Scoring Engine - Architecture Documentation Index

Complete end-to-end architecture diagrams and reference documentation for the CRM Readiness Intelligence Platform.

---

## 📋 Documentation Overview

This package contains four comprehensive architecture documents covering all aspects of the SFDC Scoring Engine system:

### 1. **ARCHITECTURE.md** - System Overview & Design
**Length:** 30+ KB | **Sections:** 13

Core system architecture and design principles for the entire platform.

**Contents:**
- ✅ System overview and high-level data flow
- ✅ Data layer (sources, quality issues, generators)
- ✅ Pipeline architecture (4 stages: Entity Resolution → Feature Engineering → Scoring → Explanation)
- ✅ Scoring layer (4 components: Engagement, Recency, Profile Fit, Account Intent)
- ✅ User interface layer (6 Streamlit pages + navigation)
- ✅ Data flow diagrams (end-to-end journey)
- ✅ File organization and directory structure
- ✅ Technology stack
- ✅ Design principles
- ✅ Quality assurance & testing
- ✅ Deployment architecture
- ✅ Extension points for future work
- ✅ Glossary & references

**When to use:**
- First-time overview of the system
- Understanding business requirements
- High-level design decisions
- Project planning

---

### 2. **COMPONENT_DIAGRAMS.md** - Detailed Component Logic
**Length:** 31+ KB | **Sections:** 11

Deep-dive into how each component calculates scores and generates explanations.

**Contents:**
- ✅ Pipeline architecture diagram (Stage 01-04 flow)
- ✅ Engagement score calculation (logic + examples)
- ✅ Recency score calculation (time decay function + curve)
- ✅ Profile fit score calculation (persona, title, ICP, completeness)
- ✅ Account intent score calculation (intent signal, classification, momentum)
- ✅ Final score combination (weighted average formula + example)
- ✅ Readiness tier assignment (score distribution & quality checks)
- ✅ UI component diagram (page hierarchy & structure)
- ✅ Data model diagram (entity-relationship overview)
- ✅ Workflow diagrams (data processing + interactive session)
- ✅ Error handling & validation checkpoints

**When to use:**
- Understanding scoring logic in detail
- Debugging score calculations
- Modifying weights or thresholds
- Explaining scores to stakeholders
- Validating score accuracy

---

### 3. **DEPLOYMENT_INTEGRATION.md** - Deployment & Integration
**Length:** 33+ KB | **Sections:** 7

Production deployment strategies, system integration, and operational procedures.

**Contents:**
- ✅ Deployment architecture (3 models: Batch, Interactive, Hybrid)
- ✅ Full production stack (end-to-end system architecture)
- ✅ Salesforce integration (extract, scoring, write-back)
- ✅ CRM system integration (HubSpot, Pipedrive, Copper, custom)
- ✅ Analytics platform integration (BigQuery, Snowflake, Redshift)
- ✅ REST API reference (5 endpoints: score, search, export, rescore, health)
- ✅ Monitoring & operations (3 dashboards + 10 alert rules)
- ✅ Disaster recovery (backup strategy, restore procedures)
- ✅ Performance tuning (optimization strategies, scaling approach)

**When to use:**
- Setting up production deployment
- Integrating with existing systems
- Building dashboards & monitoring
- Scaling the system
- Troubleshooting operational issues

---

## 🎯 Quick Navigation

### By Task

**I want to...**

| Task | Document | Section |
|------|----------|---------|
| Understand the project | ARCHITECTURE.md | 1, 2, 3 |
| See how scoring works | COMPONENT_DIAGRAMS.md | 2-6 |
| Understand engagement scoring | COMPONENT_DIAGRAMS.md | 2 |
| Understand recency | COMPONENT_DIAGRAMS.md | 3 |
| Know the UI layout | COMPONENT_DIAGRAMS.md | 8 |
| Deploy in production | DEPLOYMENT_INTEGRATION.md | 1, 2 |
| Integrate with Salesforce | DEPLOYMENT_INTEGRATION.md | 3.1 |
| Set up dashboards | DEPLOYMENT_INTEGRATION.md | 5 |
| Configure monitoring/alerts | DEPLOYMENT_INTEGRATION.md | 5.2 |
| Build an API client | DEPLOYMENT_INTEGRATION.md | 4 |
| Optimize performance | DEPLOYMENT_INTEGRATION.md | 7 |
| Recover from failures | DEPLOYMENT_INTEGRATION.md | 6 |

---

### By Audience

**I am a...**

| Role | Start Here | Then Read |
|------|-----------|-----------|
| **Product Manager** | ARCHITECTURE.md (§1-4) | COMPONENT_DIAGRAMS.md (§6) |
| **Data Engineer** | ARCHITECTURE.md | COMPONENT_DIAGRAMS.md (full) |
| **Backend Engineer** | COMPONENT_DIAGRAMS.md (§2-6) | DEPLOYMENT_INTEGRATION.md (§4) |
| **DevOps/Infrastructure** | DEPLOYMENT_INTEGRATION.md (§1-2) | DEPLOYMENT_INTEGRATION.md (§5-7) |
| **Business Analyst** | ARCHITECTURE.md (§1-3) | DEPLOYMENT_INTEGRATION.md (§5.1) |
| **QA/Tester** | ARCHITECTURE.md (§10) | COMPONENT_DIAGRAMS.md (§11) |
| **Data Analyst** | DEPLOYMENT_INTEGRATION.md (§3.3) | DEPLOYMENT_INTEGRATION.md (§5.1) |
| **Salesforce Admin** | DEPLOYMENT_INTEGRATION.md (§3.1) | ARCHITECTURE.md (§9) |

---

## 📊 Key Diagrams in This Package

### System Level

1. **System Overview** (ARCHITECTURE.md §1)
   - High-level data flow from raw data to UI
   - Shows all 4 pipeline stages
   - Displays UI rendering layer

2. **Production Architecture** (DEPLOYMENT_INTEGRATION.md §2.1)
   - Full production stack
   - All external systems (SFDC, monitoring, etc.)
   - Storage, API, frontend tiers

### Component Level

3. **Pipeline Architecture** (COMPONENT_DIAGRAMS.md §1.1)
   - Detailed Stage 01-04 flow
   - Input/output for each stage
   - Feature and score transformations

4. **Engagement Scoring** (COMPONENT_DIAGRAMS.md §2)
   - 5-step calculation logic
   - Timeboxed engagement weights
   - Automation inflation filtering

5. **Recency Scoring** (COMPONENT_DIAGRAMS.md §3)
   - Time decay function with curve
   - Example score calculations
   - Stale record detection

6. **UI Component Hierarchy** (COMPONENT_DIAGRAMS.md §8)
   - Page structure
   - Navigation flow
   - Shared utilities

### Data Level

7. **Data Model** (COMPONENT_DIAGRAMS.md §9)
   - Entity relationships
   - Scoring output schema
   - Campaign member aggregation

### Operational Level

8. **Deployment Models** (DEPLOYMENT_INTEGRATION.md §1.1)
   - Batch processing
   - Interactive dashboard
   - Production hybrid approach

9. **Integration Patterns** (DEPLOYMENT_INTEGRATION.md §3)
   - Salesforce write-back
   - CRM system connectors
   - Analytics platform imports

10. **Monitoring Dashboards** (DEPLOYMENT_INTEGRATION.md §5.1)
    - Pipeline health metrics
    - API performance tracking
    - Business metrics

---

## 🔍 Key Concepts Explained

### Scoring Components

| Component | Weight | Measures | Time Decay |
|-----------|--------|----------|-----------|
| **Engagement** | 45% | Recent activity, diversity, quality | Yes (30d×1.5, 60d×1.0, etc.) |
| **Recency** | 25% | Days since last touch | Yes (exp decay) |
| **Profile Fit** | 20% | Job persona, seniority, ICP match | No |
| **Account Intent** | 10% | Account signal, classification | No |

### Readiness Tiers

| Tier | Score Range | Expected % | Action |
|------|------------|-----------|--------|
| High Priority ⭐ | 80-100 | 10-15% | Immediate follow-up |
| Medium Priority 🟡 | 60-79 | 25-35% | Target next |
| Low Priority 🔵 | 0-59 | 50-65% | Long-tail nurture |

### Pipeline Stages

| Stage | Input | Output | Key Functions |
|-------|-------|--------|---------------|
| **01** | Raw CSV | Linked entities | Entity resolution, dedup, flag DQ |
| **02** | Linked entities | Feature-rich table | Engagement agg, time decay, normalization |
| **03** | Features | Scored entities | 4 component scores, weighted combination |
| **04** | Scores | Explained scores | Factor identification, narratives, actions |

---

## 📈 Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| **Pipeline Duration** | 30-35 sec | 20 sec |
| **Records Processed** | 1000-1100 | 10,000+ |
| **API Response Time (p95)** | ~110ms | <150ms |
| **Cache Hit Rate** | 92% | >90% |
| **Score Export Time** | 5-10 sec | <5 sec |

---

## 🔌 Integration Points

### Inbound Data Sources
- **Salesforce:** Accounts, Leads, Contacts, Campaign Members (daily extract)
- **Marketo:** Lead/Contact scores (optional enrichment)
- **Custom systems:** Any source can be adapted

### Outbound Destinations
- **Salesforce:** Write scores back via Bulk API 2.0
- **Analytics:** BigQuery, Snowflake, Redshift
- **CRM:** HubSpot, Pipedrive, Copper, custom
- **Dashboard:** Streamlit UI (local or cloud-hosted)
- **API:** REST endpoints for real-time access

---

## 🧪 Testing & Validation

### Validation Checkpoints

Each pipeline stage has validation rules:
- **Stage 01:** Email format, date ranges, dedup accuracy
- **Stage 02:** Score boundaries [0-100], no NaN values
- **Stage 03:** Component scores calculated correctly, tiers assigned
- **Stage 04:** Explanations populated, JSON valid

### Persona Validation

8 personas explicitly tested:
- Persona A: VP at named account, 3 webinars/month → **High**
- Persona B: VP, no engagement 6mo → **Low-Medium**
- Persona C: Junior, 15 responses/month → **Medium-High**
- Persona D: CISO, purchased list, no engagement → **Low**
- Persona E: Competitor, high engagement → **Flagged**
- Persona F: Opted-out, recent event → **Edge case**
- Persona G: Converted, broken link → **Flagged**
- Persona H: Automation inflated (95%) → **Adjusted**

---

## 📚 Documentation Format

All diagrams use **ASCII art** for easy viewing in:
- ✅ GitHub markdown
- ✅ Confluence
- ✅ Jupyter notebooks
- ✅ Plain text editors
- ✅ Print (monospace font)

Tables use **standard markdown** for:
- ✅ Sorting in GitHub
- ✅ Formatting in Confluence
- ✅ Import to sheets

Code blocks labeled for:
- ✅ Python
- ✅ SQL
- ✅ JSON
- ✅ Pseudocode

---

## 🔑 Key Metrics & Definitions

### Scoring Metrics

- **Engagement Score:** Measures recent activity volume and diversity
- **Recency Score:** Measures time freshness with exponential decay
- **Profile Fit Score:** Measures alignment with target persona
- **Account Intent Score:** Measures account-level buying signals
- **Readiness Score:** Weighted average of 4 components (0-100)

### Data Quality Metrics

- **DQ-1:** Broken link rate (~20% of conversions)
- **DQ-2:** Email duplication rate (~10-15%)
- **DQ-4:** ETL-dominated records (~80% leads)
- **DQ-6:** Non-prospect contamination (~40% no persona)
- **DQ-7:** Completeness gaps (variable by field)
- **DQ-8:** Automation inflation (~80% of campaigns)
- **DQ-9:** Opt-out/bounce records (~5-10%)
- **DQ-10:** Disqualification loss (~3-5%)

### Business Metrics

- **Coverage:** % of addressable universe scored
- **Distribution:** % in High/Medium/Low tiers
- **Recency:** % of records with engagement in last 30/60/90 days
- **Stale Rate:** % with no engagement 180+ days

---

## 🚀 Getting Started Checklist

### For New Developers

- [ ] Read ARCHITECTURE.md (§1-4) for overview
- [ ] Review COMPONENT_DIAGRAMS.md (§2-6) for scoring logic
- [ ] Run the pipeline stage scripts locally with sample data
- [ ] Run `streamlit run streamlit_app.py` to see UI
- [ ] Read code comments in pipeline/*.py files
- [ ] Run tests: `pytest tests/`

### For Production Deployment

- [ ] Review DEPLOYMENT_INTEGRATION.md (§1-2)
- [ ] Choose deployment model (batch, interactive, or hybrid)
- [ ] Set up monitoring (§5)
- [ ] Configure Salesforce integration (§3.1)
- [ ] Set up disaster recovery (§6)
- [ ] Performance tune (§7)
- [ ] Run load tests

### For Customization

- [ ] Understand scoring formula (COMPONENT_DIAGRAMS.md §6.1)
- [ ] Modify weights in the scoring stage scripts or pipeline configuration
- [ ] Adjust tier boundaries (COMPONENT_DIAGRAMS.md §7)
- [ ] Add new data sources (ARCHITECTURE.md §2)
- [ ] Extend feature engineering (ARCHITECTURE.md §3.2)

---

## 📞 Support & Questions

### Documentation Locations

| Question | Document | Section |
|----------|----------|---------|
| How does X score calculate? | COMPONENT_DIAGRAMS.md | Relevant component section |
| How do I deploy? | DEPLOYMENT_INTEGRATION.md | §1 |
| What's the data model? | COMPONENT_DIAGRAMS.md | §9 |
| How do I integrate with Y? | DEPLOYMENT_INTEGRATION.md | §3 |
| Why is score Z so low/high? | COMPONENT_DIAGRAMS.md | §6 + explanation logic |
| How do I monitor? | DEPLOYMENT_INTEGRATION.md | §5 |
| What if something fails? | DEPLOYMENT_INTEGRATION.md | §6 |

---

## 📅 Document Maintenance

| Document | Last Updated | Reviewer | Version |
|----------|--------------|----------|---------|
| ARCHITECTURE.md | 2026-05-31 | Data Team | 1.0 |
| COMPONENT_DIAGRAMS.md | 2026-05-31 | Data Team | 1.0 |
| DEPLOYMENT_INTEGRATION.md | 2026-05-31 | DevOps Team | 1.0 |
| INDEX.md | 2026-05-31 | PM | 1.0 |

---

## 🎓 Learning Path

### For Different Goals

**Goal: Understand the business problem**
1. ARCHITECTURE.md §1 (Business Problem)
2. ARCHITECTURE.md §3 (Design Principles)
3. ARCHITECTURE.md §4 (Personas & use cases)

**Goal: Learn how scoring works**
1. ARCHITECTURE.md §3 (Pipeline overview)
2. COMPONENT_DIAGRAMS.md §1-6 (Component details)
3. COMPONENT_DIAGRAMS.md §6.1 (Final formula)

**Goal: Set up a deployment**
1. DEPLOYMENT_INTEGRATION.md §1 (Deployment models)
2. DEPLOYMENT_INTEGRATION.md §2 (Production stack)
3. DEPLOYMENT_INTEGRATION.md §3 (Integration)

**Goal: Monitor & operate the system**
1. DEPLOYMENT_INTEGRATION.md §5 (Monitoring)
2. DEPLOYMENT_INTEGRATION.md §6 (Disaster recovery)
3. DEPLOYMENT_INTEGRATION.md §7 (Performance)

**Goal: Debug a score or issue**
1. COMPONENT_DIAGRAMS.md §1-6 (Find relevant component)
2. COMPONENT_DIAGRAMS.md §9 (Check data model)
3. COMPONENT_DIAGRAMS.md §11 (Validation rules)

---

**Total Documentation:** ~95 KB of detailed architecture diagrams  
**Diagrams:** 20+ ASCII art diagrams  
**Tables:** 40+ reference tables  
**Code Examples:** 15+ pseudocode & API examples  
**Coverage:** 100% of system components  

Created: 2026-05-31  
Version: 1.0 (Complete)
