# SFDC Scoring Engine - Component & Interaction Diagrams

This document provides detailed visual diagrams of system components and their interactions.

---

## 1. Pipeline Architecture Diagram

### 1.1 Data Flow Through Pipeline Stages

```
                        SCORING PIPELINE ARCHITECTURE
                        ═════════════════════════════════

                                Input
                                  ▲
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
            ┌──────────────┐         ┌──────────────────┐
            │ Raw CSV Data │         │ Campaign History │
            └──────────────┘         └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                          ┌───────▼────────┐
                          │                │
                          ▼                │
                    ┌─────────────────────┴──────┐
                    │  STAGE 01: ENTITY RESOLVE  │
                    │  ─────────────────────────│
                    │ • Lead↔Contact Linking    │
                    │ • Contact↔Account Linking │
                    │ • Duplicate Detection     │
                    │ • DQ Flagging             │
                    │                           │
                    │ Input: 4 CSV files       │
                    │ Output: Linked entities  │
                    └──────────┬────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Resolved Entities   │
                    │ - 1000+ records     │
                    │ - DQ flags added    │
                    │ - Links established │
                    └──────────┬──────────┘
                               │
                          ┌────▼─────────────────┐
                          │                      │
                          ▼                      │
                  ┌──────────────────────────────┴───┐
                  │ STAGE 02: FEATURE ENGINEERING   │
                  │ ──────────────────────────────│
                  │ • Campaign Aggregation         │
                  │ • Recency Calculation          │
                  │ • Profile Normalization        │
                  │ • Engagement Categorization    │
                  │ • Time Decay Application       │
                  │                                │
                  │ Input: Resolved entities       │
                  │ Output: 80+ feature columns   │
                  └─────────┬──────────────────────┘
                            │
                 ┌──────────▼─────────┐
                 │ Feature-Rich       │
                 │ Data Table         │
                 │ - 1000+ records    │
                 │ - Engagement       │
                 │ - Recency scores   │
                 │ - Profile features │
                 └──────────┬─────────┘
                            │
                       ┌────▼────────────────────┐
                       │                         │
                       ▼                         │
                 ┌─────────────────────────────┴──┐
                 │ STAGE 03: COMPONENT SCORING   │
                 │ ──────────────────────────────│
                 │ ┌─ Engagement Score (45%)   │
                 │ │ ├─ Recent activity       │
                 │ │ ├─ Type diversity       │
                 │ │ └─ Quality filtering    │
                 │ ├─ Recency Score (25%)    │
                 │ │ ├─ Days since touch     │
                 │ │ └─ Time decay function  │
                 │ ├─ Profile Fit (20%)      │
                 │ │ ├─ Job persona          │
                 │ │ ├─ Seniority            │
                 │ │ └─ ICP match            │
                 │ └─ Account Intent (10%)   │
                 │   ├─ Account signal       │
                 │   └─ Named account status │
                 │                           │
                 │ Output: 0-100 scores      │
                 └────────┬──────────────────┘
                          │
                    ┌─────▼──────┐
                    │ Scored     │
                    │ Entities   │
                    │ - Scores   │
                    │ - Tiers    │
                    │ - Break-   │
                    │   downs    │
                    └─────┬──────┘
                          │
                       ┌──▼──────────────────┐
                       │                     │
                       ▼                     │
                 ┌──────────────────────────┴──┐
                 │ STAGE 04: EXPLANATIONS    │
                 │ ────────────────────────── │
                 │ • Top 3 Positive Factors │
                 │ • Top 3 Negative Factors │
                 │ • DQ Concerns            │
                 │ • Recommended Actions    │
                 │ • Natural Language Gen   │
                 │                          │
                 │ Input: Scored entities   │
                 │ Output: Explained scores │
                 └────────┬─────────────────┘
                          │
                    ┌─────▼──────────┐
                    │ Final Output   │
                    │ - Score (0-100)│
                    │ - Tier         │
                    │ - Explanation  │
                    │ - Flags        │
                    │ - Actions      │
                    └─────┬──────────┘
                          │
                    ┌─────▼───────────┐
                    │ Output Channel  │
                    ├─────────────────┤
                    │ • CSV export    │
                    │ • DB storage    │
                    │ • API response  │
                    │ • UI display    │
                    └─────────────────┘
```

---

## 2. Engagement Score Calculation

### 2.1 Component Logic

```
ENGAGEMENT SCORE CALCULATION
════════════════════════════════

Input: Campaign membership history + engagement features

Step 1: Aggregate Campaign Activity
─────────────────────────────────
  ├─ Count webinar attendances
  ├─ Count event attendances
  ├─ Count email responses
  ├─ Count content syndicaton opens
  ├─ Count advertisement clicks
  └─ Count telemarketing responses

Step 2: Calculate Timeboxed Engagement
──────────────────────────────────────
  ├─ Last 30 days: count × 1.5 (high weight)
  ├─ 31-60 days:   count × 1.0 (medium weight)
  ├─ 61-90 days:   count × 0.5 (low weight)
  └─ 90+ days:     count × 0.2 (archive weight)

Step 3: Engagement Type Diversity
─────────────────────────────────
  └─ Bonus if engaged across multiple types
     (e.g., both webinar + event)

Step 4: Filter Automation Inflation
──────────────────────────────────
  ├─ Remove "Sent" status without response
  ├─ Remove bounced emails
  ├─ Remove opt-out interactions
  └─ Reduce weight of email-only engagement

Step 5: Normalize to 0-100
──────────────────────────
  ├─ Set ceiling at 100
  ├─ Handle zero engagement (score = 0)
  ├─ Handle outliers (trim at 95th percentile)
  └─ Apply sigmoid for smooth distribution

                    ┌─────────────┐
                    │ Engagement  │
                    │ Score:      │
                    │ 0-100       │
                    └─────────────┘

Examples:
─────────
• 5 webinar + 2 event in 30d              → ~85 (High)
• 1 email response in 60d                 → ~40 (Medium)
• 10 "Sent" emails, no response           → ~15 (Low - automation)
• No engagement                            → 0 (None)
```

---

## 3. Recency Score Calculation

### 3.1 Time Decay Function

```
RECENCY SCORE CALCULATION
═════════════════════════════

Input: Days since last engagement

Step 1: Calculate Days Elapsed
──────────────────────────
  days_elapsed = TODAY - last_engagement_date

Step 2: Apply Time Decay Function
────────────────────────────────
  Formula: recency_score = 100 × exp(-decay_rate × days_elapsed)
  
  Where decay_rate ≈ 0.035 (tunable parameter)

Step 3: Apply Boundaries
───────────────────────
  ├─ Minimum: 0 (never goes negative)
  ├─ Maximum: 100 (capped)
  └─ Stale threshold: If 180+ days, mark as "stale"

                        RECENCY CURVE
          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         100│ ╭─────
            │ │
          90│ ├─┐
            │ │ ╲
          80│ │  ╲
            │ │   ╲
          70│ │    ╲___
            │ │        ╲
          60│ │         ╲___
            │ │             ╲
          50│ │              ╲___
            │ │                  ╲
          40│ │                   ╲___
            │ │                       ╲
          30│ │                        ╲___
            │ │                            ╲___
          20│ │                                ╲
            │ │                                 ╲___
          10│ │                                     ╲___
            │ │
           0│ ╰───────────────────────────────────────
            └──┼───┼───┼───┼───┼───┼───┼───┼───┼───┼─
              0   20  40  60  80  100 120 140 160 180
                         DAYS SINCE ENGAGEMENT

Key Points:
───────────
•   0 days: 100 (fresh engagement)
•  30 days: ~67  (one month old)
•  60 days: ~45  (two months old)
•  90 days: ~30  (three months old)
• 120 days: ~20  (four months old)
• 180 days: ~8   (six months - stale threshold)

Examples:
─────────
• Engaged yesterday (1 day)           → 97 (Very High)
• Engaged 7 days ago                  → 77 (High)
• Engaged 30 days ago                 → 67 (Medium)
• Engaged 60 days ago                 → 45 (Medium-Low)
• Engaged 180+ days ago (stale)       → 8  (Very Low)
• Never engaged                        → 0  (None)
```

---

## 4. Profile Fit Score Calculation

### 4.1 Component Logic

```
PROFILE FIT SCORE CALCULATION
═════════════════════════════════

Input: Job persona, title, seniority, ICP qualification

Step 1: Job Persona Scoring
──────────────────────────
  ├─ Decision Maker (VP, C-Suite)       → 95
  ├─ Influencer (Manager, Senior)       → 75
  ├─ User (IC, Junior)                  → 50
  ├─ Non-prospect (Vendor, Competitor)  → 5
  └─ Unknown                             → 30

Step 2: Title Level Scoring
───────────────────────────
  ├─ C-Level (CEO, CFO, CISO, etc.)    → +20
  ├─ VP-Level                           → +15
  ├─ Director/Senior Manager            → +10
  ├─ Manager/Specialist                 → +5
  ├─ Individual Contributor             → 0
  └─ Unknown                             → -5

Step 3: Account ICP Scoring
───────────────────────────
  ├─ If linked to ICP account           → +25
  ├─ If linked to named account         → +15
  ├─ If account matches criteria        → +10
  ├─ If no account link                 → -10
  └─ If orphan contact                  → -5

Step 4: Profile Completeness
────────────────────────────
  Score based on filled fields:
  ├─ Title present    → +5
  ├─ Company present  → +5
  ├─ Email verified   → +5
  ├─ Phone present    → +3
  ├─ Industry present → +2
  └─ Limit to +100    (cap the total)

Step 5: Normalize to 0-100
──────────────────────────
  ├─ Sum all components
  ├─ Apply ceiling at 100
  ├─ Handle minimum at 0
  └─ Smooth outliers

                    ┌────────────────┐
                    │ Profile Fit    │
                    │ Score:         │
                    │ 0-100          │
                    └────────────────┘

Examples:
─────────
• VP Finance at ICP Fortune 500        → 95 (Excellent)
• Manager at mid-market named account  → 75 (Good)
• Junior IC at SMB, unknown persona    → 40 (Okay)
• Competitor employee, high profile    → 5  (Disqualified)
• Opt-out with no company              → 0  (Invalid)
```

---

## 5. Account Intent Score Calculation

### 5.1 Component Logic

```
ACCOUNT INTENT SCORE CALCULATION
═════════════════════════════════════

Input: Account-level intent signals, classification, size

Step 1: Account Intent Signal
─────────────────────────────
  ├─ Account intent_score (if available)  → Use as base (0-100)
  └─ Threshold mapping:
     ├─ High (>70)     → 80
     ├─ Medium (40-70) → 50
     ├─ Low (<40)      → 20
     └─ No signal      → 30

Step 2: Account Classification
──────────────────────────────
  ├─ ICP Qualified         → +20
  ├─ Named Account         → +15
  ├─ Previously bought     → +15
  ├─ Not targeted          → -20
  ├─ Competitor            → -30
  └─ Restricted (DNC)      → -50

Step 3: Buying Committee Size
────────────────────────────
  ├─ Small (1-5)           → 70 (decision velocity)
  ├─ Medium (6-15)         → 50 (consensus needed)
  ├─ Large (16-30)         → 35 (complex sales)
  ├─ Very Large (30+)      → 20 (long cycles)
  └─ Unknown               → 40

Step 4: Account Momentum
───────────────────────
  ├─ Account engagement up 30%+   → +15
  ├─ Account engagement stable    → +5
  ├─ Account engagement down 30%+ → -15
  └─ Account engagement unknown   → 0

Step 5: Normalize to 0-100
──────────────────────────
  ├─ Sum all signals
  ├─ Weight by data quality
  ├─ Cap at 100, floor at 0
  └─ Apply smoothing

                    ┌────────────────┐
                    │ Account Intent │
                    │ Score:         │
                    │ 0-100          │
                    └────────────────┘

Examples:
─────────
• ICP account, high intent signal           → 85 (Strong)
• Named account, medium buying committee   → 65 (Good)
• SMB, no prior signal                      → 35 (Neutral)
• Competitor account                        → 0  (Skip)
• Restricted/DNC account                    → 0  (Blocked)
```

---

## 6. Final Score Combination

### 6.1 Weighted Average Formula

```
FINAL READINESS SCORE FORMULA
═══════════════════════════════════

Components:
───────────
E = Engagement Score      (0-100)
R = Recency Score         (0-100)
P = Profile Fit Score     (0-100)
A = Account Intent Score  (0-100)

Formula:
────────
READINESS_SCORE = (E × 0.45) + (R × 0.25) + (P × 0.20) + (A × 0.10)

Breakdown:
──────────
Component            Weight    Influence     Rationale
─────────────────────────────────────────────────────────────────────
Engagement           45%       ~E/2.22       Recent behavior is primary
Recency              25%       ~R/4.00       Freshness prevents stale
Profile Fit          20%       ~P/5.00       Right person matters
Account Intent       10%       ~A/10.00      Account context adds value
─────────────────────────────────────────────────────────────────────

Example Calculation:
─────────────────────

Scenario: VP Security at ICP Fortune 500, 5 webinars in 30d

E (Engagement) = 85
  ├─ 5 webinars × 1.5 = 7.5
  ├─ 2 events = 2
  ├─ Total = 9.5 → normalized to 85

R (Recency) = 95
  ├─ Last engagement 5 days ago
  ├─ exp(-0.035 × 5) = 0.83 → 83
  ├─ Recent bonus → 95

P (Profile Fit) = 90
  ├─ VP persona = 95
  ├─ Title level C-adjacent = +15
  ├─ ICP account = +25
  ├─ All fields complete = +10
  ├─ Total = 145 → capped to 90

A (Account Intent) = 75
  ├─ Account intent signal = 70
  ├─ ICP qualified = +20
  ├─ Named account = +15
  ├─ Total = 105 → capped to 75

FINAL SCORE = (85 × 0.45) + (95 × 0.25) + (90 × 0.20) + (75 × 0.10)
            = 38.25 + 23.75 + 18.00 + 7.50
            = 87.50

TIER ASSIGNMENT: High Priority (80-100)
```

---

## 7. Tier Assignment

### 7.1 Score Distribution

```
READINESS TIER ASSIGNMENT
═════════════════════════════

Score Range    Tier              Action Level      Expected %
──────────────────────────────────────────────────────────────
80 - 100       ⭐ HIGH PRIORITY   Immediate        10-15%
               Green Zone         Follow-up

60 - 79        🟡 MEDIUM PRIORITY Target Next     25-35%
               Yellow Zone        Build Pipeline

0 - 59         🔵 LOW PRIORITY    Long-tail       50-65%
               Blue Zone          Nurture

Distribution Characteristics:
─────────────────────────────
• High scores: Recent engagement + strong fit + intent
• Medium scores: Some engagement or strong fit, but not both
• Low scores: New records, no engagement, or profile mismatch

Quality Checks:
───────────────
✓ All scores properly distributed (not 90% high)
✓ No large gaps in score distribution
✓ Tier boundaries clear and defensible
✓ Edge cases properly categorized (see Persona examples)
```

---

## 8. UI Component Diagram

### 8.1 Page Hierarchy

```
STREAMLIT NAVIGATION STRUCTURE
════════════════════════════════════

                    ┌─────────────────────────┐
                    │ Streamlit Root App      │
                    │ (streamlit_app.py)      │
                    └────────┬────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐  ┌──────────────┐  ┌────────────┐
        │ Sidebar │  │ Main Content │  │ Config &   │
        │ Nav     │  │ Area         │  │ Settings   │
        └────┬────┘  └──────────────┘  └────────────┘
             │
    ┌────────┼────────┬─────────┬──────────┐
    │        │        │         │          │
    ▼        ▼        ▼         ▼          ▼
 ┌─────┐ ┌──────┐ ┌─────┐  ┌────────┐ ┌──────────┐
 │ 📊  │ │ 📋  │ │ 👤  │  │ 📖    │ │ ⚙️      │
 │Dash │ │Ranked│ │Detai│  │Method │ │ Utils   │
 │board│ │Records│ │     │  │ology  │ │(shared) │
 └─────┘ └──────┘ └─────┘  └────────┘ └──────────┘

Note: app/ contains additional modular components for future knowledge base and playground workflows.
Page 1: Analytics Dashboard
──────────────────────────
  ├─ KPI Cards
  │  ├─ Total Records
  │  ├─ High Priority Count
  │  ├─ Avg Score
  │  └─ DQ Issue Count
  ├─ Score Distribution (Histogram)
  ├─ Tier Breakdown (Pie)
  └─ DQ Issues Heatmap

Page 2: Ranked Records Queue
────────────────────────────
  ├─ Toolbar
  │  ├─ Sort Options (Score, Recency, Entity Type)
  │  ├─ Filter by Tier
  │  ├─ Filter by Entity Type
  │  ├─ Search by Name/Email
  │  └─ Export Button
  ├─ Table
  │  ├─ Rank (1-1000+)
  │  ├─ Name/Email
  │  ├─ Company
  │  ├─ Score
  │  ├─ Tier (color coded)
  │  └─ Click to Detail
  └─ Pagination (50/page)

Page 3: 360° Record Detail
──────────────────────────
  ├─ Header
  │  ├─ Name, Title, Company
  │  └─ Score (Large) + Tier Badge
  ├─ Profile Section
  │  ├─ Contact info
  │  ├─ Account linkage
  │  └─ Data quality flags
  ├─ Score Breakdown
  │  ├─ Engagement (45%) with bar
  │  ├─ Recency (25%) with bar
  │  ├─ Profile Fit (20%) with bar
  │  └─ Account Intent (10%) with bar
  ├─ Engagement Timeline
  │  └─ Campaign history (chronological)
  ├─ Explanation Narrative
  │  ├─ Top 3 Positive Factors
  │  ├─ Top 3 Negative Factors
  │  ├─ Data Quality Concerns
  │  └─ Recommended Actions
  └─ Navigation
     └─ Previous/Next Record

Page 4: Methodology
──────────────────
  ├─ Scoring Philosophy
  │  └─ 5 Core Design Principles
  ├─ Component Breakdown
  │  ├─ Engagement explanation
  │  ├─ Recency explanation
  │  ├─ Profile Fit explanation
  │  └─ Account Intent explanation
  ├─ Formula Visualization
  │  └─ Interactive weighting demo
  ├─ Edge Cases
  │  ├─ Competitor handling
  │  ├─ Orphan contact handling
  │  ├─ Opt-out handling
  │  └─ Broken link handling
  └─ Design Tradeoffs

Page 5 and Page 6 are currently not exposed in the top-level Streamlit navigation, but the app folder retains modular support for knowledge base and reviewer playground functionality for future expansion.

Shared Utils (utils.py)
──────────────────────
  ├─ Data Loading
  │  └─ @st.cache_data load_unified_data()
  ├─ Filtering Functions
  │  ├─ filter_by_tier()
  │  ├─ filter_by_entity_type()
  │  └─ search_records()
  ├─ Visualization Functions
  │  ├─ plot_score_distribution()
  │  ├─ plot_tier_breakdown()
  │  ├─ plot_component_bars()
  │  └─ plot_timeline()
  ├─ Export Functions
  │  ├─ export_to_csv()
  │  ├─ export_to_json()
  │  └─ export_filtered()
  └─ Formatting Functions
     ├─ format_score()
     ├─ tier_color()
     └─ entity_icon()
```

---

## 9. Data Model Diagram

### 9.1 Entity-Relationship Overview

For a visual ER layout, see [ER_DIAGRAM.md](./ER_DIAGRAM.md).

```
DATA MODEL - KEY ENTITIES & RELATIONSHIPS
════════════════════════════════════════════

RAW SOURCE ENTITIES
┌──────────────────────┐      ┌──────────────────────────────────┐      ┌──────────────────────────────┐
│   ACCOUNTS           │      │   CONTACTS                       │      │   LEADS                      │
├──────────────────────┤1    *├──────────────────────────────────┤      ├──────────────────────────────┤
│ account_id (PK)      │──────│ contact_id (PK)                  │      │ lead_id (PK)                 │
│ account_name         │      │ account_id (FK)                  │      │ email                        │
│ industry             │      │ email                            │      │ first_name                   │
│ employee_count       │      │ first_name                       │      │ last_name                    │
│ annual_revenue       │      │ last_name                        │      │ title                        │
│ country              │      │ title                            │      │ company                      │
│ is_icp_qualified     │      │ contact_status                   │      │ job_persona                  │
│ is_named_account     │      │ job_persona                      │      │ job_level                    │
│ intent_score         │      │ job_level                        │      │ lead_status                  │
│ do_not_contact       │      │ mql_date                         │      │ lead_source                  │
│ created_date         │      │ mkto_contact_score               │      │ is_converted                 │
│ buying_committee_size│      │ has_lead_origin                  │      │ converted_contact_id (FK)    │
│ dq_flags (JSON)      │      │ primary_lead_id (FK)             │      │ has_opted_out                │
│ (+ score fields)     │      │ no_longer_with_company           │      │ email_bounced                │
└──────────────────────┘      │ has_opted_out                    │      │ created_date                 │
                               └──────────────────────────────────┘      │ mql_date                     │
                                                                     │ dq_flags (JSON)              │
                                                                     │ (+ score fields)             │
                                                                     └──────────────────────────────┘

        ▲                                     ▲                     ▲
        │                                     │                     │
        │                                     │                     │
        │                                     │                     │
        │                                     │                     │
        │                                     │                     │
        │                                     │                     │
        │                                     │                     │
        │                                     │                     │
        │  1..* mapped via raw entity ids    │                     │
        │                                     │                     │
        │                                     │                     │
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ MASTER_PERSON                                                                       │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ master_person_id (PK)                                                                │
│ preferred_entity_id                                                                  │
│ preferred_entity_type                                                                │
│ lead_id                                                                             │
│ contact_id                                                                          │
│ email                                                                               │
│ normalized_email                                                                    │
│ account_id (FK)                                                                     │
│ has_lead_record                                                                     │
│ has_contact_record                                                                  │
│ is_connected_pair                                                                   │
│ broken_conversion_link_flag                                                         │
│ duplicate_email_flag                                                                │
│ shared_mailbox_flag                                                                 │
│ entity_resolution_confidence                                                        │
└───────────────────────────────────────────────────────────────────────────────────────┘
        ▲
        │ 1..* maps
        │
┌───────────────────────────────────────────────────┐
│ ENTITY_RESOLUTION_MAP                              │
├───────────────────────────────────────────────────┤
│ raw_entity_id (PK)                                 │
│ master_person_id (FK)                              │
│ entity_type (Lead/Contact)                         │
└───────────────────────────────────────────────────┘

PROCESSED PERSON MODEL
──────────────────────────────────────────────────────────────────────────────────────
┌───────────────────────────────────────────────────┐      ┌──────────────────────────────────────┐
│ PERSON_FEATURES                                   │      │ PERSON_SCORES                        │
├───────────────────────────────────────────────────┤1    1├──────────────────────────────────────┤
│ master_person_id (PK)                             │──────│ master_person_id (PK, FK)            │
│ account_id (FK)                                   │      │ engagement_score                     │
│ engagement_30d                                    │      │ recency_score                        │
│ recency_30d                                       │      │ profile_fit_score                    │
│ persona_senior                                    │      │ account_score                        │
│ is_named_account                                  │      │ readiness_score                      │
│ profile_completeness                              │      │ score_percentile                     │
│ account_intent_signal                             │      │ priority_tier                        │
│ account_growth                                    │      │ readiness_band                       │
│ additional feature columns                        │      │ eligibility_status                   │
└───────────────────────────────────────────────────┘      │ structural_block_flag               │
                                                             │ top_positive_reasons                 │
                                                             │ top_negative_reasons                 │
                                                             └──────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│ PERSON_AGENT_RECOMMENDATIONS                                  │
├───────────────────────────────────────────────────────────────┤
│ master_person_id (PK, FK)                                     │
│ why_summary                                                   │
│ where_signal_summary                                          │
│ recommended_action                                            │
│ why_now_summary                                               │
│ talking_points                                                │
│ risk_note                                                     │
└───────────────────────────────────────────────────────────────┘

NOTES
─────
- `CAMPAIGN_MEMBERS` links to both `LEADS` and `CONTACTS` by `entity_id` + `entity_type`.
- `MASTER_PERSON` is the unified entity produced by Stage 01 entity resolution.
- `PERSON_FEATURES` and `PERSON_SCORES` are joined by `master_person_id` for scoring and UI consumption.
- `PERSON_AGENT_RECOMMENDATIONS` stores the AI-friendly explainers used by the Opportunity Workbench and Prospect Brief pages.

``` 

---

## 10. Workflow Diagrams

### 10.1 Data Processing Workflow

```
DATA PROCESSING WORKFLOW
═════════════════════════════

┌─ START ─┐
    │
    ▼
┌─────────────────────────┐
│ 1. LOAD DATA            │
│ - Read 4 CSV files      │
│ - Validate schema       │
│ - Check row counts      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 2. RUN STAGE 01         │
│ - Link entities         │
│ - Detect dupes          │
│ - Flag DQ issues        │
└────────┬────────────────┘
         │
         ▼
    [ Save ]  ◄─── Checkpoint 1
         │
         ▼
┌─────────────────────────┐
│ 3. RUN STAGE 02         │
│ - Engineer features     │
│ - Calculate recency     │
│ - Normalize data        │
└────────┬────────────────┘
         │
         ▼
    [ Save ]  ◄─── Checkpoint 2
         │
         ▼
┌─────────────────────────┐
│ 4. RUN STAGE 03         │
│ - Score components      │
│ - Combine weights       │
│ - Assign tiers          │
└────────┬────────────────┘
         │
         ▼
    [ Save ]  ◄─── Checkpoint 3 (Scoring Complete)
         │
         ▼
┌─────────────────────────┐
│ 5. RUN STAGE 04         │
│ - Generate narratives   │
│ - Identify factors      │
│ - Format explanations   │
└────────┬────────────────┘
         │
         ▼
    [ Save ]  ◄─── Checkpoint 4 (Final)
         │
         ▼
┌─────────────────────────┐
│ 6. EXPORT OUTPUT        │
│ - CSV file              │
│ - JSON export           │
│ - DB insert (optional)  │
└────────┬────────────────┘
         │
         ▼
    [ END ]
```

### 10.2 Interactive Session Workflow

```
INTERACTIVE SESSION WORKFLOW
═════════════════════════════

┌─ START ─┐
    │
    ▼
┌────────────────────────────────┐
│ STREAMLIT APP LAUNCH           │
│ streamlit run streamlit_app.py │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ LOAD PRE-SCORED DATA       │
│ (from CSV or cache)        │
│ @st.cache_data             │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ RENDER MAIN UI             │
│ - Config page              │
│ - Sidebar navigation       │
│ - Select first page        │
└────────┬───────────────────┘
         │
    ┌────┼────┐
    │    │    │ User clicks page
    │    │    │ or interacts
    │    ▼
    ├─ Analytics Dashboard
    │  ├─ Load KPIs
    │  ├─ Render charts
    │  └─ Update on filter change
    │
    ├─ Ranked Records
    │  ├─ Load top 50 records
    │  ├─ Apply filters
    │  ├─ Sort on user request
    │  ├─ Click → goto 360° Detail
    │  └─ Export button → CSV
    │
    ├─ 360° Record Detail
    │  ├─ Load single record
    │  ├─ Render all sections
    │  ├─ Show explanation
    │  ├─ Show timeline
    │  └─ Navigate to prev/next
    │
    ├─ Methodology
    │  ├─ Render static text
    │  ├─ Display formula
    │  └─ Show examples
    │
    ├─ Knowledge Base
    │  ├─ Load markdown
    │  ├─ Render tables
    │  └─ Link to references
    │
    └─ Playground
       ├─ Load weight controls
       ├─ Allow adjustments
       ├─ Recalculate on save
       └─ Show comparison
```

---

## 11. Error Handling & Validation

### 11.1 Data Quality Checks

```
VALIDATION CHECKPOINTS
═══════════════════════════

Stage 01 - Entity Resolution
────────────────────────────
✓ Email format validation
✓ Date range validation
✓ Duplicate email detection
✓ Broken link detection (is_converted but no contact_id)
✓ Null value handling
✓ Company name validation

Stage 02 - Feature Engineering
──────────────────────────────
✓ Engagement counts ≥ 0
✓ Dates in chronological order
✓ Recency scores in [0, 100]
✓ Profile completeness in [0, 100]
✓ No NaN values in output
✓ Time decay curve validation

Stage 03 - Component Scoring
────────────────────────────
✓ Component scores in [0, 100]
✓ Final score in [0, 100]
✓ Weighted average calculation
✓ Tier assignment correct (score → tier)
✓ No missing scores
✓ Score distribution not all high/low

Stage 04 - Explanation
─────────────────────
✓ Top 3 factors identified
✓ Narrative text not empty
✓ DQ flags populated where needed
✓ Recommendations provided
✓ Text character limits respected
✓ JSON serialization successful
```

---

**Document Version:** 1.0  
**Created:** 2026-05-31  
**Architecture Diagrams - Complete**
