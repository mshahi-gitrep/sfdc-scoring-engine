# Salesforce Data Model

Account
├── Contact
│   └── CampaignMember
│
Lead
├── CampaignMember
│
Lead Conversion
Lead
→ Contact
→ Account

Entity Populations

1. Orphan Leads
2. Connected Lead-Contact Pairs
3. Orphan Contacts

Target Volumes

Accounts: 200
Leads: 600
Contacts: 400
CampaignMembers: 5000

Connected Pairs: ~200

Data Quality Issues

DQ-1
DQ-2
DQ-4
DQ-6
DQ-7
DQ-8
DQ-9
DQ-10
