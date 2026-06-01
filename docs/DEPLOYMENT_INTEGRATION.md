# SFDC Scoring Engine - Deployment & Integration Guide

Comprehensive deployment architectures, integration points, and operational workflows.

---

## 1. Deployment Architecture

### 1.1 Deployment Models

```
DEPLOYMENT OPTIONS
═════════════════════════════════════════════════════════════════

OPTION 1: BATCH SCORING (Simple)
─────────────────────────────────

    ┌────────────────────────────────────────┐
    │ data/raw/                               │
    │ ├─ accounts_data.csv                     │
    │ ├─ leads_data.csv                        │
    │ ├─ contacts_data.csv                     │
    │ └─ campaign_members_data.csv             │
    └───────────────┬─────────────────────────┘
                    │
                    ▼
            ┌─────────────────────────────────┐
            │ pipeline/stage01_entity_resolution.py │
            │ pipeline/stage02_feature_engineering.py │
            │ pipeline/stage03_component_scoring.py │
            │ stage04_agentic_explainer.py (module) │
            └───────┬─────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────────────────────────────┐
        │ data/processed/person_scores.csv                 │
        │ data/processed/person_agent_recommendations.csv  │
        └──────────────────────────────────────────────────┘

Execution:
─────────
$ python -m pipeline.stage01_entity_resolution
$ python -m pipeline.stage02_feature_engineering
$ python -m pipeline.stage03_component_scoring

Use Case:
─────────

Timing:
───────
• 1000 records: 25-35 seconds total
• 10,000 records: 3-5 minutes
• 100,000 records: 30-45 minutes

Use Case:
─────────
• One-time scoring
• Nightly batch jobs
• Data validation runs
• Historical data scoring


OPTION 2: INTERACTIVE DASHBOARD (Development)
──────────────────────────────────────────────

    ┌────────────────────────────────────────────┐
    │ data/processed/person_scores.csv           │
    │ (Pre-scored results)                       │
    └───────────────┬────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────┐
        │ streamlit run             │
        │ streamlit_app.py          │
        └──────────┬─────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Streamlit Server         │
        │ localhost:8501           │
        └──────────┬─────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Browser / User Client    │
        │ 4 Pages                  │
        │ - Who Should We Call This Week?    │
        │ - Opportunity Workbench            │
        │ - Prospect Brief                   │
        │ - How The Readiness Model Works    │
        └──────────────────────────┘

Execution:
─────────
$ streamlit run streamlit_app.py

Access:
──────
Local: http://localhost:8501
Remote: http://<server-ip>:8501

Use Case:
─────────
• Interactive exploration
• Reviewer feedback
• A/B testing scoring weights
• Real-time filtering & sorting


OPTION 3: HYBRID BATCH + LIVE (Production-Ready)
─────────────────────────────────────────────────

    ┌─────────────────┐
    │ RAW DATA SOURCE │
    │ (Salesforce)    │
    └────────┬────────┘
             │
             ▼ Daily Extract (ETL job)
    ┌─────────────────────────────────┐
    │ data/                            │
    │ ├─ accounts.csv                  │
    │ ├─ leads.csv                     │
    │ ├─ contacts.csv                  │
    │ └─ campaign_members.csv          │
    └────────┬────────────────────────┘
             │
             ▼ Cron: 01:00 UTC daily
    ┌──────────────────────────────────────────────────┐
    │ BATCH SCORING JOB                                 │
    │ python -m pipeline.stage01_entity_resolution      │
    │ python -m pipeline.stage02_feature_engineering    │
    │ python -m pipeline.stage03_component_scoring      │
    │ python -c "from pipeline.stage04_agentic_explainer import SalesforceAgenticExplainer; SalesforceAgenticExplainer().calculate_recommendations()" │
    │                                                  │
    │ Stages 01-04                                     │
    └────────┬─────────────────────────────────────────┘
             │
             ▼ ~30 min execution
    ┌──────────────────────────────────────────────────────────┐
    │ data/processed/person_scores.csv                       │
    │ data/processed/person_agent_recommendations.csv        │
    │ (Latest processed results)                             │
    │                                                         │
    │ Optional: Write to DB                                   │
    │ Optional: POST to API                                   │
    └────────┬─────────────────────────────────────────────────┘
             │
             ├─ Backup CSV
             │
             ▼ User accesses
    ┌──────────────────────────────────────────────────┐
    │ LIVE DASHBOARD                                    │
    │ streamlit_app.py                                 │
    │                                                  │
    │ Loads latest data/processed/person_scores.csv    │
    │ Cached for performance                           │
    │ Refresh button available                         │
    └──────────────────────────────────────────────────┘

Cron Schedule:
──────────────
# Run scoring nightly at 1 AM
0 1 * * * cd /path/to/sfdc-scoring-engine && python -m pipeline.stage01_entity_resolution && python -m pipeline.stage02_feature_engineering && python -m pipeline.stage03_component_scoring

Monitoring:
───────────
✓ Log execution time
✓ Alert on errors
✓ Track record count
✓ Version the output files
```

---

## 2. System Architecture - Production

### 2.1 Full Production Stack

```
PRODUCTION ARCHITECTURE
═══════════════════════════════════════════════════════════════

                        EXTERNAL SYSTEMS
                        ────────────────

        ┌──────────────────────────────────────┐
        │         SALESFORCE                    │
        │  (Source of Truth for CRM Data)      │
        │  - Accounts                           │
        │  - Leads                              │
        │  - Contacts                           │
        │  - Campaign Members                   │
        └──────────┬───────────────────────────┘
                   │
                   │ Daily ETL Export
                   │ (Scheduled job)
                   ▼
        ┌──────────────────────────┐
        │  DATA PIPELINE LAYER     │
        │                          │
        │  Server: EC2/GCP VM      │
        │  OS: Linux               │
        │  Runtime: Python 3.10+   │
        │                          │
        │  /data/raw/ directory:   │
        │  ├─ accounts_data.csv     │
        │  ├─ leads_data.csv        │
        │  ├─ contacts_data.csv     │
        │  └─ campaign_members_data.csv │
        │                          │
        │  /data/processed/ directory: │
        │  ├─ master_persons.csv     │
        │  ├─ entity_resolution_map.csv │
        │  ├─ person_features.csv    │
        │  ├─ person_scores.csv      │
        │  └─ person_agent_recommendations.csv │
        │                          │
        │  /pipeline/:             │
        │  ├─ stage01_*.py         │
        │  ├─ stage02_*.py         │
        │  ├─ stage03_*.py         │
        │  └─ stage04_*.py         │
        │                          │
        │  Requirements:           │
        │  ├─ pandas               │
        │  ├─ numpy                │
        │  ├─ scipy                │
        │  └─ scikit-learn         │
        └─────────┬──────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
     CSV      Database    API
    Export    Insert     Webhook
        │         │         │
        │         ▼         ▼
        │    ┌─────────────────────────────┐
        │    │   DATA STORE LAYER          │
        │    │                             │
        │    │  Option A: PostgreSQL       │
        │    │  └─ scored_records table    │
        │    │                             │
        │    │  Option B: MongoDB          │
        │    │  └─ scored_entities coll    │
        │    │                             │
        │    │  Option C: Cloud Storage    │
        │    │  └─ S3 / GCS buckets        │
        │    └──────────┬──────────────────┘
        │               │
        └───────────────┼────────────┬──────────────────┐
                        │            │                  │
                        ▼            ▼                  ▼
            ┌──────────────────┐  ┌───────────────┐  ┌──────────────┐
            │  API LAYER       │  │  FILE EXPORT  │  │ NOTIFICATION │
            │                  │  │               │  │              │
            │ Flask/FastAPI    │  │ CSV/JSON      │  │ Webhooks     │
            │ Endpoints:       │  │ Downloads     │  │ Email alerts │
            │ /score/{id}      │  │               │  │ Slack msgs   │
            │ /search?query    │  │               │  │              │
            │ /export          │  │               │  │              │
            │ /health          │  │               │  │              │
            │                  │  │               │  │              │
            │ Port: 5000       │  │               │  │              │
            └────────┬─────────┘  └──────────┬────┘  └────────┬─────┘
                     │                       │               │
                     └───────────────────────┼───────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
        ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
        │ FRONTEND LAYER       │  │ MONITORING & LOGGING │  │ EXTERNAL SYSTEMS │
        │                      │  │                      │  │                  │
        │ Streamlit UI         │  │ • CloudWatch (AWS)   │  │ • Slack          │
        │ Port: 8501           │  │ • Stackdriver (GCP)  │  │ • Email          │
        │                      │  │ • ELK Stack (OSS)    │  │ • Salesforce     │
        │ Pages:               │  │ • Prometheus         │  │ • CRM            │
        │ • Dashboard          │  │ • Grafana            │  │                  │
        │ • Ranked Queue       │  │                      │  │                  │
        │ • 360° Detail        │  │ Metrics:             │  │                  │
        │ • Methodology        │  │ • Pipeline duration  │  │                  │
        │ • Knowledge Base     │  │ • Record count       │  │                  │
        │ • Playground         │  │ • Error rate         │  │                  │
        │                      │  │ • Cache hit ratio    │  │                  │
        │ Performance:         │  │ • API response time  │  │                  │
        │ • Cached data        │  │ • UI page load time  │  │                  │
        │ • 1-2 sec load       │  │                      │  │                  │
        │ • 50+ records/page   │  │ Logging:             │  │                  │
        │                      │  │ • Execution logs     │  │                  │
        │ Auth:                │  │ • Error traces       │  │                  │
        │ • LDAP / OAuth2      │  │ • Audit trails       │  │                  │
        │ • Multi-user         │  │ • Alert history      │  │                  │
        │ • Row-level access   │  │                      │  │                  │
        └──────────────────────┘  └──────────────────────┘  └──────────────────┘
                    │                        │                        │
                    └────────────────────────┴────────────────────────┘
                                             │
                                             ▼
                        ┌────────────────────────────────────────┐
                        │  USERS                                 │
                        │  - Sales Managers (view only)          │
                        │  - Reviewers (full access)             │
                        │  - Admins (configuration)              │
                        │  - Data Analysts (export access)       │
                        └────────────────────────────────────────┘
```

---

## 3. Integration Points

### 3.1 Salesforce Integration

```
SALESFORCE INTEGRATION
═════════════════════════════════════════════════════════════

┌─────────────────────────────────┐
│ SALESFORCE PRODUCTION            │
│ ├─ Account object                │
│ ├─ Lead object                   │
│ ├─ Contact object                │
│ ├─ CampaignMember object         │
│ └─ Custom fields (optional):     │
│    ├─ Readiness_Score__c         │
│    ├─ Readiness_Tier__c          │
│    ├─ Engagement_Score__c        │
│    ├─ Recency_Score__c           │
│    ├─ Profile_Fit_Score__c       │
│    ├─ Account_Intent_Score__c    │
│    ├─ Readiness_Explanation__c   │
│    ├─ Top_Factors__c             │
│    ├─ DQ_Flags__c                │
│    └─ Last_Scored_Date__c        │
└──────────────┬────────────────────┘
               │
        ┌──────┴──────┐
        │             │
EXTRACT │             │ WRITE-BACK
    ┌───▼────┐    ┌────▼──────┐
    │ Batch  │    │ Scheduled │
    │ Export │    │ Update    │
    │ (Nightly)   │ Job       │
    └───┬────┘    └────┬──────┘
        │              │
        ▼              ▼
   CSV/Parquet    Salesforce REST API
        │         ├─ Bulk API 2.0
        │         ├─ REST API (batch)
        │         └─ Async API
        │
        ▼
   SCORING ENGINE
        │
        ├─ Load records
        ├─ Stage 01-04
        ├─ Generate scores
        └─ Prepare updates
        │
        ▼
   WRITE-BACK PROCESS
   ├─ Transform scores to SF format
   ├─ Handle duplicates
   ├─ Validate before insert
   ├─ Batch into groups of 10k
   ├─ POST to Salesforce
   ├─ Handle partial failures
   ├─ Retry failed records
   └─ Log success/failure

Example Bulk API Job:
────────────────────
POST /services/data/v60.0/jobs/ingest
{
  "object": "Lead",
  "operation": "upsert",
  "externalIdFieldName": "Id",
  "contentType": "CSV"
}

CSV Upload:
───────────
Id,Readiness_Score__c,Readiness_Tier__c,Last_Scored_Date__c
00Q2x000000IZ3EEAU,85,High,2026-05-31
00Q2x000000IZ3FEAF,42,Low,2026-05-31
...

Upsert Rate:
────────────
• 10,000 records: ~2-3 minutes
• 100,000 records: ~15-20 minutes
• Job runs nightly after scoring completes

Error Handling:
───────────────
✓ Validate score format before upload
✓ Catch duplicate key errors
✓ Retry with backoff on rate limits
✓ Log all failures for review
✓ Alert on high failure rate (>5%)
✓ Keep manual review queue for edge cases
```

### 3.2 CRM System Integration

```
CRM INTEGRATION (Alternative Targets)
════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────┐
│ SCORING ENGINE OUTPUT                                  │
│                                                        │
│ data/processed/person_scores.csv / JSON API            │
└────────────┬──────────────────────────────────────────┘
             │
    ┌────────┼────────┬──────────┬──────────┐
    │        │        │          │          │
    ▼        ▼        ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│SFDC  │ │Hubspot│ │Pipedrive│ │Copper│ │Custom CRM│
│Leads │ │Contacts│ │Deals    │ │      │ │          │
└──────┘ └──────┘ └──────┘ └──────┘ └──────────┘

Integration Methods:
────────────────────

1. CSV Import (Simplest)
   └─ Export CSV from Engine
   └─ Import to CRM manually or via UI

2. REST API (Recommended)
   └─ Engine calls CRM API endpoint
   └─ Updates records programmatically
   └─ Handles retries automatically

3. Webhook (Real-time)
   └─ Engine triggers webhook on score change
   └─ CRM receives and processes update
   └─ Enables real-time workflows

4. Scheduled Sync (Robust)
   └─ CRM pulls scores from our API nightly
   └─ CRM maintains control of sync schedule
   └─ Reduces dependency on our job timing

Example: HubSpot Integration
────────────────────────────

PUT https://api.hubapi.com/crm/v3/objects/contacts/batch/update

{
  "inputs": [
    {
      "id": "hub_contact_id_123",
      "properties": {
        "readiness_score": "85",
        "readiness_tier": "High",
        "engagement_score": "82",
        "recency_score": "95",
        "profile_fit": "90",
        "account_intent": "75",
        "top_factors": "VP at ICP account;5 webinars;recent",
        "dq_concerns": "Email via ETL bulk load",
        "next_actions": "LinkedIn outreach;research committee"
      }
    }
  ]
}
```

### 3.3 Analytics Platform Integration

```
ANALYTICS INTEGRATION
═══════════════════════════════════════════════════════════

┌──────────────────────────────────┐
│ SCORING ENGINE                    │
│ /pipeline/stage03_component_scoring.py      │
│ & /pipeline/stage04_agentic_explainer.py            │
└──────────────┬───────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│BigQuery│ │Snowflake │ │Redshift  │
│Dataset │ │Schema    │ │Database  │
└────────┘ └──────────┘ └──────────┘

Integration Pattern:
────────────────────

Engine Output → CSV → Cloud Storage (S3/GCS) → DW Import

1. Generate data/processed/person_scores.csv
2. Upload to S3/GCS (versioned path)
3. Cloud DW detects new file
4. Triggers import job
5. Loads into analytics tables
6. Available for BI dashboards

Table Structure:
────────────────
CREATE TABLE analytics.readiness_scores (
  entity_id STRING,
  entity_type STRING,
  email STRING,
  account_name STRING,
  
  -- Scores
  engagement_score INT64,
  recency_score INT64,
  profile_fit_score INT64,
  account_intent_score INT64,
  readiness_score INT64,
  readiness_tier STRING,
  
  -- Explanations
  top_positive_factors STRING,
  top_negative_factors STRING,
  dq_flags STRING,
  recommended_actions STRING,
  explanation_narrative TEXT,
  
  -- Metadata
  scored_date DATE,
  scoring_version STRING,
  
  PRIMARY KEY (entity_id, entity_type, scored_date)
);

BI Dashboard Query:
───────────────────
SELECT
  readiness_tier,
  COUNT(*) as count,
  AVG(engagement_score) as avg_engagement,
  AVG(readiness_score) as avg_score,
  MIN(scored_date) as earliest,
  MAX(scored_date) as latest
FROM analytics.readiness_scores
WHERE scored_date = CURRENT_DATE()
GROUP BY readiness_tier
ORDER BY
  CASE WHEN readiness_tier = 'High' THEN 1
       WHEN readiness_tier = 'Medium' THEN 2
       ELSE 3 END;
```

---

## 4. API Reference

### 4.1 Batch Scoring API

```
SCORING ENGINE - REST API ENDPOINTS
═════════════════════════════════════════════════════════════

Base URL: https://api.scoring-engine.company.com/v1

ENDPOINT 1: Get Record Score
──────────────────────────────────────────────────────────
GET /score/{entity_id}

Parameters:
  entity_id    (required) - Lead ID or Contact ID
  entity_type  (optional) - 'lead' | 'contact' (auto-detect)

Response (200 OK):
{
  "entity_id": "00Q2x000000IZ3EEAU",
  "entity_type": "lead",
  "email": "john.doe@acme.com",
  "name": "John Doe",
  
  "score": 78,
  "tier": "Medium",
  
  "components": {
    "engagement_score": 75,
    "recency_score": 85,
    "profile_fit_score": 80,
    "account_intent_score": 65
  },
  
  "explanation": {
    "positive_factors": [
      "5 webinar attendances in 30 days",
      "VP-level title at target account",
      "Engagement in past 7 days"
    ],
    "negative_factors": [
      "No 2-way email responses",
      "Large buying committee (50+ members)"
    ],
    "dq_flags": ["Email via ETL bulk load"],
    "actions": ["LinkedIn outreach", "Build business case"]
  },
  
  "metadata": {
    "last_scored": "2026-05-31T09:15:00Z",
    "version": "2.1"
  }
}

Error Response (404 Not Found):
{
  "error": "Record not found",
  "entity_id": "unknown123"
}


ENDPOINT 2: Search & Filter
──────────────────────────────────────────────────────────
GET /search

Query Parameters:
  q              - Search by email/name/company
  tier           - 'High' | 'Medium' | 'Low'
  entity_type    - 'lead' | 'contact' | 'all'
  min_score      - Filter by min score (0-100)
  max_score      - Filter by max score (0-100)
  limit          - Number of results (default 50, max 1000)
  offset         - Pagination offset (default 0)
  sort           - Sort by field (score | recency | name)
  direction      - Sort direction (asc | desc)

Example Request:
/search?tier=High&entity_type=lead&sort=score&direction=desc&limit=100

Response (200 OK):
{
  "total_count": 3421,
  "page_size": 100,
  "offset": 0,
  "has_next": true,
  "results": [
    {
      "entity_id": "00Q2x000000IZ3EEAU",
      "email": "vp@bigcorp.com",
      "name": "Jane Smith",
      "company": "Big Corp Inc",
      "score": 95,
      "tier": "High"
    },
    ...
  ]
}


ENDPOINT 3: Bulk Export
──────────────────────────────────────────────────────────
POST /export

Request Body:
{
  "entity_type": "all",  // or "lead" | "contact"
  "tier": "High",        // or null for all tiers
  "format": "csv",       // or "json" | "parquet"
  "include_explanation": true,
  "fields": ["entity_id", "score", "tier", "engagement_score"]  // optional
}

Response (202 Accepted):
{
  "job_id": "exp_abc123def456",
  "status": "pending",
  "created_at": "2026-05-31T10:00:00Z",
  "estimated_duration": "30 seconds"
}

Poll Status:
GET /export/exp_abc123def456/status

Response:
{
  "job_id": "exp_abc123def456",
  "status": "completed",
  "record_count": 350,
  "file_url": "https://storage.company.com/exports/exp_abc123def456.csv",
  "expires_at": "2026-06-07T10:00:00Z"
}


ENDPOINT 4: Regenerate Scores
──────────────────────────────────────────────────────────
POST /rescore

Request Body:
{
  "weights": {
    "engagement": 0.40,
    "recency": 0.30,
    "profile_fit": 0.20,
    "account_intent": 0.10
  },
  "entity_ids": ["00Q2x000000IZ3EEAU"],  // optional, all if omitted
  "tier_boundaries": {
    "high_min": 75,
    "medium_min": 50
  }
}

Response (200 OK):
{
  "job_id": "rescore_xyz789",
  "status": "submitted",
  "records_submitted": 1,
  "estimated_duration": "5 seconds",
  "callback_url": "https://..."  // optional webhook
}


ENDPOINT 5: Health Check
──────────────────────────────────────────────────────────
GET /health

Response (200 OK):
{
  "status": "healthy",
  "timestamp": "2026-05-31T10:15:30Z",
  "version": "2.1",
  "data_freshness": {
    "last_scoring_run": "2026-05-31T01:00:00Z",
    "record_count": 1047,
    "staged_at": "2026-05-31T10:14:22Z"
  },
  "performance": {
    "avg_response_time_ms": 45,
    "p95_response_time_ms": 120,
    "cache_hit_rate": 0.92
  },
  "errors_24h": 2
}

Health Response (503 Service Unavailable):
{
  "status": "degraded",
  "timestamp": "2026-05-31T10:15:30Z",
  "reason": "Last scoring run failed 2 hours ago",
  "last_known_good": "2026-05-30T01:00:00Z",
  "error_details": "..."
}
```

---

## 5. Monitoring & Operations

### 5.1 Operational Dashboards

```
MONITORING DASHBOARDS
═════════════════════════════════════════════════════════════

Dashboard 1: PIPELINE HEALTH
──────────────────────────────

Status Indicators:
├─ Last Scoring Run
│  ├─ Success / Failure
│  ├─ Duration (Target: <30 min)
│  ├─ Record Count
│  └─ Error Rate
│
├─ Data Quality
│  ├─ DQ Issues Found
│  ├─ Broken Links %
│  ├─ Duplicate Emails %
│  └─ Opt-outs %
│
├─ Score Distribution
│  ├─ Avg Score
│  ├─ Median Score
│  ├─ Std Deviation
│  └─ Tier Breakdown (% High/Med/Low)
│
└─ Resource Usage
   ├─ CPU %
   ├─ Memory %
   ├─ Disk Usage
   └─ Network I/O

Alerts:
├─ ⚠️  Pipeline took > 45 min
├─ ⚠️  Error rate > 5%
├─ ⚠️  Data freshness > 24h
├─ 🔴 No records scored (< 100)
└─ 🔴 Broken links > 50%


Dashboard 2: API PERFORMANCE
──────────────────────────────

Request Metrics:
├─ Total Requests (24h)
├─ Requests per Second (RPS)
├─ Error Rate %
├─ Success Rate %
│
├─ Endpoint Performance
│  ├─ /score/{id}         : 45ms avg
│  ├─ /search             : 120ms avg
│  ├─ /export             : async
│  └─ /health             : 5ms avg
│
├─ Response Time Percentiles
│  ├─ p50: 45ms
│  ├─ p95: 110ms
│  └─ p99: 250ms
│
└─ Cache Performance
   ├─ Hit Rate: 92%
   ├─ Miss Rate: 8%
   ├─ Memory: 4.2 GB / 8 GB
   └─ Evictions: 342 items

Alerts:
├─ ⚠️  Error rate > 1%
├─ ⚠️  Response time p95 > 200ms
├─ ⚠️  Cache hit rate < 80%
└─ 🔴 RPS spike > 2x baseline


Dashboard 3: BUSINESS METRICS
──────────────────────────────

Coverage:
├─ Total Leads Scored: 1,200
├─ Total Contacts Scored: 800
├─ Coverage %: 92% of addressable universe
└─ New Records Scored Today: 45

Quality:
├─ Avg Engagement Score: 48
├─ Avg Recency Score: 62
├─ Avg Profile Fit Score: 55
├─ Avg Account Intent Score: 41
├─ Final Avg Readiness: 54

Distribution:
├─ High Priority (80-100): 12% (≈ 144 records)
├─ Medium Priority (60-79): 31% (≈ 372 records)
└─ Low Priority (0-59): 57% (≈ 684 records)

Trends:
├─ High Priority Count: ↑ 8% from last week
├─ Avg Score Trend: ↑ 2 points from last week
├─ Stale Records %: ↓ 5% from last week
└─ DQ Issues: ↔ Stable

Engagement:
├─ Total Engagements: 2,847 (last 30d)
├─ Avg per Record: 2.7
├─ High Recency Records: 34%
└─ No Engagement: 42%
```

### 5.2 Alert Rules

```
ALERT RULES & THRESHOLDS
═════════════════════════════════════════════════════════════

CATEGORY: PIPELINE EXECUTION
─────────────────────────────

Alert 1: Scoring Job Failure
  Condition: Last scoring run status = FAILED
  Severity: CRITICAL
  Action: Email + Slack + PagerDuty
  Recovery: Check logs, restart job, notify team

Alert 2: Slow Pipeline
  Condition: Pipeline duration > 45 minutes
  Severity: WARNING
  Action: Slack notification
  Recovery: Investigate performance, consider optimization

Alert 3: Data Staleness
  Condition: Last successful score > 36 hours old
  Severity: WARNING
  Action: Slack notification
  Recovery: Check data extract, verify source systems

Alert 4: Low Record Count
  Condition: Scored records < 100
  Severity: CRITICAL
  Action: Email + Slack + PagerDuty
  Recovery: Verify data sources, check data validation


CATEGORY: API PERFORMANCE
──────────────────────────

Alert 5: High Error Rate
  Condition: Error rate > 5% (5 min window)
  Severity: CRITICAL
  Action: Page on-call
  Recovery: Check database, verify cache, restart service

Alert 6: Slow API Response
  Condition: p95 response time > 500ms (5 min window)
  Severity: WARNING
  Action: Slack notification
  Recovery: Check load, optimize queries, scale resources

Alert 7: Cache Miss Rate
  Condition: Cache hit rate < 70% (1 hour window)
  Severity: INFO
  Action: Log only
  Recovery: Analyze access patterns, adjust cache TTL


CATEGORY: DATA QUALITY
──────────────────────

Alert 8: High Broken Link Rate
  Condition: Broken links > 30% of conversions
  Severity: WARNING
  Action: Slack notification
  Recovery: Investigate data quality, notify team

Alert 9: Unusual Score Distribution
  Condition: > 80% of scores in single tier
  Severity: WARNING
  Action: Slack notification
  Recovery: Review scoring logic, check data quality

Alert 10: Duplicate Email Spike
  Condition: Duplicate emails > 25%
  Severity: WARNING
  Action: Slack notification
  Recovery: Investigate source data, run dedup audit
```

---

## 6. Disaster Recovery

### 6.1 Backup & Recovery Strategy

```
BACKUP & DISASTER RECOVERY
═════════════════════════════════════════════════════════════

Backup Objects:
───────────────

1. Input Data (Raw CSV files)
   ├─ Frequency: Daily (after extract)
   ├─ Retention: 90 days
   ├─ Location: S3 versioned bucket
   ├─ RPO: 24 hours
   └─ RTO: < 1 hour (restore from snapshot)

2. Scored Output
   ├─ Frequency: After each pipeline run
   ├─ Retention: 30 days (full), 365 days (daily snapshot)
   ├─ Location: S3 + Archive Storage
   ├─ RPO: 0 (incremental after run)
   └─ RTO: < 5 minutes (serve from snapshot)

3. Database Backups (if used)
   ├─ Frequency: Hourly incremental, daily full
   ├─ Retention: 30 days
   ├─ Location: AWS RDS backup storage
   ├─ RPO: 1 hour
   └─ RTO: < 15 minutes (restore to point-in-time)

4. Application Code
   ├─ Frequency: On commit (Git)
   ├─ Retention: Indefinite
   ├─ Location: GitHub + S3 artifact store
   ├─ RPO: 0 (version controlled)
   └─ RTO: < 5 minutes (re-deploy)

5. Configuration
   ├─ Frequency: On change
   ├─ Retention: Indefinite
   ├─ Location: GitHub (config repo)
   ├─ RPO: 0 (version controlled)
   └─ RTO: < 5 minutes (restart with new config)

Restore Procedures:
───────────────────

Scenario 1: Pipeline Script Error
  Step 1: Revert code to last known good version
  Step 2: Re-run pipeline with current input data
  Step 3: Validate output scores
  Step 4: Deploy fix to production
  Duration: ~35 minutes

Scenario 2: Input Data Corruption
  Step 1: Restore previous day's CSV backup
  Step 2: Re-run pipeline with restored data
  Step 3: Compare output with last run
  Step 4: Use yesterday's scores as fallback
  Duration: ~40 minutes

Scenario 3: Output Data Loss
  Step 1: Restore data/processed/person_scores.csv from S3 backup
  Step 2: Reload UI cache
  Step 3: Verify API responses
  Step 4: Notify users if <1 day delay
  Duration: ~5 minutes

Scenario 4: Complete System Failure
  Step 1: Spin up new VM instance
  Step 2: Restore application code from Git
  Step 3: Restore latest data from S3
  Step 4: Reconfigure environment variables
  Step 5: Start services
  Step 6: Run smoke tests
  Duration: ~20 minutes
```

---

## 7. Performance Tuning

### 7.1 Optimization Strategies

```
PERFORMANCE TUNING STRATEGIES
═════════════════════════════════════════════════════════════

PIPELINE OPTIMIZATION
──────────────────────

Stage 01 (Entity Resolution):
├─ Current: 10 seconds
├─ Optimization:
│  ├─ Index email columns
│  ├─ Use vectorized string matching
│  ├─ Pre-filter duplicates
│  └─ Parallel processing by account
└─ Target: 5-7 seconds

Stage 02 (Feature Engineering):
├─ Current: 5 seconds
├─ Optimization:
│  ├─ Vectorize date calculations
│  ├─ Pre-aggregate campaigns by type
│  ├─ Use NumPy for recency scores
│  └─ Batch normalize operations
└─ Target: 2-3 seconds

Stage 03 (Scoring):
├─ Current: 3 seconds
├─ Optimization:
│  ├─ Vectorize score calculations
│  ├─ Use NumPy arrays vs. loops
│  ├─ Minimize conditional checks
│  └─ Cache tier thresholds
└─ Target: 1-2 seconds

Stage 04 (Explanation):
├─ Current: 15 seconds
├─ Optimization:
│  ├─ Batch LLM calls (parallel requests)
│  ├─ Cache explanations for common patterns
│  ├─ Use templates for high-volume cases
│  └─ Async explain (non-blocking)
└─ Target: 8-10 seconds

Overall Pipeline Target: 20 seconds (vs. current 30-35 sec)


API OPTIMIZATION
─────────────────

Caching Strategy:
├─ In-Memory Cache (Redis)
│  ├─ Store: Score objects (entity_id → score)
│  ├─ TTL: 1 hour (refresh on pipeline run)
│  ├─ Hit Rate Target: > 90%
│  └─ Size: Max 2 GB
├─ Browser Cache
│  ├─ Static assets: 30 days
│  ├─ Data export: 1 hour
│  └─ API responses: 5 minutes
└─ Query Results Cache
   ├─ Search results: 5 minutes
   ├─ Tier breakdown: 1 hour
   └─ Export jobs: 24 hours

Database Optimization:
├─ Indexing:
│  ├─ entity_id (primary)
│  ├─ email (secondary)
│  ├─ score (for sorting)
│  ├─ tier (for filtering)
│  └─ scored_date (for range queries)
├─ Query Optimization:
│  ├─ Use prepared statements
│  ├─ Limit result sets (pagination)
│  ├─ Avoid N+1 queries
│  └─ Denormalize for common queries
└─ Connection Pooling:
   ├─ Min: 5 connections
   ├─ Max: 50 connections
   └─ Timeout: 30 seconds

Streaming Large Results:
├─ /export endpoint
├─ Stream CSV rows (not load all)
├─ Reduce memory footprint
└─ Enable browser download progress


INFRASTRUCTURE OPTIMIZATION
────────────────────────────

Compute:
├─ Pipeline VM: 4 vCPU, 16 GB RAM
├─ API Server: 2 vCPU, 8 GB RAM (scaled to 4 on demand)
├─ Cache Server: 1 vCPU, 4 GB RAM
└─ Database: 2 vCPU, 8 GB RAM (RDS reserved)

Storage:
├─ Data volume: 5 GB (data + backups)
├─ Archive: Glacier (cold tier, 90+ days old)
├─ CDN: CloudFront for static assets
└─ Compression: gzip for CSV exports

Network:
├─ API latency: ~50ms (same region)
├─ Transfer rate: 100 Mbps minimum
├─ Load balancer: Health check every 10s
└─ DDoS protection: CloudFlare or AWS Shield

Scaling Strategy:
├─ Vertical (before horizontal):
│  ├─ Increase vCPU on pipeline box
│  ├─ Increase RAM for caching
│  └─ Use SSD for database
├─ Horizontal (if needed):
│  ├─ Auto-scale API servers (2-4 replicas)
│  ├─ Read replicas for database
│  ├─ Distributed cache (Redis cluster)
│  └─ Multiple pipeline workers (parallel stages)
└─ Cost optimization:
   ├─ Reserved instances (1-year commitment)
   ├─ Spot instances for batch jobs
   ├─ Right-sized instances (no over-provisioning)
   └─ Archive old backups to Glacier
```

---

**Document Version:** 1.0  
**Created:** 2026-05-31  
**Deployment & Integration - Complete**
