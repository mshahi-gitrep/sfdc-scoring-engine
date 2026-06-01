# End-to-End Architecture

Accounts
 ├─ Contacts
 │   └─ CampaignMembers
 │
 Leads
 └─ CampaignMembers

Lead Conversion

Lead
  → Contact
  → Account

Scoring Pipeline

Raw Data
→ Cleaning
→ Entity Resolution
→ Feature Engineering
→ Component Scoring
→ Final Readiness
→ Explanations