"""
Stage 01: Entity Resolution Pipeline Stage.

This module resolves Salesforce Leads and Contacts into a unified, deduplicated 
Master Person database. It constructs a connectivity graph using a Union-Find
algorithm to resolve:
1. Connected Lead-Contact pairs.
2. Broken conversion links (preserves link via primary_lead_id or fallback email matching).
3. Duplicate emails (flagging and ignoring shared mailboxes to prevent incorrect merges).

Outputs:
- data/processed/master_persons.csv
- data/processed/entity_resolution_map.csv

Author: Senior Data Engineer
"""

import os
import sys
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple, Any


class UnionFind:
    """Standard Union-Find disjoint-set data structure with path compression."""

    def __init__(self, elements: List[str]):
        self.parent = {el: el for el in elements}
        self.rank = {el: 0 for el in elements}

    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x: str, y: str):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            if self.rank[root_x] < self.rank[root_y]:
                self.parent[root_x] = root_y
            elif self.rank[root_x] > self.rank[root_y]:
                self.parent[root_y] = root_x
            else:
                self.parent[root_y] = root_x
                self.rank[root_x] += 1


class SalesforceEntityResolver:
    """Resolves Leads and Contacts into master persons with robust survivorship and DQ tracking."""

    def __init__(self, leads_path: str = "data/raw/leads_data.csv",
                 contacts_path: str = "data/raw/contacts_data.csv"):
        self.leads_path = leads_path
        self.contacts_path = contacts_path

        # Shared mailbox usernames list
        self.shared_usernames = {
            "info", "sales", "security", "support", "admin", 
            "marketing", "office", "contact", "jobs", "careers"
        }

    def _normalize_email(self, email: Any) -> str:
        """Trims, lowercases, and returns a clean email string."""
        if pd.isnull(email) or not isinstance(email, str):
            return ""
        return email.strip().lower()

    def _is_shared_mailbox(self, email: str) -> bool:
        """Determines if the normalized email username is a standard shared mailbox."""
        if not email or "@" not in email:
            return False
        username = email.split("@")[0].strip()
        return username in self.shared_usernames

    def resolve_entities(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Runs the complete Entity Resolution process."""
        # 1. Load Datasets
        if not os.path.exists(self.leads_path):
            raise FileNotFoundError(f"[ERROR] Leads file not found at {self.leads_path}")
        if not os.path.exists(self.contacts_path):
            raise FileNotFoundError(f"[ERROR] Contacts file not found at {self.contacts_path}")

        leads_df = pd.read_csv(self.leads_path)
        contacts_df = pd.read_csv(self.contacts_path)

        print(f"[INFO] Ingesting {len(leads_df)} Leads and {len(contacts_df)} Contacts...")

        # 2. Normalize emails and identify attributes
        leads_df["_norm_email"] = leads_df["email"].apply(self._normalize_email)
        contacts_df["_norm_email"] = contacts_df["email"].apply(self._normalize_email)

        # Store lookup dictionaries
        leads_dict = {}
        for _, row in leads_df.iterrows():
            leads_dict[row["lead_id"]] = row.to_dict()

        contacts_dict = {}
        for _, row in contacts_df.iterrows():
            contacts_dict[row["contact_id"]] = row.to_dict()

        # Compile all node IDs
        all_node_ids = list(leads_dict.keys()) + list(contacts_dict.keys())
        uf = UnionFind(all_node_ids)

        # Keep track of edge reasons and flags
        # Map: entity_id -> flag dict
        edge_metadata: Dict[str, Dict[str, Any]] = {}
        for node in all_node_ids:
            edge_metadata[node] = {
                "is_connected_pair": False,
                "broken_conversion_link_flag": False,
                "duplicate_email_flag": False,
                "shared_mailbox_flag": self._is_shared_mailbox(
                    leads_dict[node]["_norm_email"] if node.startswith("00Q") else contacts_dict[node]["_norm_email"]
                ),
                "resolution_confidence": 1.0
            }

        # ----------------------------------------------------
        # Link Stage 1: Explicit Salesforce Conversion Links
        # ----------------------------------------------------
        explicit_links_count = 0
        for lid, lead in leads_dict.items():
            if lead.get("is_converted") is True or str(lead.get("is_converted")).strip().lower() == "true":
                conv_cid = lead.get("converted_contact_id")
                if pd.notnull(conv_cid) and str(conv_cid).strip() != "":
                    cid = str(conv_cid).strip()
                    if cid in contacts_dict:
                        uf.union(lid, cid)
                        explicit_links_count += 1
                        edge_metadata[lid]["is_connected_pair"] = True
                        edge_metadata[cid]["is_connected_pair"] = True

        # ----------------------------------------------------
        # Link Stage 2: Recovered Broken Conversion Links (Contact Backlinks)
        # ----------------------------------------------------
        backlink_recovered_count = 0
        for cid, contact in contacts_dict.items():
            if contact.get("has_lead_origin") is True or str(contact.get("has_lead_origin")).strip().lower() == "true":
                prim_lid = contact.get("primary_lead_id")
                if pd.notnull(prim_lid) and str(prim_lid).strip() != "":
                    lid = str(prim_lid).strip()
                    if lid in leads_dict:
                        # Check if lead represents a broken conversion link (converted_contact_id is null)
                        lead = leads_dict[lid]
                        is_lead_converted = lead.get("is_converted") is True or str(lead.get("is_converted")).strip().lower() == "true"
                        conv_cid = lead.get("converted_contact_id")
                        is_broken_link = is_lead_converted and (pd.isnull(conv_cid) or str(conv_cid).strip() == "")
                        
                        root_lid_before = uf.find(lid)
                        root_cid_before = uf.find(cid)
                        
                        if root_lid_before != root_cid_before:
                            uf.union(lid, cid)
                            backlink_recovered_count += 1
                            
                        # Mark broken conversion flag for both elements
                        if is_broken_link:
                            edge_metadata[lid]["broken_conversion_link_flag"] = True
                            edge_metadata[cid]["broken_conversion_link_flag"] = True
                            edge_metadata[lid]["is_connected_pair"] = True
                            edge_metadata[cid]["is_connected_pair"] = True

        # ----------------------------------------------------
        # Link Stage 3: Broken Conversion Links Fallback (Email Match)
        # ----------------------------------------------------
        email_recovered_count = 0
        for lid, lead in leads_dict.items():
            is_lead_converted = lead.get("is_converted") is True or str(lead.get("is_converted")).strip().lower() == "true"
            conv_cid = lead.get("converted_contact_id")
            is_broken = is_lead_converted and (pd.isnull(conv_cid) or str(conv_cid).strip() == "")
            
            # If lead is broken converted, and hasn't been merged with a contact yet
            if is_broken:
                root_lid = uf.find(lid)
                has_resolved_contact = any(x.startswith("003") for x in all_node_ids if uf.find(x) == root_lid)
                
                if not has_resolved_contact:
                    norm_email = lead["_norm_email"]
                    if norm_email and not self._is_shared_mailbox(norm_email):
                        # Find a contact with the same email
                        matching_contacts = [cid for cid, c in contacts_dict.items() if c["_norm_email"] == norm_email]
                        if matching_contacts:
                            # Pick the first matching contact
                            cid = matching_contacts[0]
                            uf.union(lid, cid)
                            email_recovered_count += 1
                            edge_metadata[lid]["broken_conversion_link_flag"] = True
                            edge_metadata[cid]["broken_conversion_link_flag"] = True
                            edge_metadata[lid]["is_connected_pair"] = True
                            edge_metadata[cid]["is_connected_pair"] = True
                            edge_metadata[lid]["resolution_confidence"] = min(edge_metadata[lid]["resolution_confidence"], 0.85)
                            edge_metadata[cid]["resolution_confidence"] = min(edge_metadata[cid]["resolution_confidence"], 0.85)

        # ----------------------------------------------------
        # Link Stage 4: Duplicate Emails (Normal Prospects Consolidation)
        # ----------------------------------------------------
        duplicate_emails_consolidated = 0
        # Map: email -> list of entities
        email_groups: Dict[str, List[str]] = {}
        for nid in all_node_ids:
            email = leads_dict[nid]["_norm_email"] if nid.startswith("00Q") else contacts_dict[nid]["_norm_email"]
            if email and not self._is_shared_mailbox(email):
                email_groups.setdefault(email, []).append(nid)

        for email, nids in email_groups.items():
            if len(nids) > 1:
                base_nid = nids[0]
                for nid in nids[1:]:
                    root_a = uf.find(base_nid)
                    root_b = uf.find(nid)
                    if root_a != root_b:
                        uf.union(base_nid, nid)
                        duplicate_emails_consolidated += 1
                        
                for nid in nids:
                    edge_metadata[nid]["duplicate_email_flag"] = True
                    edge_metadata[nid]["resolution_confidence"] = min(edge_metadata[nid]["resolution_confidence"], 0.90)

        # ----------------------------------------------------
        # Extract Connected Components & Assign Deterministic master_person_id
        # ----------------------------------------------------
        components: Dict[str, List[str]] = {}
        for nid in all_node_ids:
            root = uf.find(nid)
            components.setdefault(root, []).append(nid)

        # Sort elements inside components alphabetically
        for root in components:
            components[root].sort()

        # Sort the components alphabetically by their minimum element ID to be 100% deterministic
        sorted_roots = sorted(components.keys(), key=lambda r: components[r][0])

        master_persons: List[Dict[str, Any]] = []
        resolution_mappings: List[Dict[str, Any]] = []

        # Track stats for report
        total_unique_master_persons = len(sorted_roots)
        connected_pairs_resolved = 0
        broken_links_recovered = 0
        duplicate_email_groups = 0
        shared_mailbox_groups = 0

        print(f"[INFO] Resolving into {total_unique_master_persons} unique Master Person components...")

        for idx, root in enumerate(sorted_roots):
            nids = components[root]
            master_id = f"MP{idx+1:014d}"  # Deterministic MP ID

            # Compile IDs in this master person
            lead_ids = [nid for nid in nids if nid.startswith("00Q")]
            contact_ids = [nid for nid in nids if nid.startswith("003")]

            # Fill resolution mappings
            for nid in nids:
                resolution_mappings.append({
                    "raw_entity_id": nid,
                    "master_person_id": master_id,
                    "entity_type": "Lead" if nid.startswith("00Q") else "Contact"
                })

            # ----------------------------------------------------
            # Survivorship Priority: Contact takes precedence over Lead
            # ----------------------------------------------------
            preferred_entity_id = ""
            preferred_entity_type = ""
            
            if contact_ids:
                # Preferred is the first Contact (sorted alphabetically)
                preferred_entity_id = contact_ids[0]
                preferred_entity_type = "Contact"
            else:
                preferred_entity_id = lead_ids[0]
                preferred_entity_type = "Lead"

            # Consolidated flags
            is_connected_pair = any(edge_metadata[nid]["is_connected_pair"] for nid in nids)
            broken_conversion_link_flag = any(edge_metadata[nid]["broken_conversion_link_flag"] for nid in nids)
            duplicate_email_flag = any(edge_metadata[nid]["duplicate_email_flag"] for nid in nids)
            shared_mailbox_flag = any(edge_metadata[nid]["shared_mailbox_flag"] for nid in nids)
            confidence = min(edge_metadata[nid]["resolution_confidence"] for nid in nids)
            if len(nids) == 1:
                confidence = 1.0  # single record has absolute confidence

            # Track validation report metrics
            if is_connected_pair:
                connected_pairs_resolved += 1
            if broken_conversion_link_flag:
                broken_links_recovered += 1
            if duplicate_email_flag:
                duplicate_email_groups += 1
            if shared_mailbox_flag:
                shared_mailbox_groups += 1

            # Survivorship attribute mapping
            # Pick preferred value, fallback to any other record in component if NULL
            def survive_field(field_name: str) -> Any:
                # Try preferred first
                pref_val = None
                if preferred_entity_type == "Contact":
                    pref_val = contacts_dict[preferred_entity_id].get(field_name)
                else:
                    pref_val = leads_dict[preferred_entity_id].get(field_name)

                if pd.notnull(pref_val) and str(pref_val).strip() != "" and str(pref_val).strip() != "nan":
                    return pref_val

                # Fallback to other nodes in the component
                for nid in nids:
                    val = leads_dict[nid].get(field_name) if nid.startswith("00Q") else contacts_dict[nid].get(field_name)
                    if pd.notnull(val) and str(val).strip() != "" and str(val).strip() != "nan":
                        return val
                return np.nan

            # Retrieve survived values
            first_name = survive_field("first_name")
            last_name = survive_field("last_name")
            email = survive_field("email")
            norm_email = survive_field("_norm_email")
            title = survive_field("title")
            job_persona = survive_field("job_persona")
            job_level = survive_field("job_level")

            # Account ID survivorship: exclusively from contact record (Leads do not have account_id)
            account_id = np.nan
            for cid in contact_ids:
                acc_val = contacts_dict[cid].get("account_id")
                if pd.notnull(acc_val) and str(acc_val).strip() != "":
                    account_id = acc_val
                    break

            # Compile source entity list
            source_types = []
            if lead_ids:
                source_types.append("Lead")
            if contact_ids:
                source_types.append("Contact")
            source_entity_types = ",".join(source_types)

            # Master Person record
            master_persons.append({
                "master_person_id": master_id,
                "preferred_entity_id": preferred_entity_id,
                "preferred_entity_type": preferred_entity_type,
                "lead_id": lead_ids[0] if len(lead_ids) == 1 else (",".join(lead_ids) if lead_ids else np.nan),
                "contact_id": contact_ids[0] if len(contact_ids) == 1 else (",".join(contact_ids) if contact_ids else np.nan),
                "email": email,
                "normalized_email": norm_email,
                "account_id": account_id,
                "first_name": first_name,
                "last_name": last_name,
                "title": title,
                "job_persona": job_persona,
                "job_level": job_level,
                "source_entity_types": source_entity_types,
                "has_lead_record": len(lead_ids) > 0,
                "has_contact_record": len(contact_ids) > 0,
                "is_connected_pair": is_connected_pair,
                "broken_conversion_link_flag": broken_conversion_link_flag,
                "duplicate_email_flag": duplicate_email_flag,
                "shared_mailbox_flag": shared_mailbox_flag,
                "entity_resolution_confidence": confidence
            })

        # Convert outputs to DataFrames
        master_persons_df = pd.DataFrame(master_persons)
        resolution_map_df = pd.DataFrame(resolution_mappings)

        # Print detailed validation report
        self._print_validation_report(
            total_leads=len(leads_df),
            total_contacts=len(contacts_df),
            total_unique_master_persons=total_unique_master_persons,
            connected_pairs=connected_pairs_resolved,
            broken_links=broken_links_recovered,
            duplicate_emails=duplicate_email_groups,
            shared_mailboxes=shared_mailbox_groups
        )

        return master_persons_df, resolution_map_df

    def _print_validation_report(self, total_leads: int, total_contacts: int,
                                 total_unique_master_persons: int, connected_pairs: int,
                                 broken_links: int, duplicate_emails: int,
                                 shared_mailboxes: int):
        """Prints a professional summary of resolved entities and telemetry metrics."""
        print("=" * 70)
        print("                 STAGE 01: ENTITY RESOLUTION REPORT               ")
        print("=" * 70)
        print(f"Total Leads Processed:              {total_leads:4d}")
        print(f"Total Contacts Processed:           {total_contacts:4d}")
        print(f"Total Unique Master Persons:        {total_unique_master_persons:4d}")
        print("-" * 70)
        print(f"Connected Pairs Mapped (Converted): {connected_pairs:4d}")
        print(f"Broken Conversion Links Mapped:     {broken_links:4d}")
        print(f"Duplicate Email Merges Completed:   {duplicate_emails:4d}")
        print(f"Shared Mailbox Groups Identified:   {shared_mailboxes:4d}")
        print("=" * 70)


def main():
    """Execution entry point."""
    leads_csv = "data/raw/leads_data.csv"
    contacts_csv = "data/raw/contacts_data.csv"
    output_dir = "data/processed"

    # Instantiate resolver and execute
    resolver = SalesforceEntityResolver(leads_path=leads_csv, contacts_path=contacts_csv)
    master_persons_df, resolution_map_df = resolver.resolve_entities()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save to outputs
    master_persons_file = os.path.join(output_dir, "master_persons.csv")
    entity_resolution_map_file = os.path.join(output_dir, "entity_resolution_map.csv")

    master_persons_df.to_csv(master_persons_file, index=False)
    resolution_map_df.to_csv(entity_resolution_map_file, index=False)

    print(f"\n[SUCCESS] Exported resolved Master Persons to: {master_persons_file}")
    print(f"[SUCCESS] Exported Entity Resolution Map to:   {entity_resolution_map_file}\n")


if __name__ == "__main__":
    main()
