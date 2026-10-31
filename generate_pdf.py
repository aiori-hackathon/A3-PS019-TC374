"""
Official AIORI-3 Hackathon PDF Generator: Proposed-structure-hackathon.pdf
Strictly adheres to AIORI Level 1 Evaluation Structure:
  1. Problem Description
  2. Solution Proposed
  3. Optimization Proposed by the Team
  4. Solution Architecture and Design
  5. Implementation Details & Prototype Demonstration (with Pseudocode)
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Proposed-structure-hackathon.pdf"
)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 755, "AIORI-3 HACKATHON | PS-019: Personal-Data Discovery & Privacy Evidence Inventory")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)

        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Confidential - Level 1 Evaluation Submission | MeitY DPDPA 2023 Technical Alignment")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284C7"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0F172A")
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#991B1B")
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("AIORI-3 HACKATHON LEVEL 1 EVALUATION PROPOSAL", title_style))
    story.append(Paragraph("<strong>Problem Statement:</strong> PS-019: Personal-Data Discovery and Privacy Evidence Inventory<br/>"
                           "<strong>Category:</strong> Cybersecurity | <strong>Framework:</strong> MeitY DPDPA 2023 Aligned", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceAfter=8))

    # Executive Summary Card
    exec_text = (
        "<strong>Executive Overview:</strong> Under modern privacy regimes like India's Digital Personal Data Protection Act "
        "(DPDPA 2023), organizations must catalog all stored Personally Identifiable Information (PII) and bind it to declared "
        "purposes and statutory retention schedules. Unindexed transactional databases and flat spreadsheets frequently accumulate "
        "'shadow personal data' without documentation. This project presents a technical discovery scanner and evidence inventory engine "
        "that inspects synthetic CSVs and structured SQL databases, classifies personal-data across five classes with "
        "<strong>95.4% Macro F1-score</strong>, maps governance metadata, and unmasks compliance gaps without overstepping into "
        "automated legal interpretations."
    )
    exec_table = Table([[Paragraph(exec_text, body_style)]], colWidths=[504])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F9FF")),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor("#BAE6FD")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 8))

    # SECTION 1: Problem Description
    story.append(Paragraph("1. Problem Description", h1_style))
    story.append(Paragraph(
        "Modern enterprise systems continuously ingest user information across operational pipelines. Over time, personal data accumulates "
        "in unindexed database tables and ad-hoc CSV exports without audit trails. Organizations face substantial statutory liabilities "
        "if they fail to identify stored PII or hold data beyond legitimate necessity (storage limitation). However, technical scanners must "
        "strictly distinguish objective technical evidence from legal compliance decisions: automated systems must NOT make legal lawful-basis "
        "determinations or infer universal cross-border flows. The challenge is to engineer an accurate, configurable technical discovery scanner "
        "that maps data across 5 distinct classes, links fields to corporate retention policies, and surfaces evidence gaps for human DPO sign-off.",
        body_style
    ))

    # SECTION 2: Solution Proposed
    story.append(Paragraph("2. Solution Proposed", h1_style))
    story.append(Paragraph(
        "We have developed a comprehensive discovery and privacy evidence inventory suite supporting both multi-table SQL databases (SQLite) "
        "and flat CSV datasets. The solution incorporates:",
        body_style
    ))
    sol_bullets = (
        "• <strong>Five Predefined Data Classes:</strong> (1) Direct Personal Identifiers, (2) Contact & Location Data, "
        "(3) Government National IDs (Aadhaar, PAN, Passport), (4) Financial & Banking Data (Cards, Bank Acc, IFSC, UPI), "
        "and (5) Digital Identity & Telemetry (IP, MAC, Hashes, Session UUIDs).<br/>"
        "• <strong>Purpose & Retention Linker:</strong> Connects discovered columns with declared corporate privacy policies "
        "(<code>governance_registry.json</code>), mapping business purposes, retention periods, and statutory citations.<br/>"
        "• <strong>Evidence Gap & Shadow Data Flags:</strong> Flags fields with missing purposes (<code>GAP_MISSING_PURPOSE</code>) "
        "or missing/indefinite retention (<code>GAP_MISSING_RETENTION</code>).<br/>"
        "• <strong>Legal Safeguard Boundaries:</strong> Explicitly classifies output as 'Technical Evidence Inventory' with mandatory disclaimers."
    )
    story.append(Paragraph(sol_bullets, body_style))
    story.append(Spacer(1, 6))

    # SECTION 3: Optimization Proposed by the Team
    story.append(Paragraph("3. Optimization Proposed by the Team", h1_style))
    story.append(Paragraph(
        "To avoid the fragility of pure column-name heuristics and the computational overhead of full-table scanning, our team engineered "
        "a <strong>Two-Tier Hybrid Classification Engine with Cross-Validation Boosting</strong>:",
        body_style
    ))
    opt_bullets = (
        "• <strong>Header Semantic Normalization (Tier 1):</strong> Evaluates regular expressions against normalized column headers ($W_h = 0.50$).<br/>"
        "• <strong>Deep Sample-Value Regex Inspection (Tier 2):</strong> Samples up to 100 non-null values and runs specialized patterns ($W_v = 0.50$), "
        "including Luhn heuristics, Verhoeff Aadhaar patterns, Indian IFSC formats, and RFC-5322 email syntax.<br/>"
        "• <strong>Cross-Validation Bonus (+0.10):</strong> If both header syntax and actual sample values match, confidence is boosted.<br/>"
        "• <strong>Negative Specificity Safeguard (93.94%):</strong> Prevents false alarms on generic business numbers (SKU, price, stock quantity)."
    )
    story.append(Paragraph(opt_bullets, body_style))
    story.append(Spacer(1, 8))

    # Page Break for Architecture & Evaluation
    story.append(PageBreak())

    # SECTION 4: Solution Architecture and Design
    story.append(Paragraph("4. Solution Architecture and Design", h1_style))
    story.append(Paragraph(
        "The architecture decouples data ingestion, pattern classification, governance policy mapping, and benchmark evaluation:",
        body_style
    ))

    arch_data = [
        ["Module / Layer", "Component Role", "Implementation Files"],
        ["Data Ingestion", "Introspects SQL tables and flat CSVs, extracts 100 sample rows", "core/scanner.py, data/raw/, enterprise.db"],
        ["Rules Engine", "Two-tier header and sample pattern evaluation across 5 classes", "core/rules_engine.py, config/rules_config.json"],
        ["Metadata Linker", "Maps declared purpose, retention schedules, and flags shadow PII", "core/metadata_linker.py, config/governance_registry.json"],
        ["Evaluation Suite", "Calculates TP, FP, FN, Precision, Recall, F1 & Confusion Matrix", "core/evaluator.py, data/benchmark/ground_truth_labels.json"],
        ["Presentation Layer", "Interactive Flask Web Dashboard and Rich Terminal CLI", "web/app.py, web/templates/, cli.py"]
    ]

    arch_table = Table([[Paragraph(c, body_style) for c in row] for row in arch_data], colWidths=[110, 234, 160])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 8))

    # Empirical Results Table
    story.append(Paragraph("<strong>Evaluation Benchmark Performance (66 Columns Evaluated):</strong>", body_style))
    bench_data = [
        ["Data Class", "TP", "FP", "FN", "Support", "Precision", "Recall", "F1-Score"],
        ["Direct Personal Identifiers", "7", "0", "0", "7", "100.0%", "100.0%", "100.0%"],
        ["Contact & Location Data", "10", "1", "0", "10", "90.91%", "100.0%", "95.24%"],
        ["Government & National IDs", "2", "0", "0", "2", "100.0%", "100.0%", "100.0%"],
        ["Financial & Banking Data", "5", "0", "1", "6", "100.0%", "83.33%", "90.91%"],
        ["Digital Identity & Telemetry", "8", "2", "0", "8", "80.00%", "100.0%", "88.89%"],
        ["Macro Average / Summary", "32", "3", "1", "33", "94.18%", "96.67%", "95.41%"],
        ["Non-PII Negative Specificity", "--", "--", "--", "33", "--", "--", "93.94%"]
    ]
    bench_table = Table([[Paragraph(c, body_style) for c in row] for row in bench_data], colWidths=[150, 40, 40, 40, 50, 60, 60, 64])
    bench_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284C7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,-2), (-1,-2), colors.HexColor("#E0F2FE")),
        ('FONTNAME', (0,-2), (-1,-2), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-3), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(bench_table)
    story.append(Spacer(1, 8))

    # SECTION 5: Implementation Details & Prototype Demonstration
    story.append(Paragraph("5. Implementation Details & Prototype Demonstration (Pseudocode)", h1_style))
    story.append(Paragraph("Core discovery, value validation, and governance mapping pseudocode for mentor evaluation:", body_style))

    pseudocode_lines = """Algorithm: PersonalDataDiscoveryAndPrivacyEvidenceInventory(D, Rules, GovernanceRegistry)
Input:  Datasets D = {CSV_Files, SQLite_Tables}, Rules R, Corporate Governance Registry G
Output: Technical Privacy Evidence Inventory with Precision/Recall Metrics & Evidence Gaps

1:  for each dataset in D:
2:      for each column in dataset.columns:
3:          samples = SampleNonEmptyRows(column, max_limit=100)
4:          best_class = 'Non_PII', max_confidence = 0.0
5:          for each class C in R.classes:
6:              h_score = 1.0 if RegexMatch(column.name, C.header_patterns) else 0.0
7:              val_matches = CountRegexMatches(samples, C.value_patterns)
8:              val_ratio = val_matches / len(samples)
9:              v_score = min(1.0, val_ratio / C.min_sample_ratio)
10:             confidence = (h_score * C.Wh) + (v_score * C.Wv)
11:             if h_score > 0 and val_matches > 0:
12:                 confidence = min(1.0, confidence + 0.10)  # Hybrid cross-validation bonus
13:             if confidence >= C.min_threshold and confidence > max_confidence:
14:                 best_class = C, max_confidence = confidence
15:         
16:         # Step 2: Link Declared Governance Metadata & Flag Evidence Gaps
17:         policy = LookupPolicy(G, dataset.name, column.name)
18:         gaps = []
19:         if best_class != 'Non_PII':
20:             if policy.purpose is NULL: gaps.append('GAP_MISSING_PURPOSE')
21:             if policy.retention is NULL: gaps.append('GAP_MISSING_RETENTION')
22:         
23:         Inventory.append(RecordEvidence(column, best_class, max_confidence, policy, gaps))
24: return Inventory, ComputeBenchmarkMetrics(Inventory, GroundTruth)"""

    pseudo_table = Table([[Paragraph(pseudocode_lines.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style)]], colWidths=[504])
    pseudo_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#E2E8F0")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor("#334155")),
    ]))
    story.append(pseudo_table)
    story.append(Spacer(1, 8))

    # Submission Compliance Footer Note
    story.append(Paragraph(
        "<strong>MeitY DPDPA 2023 Alignment:</strong> This technical suite implements technical evidence discovery aligned with "
        "the MeitY Data Protection Framework (https://www.meity.gov.in/data-protection-framework). It creates objective evidence records "
        "without making automated legal determinations, empowering Data Protection Officers to conduct defensible compliance audits.",
        callout_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Recompiled Proposed-structure-hackathon.pdf with exact AIORI Level 1 Sections: {PDF_OUTPUT_PATH}")

if __name__ == "__main__":
    build_pdf()
