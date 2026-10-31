"""
Unified Personal-Data Discovery Scanner for CSV and SQL Database Sources.
Introspects structured datasets, executes two-tier rule classification,
and produces the Technical Privacy Evidence Inventory.
"""

import os
import csv
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from core.rules_engine import RulesEngine
from core.metadata_linker import MetadataLinker, LEGAL_BOUNDARY_DISCLAIMER

class PersonalDataScanner:
    """
    High-performance discovery engine scanning flat CSV files and relational SQL tables
    to catalog candidate personal-data fields and map governance metadata.
    """

    def __init__(
        self,
        rules_config_path: Optional[str] = None,
        governance_path: Optional[str] = None
    ):
        if rules_config_path:
            self.rules_engine = RulesEngine(rules_config_path)
        else:
            self.rules_engine = RulesEngine()

        if governance_path:
            self.metadata_linker = MetadataLinker(governance_path)
        else:
            self.metadata_linker = MetadataLinker()

    def scan_csv_file(self, file_path: str, max_samples: int = 100) -> List[Dict[str, Any]]:
        """Scans a single CSV file and evaluates all columns."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        file_name = os.path.basename(file_path)
        results = []

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return []

            # Read sample rows
            samples_by_col = [[] for _ in headers]
            row_count = 0
            for row in reader:
                if row_count >= max_samples:
                    break
                row_count += 1
                for idx, val in enumerate(row):
                    if idx < len(samples_by_col):
                        samples_by_col[idx].append(val)

            # Evaluate each column
            for idx, col_name in enumerate(headers):
                col_name_clean = col_name.strip()
                sample_data = samples_by_col[idx] if idx < len(samples_by_col) else []

                # Classify via Rules Engine
                eval_res = self.rules_engine.evaluate_column(col_name_clean, sample_data)

                # Link governance metadata and flag gaps
                meta_res = self.metadata_linker.link_field(
                    source_type="CSV",
                    dataset_name=file_name,
                    field_name=col_name_clean,
                    predicted_class=eval_res["predicted_class"],
                    is_personal_data=eval_res["is_personal_data"]
                )

                field_record = {
                    "source_type": "CSV",
                    "source_location": file_path,
                    "dataset_name": file_name,
                    "field_name": col_name_clean,
                    "field_index": idx,
                    "predicted_class": eval_res["predicted_class"],
                    "class_display_name": eval_res["evidence"].get("class_display_name", eval_res["predicted_class"]),
                    "confidence_score": eval_res["confidence_score"],
                    "is_personal_data": eval_res["is_personal_data"],
                    "detection_evidence": eval_res["evidence"],
                    "governance_metadata": {
                        "is_documented": meta_res["is_documented"],
                        "declared_purpose": meta_res["declared_purpose"],
                        "retention_period": meta_res["retention_period"],
                        "retention_law_reference": meta_res["retention_law_reference"],
                        "data_owner": meta_res["data_owner"],
                        "human_legal_note": meta_res["human_legal_note"]
                    },
                    "evidence_gaps": meta_res["evidence_gaps"],
                    "audit_status": meta_res["audit_status"],
                    "human_review_required": meta_res["human_review_required"]
                }
                results.append(field_record)

        return results

    def scan_sqlite_db(self, db_path: str, max_samples: int = 100) -> List[Dict[str, Any]]:
        """Scans all tables in a structured SQLite database."""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite DB not found: {db_path}")

        db_name = os.path.basename(db_path)
        results = []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query all user tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        for tbl in tables:
            dataset_identifier = f"{db_name}:{tbl}"

            # Table columns info: cid, name, type, notnull, dflt_value, pk
            cursor.execute(f"PRAGMA table_info('{tbl}');")
            col_info = cursor.fetchall()
            headers = [c[1] for c in col_info]

            # Fetch samples
            cursor.execute(f"SELECT * FROM '{tbl}' LIMIT {max_samples};")
            rows = cursor.fetchall()

            samples_by_col = [[] for _ in headers]
            for row in rows:
                for idx, val in enumerate(row):
                    if idx < len(samples_by_col):
                        samples_by_col[idx].append(val)

            for idx, col_name in enumerate(headers):
                col_name_clean = col_name.strip()
                sample_data = samples_by_col[idx] if idx < len(samples_by_col) else []

                eval_res = self.rules_engine.evaluate_column(col_name_clean, sample_data)

                meta_res = self.metadata_linker.link_field(
                    source_type="SQL",
                    dataset_name=dataset_identifier,
                    field_name=col_name_clean,
                    predicted_class=eval_res["predicted_class"],
                    is_personal_data=eval_res["is_personal_data"]
                )

                field_record = {
                    "source_type": "SQL",
                    "source_location": db_path,
                    "dataset_name": dataset_identifier,
                    "table_name": tbl,
                    "field_name": col_name_clean,
                    "field_index": idx,
                    "predicted_class": eval_res["predicted_class"],
                    "class_display_name": eval_res["evidence"].get("class_display_name", eval_res["predicted_class"]),
                    "confidence_score": eval_res["confidence_score"],
                    "is_personal_data": eval_res["is_personal_data"],
                    "detection_evidence": eval_res["evidence"],
                    "governance_metadata": {
                        "is_documented": meta_res["is_documented"],
                        "declared_purpose": meta_res["declared_purpose"],
                        "retention_period": meta_res["retention_period"],
                        "retention_law_reference": meta_res["retention_law_reference"],
                        "data_owner": meta_res["data_owner"],
                        "human_legal_note": meta_res["human_legal_note"]
                    },
                    "evidence_gaps": meta_res["evidence_gaps"],
                    "audit_status": meta_res["audit_status"],
                    "human_review_required": meta_res["human_review_required"]
                }
                results.append(field_record)

        conn.close()
        return results

    def run_full_scan(
        self,
        csv_dir_or_files: Any,
        sql_db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a complete scan across CSV directory/files and SQL database,
        aggregates inventory, computes gap metrics, and outputs comprehensive report.
        """
        start_time = time.time()
        scanned_inventory: List[Dict[str, Any]] = []

        # 1. Process CSVs
        csv_files = []
        if isinstance(csv_dir_or_files, str):
            if os.path.isdir(csv_dir_or_files):
                for root, _, files in os.walk(csv_dir_or_files):
                    for f in files:
                        if f.lower().endswith(".csv"):
                            csv_files.append(os.path.join(root, f))
            elif os.path.isfile(csv_dir_or_files) and csv_dir_or_files.lower().endswith(".csv"):
                csv_files.append(csv_dir_or_files)
        elif isinstance(csv_dir_or_files, list):
            csv_files = csv_dir_or_files

        for cf in csv_files:
            try:
                res = self.scan_csv_file(cf)
                scanned_inventory.extend(res)
            except Exception as e:
                print(f"[-] Error scanning CSV {cf}: {e}")

        # 2. Process SQL Database
        if sql_db_path and os.path.exists(sql_db_path):
            try:
                db_res = self.scan_sqlite_db(sql_db_path)
                scanned_inventory.extend(db_res)
            except Exception as e:
                print(f"[-] Error scanning SQL DB {sql_db_path}: {e}")

        elapsed = round(time.time() - start_time, 3)

        # 3. Summarize metrics
        total_fields = len(scanned_inventory)
        personal_fields = [f for f in scanned_inventory if f["is_personal_data"]]
        non_pii_fields = [f for f in scanned_inventory if not f["is_personal_data"]]

        # Class breakdown
        class_breakdown: Dict[str, int] = {
            "Direct_Personal_Identifiers": 0,
            "Contact_Location_Data": 0,
            "Government_National_IDs": 0,
            "Financial_Banking_Data": 0,
            "Authentication_Digital_Telemetry": 0
        }
        for f in personal_fields:
            c = f["predicted_class"]
            if c in class_breakdown:
                class_breakdown[c] += 1

        # Evidence gaps breakdown
        gap_fields = [f for f in personal_fields if f["audit_status"] == "EVIDENCE_GAP_FLAGGED"]
        fully_documented = [f for f in personal_fields if f["audit_status"] == "DOCUMENTED_INVENTORY"]

        missing_purpose_count = sum(
            1 for f in personal_fields if any(g["gap_code"] == "GAP_MISSING_PURPOSE" for g in f["evidence_gaps"])
        )
        missing_retention_count = sum(
            1 for f in personal_fields if any(g["gap_code"] == "GAP_MISSING_RETENTION" for g in f["evidence_gaps"])
        )
        indefinite_retention_count = sum(
            1 for f in personal_fields if any(g["gap_code"] == "GAP_INDEFINITE_RETENTION" for g in f["evidence_gaps"])
        )

        # Orphaned catalog entries
        scanned_field_tuples = [
            {"dataset_name": f["dataset_name"], "field_name": f["field_name"]}
            for f in scanned_inventory
        ]
        orphans = self.metadata_linker.find_orphaned_governance_entries(scanned_field_tuples)

        # Compile final structured payload
        report = {
            "scan_metadata": {
                "scan_timestamp": datetime.now().isoformat(),
                "duration_seconds": elapsed,
                "scanner_version": "PS-019-v1.0",
                "framework_alignment": "MeitY DPDPA 2023 & ISO/IEC 27701",
                "legal_disclaimer": LEGAL_BOUNDARY_DISCLAIMER
            },
            "summary_metrics": {
                "total_columns_inspected": total_fields,
                "candidate_personal_data_fields": len(personal_fields),
                "non_personal_data_fields": len(non_pii_fields),
                "documented_personal_fields": len(fully_documented),
                "shadow_pii_with_evidence_gaps": len(gap_fields),
                "evidence_gap_rate_percent": round((len(gap_fields) / len(personal_fields) * 100), 2) if personal_fields else 0.0,
                "class_counts": class_breakdown,
                "missing_purpose_count": missing_purpose_count,
                "missing_retention_count": missing_retention_count,
                "indefinite_retention_count": indefinite_retention_count,
                "orphaned_governance_policies": len(orphans)
            },
            "orphaned_policies": orphans,
            "evidence_inventory": scanned_inventory
        }

        return report
