# End-to-End Application Architecture

This file captures the full SFDC Scoring Engine architecture from raw data ingestion through model scoring, explanation generation, and Streamlit application delivery.

```mermaid
flowchart LR
    subgraph Data[Data Layer]
        A1[Accounts CSV] --> D1[Raw Data Ingestion]
        A2[Leads CSV] --> D1
        A3[Contacts CSV] --> D1
        A4[CampaignMembers CSV] --> D1
        D1 --> P1[Generator / CSV Loader]
    end

    subgraph Pipeline[Pipeline Layer]
        P1 --> E1[Stage 01: Entity Resolution]
        E1 --> E2[Stage 02: Feature Engineering]
        E2 --> E3[Stage 03: Component Scoring]
        E3 --> E4[Stage 04: Agentic Explainer]
    end

    subgraph Processed[Processed Output]
        E1 --> M1[master_persons.csv]
        E2 --> F1[person_features.csv]
        E3 --> S1[person_scores.csv]
        E4 --> R1[person_agent_recommendations.csv]
        M1 --> F1
        F1 --> S1
        S1 --> R1
    end

    subgraph App[Application Layer]
        U1[streamlit_app.py]
        U2[Dashboard Page]
        U3[Opportunity Workbench]
        U4[Prospect Brief]
        U5[Methodology Page]
        U6[Knowledge Base / Reviewer Playground]
        U1 --> U2
        U1 --> U3
        U1 --> U4
        U1 --> U5
        U1 --> U6
    end

    subgraph Utilities[Supporting Services]
        U7[app/utils.py]
        U8[Auto-regenerate Stage 04]
        U9[CSV Export / API support]
        U7 --> U8
        U7 --> U9
        S1 --> U7
        R1 --> U7
    end

    P1 -->|source data| E1
    E4 -->|explained scores| U7
    U7 -->|loads latest files| U1
    R1 --> U4
    S1 --> U2
    S1 --> U3
    S1 --> U4
    U9 -->|optional| U10[UI Data Export]

    classDef layer fill:#f4f7ff,stroke:#a3bffa,stroke-width:1px;
    class Data,Pipeline,Processed,App,Utilities layer;
```