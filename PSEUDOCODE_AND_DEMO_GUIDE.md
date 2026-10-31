# PS-019: Prototype Demonstration & Pseudocode Guide for Mentors

## 1. Core Pseudocode Snippet

The following algorithm details the two-tier detection architecture, sample-value regex inspection, corporate governance metadata linking, and automated evidence gap analysis.

```python
Algorithm: PersonalDataDiscoveryAndPrivacyEvidenceInventory
Input:
    Datasets D           := Set of synthetic CSV files and SQLite relational tables
    DetectionRules R     := Configurable 5-class rules (HeaderRegex, ValueRegex, Weights Wh/Wv, Threshold T)
    GovernanceRegistry G := Declared business purposes, retention schedules, and data custodians
    GroundTruth GT       := Manually labelled benchmark evaluation set

Output:
    EvidenceInventory    := Technical catalog of discovered fields, confidence scores, and forensic evidence
    EvidenceGaps         := Flagged shadow personal data missing purpose or retention schedules
    EvaluationReport     := Per-class Precision, Recall, F1-scores, and Confusion Matrix

BEGIN
    Initialize Inventory <- []
    Initialize Gaps <- []

    FOR EACH dataset IN D DO:
        FOR EACH column IN dataset.columns DO:
            // 1. Extract Sample Values (Handles edge cases, nulls, whitespace)
            samples <- ExtractNonEmptySamples(column, max_limit=100)
            
            best_class <- "Non_PII"
            max_confidence <- 0.0
            evidence_details <- NULL

            // 2. Evaluate Against 5 Predefined Personal Data Classes
            FOR EACH class C IN R.classes DO:
                // Tier 1: Semantic Header Heuristic Evaluation
                header_match <- RegexMatch(column.name, C.header_patterns)
                header_score <- (1.0 IF header_match ELSE 0.0)

                // Tier 2: Deep Sample Value Regex Inspection
                matching_sample_count <- CountRegexMatches(samples, C.value_patterns)
                sample_ratio <- matching_sample_count / Length(samples)
                value_score <- Min(1.0, sample_ratio / C.min_sample_ratio)

                // Compute Hybrid Confidence Score
                confidence <- (header_score * C.Wh) + (value_score * C.Wv)

                // Cross-validation reinforcement bonus if both header & values match
                IF header_match AND (matching_sample_count > 0) THEN:
                    confidence <- Min(1.0, confidence + 0.10)
                END IF

                // Threshold Gate
                IF (confidence >= C.min_confidence_threshold) AND (confidence > max_confidence) THEN:
                    best_class <- C.name
                    max_confidence <- confidence
                    evidence_details <- {
                        "matched_header_pattern": header_match.pattern,
                        "sample_match_ratio": sample_ratio,
                        "masked_examples": MaskSensitiveTokens(samples[0..2])
                    }
                END IF
            END FOR

            // 3. Metadata Linking & Gap Detection
            policy <- LookupGovernancePolicy(G, dataset.name, column.name)
            column_gaps <- []

            IF best_class != "Non_PII" THEN:
                IF policy.declared_purpose IS NULL OR Empty(policy.declared_purpose) THEN:
                    column_gaps.Append({
                        "code": "GAP_MISSING_PURPOSE",
                        "severity": "HIGH",
                        "message": "Personal data stored without declared business processing purpose."
                    })
                END IF

                IF policy.retention_period IS NULL OR Empty(policy.retention_period) THEN:
                    column_gaps.Append({
                        "code": "GAP_MISSING_RETENTION",
                        "severity": "HIGH",
                        "message": "Personal data stored without bounded lifecycle or retention schedule."
                    })
                ELSE IF ContainsIgnoreCase(policy.retention_period, "indefinite") THEN:
                    column_gaps.Append({
                        "code": "GAP_INDEFINITE_RETENTION",
                        "severity": "MEDIUM",
                        "message": "Retention is declared indefinite; violates storage limitation mandates."
                    })
                END IF
            END IF

            // 4. Record Technical Inventory Evidence
            record <- {
                "dataset": dataset.name,
                "column": column.name,
                "predicted_class": best_class,
                "confidence_score": max_confidence,
                "is_personal_data": (best_class != "Non_PII"),
                "evidence": evidence_details,
                "governance_metadata": policy,
                "evidence_gaps": column_gaps,
                "audit_status": ("EVIDENCE_GAP_FLAGGED" IF Length(column_gaps) > 0 ELSE "DOCUMENTED_INVENTORY"),
                "human_review_required": True,
                "legal_disclaimer": "Technical evidence only. Human review required for lawful basis determination."
            }

            Inventory.Append(record)
            IF Length(column_gaps) > 0 THEN:
                Gaps.Append(record)
            END IF
        END FOR
    END FOR

    // 5. Evaluate Against Ground Truth Benchmark
    EvaluationReport <- ComputePerClassMetrics(Inventory, GT)

    RETURN Inventory, Gaps, EvaluationReport
END
```

---

## 2. Step-by-Step Mentor Demonstration Script (3-5 Minute Pitch)

### Step 1: Context & The Compliance Boundary (1 Minute)
> *"Hello Mentors, modern data protection acts like India's Digital Personal Data Protection Act (DPDPA 2023) and GDPR mandate that organizations maintain an accurate record of personal data mapped to specific processing purposes and retention schedules. Over time, unindexed databases and flat CSV spreadsheets accumulate shadow personal data without documentation.*
> 
> *Our project, PS-019, solves this by scanning structured data sources (CSV files and SQL databases), detecting candidate personal-data across five standardized data classes, and linking each field to corporate governance policies. Crucially, as required by the problem statement, our tool strictly separates technical evidence from legal interpretation: it does not assert lawful basis or infer data flows—it creates the factual evidence inventory for human DPO review."*

### Step 2: Show the Live Terminal CLI & Evaluation (1 Minute)
Run:
```bash
python cli.py evaluate
```
Point out:
- **Macro Precision:** 94.18%
- **Macro Recall:** 96.67%
- **Macro F1-Score:** 95.41%
- **Non-PII Negative Specificity:** 93.94% (preventing false alarms on regular business columns like product SKU, price, stock).
- Breakdown across the **5 Predefined Data Classes**:
  1. *Direct Personal Identifiers* (Names, DOB, Gender): 100% F1
  2. *Contact & Location Data* (Email, Phone, Address, PIN Code): 95.2% F1
  3. *Government & National IDs* (Aadhaar, PAN, Passport): 100% F1
  4. *Financial & Banking Data* (Cards, Bank Accounts, IFSC, UPI): 90.9% F1
  5. *Digital Identity & Telemetry* (IP, MAC, Hashes, Device UUIDs): 88.9% F1

### Step 3: Demonstrate the Interactive Web Dashboard (1.5 Minutes)
Start the dashboard:
```bash
python web/app.py
```
Open `http://127.0.0.1:5000` in the browser:
1. **Show KPI Bar:** 66 Inspected Columns, 33 Candidate PII Fields, 10 Documented, 23 Shadow Data Gaps.
2. **Show the Disclaimer Banner:** Emphasize the mandatory compliance notice in red: *"Technical Evidence Inventory Only — Not a Legal Compliance Determination."*
3. **Show Tab 1 (Inventory):**
   - Click a row (e.g. `pan_card_no` or `aadhaar_number`) to open the **Field Forensic Modal**.
   - Show how it captures the matched regex, sample values masked for privacy, the declared purpose (*"Statutory Financial KYC Verification"*), and the statutory retention law (*"Income Tax Act, 1961 Section 149"*).
4. **Show Tab 2 (Evidence Gaps & Shadow Data):**
   - Point to the flagged fields where developers stored personal data in support tickets or telemetry tables without declared business purpose (`GAP_MISSING_PURPOSE`) or retention duration (`GAP_MISSING_RETENTION`).
5. **Show Tab 3 (Precision & Recall):**
   - Review the Confusion Matrix and per-class performance tables.
6. **Show Tab 4 (Configurable Rules):**
   - Show how privacy engineers can tweak regex patterns and thresholds without modifying application code.

### Step 4: MeitY Data Protection Framework Grounding (30 Seconds)
Point mentors to the alignment with the [MeitY Data Protection Framework](https://www.meity.gov.in/data-protection-framework):
- Section 4-6 DPDPA obligations on Data Fiduciaries to demonstrate purpose limitation and storage limitation.
- Support for Indian statutory identifiers (Aadhaar, PAN card, IFSC, Indian mobile and PIN codes).
- Exportable CSV and JSON reports ready for regulatory audit submission.
