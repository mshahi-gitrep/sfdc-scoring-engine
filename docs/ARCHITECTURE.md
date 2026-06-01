# SFDC Scoring Engine - End-to-End Architecture

## 1. System Overview

The CRM Readiness Intelligence Platform is a modular, layered architecture that transforms raw Salesforce data into explainable readiness scores. The system prioritizes transparency, data quality awareness, and entity fairness.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SFDC Scoring Engine - System Flow                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DATA LAYER          PIPELINE LAYER          SCORING LAYER   UI LAYER  │
│  ───────────         ──────────────          ─────────────   ────────  │
│                                                                         │
│  ┌──────────────┐    ┌─────────────┐      ┌──────────────┐ ┌────────┐ │
│  │   Accounts   │    │   Stage 01  │      │              │ │        │ │
│  │   Leads      │───▶│ Entity      │─────▶│  Component   │─▶│ UI    │ │
│  │   Contacts   │    │ Resolution  │      │  Scoring &   │ │Render │ │
│  │ Campaign     │    │             │      │  Weighing    │ │        │ │
│  │ Members      │    └─────────────┘      └──────────────┘ └────────┘ │
│  │              │           │                                          │
│  └──────────────┘           │            ┌──────────────┐              │
│                             │            │              │              │
│                     ┌───────▼────────┐   │  Stage 04    │              │
│                     │    Stage 02    │───▶│ Agentic      │              │
│                     │   Feature      │   │ Explainer    │              │
│                     │  Engineering   │   │              │              │
│                     └────────────────┘   └──────────────┘              │
│                             │                    │                     │
│                     ┌───────▼────────┐          │                     │
│                     │    Stage 03    │          │                     │
│                     │   Component    │──────────┘                     │
│                     │    Scoring     │                               │
│                     └────────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Layer

### 2.1 Data Sources

```
DATA GENERATION & INGESTION
───────────────────────────

Raw Data Files
├── Accounts (200 records)
│   └── account_id, name, industry, employee_count, revenue, intent_score, ICP status, DNC flag
├── Leads (600 records)
│   └── lead_id, email, name, title, company, status, source, job_persona, MQL date, Marketo score
├── Contacts (400 records)
│   ├── 200 connected (with account_id)
│   └── 200 orphan (without account_id)
│       └── contact_id, account_id, email, name, title, MQL date, Marketo score, lead_origin
└── CampaignMembers (5000+ records)
    └── cm_id, entity_id, entity_type, campaign_name, campaign_type, member_status, response_date

GENERATORS (Python)
├── generate_accounts.py
├── generate_leads.py
├── generate_contacts.py
└── generate_campaignmembers.py

OUTPUT: CSV files in /data directory
```

### 2.2 Data Quality Issues Embedded

The system simulates 10 realistic data quality challenges:

| Issue | Type | Example | Target |
|-------|------|---------|--------|
| DQ-1 | Broken Links | is_converted=True but converted_contact_id=NULL | 20% of conversions |
| DQ-2 | Email Duplication | Multiple leads with same email | 10-15% of emails |
| DQ-4 | ETL Domination | created_date reflects bulk load, not true entry | 80% Leads, 34% Contacts |
| DQ-6 | Non-Prospect | Competitors, vendors in prospect lists | ~40% missing job_persona |
| DQ-7 | Completeness Gaps | Missing title, industry, account linkage | Variable |
| DQ-8 | Automation Inflation | Campaign Sent ≠ Real Engagement | 80% of campaigns |
| DQ-9 | Opt-Out/Bounce | Stale records still in active lists | ~5-10% |
| DQ-10 | Disqualification Loss | Re-MQL clears historical DQ flags | ~3-5% |

---

## 3. Pipeline Layer

The pipeline transforms raw data into scores through 4 distinct stages, each independently testable.

### 3.1 Stage 01: Entity Resolution

**Purpose:** Link and deduplicate records across systems

**Key Functions:**
- Link leads to contacts via email matching
- Resolve duplicate emails (shared mailboxes, test accounts)
- Link contacts to accounts (direct + via email domain)
- Flag broken conversion links
- Detect competitor/vendor records

**Input:** Raw CSV files from /data
**Output:** Unified entity table with resolution metadata

```python
# /pipeline/stage01_entity_resolution.py
├── resolve_lead_contact_links()
├── resolve_contact_account_links()
├── detect_duplicate_emails()
├── flag_broken_conversions()
└── enrich_entity_resolution()
```

**Data Quality Flags Set:**
- `dq_broken_link`
- `dq_duplicate_email`
- `dq_competitor_vendor_flag`
- `dq_orphan_contact` (no account linkage)

---

### 3.2 Stage 02: Feature Engineering

**Purpose:** Extract and normalize engagement features with time decay

**Key Functions:**
- Aggregate engagement from campaign history
- Apply recency weighting (time decay function)
- Normalize profile attributes
- Calculate engagement counts by type (webinar, event, email, etc.)
- Detect stale records (no engagement in 6+ months)

**Input:** Resolved entity table + campaign member history
**Output:** Feature-rich entity table with normalized columns

```python
# /pipeline/stage02_feature_engineering.py
├── aggregate_campaign_engagement()
├── calculate_recency_weights()
├── normalize_profile_features()
├── compute_engagement_by_type()
└── flag_stale_records()
```

**Features Created:**
- `engagement_count_30d`, `60d`, `90d`, `all_time`
- `engagement_types` (webinar, event, email, etc.)
- `recency_score` (days since last engagement)
- `profile_completeness` (title, company, industry coverage)
- `account_intent_signal`

---

### 3.3 Stage 03: Component Scoring

**Purpose:** Calculate 4 readiness sub-scores and combine into final 0-100 score

**Scoring Components:**

1. **Engagement Score (45% weight)**
   - Recent engagement (30d, 60d) + all-time trending
   - Engagement type diversity
   - Quality filtering (remove automation inflation)
   - Formula: `(recent_engagement × recency_multiplier) + historical_engagement`

2. **Recency Score (25% weight)**
   - Days since last touch
   - Time decay function: `exp(-decay_rate × days_elapsed)`
   - Accounts for record stagnation

3. **Profile Fit Score (20% weight)**
   - Job persona match (C-suite/executive vs. individual contributor)
   - Title seniority level
   - ICP account qualification (if linked)
   - Profile completeness

4. **Account Intent Score (10% weight)**
   - Account-level intent signal
   - Named account status
   - Buying committee size (if available)
   - Account growth trajectory

**Input:** Feature-rich entity table
**Output:** Scored entity table with component breakdowns

```python
# /pipeline/stage03_component_scoring.py
├── calculate_engagement_score()
├── calculate_recency_score()
├── calculate_profile_fit_score()
├── calculate_account_intent_score()
├── combine_component_scores()
└── normalize_to_0_100()
```

**Final Score Formula:**
```
readiness_score = (
    engagement_score × 0.45 +
    recency_score × 0.25 +
    profile_fit_score × 0.20 +
    account_intent_score × 0.10
)
```

**Readiness Tiers:**
- **High Priority** (80-100): Immediate follow-up
- **Medium Priority** (60-79): Target next
- **Low Priority** (0-59): Long-tail nurture

---

### 3.4 Stage 04: Agentic Explainer

**Purpose:** Generate human-readable explanations for every score

**Key Functions:**
- Decompose score into contributing factors
- Highlight top 3 positive factors
- Highlight top 3 negative factors / blockers
- Flag data quality concerns
- Suggest follow-up actions

**Input:** Scored entity table with component details
**Output:** Scored table with explanation narratives

```python
# /pipeline/stage04_agentic_explainer.py
├── generate_score_narrative()
├── identify_top_contributors()
├── identify_top_detractors()
├── flag_data_quality_concerns()
├── suggest_actions()
└── format_explanation()
```

**Explanation Format:**
```
READINESS SUMMARY
─────────────────
Score: 78 (Medium Priority)

WHY THIS SCORE?
 ✓ 5 webinar attendances in last 30 days (HIGH ENGAGEMENT)
 ✓ VP-level title at ICP-qualified account (STRONG FIT)
 ✓ Engagement in last 7 days (VERY RECENT)
 ✗ No email responses (LIMITED 2-WAY)
 ✗ Account has 50+ buying committee (LARGE CONSENSUS)

DATA QUALITY FLAGS
 ⚠ Email verified but record created via ETL bulk load (DQ-4)
 ⚠ No phone number available (COMPLETENESS)

RECOMMENDED ACTIONS
 → Contact via LinkedIn for direct engagement
 → Research buying committee roles
 → Prepare multi-threaded approach
```

---

## 4. Scoring Architecture

### 4.1 Scoring Flow

```
COMPONENT SCORING PIPELINE
──────────────────────────

Raw Features (Stage 02 Output)
│
├─────────────────────────────────────┬──────────────────┬───────────────┬──────────────┐
│                                     │                  │               │              │
▼                                     ▼                  ▼               ▼              ▼
┌──────────────────────┐   ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Engagement Component │   │ Recency Component│  │ Profile Fit  │  │ Account      │
│                      │   │                  │  │ Component    │  │ Intent       │
│ - 30d count (×1.5)   │   │ - Days elapsed   │  │              │  │              │
│ - 60d count (×1.0)   │   │ - Decay fn       │  │ - Job persona│  │ - Account    │
│ - 90d count (×0.5)   │   │ - Stale flag     │  │ - Seniority  │  │   intent     │
│ - Type diversity     │   │                  │  │ - ICP match  │  │ - Named acct │
│ - Auto inflation adj │   │ Output: 0-100    │  │ - Complete   │  │ - Buy cmte   │
│                      │   │                  │  │              │  │              │
│ Output: 0-100        │   │                  │  │ Output:      │  │ Output:      │
│                      │   │                  │  │ 0-100        │  │ 0-100        │
└──────────────────────┘   └──────────────────┘  └──────────────┘  └──────────────┘
         │                           │                  │                  │
         │                           │                  │                  │
         │        ┌─────────────────┴──────────────────┴──────────────────┤
         │        │                                                       │
         │        ▼                                                       │
         │   WEIGHTED AVERAGE COMBINER                                    │
         │   ├─ Engagement (45%)                                         │
         │   ├─ Recency (25%)                                            │
         │   ├─ Profile Fit (20%)                                        │
         │   └─ Account Intent (10%)                                     │
         │        │                                                      │
         └────────┼──────────────────────────────────────────────────────┘
                  │
                  ▼
           ┌──────────────┐
           │ Final Score  │
           │ (0-100)      │
           └──────────────┘
                  │
                  ▼
           ┌──────────────┐
           │ Tier Assignment
           │ - High (80-100)
           │ - Medium (60-79)
           │ - Low (0-59)
           └──────────────┘
```

### 4.2 Time Decay Function

Readiness prioritizes recent engagement over historical depth:

```
Recency Score = exp(-decay_rate × days_since_engagement)

Example Curve:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
100 ─ ╱╲
      ╱  ╲
  80 ╱    ╲___
     ╱         ╲___
  60           ╱   ╲___
               ╱       ╲___
  40          ╱           ╲___
              ╱               ╲
  20         ╱                 ╲____
              ╱                      ╲____
   0 ───────────────────────────────────────
    0      30      60      90     120    180
         Days Since Engagement

Key Points:
 • 0-30 days: Full credit
 • 30-60 days: 75% credit
 • 60-90 days: 50% credit
 • 90+ days: Declining credit
 • 180+ days: Minimal credit (stale)
```

---

## 5. User Interface Layer

### 5.1 Streamlit Application Structure

```
FRONTEND ARCHITECTURE
─────────────────────

┌─────────────────────────────────────────────────────────────┐
│           STREAMLIT ROOT APPLICATION                         │
│           streamlit_app.py                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Page Configuration | Sidebar Navigation | Auth         │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬─────────────┬─────────┬──────────┬──────────┐
    │            │            │             │         │          │          │
    ▼            ▼            ▼             ▼         ▼          ▼          ▼
┌───────┐  ┌──────────┐  ┌───────┐  ┌──────────┐ ┌──────┐  ┌──────┐  ┌───────────┐
│ Page1 │  │ Page 2   │  │Page 3 │  │ Page 4   │ │Page5 │  │Page6 │  │Utils      │
│       │  │          │  │       │  │          │ │      │  │      │  │           │
│Dash   │  │Ranked    │  │360°   │  │Method    │ │Know  │  │Review│  │Helpers    │
│board  │  │Records   │  │Detail │  │ology     │ │ledge │  │Play  │  │           │
│       │  │          │  │       │  │          │ │Base  │  │ground│  │- Plotting │
│       │  │          │  │       │  │          │ │      │  │      │  │- Filtering│
└───────┘  └──────────┘  └───────┘  └──────────┘ └──────┘  └──────┘  │- Sorting  │
                                                                      │- Export  │
                                                                      └───────────┘

Page Files in /app:
├── dashboard.py           (Analytics, distribution, KPIs)
├── ranked_records.py      (Sortable/filterable queue)
├── record_detail.py       (360° view with explanations)
├── methodology.py         (Scoring explanation & design)
├── knowledge_base.py      (DQ catalog, discovery notes)
├── reviewer_playground.py (Ad-hoc testing)
└── utils.py              (Shared utilities)
```

### 5.2 Page Descriptions

| Page | Purpose | Key Features |
|------|---------|--------------|
| **Analytics Dashboard** | System overview | Score distribution, tier breakdown, DQ summary, KPIs |
| **Ranked Queue** | Prioritization view | Sort by score, filter by tier/entity type, search, export |
| **360° Record Detail** | Deep dive | Profile, engagement timeline, score breakdown, DQ flags, recommendations |
| **Methodology** | Transparency | Scoring formula, design principles, weighting rationale, edge cases |

---

## 6. Data Flow Diagram

### 6.1 End-to-End Data Journey

```
END-TO-END DATA FLOW
────────────────────

┌───────────────────┐
│ Raw Data Sources  │
├───────────────────┤
│ • Accounts CSV    │
│ • Leads CSV       │
│ • Contacts CSV    │
│ • Campaigns CSV   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────┐
│  STAGE 01: ENTITY RES.    │
├───────────────────────────┤
│ • Link leads↔contacts     │
│ • Link contacts↔accounts  │
│ • Dedup emails            │
│ • Flag broken conversions │
│ • Detect non-prospects    │
└──────┬──────────────┬─────┘
       │              └─────────┐
       ▼                        │
  [DQ Issues]            ┌──────▼─────────┐
  ├─ dq_duplicate_email  │ Resolved       │
  ├─ dq_broken_link      │ Entity Table   │
  ├─ dq_orphan_contact   │                │
  └─ dq_competitor       │ ~1000 records  │
                         └──────┬─────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │  STAGE 02: FEATURE ENG.   │
                    ├───────────────────────────┤
                    │ • Agg campaign activity   │
                    │ • Apply time decay        │
                    │ • Normalize profiles      │
                    │ • Engagement by type      │
                    │ • Stale record detection  │
                    └──────┬──────────────┬─────┘
                           │              └──────────┐
                           ▼                         │
                      [Features]            ┌────────▼──────────┐
                      ├─ recency_score      │ Feature-Rich      │
                      ├─ engagement_30d     │ Entity Table      │
                      ├─ profile_complete   │                   │
                      ├─ persona_senior     │ ~1000 records     │
                      └─ intent_signal      │ +80 columns       │
                                            └────────┬──────────┘
                                                     │
                                                     ▼
                                    ┌──────────────────────────┐
                                    │ STAGE 03: COMPONENT SCORE│
                                    ├──────────────────────────┤
                                    │ • Engagement (45%)       │
                                    │ • Recency (25%)          │
                                    │ • Profile Fit (20%)      │
                                    │ • Account Intent (10%)   │
                                    │ • Normalize 0-100        │
                                    │ • Assign tier            │
                                    └────────┬─────────────┬──┘
                                             │             │
                                             ▼             │
                                        [Scores]   ┌───────▼────────────┐
                                        ├─ score   │ Scored Entity Table│
                                        ├─ tier    │                    │
                                        ├─ eng_sc  │ ~1000 records      │
                                        ├─ rec_sc  │ +4 score columns   │
                                        ├─ prof_sc │                    │
                                        └─ intent  │ READY FOR EXPORT   │
                                                   └───────┬────────────┘
                                                           │
                                                           ▼
                                            ┌──────────────────────┐
                                            │ STAGE 04: EXPLAINER  │
                                            ├──────────────────────┤
                                            │ • Top 3 factors (+)  │
                                            │ • Top 3 factors (-)  │
                                            │ • DQ concerns        │
                                            │ • Actions (next)     │
                                            │ • Narrative gen      │
                                            └────────┬─────────────┘
                                                     │
                                                     ▼
                                        ┌──────────────────────┐
                                        │ FINAL OUTPUT TABLE   │
                                        ├──────────────────────┤
                                        │ • All prior columns  │
                                        │ • Score              │
                                        │ • Tier               │
                                        │ • Explanation ████░ │
                                        │ • Top factors        │
                                        │ • DQ flags           │
                                        │ • Recommendations    │
                                        │                      │
                                        │ ~1000 records        │
                                        │ Ready for UI display │
                                        └──────────┬───────────┘
                                                   │
                           ┌───────────────────────┼───────────────┐
                           │                       │               │
                           ▼                       ▼               ▼
                      ┌──────────┐           ┌──────────┐     ┌──────────┐
                      │ Dashboard│           │ Ranked   │     │ 360°     │
                      │ Render   │           │ Records  │     │ Detail   │
                      └──────────┘           └──────────┘     └──────────┘
```

---

## 7. File Organization

### 7.1 Directory Structure

```
sfdc-scoring-engine/
├── README.md                         # Project overview
├── project_requirements.md           # Business requirements
├── requirements.txt                  # Python dependencies
│
├── data/                             # Data storage
│   ├── raw/                          # Source dataset exports
│   │   ├── accounts_data.csv
│   │   ├── leads_data.csv
│   │   ├── contacts_data.csv
│   │   └── campaign_members_data.csv
│   └── processed/                    # Pipeline outputs
│       ├── master_persons.csv
│       ├── entity_resolution_map.csv
│       ├── person_features.csv
│       ├── person_scores.csv
│       └── person_agent_recommendations.csv
│
├── generators/                       # Data generation module
│   ├── __init__.py
│   └── ...
│
├── pipeline/                         # Core scoring pipeline
│   ├── stage01_entity_resolution.py  # Link & deduplicate
│   ├── stage02_feature_engineering.py # Feature extraction
│   ├── stage03_component_scoring.py  # Score calculation
│   └── stage04_agentic_explainer.py  # Explanation generation
│
├── app/                              # Streamlit UI modules
│   ├── dashboard.py                  # Analytics page
│   ├── ranked_records.py             # Queue page
│   ├── record_detail.py              # Detail page
│   ├── methodology.py                # Methodology page
│   ├── methodology_new.py            # Alternate methodology module
│   ├── knowledge_base.py             # Knowledge base module
│   ├── reviewer_playground.py        # Playground module
│   └── utils.py                      # Shared utilities
│
├── streamlit_app.py                  # UI entry point
│
├── tests/                            # Test suite
│   ├── test_entity_resolution.py
│   ├── test_feature_engineering.py
│   ├── test_component_scoring.py
│   └── test_agentic_explainer.py
│
├── notebooks/                        # Jupyter notebooks
│   └── exploration.ipynb             # Data exploration
│
├── knowledge_base/                   # Documentation
│   ├── dq_catalog.md                 # Data quality issues
│   ├── discovery_notes.md            # Research findings
│   └── lessons_learned.md            # Insights & tradeoffs
│
└── docs/                             # Architecture documentation
    ├── ARCHITECTURE.md               # This file
    └── API.md                        # API documentation
```

---

## 8. Technology Stack

### 8.1 Languages & Frameworks

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Generation** | Python 3.x | Realistic synthetic data creation |
| **Pipeline** | Python (Pandas, NumPy) | Data transformation & scoring |
| **Frontend** | Streamlit | Interactive web dashboard |
| **Explanation** | LLM (Claude) | Natural language score narratives |
| **Testing** | Pytest, Fixtures | Component & integration tests |

### 8.2 Key Libraries

```
Core Dependencies:
├── pandas >= 1.5.0           # Data manipulation
├── numpy >= 1.21.0           # Numerical computing
├── streamlit >= 1.28.0       # UI framework
├── plotly >= 5.0.0           # Interactive charts
├── scikit-learn >= 1.0.0     # ML utilities (preprocessing)
├── scipy >= 1.7.0            # Statistical functions
└── python-dotenv >= 0.19.0   # Config management
```

---

## 9. Key Design Principles

### 9.1 Explainability First
- Every score is decomposable into 4 components
- Explanations surface top factors and concerns
- Data quality flags are visible to users

### 9.2 Fairness Across Entity Types
- Leads and Contacts scored on comparable scales
- Account context weighted appropriately
- Orphan contacts not penalized for missing links

### 9.3 Recency Over History
- Recent engagement (30d) weighted 1.5x
- Historical engagement (6mo+) weighted 0.5x
- Time decay prevents stale records from ranking high

### 9.4 Transparency Through Layers
- Each pipeline stage produces testable outputs
- Data quality concerns tracked throughout
- Scoring formula is fixed and documented

### 9.5 Enterprise Grade
- Handles realistic data quality issues
- Performs on 1000+ records efficiently
- Supports bulk export and integration

---

## 10. Quality Assurance

### 10.1 Validation Points

```
Validation Checkpoints:
───────────────────────

[Stage 01] ─ Validate entity resolution
  ├─ 100% of leads & contacts should have resolution attempt
  ├─ Broken link detection accuracy
  └─ Email dedup correctly identifies duplicates

[Stage 02] ─ Validate features
  ├─ Recency scores in 0-100 range
  ├─ Engagement counts positive
  └─ Profile features correctly normalized

[Stage 03] ─ Validate scores
  ├─ Component scores in 0-100 range
  ├─ Final scores in 0-100 range
  ├─ Tier assignment correct
  └─ Score distribution reasonable (not all high)

[Stage 04] ─ Validate explanations
  ├─ Top 3 factors identified
  ├─ DQ flags populated when present
  └─ Explanations readable & actionable
```

### 10.2 Test Coverage

```
Unit Tests:
├── Entity resolution (linking, dedup, flags)
├── Feature engineering (recency, engagement, normalization)
├── Component scoring (each component independently)
├── Score combination (weighted average)
└── Explanation generation (narrative output)

Integration Tests:
├── Full pipeline end-to-end
├── Data persistence (save/load)
├── UI rendering with sample data
└── Export formats (CSV, JSON)

Persona Tests (Validation):
├── Persona A (VP, named account, recent engagement) → High
├── Persona B (VP, no engagement 6mo) → Low-Medium
├── Persona C (Junior, high response rate) → Medium-High
├── Persona D (CISO, purchased list, no engagement) → Low
├── Persona E (Competitor, high engagement) → Flagged + Low
├── Persona F (Opted-out, recent event) → Edge case analyzed
├── Persona G (Converted, broken link) → Flagged + investigated
└── Persona H (Automation inflation) → Adjusted score
```

---

## 11. Deployment Architecture

### 11.1 Execution Flow

```
DEPLOYMENT & EXECUTION
──────────────────────

Option 1: Batch Scoring (pipeline modules)
└─ Run pipeline stage scripts in order
   ├── Load raw data from data/raw
   ├── Run Stage 01-03 as CLI scripts
   ├── Run Stage 04 as a recommendation module
   ├── Generate person_scores.csv and person_agent_recommendations.csv
   └── Log execution metrics

Option 2: Interactive Dashboard (streamlit_app.py)
└─ streamlit run streamlit_app.py
   ├── Load pre-scored data from data/processed/person_scores.csv
   ├── Render 4 navigation pages
   ├── Enable filtering, sorting, export
   └── Serve on localhost:8501

Option 3: Scheduled Batch + Live Dashboard
├── Cron job: Run pipeline stage scripts nightly
├── Dashboard: Load latest data/processed/person_scores.csv
└── Users: Always see fresh scores
```

### 11.2 Performance Characteristics

| Operation | Input Size | Expected Duration |
|-----------|------------|-------------------|
| Entity Resolution | 1000 records | ~5-10 seconds |
| Feature Engineering | 1000 records | ~3-5 seconds |
| Component Scoring | 1000 records | ~2-3 seconds |
| Explanation Gen | 1000 records | ~10-15 seconds (LLM dependent) |
| **Full Pipeline** | **1000 records** | **~25-35 seconds** |
| Dashboard Page Load | Pre-scored | <1 second |
| Detail Page Gen | 1 record | <2 seconds |

---

## 12. Extension Points

### 12.1 Future Enhancements

```
Future Roadmap:
───────────────

Phase 2: Advanced Scoring
├─ Multi-account companies (consolidation)
├─ Buying stage detection
├─ Competitive displacement signals
└─ Geographic targeting

Phase 3: ML Integration
├─ Propensity modeling (purchase likelihood)
├─ Churn prediction
├─ Optimal contact timing
└─ Channel preference inference

Phase 4: Operations Integration
├─ CRM sync (write scores back to Salesforce)
├─ Real-time API scoring
├─ Webhook notifications (high-score triggers)
└─ Mobile app for field access

Phase 5: Analytics & Learning
├─ Score vs. outcome tracking
├─ Model performance dashboards
├─ Weight auto-optimization
└─ Feedback loops for continuous improvement
```

---

## 13. References & Glossary

### 13.1 Key Definitions

| Term | Definition |
|------|-----------|
| **Readiness Score** | 0-100 score indicating how ready a prospect is for engagement |
| **Engagement** | Interaction with campaigns (webinar, event, email, content) |
| **Recency** | How recent the most recent engagement was |
| **Time Decay** | Function that reduces credit for old engagement |
| **Entity Resolution** | Process of linking and deduplicating records |
| **DQ Flag** | Data quality concern surfaced to user |
| **Component Score** | One of 4 sub-scores (Engagement, Recency, Profile Fit, Account Intent) |
| **Tier** | Category assignment (High, Medium, Low Priority) |
| **ICP** | Ideal Customer Profile (account type we target) |
| **MQL** | Marketing Qualified Lead (Marketo qualification status) |

### 13.2 Abbreviations

| Abbrev | Full Form |
|--------|-----------|
| SFDC | Salesforce |
| DQ | Data Quality |
| BDR | Sales Development Representative |
| ICP | Ideal Customer Profile |
| MQL | Marketing Qualified Lead |
| CSV | Comma-Separated Values |
| LLM | Large Language Model |
| ETL | Extract-Transform-Load |
| DNC | Do Not Contact |

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-31  
**Architecture Owner:** Data Engineering Team
