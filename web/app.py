"""
Flask Web Application for PS-019 Personal-Data Discovery & Privacy Evidence Inventory.
Exposes REST APIs for real-time scanning, benchmark evaluation, rule updates,
and renders an interactive Privacy Engineering & DPO Operations Dashboard.
"""

import os
import sys
import json
import csv
import io
from flask import Flask, render_template, jsonify, request, send_file, Response
from werkzeug.utils import secure_filename

# Ensure project root is on the path regardless of where this is invoked from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scanner import PersonalDataScanner
from core.evaluator import BenchmarkEvaluator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "data", "enterprise.db")
RULES_PATH = os.path.join(BASE_DIR, "config", "rules_config.json")
GOVERNANCE_PATH = os.path.join(BASE_DIR, "config", "governance_registry.json")
BENCHMARK_PATH = os.path.join(BASE_DIR, "data", "benchmark", "ground_truth_labels.json")

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)

# Global cached scan state
CACHED_REPORT = None

def get_or_run_scan(force: bool = False):
    global CACHED_REPORT
    if CACHED_REPORT is None or force:
        scanner = PersonalDataScanner(RULES_PATH, GOVERNANCE_PATH)
        CACHED_REPORT = scanner.run_full_scan(
            csv_dir_or_files=DATA_DIR,
            sql_db_path=DB_PATH if os.path.exists(DB_PATH) else None
        )
    return CACHED_REPORT

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan", methods=["GET", "POST"])
def api_scan():
    force = request.args.get("refresh", "false").lower() == "true" or request.method == "POST"
    report = get_or_run_scan(force=force)
    return jsonify({"success": True, "data": report})

@app.route("/api/evaluate", methods=["GET", "POST"])
def api_evaluate():
    report = get_or_run_scan(force=False)
    evaluator = BenchmarkEvaluator(BENCHMARK_PATH)
    eval_res = evaluator.evaluate(report["evidence_inventory"])
    return jsonify({"success": True, "data": eval_res})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Handles CSV file upload.
    Saves the file to data/raw/ and triggers an immediate re-scan.
    """
    if "file" not in request.files and "files" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded. Please select a CSV file."}), 400

    uploaded_files = request.files.getlist("files") or [request.files.get("file")]
    saved_files = []

    os.makedirs(DATA_DIR, exist_ok=True)

    for file_obj in uploaded_files:
        if not file_obj or not file_obj.filename:
            continue

        clean_filename = secure_filename(file_obj.filename)
        if not clean_filename:
            clean_filename = "uploaded_dataset.csv"
        elif not clean_filename.lower().endswith(".csv"):
            clean_filename = f"{clean_filename}.csv"

        target_path = os.path.join(DATA_DIR, clean_filename)
        file_obj.save(target_path)
        saved_files.append(clean_filename)

    if not saved_files:
        return jsonify({"success": False, "error": "No valid CSV files were uploaded."}), 400

    # Force a fresh scan across all data sources including the newly uploaded file(s)
    report = get_or_run_scan(force=True)

    # Calculate statistics specifically for the newly uploaded file(s)
    new_fields = [
        f for f in report.get("evidence_inventory", [])
        if f.get("dataset_name") in saved_files
    ]
    new_pii = [f for f in new_fields if f.get("is_personal_data")]

    return jsonify({
        "success": True,
        "message": f"Successfully uploaded {len(saved_files)} CSV file(s): {', '.join(saved_files)}",
        "uploaded_files": saved_files,
        "new_columns_count": len(new_fields),
        "new_pii_count": len(new_pii),
        "data": report
    })

@app.route("/api/datasets", methods=["GET"])
def api_list_datasets():
    """Returns list of currently active CSV datasets in data/raw."""
    files_info = []
    if os.path.exists(DATA_DIR):
        for fname in sorted(os.listdir(DATA_DIR)):
            if fname.lower().endswith(".csv"):
                fpath = os.path.join(DATA_DIR, fname)
                size_kb = round(os.path.getsize(fpath) / 1024, 1)
                col_count = 0
                row_count = 0
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        reader = csv.reader(f)
                        headers = next(reader, None)
                        if headers:
                            col_count = len(headers)
                            row_count = sum(1 for _ in reader)
                except Exception:
                    pass

                files_info.append({
                    "filename": fname,
                    "size_kb": size_kb,
                    "columns": col_count,
                    "rows": row_count,
                    "modified": os.path.getmtime(fpath)
                })

    return jsonify({"success": True, "datasets": files_info})

@app.route("/api/datasets/<filename>", methods=["DELETE"])
def api_delete_dataset(filename):
    """Deletes an uploaded CSV dataset and triggers re-scan."""
    clean_name = secure_filename(filename)
    target_path = os.path.join(DATA_DIR, clean_name)

    if not os.path.exists(target_path):
        return jsonify({"success": False, "error": f"File '{clean_name}' not found"}), 404

    try:
        os.remove(target_path)
        report = get_or_run_scan(force=True)
        return jsonify({
            "success": True,
            "message": f"Deleted '{clean_name}' and updated inventory.",
            "data": report
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/sample_csv", methods=["POST"])
def api_create_sample_csv():
    """Generates a demo CSV file with sample personal data for quick testing."""
    req_data = request.get_json() or {}
    sample_type = req_data.get("type", "patient_records.csv")

    clean_name = secure_filename(sample_type)
    if not clean_name.lower().endswith(".csv"):
        clean_name = f"{clean_name}.csv"

    target_path = os.path.join(DATA_DIR, clean_name)

    if "patient" in clean_name.lower():
        rows = [
            ["patient_id", "full_name", "aadhaar_number", "contact_phone", "email_address", "blood_group", "diagnosis_code", "consulting_doctor"],
            ["PT-1001", "Aarav Sharma", "4521 8963 1245", "+91 98765 43210", "aarav.sharma@example.in", "O+", "DIAB-02", "Dr. S. Nair"],
            ["PT-1002", "Priya Venkatesh", "9854 1236 7845", "+91 94441 23456", "priya.v@carehospital.org", "B+", "HYP-01", "Dr. K. Mehta"],
            ["PT-1003", "Rahul Sundaram", "6541 2398 4712", "+91 98840 98765", "rahul.sundaram@techindia.com", "A-", "CARD-04", "Dr. S. Nair"],
            ["PT-1004", "Ananya Deshmukh", "3214 7896 5412", "+91 91234 56789", "ananya.d@fintech.co", "AB+", "DERM-09", "Dr. R. Gupta"]
        ]
    elif "kyc" in clean_name.lower():
        rows = [
            ["applicant_id", "customer_name", "pan_card_number", "passport_number", "residential_city", "annual_income_inr", "kyc_verification_status"],
            ["KYC-801", "Vikramaditya Bose", "ABCDE1234F", "M8965412", "Kolkata", "1850000", "VERIFIED"],
            ["KYC-802", "Deepika Padukone", "PQRST5678K", "Z1234567", "Bengaluru", "4200000", "VERIFIED"],
            ["KYC-803", "Siddharth Malhotra", "FGHIJ9012L", "K9876543", "Mumbai", "2600000", "PENDING_REVIEW"],
            ["KYC-804", "Meenakshi Sundaram", "UVWXY3456M", "P5432109", "Chennai", "1450000", "VERIFIED"]
        ]
    else:
        rows = [
            ["employee_code", "first_name", "last_name", "mobile_no", "official_email", "emergency_contact", "monthly_salary"],
            ["EMP-901", "Karthik", "Raman", "9840123456", "karthik.r@enterprise.com", "9840999888", "95000"],
            ["EMP-902", "Sneha", "Reddy", "9712345678", "sneha.r@enterprise.com", "9712999000", "110000"],
            ["EMP-903", "Manoj", "Kumar", "9988776655", "manoj.k@enterprise.com", "9988112233", "82000"]
        ]

    with open(target_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    report = get_or_run_scan(force=True)

    return jsonify({
        "success": True,
        "message": f"Generated sample dataset '{clean_name}' and scanned.",
        "filename": clean_name,
        "data": report
    })

@app.route("/api/rules", methods=["GET", "POST"])
def api_rules():
    if request.method == "GET":
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return jsonify({"success": True, "rules": cfg})
    else:
        new_cfg = request.get_json()
        if not new_cfg or "classes" not in new_cfg:
            return jsonify({"success": False, "error": "Invalid rules payload"}), 400
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(new_cfg, f, indent=2)
        # Re-run scan with updated rules
        get_or_run_scan(force=True)
        return jsonify({"success": True, "message": "Detection rules updated successfully"})

@app.route("/api/governance", methods=["GET"])
def api_governance():
    with open(GOVERNANCE_PATH, "r", encoding="utf-8") as f:
        gov = json.load(f)
    return jsonify({"success": True, "governance": gov})

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    report = get_or_run_scan(force=False)
    inventory = report.get("evidence_inventory", [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Source Type",
        "Dataset Name",
        "Field Name",
        "Predicted Class",
        "Confidence Score",
        "Is Personal Data",
        "Declared Purpose",
        "Retention Schedule",
        "Retention Reference Law",
        "Data Owner",
        "Audit Status",
        "Human Review Required",
        "Evidence Gaps"
    ])

    for f in inventory:
        gaps_str = "; ".join([g["gap_code"] for g in f["evidence_gaps"]]) if f["evidence_gaps"] else "None"
        writer.writerow([
            f["source_type"],
            f["dataset_name"],
            f["field_name"],
            f["predicted_class"],
            f"{int(f['confidence_score'] * 100)}%",
            "YES" if f["is_personal_data"] else "NO",
            f["governance_metadata"]["declared_purpose"],
            f["governance_metadata"]["retention_period"],
            f["governance_metadata"]["retention_law_reference"],
            f["governance_metadata"]["data_owner"],
            f["audit_status"],
            "YES" if f["human_review_required"] else "NO",
            gaps_str
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=privacy_evidence_inventory.csv"}
    )

@app.route("/api/export/json", methods=["GET"])
def export_json():
    report = get_or_run_scan(force=False)
    return Response(
        json.dumps(report, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=privacy_evidence_inventory.json"}
    )

if __name__ == "__main__":
    print("[+] Starting PS-019 Privacy Evidence Inventory Web Dashboard on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
