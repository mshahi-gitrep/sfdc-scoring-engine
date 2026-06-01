"""
Synced Knowledge Base Submodule for Streamlit Application.

Programmatically reads and renders active markdown technical documentation
directly from the disk, ensuring zero documentation drift.

"""

import os
import streamlit as st


def render_knowledge_base():
    """Renders the Synced Knowledge Base page."""
    st.markdown("<h1 style='color: #1E90FF;'>🎯 Synced Knowledge Base</h1>", unsafe_allow_html=True)
    st.markdown("Programmatically synchronized technical documentation, gap analysis catalogs, and CRM discovery logs.")
    st.markdown("---")

    # Define available documents and their paths on disk
    docs = {
        "1. CRM Implementation Gap Analysis Catalog": "knowledge_base/gap_analysis.md",
        "2. Central Architecture Design Decisions Log": "knowledge_base/design_decisions.md",
        "3. Salesforce CampaignMember Specification": "knowledge_base/campaignmember_design.md",
        "4. Agent Behaviour and Guardrails": "knowledge_base/agent_behaviour_and_guardrails.md"
    }

    # Document selector
    selected_doc_name = st.selectbox("Select Knowledge Base Document to Review:", list(docs.keys()))
    filepath = docs[selected_doc_name]

    st.markdown("---")

    # Load and render chosen markdown document
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Display document title in info panel
            st.info(f"📖 Rendering document from: {filepath}")
            st.markdown(content, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"[ERROR] Failed to read document at {filepath}: {str(e)}")
    else:
        st.warning(f"⚠️ Document not found at filepath: {filepath}. Please ensure files are present in the repository.")
