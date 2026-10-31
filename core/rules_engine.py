"""
Configurable Rules Engine for Personal Data Classification.
Implements two-tier detection combining semantic header analysis and
value-level regex pattern evaluation across sample records.
"""

import re
import json
import os
from typing import Dict, List, Any, Tuple, Optional

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "rules_config.json"
)

class RulesEngine:
    """
    Two-tier rule evaluator that matches field names (headers) and sampled values
    against configurable regular expressions and heuristics.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.classes: Dict[str, Any] = {}
        self.sampling_cfg: Dict[str, Any] = {}
        self.compiled_headers: Dict[str, List[re.Pattern]] = {}
        self.compiled_values: Dict[str, List[re.Pattern]] = {}
        self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """Loads and pre-compiles regex patterns from JSON configuration."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Rules configuration not found at {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.classes = cfg.get("classes", {})
        self.sampling_cfg = cfg.get("sampling", {"sample_row_limit": 100, "min_sample_match_ratio": 0.20})

        self.compiled_headers = {}
        self.compiled_values = {}

        for class_id, class_def in self.classes.items():
            self.compiled_headers[class_id] = [
                re.compile(pat) for pat in class_def.get("header_patterns", [])
            ]
            self.compiled_values[class_id] = [
                re.compile(pat) for pat in class_def.get("value_patterns", [])
            ]

    def evaluate_column(
        self,
        column_name: str,
        sample_values: List[Any]
    ) -> Dict[str, Any]:
        """
        Evaluates a column against all 5 predefined data classes.
        Returns the top predicted class, confidence score, and forensic evidence breakdown.
        """
        # Clean sample values: ignore None, empty strings, and pure whitespace
        cleaned_samples = [
            str(v).strip() for v in sample_values
            if v is not None and str(v).strip() != "" and str(v).lower() != "nan" and str(v).lower() != "null"
        ]

        best_class = "Non_PII"
        highest_confidence = 0.0
        best_evidence: Dict[str, Any] = {
            "header_matched": False,
            "matching_header_pattern": None,
            "sample_match_ratio": 0.0,
            "sample_matches_count": 0,
            "sample_size": len(cleaned_samples),
            "matched_sample_examples": []
        }

        # Test against each of the 5 data classes
        for class_id, class_def in self.classes.items():
            header_matched = False
            matched_header_pat = None
            for pat in self.compiled_headers[class_id]:
                if pat.search(column_name):
                    header_matched = True
                    matched_header_pat = pat.pattern
                    break

            # Value evaluation
            sample_matches = 0
            matching_examples = []
            if cleaned_samples:
                for val in cleaned_samples:
                    matched_val = False
                    for val_pat in self.compiled_values[class_id]:
                        if val_pat.search(val):
                            matched_val = True
                            break
                    if matched_val:
                        sample_matches += 1
                        if len(matching_examples) < 3:
                            # Partially mask sensitive example for privacy evidence log
                            if len(val) > 6:
                                masked = val[:2] + "*" * (len(val) - 4) + val[-2:]
                            else:
                                masked = "***"
                            matching_examples.append(masked)

                sample_ratio = sample_matches / len(cleaned_samples)
            else:
                sample_ratio = 0.0

            weights = class_def.get("weights", {"header_weight": 0.5, "value_weight": 0.5})
            h_weight = weights.get("header_weight", 0.5)
            v_weight = weights.get("value_weight", 0.5)

            # Compute combined score
            header_score = 1.0 if header_matched else 0.0
            
            # If sample ratio meets min threshold, reward value score
            val_score = min(1.0, sample_ratio / max(self.sampling_cfg.get("min_sample_match_ratio", 0.2), 0.01)) if sample_matches > 0 else 0.0

            # Boost if both header and sample match
            combined_confidence = (header_score * h_weight) + (val_score * v_weight)
            if header_matched and sample_matches > 0:
                combined_confidence = min(1.0, combined_confidence + 0.10)

            # Check threshold
            min_thresh = class_def.get("min_confidence_threshold", 0.65)
            if combined_confidence >= min_thresh and combined_confidence > highest_confidence:
                highest_confidence = combined_confidence
                best_class = class_id
                best_evidence = {
                    "header_matched": header_matched,
                    "matching_header_pattern": matched_header_pat,
                    "sample_match_ratio": round(sample_ratio, 3),
                    "sample_matches_count": sample_matches,
                    "sample_size": len(cleaned_samples),
                    "matched_sample_examples": matching_examples,
                    "class_display_name": class_def.get("display_name", class_id),
                    "class_description": class_def.get("description", "")
                }

        return {
            "predicted_class": best_class,
            "confidence_score": round(highest_confidence, 3),
            "is_personal_data": best_class != "Non_PII",
            "evidence": best_evidence
        }
