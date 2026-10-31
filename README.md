# AIORI-3-HACKATHON-PROJECTS
# 🛡️ PS-019: Personal-Data Discovery & Privacy Evidence Inventory Engine

[![AIORI Hackathon 3](https://img.shields.io/badge/AIORI%20Hackathon-3-blue.svg)](https://portal.aiori.in/)
[![Problem Statement](https://img.shields.io/badge/Problem%20Statement-PS--019-orange.svg)](https://portal.aiori.in/)
[![Category](https://img.shields.io/badge/Category-Cybersecurity%20%26%20Data%20Privacy-green.svg)](https://portal.aiori.in/)
[![Framework: MeitY DPDPA 2023](https://img.shields.io/badge/Standard-MeitY%20DPDPA%202023-orange.svg)](https://www.meity.gov.in/data-protection-framework)
[![Evaluation: 95.4% Macro F1](https://img.shields.io/badge/Benchmark-95.4%25%20Macro%20F1-brightgreen.svg)]()
[![Platform: Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

---

## 📌 Team & Overview
* **Team Code:** A3-PS019-TC374
* **Problem Statement:** PS-019: Personal-Data Discovery and Privacy Evidence Inventory
* **Category:** Cybersecurity & Data Governance
* **Event:** AIORI Hackathon 3 (2026)

---

## 📹 Team Introduction & Pitch Video

Check out our team orientation video where we explain our understanding of the problem statement, technical architecture, and individual roles:

[![Watch Video](https://img.shields.io/badge/YouTube-Video%20Pitch-red?logo=youtube)](https://youtube.com/shorts/i9Xan_Pkv70?si=Q5aAwUrC9G4kIBys)

🔗 **YouTube Direct Link:** [Click here to watch our pitch on YouTube](https://youtube.com/shorts/i9Xan_Pkv70?si=Q5aAwUrC9G4kIBys)

---

## ⚠️ Mandatory Compliance & Legal Boundary Notice

> **TECHNICAL EVIDENCE INVENTORY ONLY — NOT A LEGAL COMPLIANCE DETERMINATION**  
> In strict compliance with PS-019 project specifications:
> - This software produces **objective technical evidence** (field syntax, statistical pattern matches, and declared governance linkages) to assist Data Protection Officers (DPOs) and Privacy Engineers.
> - It **does NOT make automated lawful-basis determinations** (e.g., automated consent validation under DPDPA Section 4–6 / GDPR Art 6).
> - It **does NOT infer universal cross-border data flows**.
> - All technical findings are marked as *Candidate Evidence* requiring human audit and sign-off.

---

## 🌟 Key Capabilities & Requirements Matrix

| Hackathon Requirement | Project Implementation & Proof Point |
| :--- | :--- |
| **1. Support CSV & SQL Database** | Unified inspection across flat CSV files (`customers.csv`, `hr_employees.csv`, etc.) and multi-table relational SQLite (`enterprise.db` with 5 tables). Includes drag-and-drop custom CSV dataset ingestion. |
| **2. Identify 5 Predefined Data Classes** | 1. Direct Personal Identifiers<br>2. Contact & Location Data<br>3. Government & National IDs (Aadhaar, PAN, Passport)<br>4. Financial & Banking Data<br>5. Digital Identity & Telemetry |
| **3. Manually Labelled Test Set** | Human-verified ground truth benchmark (`ground_truth_labels.json`) covering 66 structured columns with negative controls. |
| **4. Configurable Detection Rules** | Two-tier hybrid engine (`rules_config.json`) marrying semantic header regular expressions with deep sample-value pattern inspection. |
| **5. Purpose & Retention Mapping** | Automated metadata binding against corporate policy registry (`governance_registry.json`), capturing purpose, retention period, and legal citations. |
| **6. Flag Missing Metadata Gaps** | Flags high-risk **Shadow Personal Data**: `GAP_MISSING_PURPOSE`, `GAP_MISSING_RETENTION`, `GAP_INDEFINITE_RETENTION`, and orphaned policies. |
| **7. Report Per-Class Precision & Recall** | Automated evaluation engine computing per-class Precision, Recall, F1, and full Confusion Matrix (**95.4% Macro F1, 93.9% Specificity**). |
| **8. Legal vs Technical Separation** | Prominent disclaimers, audit status tags (`DOCUMENTED_INVENTORY` vs `EVIDENCE_GAP_FLAGGED`), and human review queues. |
| **9. Official Deliverables** | Includes `Proposed-structure-hackathon.pdf`, `PSEUDOCODE_AND_DEMO_GUIDE.md`, and official GitHub repository for `aiori-hackathon/A3-PS019-TC374`. |

---

## 📊 Empirical Evaluation Benchmark Results

Evaluated against the 66-column ground-truth benchmark across all 5 classes and negative Non-PII control tables:

```
+-----------------------------------------------------------------------------+
| Data Class         | TP | FP | FN | Support | Precision | Recall | F1-Score |
|--------------------+----+----+----+---------+-----------+--------+----------|
| Direct Personal    | 7  | 0  | 0  |    7    |    100.0% | 100.0% |   100.0% |
| Identifiers        |    |    |    |         |           |        |          |
| Contact Location   | 10 | 1  | 0  |   10    |    90.91% | 100.0% |   95.24% |
| Data               |    |    |    |         |           |        |          |
| Government         | 2  | 0  | 0  |    2    |    100.0% | 100.0% |   100.0% |
| National IDs       |    |    |    |         |           |        |          |
| Financial Banking  | 5  | 0  | 1  |    6    |    100.0% | 83.33% |   90.91% |
| Data               |    |    |    |         |           |        |          |
| Authentication     | 8  | 2  | 0  |    8    |     80.0% | 100.0% |   88.89% |
| Digital Telemetry  |    |    |    |         |           |        |          |
+-----------------------------------------------------------------------------+
| Macro Precision: 94.18%  |  Macro Recall: 96.67%  |  Macro F1-Score: 95.41% |
| Non-PII Negative Specificity: 93.94%  |  Binary PII Detection F1: 94.12%    |
+-----------------------------------------------------------------------------+
```

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and install the standard dependencies:
```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Environment (CSVs + SQL DB + Benchmark)
```bash
python data/synthetic_generator.py
```

### 3. Run Command-Line Discovery Scanner
```bash
# Run discovery scan across CSVs and SQLite database
python cli.py scan

# Run benchmark precision and recall evaluation
python cli.py evaluate
```

### 4. Launch Interactive Privacy Operations Web Dashboard
```bash
python web/app.py
```
Open your browser at **`http://127.0.0.1:5000`** to view:
- **Interactive Privacy Evidence Inventory** with searchable columns and status badges.
- **Drag-and-Drop CSV Ingestion**: Upload external custom CSV datasets with instant real-time scanning.
- **Evidence Gap & Shadow Data Audit** highlighting missing purposes and unconstrained retention.
- **Precision/Recall Radar & Confusion Matrix**.
- **Live Rules Inspector & Editor**.
- **Mentor Demonstration Pseudocode & Architecture Walkthrough**.
- Export buttons for **CSV** and **JSON** regulatory filings.

### 5. Generate Official PDF Deliverable
```bash
python generate_pdf.py
```
Outputs the official submission document: **`Proposed-structure-hackathon.pdf`**.

---

## 📁 Repository Structure

```
.
├── config/
│   ├── rules_config.json              # Configurable regex heuristics & weights for 5 classes
│   └── governance_registry.json       # Declared purposes, retention schedules & data owners
├── core/
│   ├── scanner.py                     # Unified CSV and SQLite discovery engine
│   ├── rules_engine.py                # Two-tier header + sample value pattern evaluator
│   ├── metadata_linker.py             # Governance linker & evidence gap analyzer
│   └── evaluator.py                   # Precision, recall, F1 & confusion matrix calculator
├── data/
│   ├── synthetic_generator.py         # Generator for realistic CSVs, SQLite DB & labels
│   ├── raw/                           # Synthetic CSV datasets
│   ├── enterprise.db                  # Multi-table SQLite database
│   └── benchmark/
│       └── ground_truth_labels.json   # 66-column ground truth evaluation set
├── web/
│   ├── app.py                         # Flask REST API server with CSV upload & dataset endpoints
│   ├── static/                        # Cyber-dark theme CSS and vanilla JS dashboard
│   └── templates/index.html           # Modern privacy operations center dashboard
├── cli.py                             # Rich CLI for scanning and evaluation
├── generate_pdf.py                    # ReportLab script compiling official proposal PDF
├── Proposed-structure-hackathon.pdf   # Official Hackathon PDF Deliverable
├── PSEUDOCODE_AND_DEMO_GUIDE.md       # Prototype demo script & annotated pseudocode
├── LEVEL_1_EXECUTION_CHECKLIST.md     # Official Level 1 submission guide
└── README.md                          # Main project documentation with Team Video pitch
```

---

## 🇮🇳 Grounding in MeitY Data Protection Framework (DPDPA 2023)

As referenced in the problem statement ([MeitY Data Protection Framework](https://www.meity.gov.in/data-protection-framework)):
1. **Purpose Limitation (Section 4):** Our tool unmasks "Shadow PII"—fields where personal data is collected without registered business purposes.
2. **Storage Limitation & Erasure (Section 8(7)):** Discovered fields lacking a defined retention schedule or tagged with "Indefinite" storage are flagged with `GAP_MISSING_RETENTION` and `GAP_INDEFINITE_RETENTION`.
3. **Statutory National Identifiers:** Built-in heuristics for Indian identifiers:
   - **Aadhaar Numbers:** 12-digit format with UIDAI validation heuristics.
   - **PAN Cards:** 10-character alphanumeric `[A-Z]{5}[0-9]{4}[A-Z]`.
   - **Indian Financial Identifiers:** IFSC code validation (`[A-Z]{4}0[A-Z0-9]{6}`), UPI VPA format.
   - **Statutory Retention Mappings:** Linking data to Section 149 of Income Tax Act (8-year retention) and EPFO mandates.
