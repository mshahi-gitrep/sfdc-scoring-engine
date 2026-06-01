# SFDC Scoring Engine

CRM Readiness Intelligence Platform for Salesforce-style synthetic data, scoring, and Streamlit decision support.

## Project structure

- `generate_accounts.py`, `generate_campaignmembers.py`, `generate_contacts.py`, `generate_leads.py` - generator entrypoints for synthetic data.
- `streamlit_app.py` - Streamlit root application.
- `data/raw/` - source CSV exports used by the pipeline.
- `data/processed/` - pipeline outputs including `master_persons.csv`, `person_features.csv`, `person_scores.csv`, and `person_agent_recommendations.csv`.
- `pipeline/` - core scoring pipeline stages.
- `app/` - Streamlit page modules and shared utilities.
- `docs/` - architecture, component, and deployment documentation.
- `tests/` - unit and integration tests.
- `requirements.txt` - Python dependencies.

## Getting started

1. Generate or place source files in `data/raw/`.
2. Run Stage 01: `python -m pipeline.stage01_entity_resolution`
3. Run Stage 02: `python -m pipeline.stage02_feature_engineering`
4. Run Stage 03: `python -m pipeline.stage03_component_scoring`
5. Optionally run Stage 04: `python -c "from pipeline.stage04_agentic_explainer import SalesforceAgenticExplainer; SalesforceAgenticExplainer().calculate_recommendations()"`
6. Launch the interactive app: `streamlit run streamlit_app.py`

## Streamlit pages

- `Who Should We Call This Week?`
- `Opportunity Workbench`
- `Prospect Brief`
- `How The Readiness Model Works`

## Documentation

- `docs/INDEX.md`
- `docs/ARCHITECTURE.md`
- `docs/COMPONENT_DIAGRAMS.md`
- `docs/DEPLOYMENT_INTEGRATION.md`
