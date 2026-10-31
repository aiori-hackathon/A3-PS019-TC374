"""
Precision and Recall Evaluation Suite for PS-019.
Evaluates discovery predictions against the manually labelled ground truth benchmark,
computing per-class Precision, Recall, F1-score, and Confusion Matrix.
"""

import os
import json
from typing import Dict, List, Any, Optional

DEFAULT_GROUND_TRUTH_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "benchmark",
    "ground_truth_labels.json"
)

PREDEFINED_CLASSES = [
    "Direct_Personal_Identifiers",
    "Contact_Location_Data",
    "Government_National_IDs",
    "Financial_Banking_Data",
    "Authentication_Digital_Telemetry"
]

ALL_CLASSES = PREDEFINED_CLASSES + ["Non_PII"]

class BenchmarkEvaluator:
    """
    Computes rigorous machine learning and statistical detection evaluation metrics
    for the Personal-Data Discovery Scanner.
    """

    def __init__(self, ground_truth_path: str = DEFAULT_GROUND_TRUTH_PATH):
        self.ground_truth_path = ground_truth_path
        self.ground_truth_records: List[Dict[str, Any]] = []
        self.load_ground_truth(ground_truth_path)

    def load_ground_truth(self, ground_truth_path: str) -> None:
        """Loads human-verified ground-truth labels."""
        if not os.path.exists(ground_truth_path):
            raise FileNotFoundError(f"Ground truth benchmark file not found at: {ground_truth_path}")

        with open(ground_truth_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.ground_truth_records = data.get("labels", [])

    def _normalize(self, val: str) -> str:
        return os.path.basename(val).strip().lower()

    def evaluate(self, scan_inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Matches each scan prediction against ground truth label and calculates
        per-class True Positives, False Positives, False Negatives, Precision, Recall, and F1.
        """
        # Index scan predictions by (dataset_basename, field_name_lower)
        scan_map = {}
        for item in scan_inventory:
            key = (self._normalize(item["dataset_name"]), item["field_name"].strip().lower())
            scan_map[key] = item["predicted_class"]

        # Confusion matrix data structure: rows = Actual, cols = Predicted
        confusion_matrix = {
            actual: {pred: 0 for pred in ALL_CLASSES}
            for actual in ALL_CLASSES
        }

        matched_evaluations = []
        unmatched_ground_truth = []

        for gt in self.ground_truth_records:
            ds = self._normalize(gt["dataset_name"])
            field = gt["field_name"].strip().lower()
            actual_class = gt["ground_truth_class"]

            key = (ds, field)
            if key in scan_map:
                pred_class = scan_map[key]
                confusion_matrix[actual_class][pred_class] += 1
                matched_evaluations.append({
                    "dataset_name": gt["dataset_name"],
                    "field_name": gt["field_name"],
                    "actual_class": actual_class,
                    "predicted_class": pred_class,
                    "is_correct": (actual_class == pred_class)
                })
            else:
                unmatched_ground_truth.append(gt)

        # Compute per-class Precision, Recall, and F1 for the 5 PII classes
        per_class_metrics = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for cls in PREDEFINED_CLASSES:
            # TP: Actual is cls, Predicted is cls
            tp = confusion_matrix[cls][cls]

            # FP: Actual is NOT cls, but Predicted is cls
            fp = sum(confusion_matrix[other_actual][cls] for other_actual in ALL_CLASSES if other_actual != cls)

            # FN: Actual is cls, but Predicted is NOT cls
            fn = sum(confusion_matrix[cls][other_pred] for other_pred in ALL_CLASSES if other_pred != cls)

            # TN: Actual is NOT cls, Predicted is NOT cls
            tn = sum(
                confusion_matrix[a][p]
                for a in ALL_CLASSES if a != cls
                for p in ALL_CLASSES if p != cls
            )

            precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0 if (tp == 0 and fp == 0) else 0.0
            recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0 if (tp == 0 and fn == 0) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            actual_support = sum(confusion_matrix[cls].values())

            per_class_metrics[cls] = {
                "display_name": cls.replace("_", " "),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
                "support": actual_support,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "precision_percent": round(precision * 100, 2),
                "recall_percent": round(recall * 100, 2),
                "f1_percent": round(f1 * 100, 2)
            }

            total_tp += tp
            total_fp += fp
            total_fn += fn

        # Macro average (unweighted mean across 5 classes)
        macro_prec = sum(m["precision"] for m in per_class_metrics.values()) / len(PREDEFINED_CLASSES)
        macro_rec = sum(m["recall"] for m in per_class_metrics.values()) / len(PREDEFINED_CLASSES)
        macro_f1 = (2 * macro_prec * macro_rec / (macro_prec + macro_rec)) if (macro_prec + macro_rec) > 0 else 0.0

        # Overall PII Micro average (binary PII detection)
        micro_prec = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
        micro_rec = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
        micro_f1 = (2 * micro_prec * micro_rec / (micro_prec + micro_rec)) if (micro_prec + micro_rec) > 0 else 0.0

        # Non-PII Specificity
        non_pii_actual = sum(confusion_matrix["Non_PII"].values())
        non_pii_correct = confusion_matrix["Non_PII"]["Non_PII"]
        non_pii_specificity = (non_pii_correct / non_pii_actual) if non_pii_actual > 0 else 1.0

        evaluation_report = {
            "evaluation_summary": {
                "total_ground_truth_samples": len(self.ground_truth_records),
                "matched_evaluated_samples": len(matched_evaluations),
                "unmatched_samples": len(unmatched_ground_truth),
                "macro_precision": round(macro_prec, 4),
                "macro_recall": round(macro_rec, 4),
                "macro_f1_score": round(macro_f1, 4),
                "macro_precision_percent": round(macro_prec * 100, 2),
                "macro_recall_percent": round(macro_rec * 100, 2),
                "macro_f1_percent": round(macro_f1 * 100, 2),
                "micro_precision": round(micro_prec, 4),
                "micro_recall": round(micro_rec, 4),
                "micro_f1_score": round(micro_f1, 4),
                "non_pii_specificity_percent": round(non_pii_specificity * 100, 2)
            },
            "per_class_metrics": per_class_metrics,
            "confusion_matrix": confusion_matrix,
            "sample_predictions": matched_evaluations
        }

        return evaluation_report
