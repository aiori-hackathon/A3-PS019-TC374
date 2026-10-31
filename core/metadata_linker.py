"""
Metadata Linker and Evidence Gap Analyzer.
Binds discovered personal-data fields to declared purpose and retention policies,
identifies governance gaps (Shadow PII, missing retention schedules),
and enforces strict legal-boundary disclaimers.
"""

import json
import os
from typing import Dict, List, Any, Optional

DEFAULT_GOVERNANCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "governance_registry.json"
)

LEGAL_BOUNDARY_DISCLAIMER = (
    "TECHNICAL EVIDENCE ONLY: This inventory represents technical observations of "
    "data syntax, column semantics, and documented governance links. It does NOT constitute "
    "legal advice or an automated certification of lawful basis under the Digital Personal Data "
    "Protection Act (DPDPA 2023) or GDPR. All findings require human review by designated Data "
    "Protection Officers (DPOs) or privacy legal counsel."
)

class MetadataLinker:
    """
    Connects technical scan discoveries with declared corporate data governance policies.
    Identifies undocumented fields and flags evidence gaps.
    """

    def __init__(self, registry_path: str = DEFAULT_GOVERNANCE_PATH):
        self.registry_path = registry_path
        self.mappings: List[Dict[str, Any]] = []
        self.load_registry(registry_path)

    def load_registry(self, registry_path: str) -> None:
        """Loads declared corporate privacy metadata from JSON."""
        if not os.path.exists(registry_path):
            raise FileNotFoundError(f"Governance registry not found at {registry_path}")

        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.mappings = data.get("declared_mappings", [])

    def _normalize_name(self, name: str) -> str:
        """Helper to match dataset and field identifiers cleanly."""
        return os.path.basename(name).strip().lower()

    def link_field(
        self,
        source_type: str,
        dataset_name: str,
        field_name: str,
        predicted_class: str,
        is_personal_data: bool
    ) -> Dict[str, Any]:
        """
        Looks up governance declaration for a given field and evaluates documentation completeness.
        """
        norm_dataset = self._normalize_name(dataset_name)
        norm_field = field_name.strip().lower()

        # Find exact or best matching registry entry
        matched_entry: Optional[Dict[str, Any]] = None
        for entry in self.mappings:
            entry_ds = self._normalize_name(entry.get("dataset_name", ""))
            entry_field = entry.get("field_name", "").strip().lower()

            if (entry_ds == norm_dataset or entry_ds in norm_dataset) and entry_field == norm_field:
                matched_entry = entry
                break

        # If not personal data, governance linkage is not strictly required
        if not is_personal_data:
            return {
                "is_documented": matched_entry is not None,
                "declared_purpose": matched_entry.get("declared_purpose") if matched_entry else "N/A (Non-PII)",
                "retention_period": matched_entry.get("retention_period") if matched_entry else "N/A (Non-PII)",
                "retention_law_reference": matched_entry.get("retention_law_reference") if matched_entry else "N/A",
                "data_owner": matched_entry.get("data_owner") if matched_entry else "N/A",
                "human_legal_note": matched_entry.get("legal_basis_reference") if matched_entry else "N/A",
                "evidence_gaps": [],
                "audit_status": "NON_PII_EXCLUDED",
                "human_review_required": False,
                "legal_disclaimer": LEGAL_BOUNDARY_DISCLAIMER
            }

        # For detected personal data, analyze compliance evidence completeness
        gaps: List[Dict[str, str]] = []
        is_documented = matched_entry is not None

        declared_purpose = matched_entry.get("declared_purpose") if matched_entry else None
        retention_period = matched_entry.get("retention_period") if matched_entry else None
        retention_law = matched_entry.get("retention_law_reference") if matched_entry else None
        data_owner = matched_entry.get("data_owner") if matched_entry else None
        legal_basis_ref = matched_entry.get("legal_basis_reference") if matched_entry else None

        if not declared_purpose or declared_purpose.strip() == "":
            gaps.append({
                "gap_code": "GAP_MISSING_PURPOSE",
                "severity": "HIGH",
                "message": "Field contains Personal Data with NO registered business processing purpose."
            })

        if not retention_period or retention_period.strip() == "":
            gaps.append({
                "gap_code": "GAP_MISSING_RETENTION",
                "severity": "HIGH",
                "message": "Field contains Personal Data with NO declared lifecycle or retention schedule."
            })
        elif "indefinite" in retention_period.lower():
            gaps.append({
                "gap_code": "GAP_INDEFINITE_RETENTION",
                "severity": "MEDIUM",
                "message": "Retention schedule is declared as Indefinite; risks statutory storage limitation breaches."
            })

        if not data_owner or data_owner.strip() == "":
            gaps.append({
                "gap_code": "GAP_MISSING_OWNER",
                "severity": "LOW",
                "message": "No functional business department or data fiduciary custodian assigned."
            })

        # Determine audit status
        if gaps:
            audit_status = "EVIDENCE_GAP_FLAGGED"
            review_required = True
        else:
            audit_status = "DOCUMENTED_INVENTORY"
            review_required = True  # All personal data requires human signoff in technical inventory

        return {
            "is_documented": is_documented,
            "declared_purpose": declared_purpose or "NOT DECLARED [GAP]",
            "retention_period": retention_period or "NOT SPECIFIED [GAP]",
            "retention_law_reference": retention_law or "N/A",
            "data_owner": data_owner or "UNASSIGNED [GAP]",
            "human_legal_note": legal_basis_ref or "Awaiting Human Legal Assessment",
            "evidence_gaps": gaps,
            "audit_status": audit_status,
            "human_review_required": review_required,
            "legal_disclaimer": LEGAL_BOUNDARY_DISCLAIMER
        }

    def find_orphaned_governance_entries(self, scanned_fields: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Flags declared registry policies that point to tables or columns
        that were NOT discovered in active datasets (Stale / Phantom inventory records).
        """
        scanned_pairs = {
            (self._normalize_name(f["dataset_name"]), f["field_name"].strip().lower())
            for f in scanned_fields
        }

        orphans = []
        for entry in self.mappings:
            entry_ds = self._normalize_name(entry.get("dataset_name", ""))
            entry_field = entry.get("field_name", "").strip().lower()

            found = any(
                (ds == entry_ds or entry_ds in ds) and field == entry_field
                for ds, field in scanned_pairs
            )
            if not found:
                orphans.append({
                    "dataset_name": entry.get("dataset_name"),
                    "field_name": entry.get("field_name"),
                    "declared_purpose": entry.get("declared_purpose"),
                    "retention_period": entry.get("retention_period"),
                    "issue": "Policy declared in registry but field was not found in scanned data source."
                })

        return orphans
