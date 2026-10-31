"""
Synthetic Dataset Generator for PS-019 Personal-Data Discovery Scanner.
Generates realistic CSV datasets and an enterprise SQLite database containing
a mix of PII fields across 5 predefined classes and Non-PII business fields.
Also outputs the official ground_truth_labels.json benchmark test set for evaluation.
"""

import os
import csv
import json
import sqlite3
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
BENCHMARK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enterprise.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BENCHMARK_DIR, exist_ok=True)

# Helper generators
FIRST_NAMES = ["Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Sneha", "Aditya", "Pooja", "Arjun", "Neha", "Rahul", "Kavita"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Reddy", "Iyer", "Mehta", "Singh", "Nair", "Gupta", "Deshmukh", "Chopra", "Das"]
DOMAINS = ["example.com", "enterprise.org", "mailservice.in", "techcorp.io", "cloudindia.net"]
CITIES = ["Mumbai", "Bengaluru", "New Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]
STREETS = ["MG Road", "Brigade Road", "Ring Road", "Park Street", "Connaught Place", "Banjara Hills", "Koramangala"]

def generate_aadhaar():
    # 12 digits, first digit 2-9
    first = str(random.randint(2, 9))
    rest = "".join([str(random.randint(0, 9)) for _ in range(11)])
    num = first + rest
    return f"{num[0:4]} {num[4:8]} {num[8:12]}"

def generate_pan():
    # 5 letters, 4 digits, 1 letter
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
    digits = "".join(random.choices("0123456789", k=4))
    last = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f"{letters}{digits}{last}"

def generate_phone():
    # 10 digits Indian mobile format
    start = random.choice(["9", "8", "7", "6"])
    rest = "".join(random.choices("0123456789", k=9))
    return f"{start}{rest}"

def generate_ip():
    return f"{random.randint(11, 223)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

def generate_mac():
    return ":".join([f"{random.randint(0, 255):02X}" for _ in range(6)])

def generate_card():
    # 16 digit masked card
    return f"4532-XXXX-XXXX-{random.randint(1000, 9999)}"

def generate_ifsc():
    bank = random.choice(["HDFC", "SBIN", "ICIC", "UTIB", "KKBK"])
    code = "".join(random.choices("0123456789", k=6))
    return f"{bank}0{code}"

def generate_dob():
    start_date = datetime(1965, 1, 1)
    end_date = datetime(2003, 12, 31)
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

def generate_all():
    print("[+] Generating synthetic datasets for PS-019...")

    # 1. customers.csv
    cust_file = os.path.join(DATA_DIR, "customers.csv")
    with open(cust_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "full_name", "email_address", "phone_number", "residential_address", "pin_code", "pan_card_no", "created_date", "account_status"])
        for i in range(1, 121):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}{i}@{random.choice(DOMAINS)}"
            phone = generate_phone()
            addr = f"{random.randint(10, 999)}, {random.choice(STREETS)}, {random.choice(CITIES)}"
            pincode = f"{random.randint(110001, 700100)}"
            pan = generate_pan()
            created = (datetime.now() - timedelta(days=random.randint(10, 500))).strftime("%Y-%m-%d")
            status = random.choice(["ACTIVE", "DORMANT", "PENDING_KYC", "VERIFIED"])
            writer.writerow([f"CUST-{1000+i}", name, email, phone, addr, pincode, pan, created, status])
    print(f"    - Generated {cust_file}")

    # 2. hr_employees.csv
    hr_file = os.path.join(DATA_DIR, "hr_employees.csv")
    with open(hr_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["emp_id", "employee_name", "dob", "aadhaar_number", "bank_account_no", "ifsc_code", "salary_ctc", "department"])
        for i in range(1, 101):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            dob = generate_dob()
            aadhaar = generate_aadhaar()
            acc = str(random.randint(10000000000, 99999999999))
            ifsc = generate_ifsc()
            salary = str(random.randint(450000, 2400000))
            dept = random.choice(["Engineering", "Human Resources", "Finance", "Legal", "Operations", "Sales"])
            writer.writerow([f"EMP-{500+i}", name, dob, aadhaar, acc, ifsc, salary, dept])
    print(f"    - Generated {hr_file}")

    # 3. support_tickets.csv
    tickets_file = os.path.join(DATA_DIR, "support_tickets.csv")
    with open(tickets_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ticket_id", "reporter_email", "customer_ip", "device_id", "issue_description", "resolution_status", "priority_level"])
        for i in range(1, 81):
            email = f"user_{i}@{random.choice(DOMAINS)}"
            ip = generate_ip()
            dev_id = f"dev-uuid-{random.randint(1000,9999)}-{random.randint(100,999)}"
            issue = random.choice(["Login failed on mobile app", "Payment timeout error", "Address update pending", "Password reset link expired"])
            status = random.choice(["OPEN", "RESOLVED", "IN_PROGRESS", "CLOSED"])
            priority = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            writer.writerow([f"TCK-{2000+i}", email, ip, dev_id, issue, status, priority])
    print(f"    - Generated {tickets_file}")

    # 4. financial_transactions.csv
    fin_file = os.path.join(DATA_DIR, "financial_transactions.csv")
    with open(fin_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["txn_id", "credit_card_mask", "upi_vpa", "amount_inr", "txn_timestamp", "merchant_category_code"])
        for i in range(1, 101):
            card = generate_card()
            vpa = f"pay_{i}@{random.choice(['okhdfcbank', 'okaxis', 'paytm', 'ybl'])}"
            amt = f"{random.randint(99, 45000)}.{random.randint(10, 99)}"
            ts = (datetime.now() - timedelta(minutes=random.randint(5, 10000))).isoformat()
            mcc = random.choice(["5411", "5812", "5311", "4121", "5999"])
            writer.writerow([f"TXN-{80000+i}", card, vpa, amt, ts, mcc])
    print(f"    - Generated {fin_file}")

    # 5. telemetry_logs.csv
    tel_file = os.path.join(DATA_DIR, "telemetry_logs.csv")
    with open(tel_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["log_id", "client_ip", "mac_address", "session_token", "http_status", "bytes_transferred"])
        for i in range(1, 151):
            ip = generate_ip()
            mac = generate_mac()
            token = f"sess_{random.randint(10000000, 99999999)}_{i}"
            status = random.choice([200, 201, 304, 400, 401, 403, 500])
            bytes_xfer = random.randint(128, 65536)
            writer.writerow([f"LOG-{i}", ip, mac, token, status, bytes_xfer])
    print(f"    - Generated {tel_file}")

    # 6. SQLite Database (enterprise.db)
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: users
    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        full_name TEXT,
        user_id_email TEXT,
        phone_number TEXT,
        password_hash TEXT,
        role TEXT
    )
    """)
    for i in range(1, 75):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (i, f"{fn} {ln}", f"{fn.lower()}.{ln.lower()}@corp.internal", generate_phone(), f"$2b$12${random.randint(100000,999999)}abcdefghijklmnopqrstuvwxyz12345", random.choice(["ADMIN", "AUDITOR", "ANALYST", "USER"]))
        )

    # Table 2: billing_details
    cursor.execute("""
    CREATE TABLE billing_details (
        billing_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        credit_card_mask TEXT,
        billing_address TEXT,
        billing_pincode TEXT,
        currency TEXT
    )
    """)
    for i in range(1, 60):
        cursor.execute(
            "INSERT INTO billing_details VALUES (?, ?, ?, ?, ?, ?)",
            (i, random.randint(1, 74), generate_card(), f"Plot {random.randint(1,100)}, {random.choice(STREETS)}, {random.choice(CITIES)}", f"{random.randint(110001, 700100)}", "INR")
        )

    # Table 3: patient_records
    cursor.execute("""
    CREATE TABLE patient_records (
        patient_id INTEGER PRIMARY KEY,
        patient_name TEXT,
        dob TEXT,
        gender TEXT,
        emergency_contact_phone TEXT,
        blood_group TEXT,
        admission_notes TEXT
    )
    """)
    for i in range(1, 50):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        cursor.execute(
            "INSERT INTO patient_records VALUES (?, ?, ?, ?, ?, ?, ?)",
            (i, f"{fn} {ln}", generate_dob(), random.choice(["Male", "Female"]), generate_phone(), random.choice(["O+", "A+", "B+", "AB+", "O-"]), "Regular health checkup observation")
        )

    # Table 4: auth_sessions
    cursor.execute("""
    CREATE TABLE auth_sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        client_ip_address TEXT,
        user_agent_token TEXT,
        login_time TEXT
    )
    """)
    for i in range(1, 90):
        cursor.execute(
            "INSERT INTO auth_sessions VALUES (?, ?, ?, ?, ?)",
            (i, random.randint(1, 74), generate_ip(), f"Mozilla/5.0 AuthToken_{i}_{random.randint(1000,9999)}", (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat())
        )

    # Table 5: inventory_products (Pure Non-PII control table to test false positive resistance!)
    cursor.execute("""
    CREATE TABLE inventory_products (
        product_id INTEGER PRIMARY KEY,
        sku_code TEXT,
        unit_price REAL,
        stock_quantity INTEGER,
        warehouse_bay TEXT,
        reorder_threshold INTEGER
    )
    """)
    for i in range(1, 80):
        cursor.execute(
            "INSERT INTO inventory_products VALUES (?, ?, ?, ?, ?, ?)",
            (i, f"SKU-{random.randint(10000, 99999)}", round(random.uniform(15.0, 1500.0), 2), random.randint(5, 500), f"BAY-{random.choice(['A','B','C','D'])}-{random.randint(1,20)}", 15)
        )

    conn.commit()
    conn.close()
    print(f"    - Generated SQLite database: {DB_PATH}")

    # Generate Ground Truth Labels for Evaluation Benchmark
    ground_truth = {
        "metadata": {
            "title": "PS-019 Privacy Evidence Ground Truth Benchmark",
            "version": "1.0",
            "description": "Exhaustive human-verified labels for synthetic CSVs and SQLite database columns.",
            "total_columns": 51
        },
        "labels": [
            # customers.csv
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "customer_id", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "full_name", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "email_address", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "phone_number", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "residential_address", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "pin_code", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "pan_card_no", "ground_truth_class": "Government_National_IDs"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "created_date", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "customers.csv", "field_name": "account_status", "ground_truth_class": "Non_PII"},

            # hr_employees.csv
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "emp_id", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "employee_name", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "dob", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "aadhaar_number", "ground_truth_class": "Government_National_IDs"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "bank_account_no", "ground_truth_class": "Financial_Banking_Data"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "ifsc_code", "ground_truth_class": "Financial_Banking_Data"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "salary_ctc", "ground_truth_class": "Financial_Banking_Data"},
            {"source_type": "CSV", "dataset_name": "hr_employees.csv", "field_name": "department", "ground_truth_class": "Non_PII"},

            # support_tickets.csv
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "ticket_id", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "reporter_email", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "customer_ip", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "device_id", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "issue_description", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "resolution_status", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "support_tickets.csv", "field_name": "priority_level", "ground_truth_class": "Non_PII"},

            # financial_transactions.csv
            {"source_type": "CSV", "dataset_name": "financial_transactions.csv", "field_name": "txn_id", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "financial_transactions.csv", "field_name": "credit_card_mask", "ground_truth_class": "Financial_Banking_Data"},
            {"source_type": "CSV", "dataset_name": "financial_transactions.csv", "field_name": "upi_vpa", "ground_truth_class": "Financial_Banking_Data"},
            {"source_type": "CSV", "dataset_name": "financial_transactions.csv", "field_name": "amount_inr", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "financial_transactions.csv", "field_name": "txn_timestamp", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "financial_transactions.csv", "field_name": "merchant_category_code", "ground_truth_class": "Non_PII"},

            # telemetry_logs.csv
            {"source_type": "CSV", "dataset_name": "telemetry_logs.csv", "field_name": "log_id", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "telemetry_logs.csv", "field_name": "client_ip", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "CSV", "dataset_name": "telemetry_logs.csv", "field_name": "mac_address", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "CSV", "dataset_name": "telemetry_logs.csv", "field_name": "session_token", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "CSV", "dataset_name": "telemetry_logs.csv", "field_name": "http_status", "ground_truth_class": "Non_PII"},
            {"source_type": "CSV", "dataset_name": "telemetry_logs.csv", "field_name": "bytes_transferred", "ground_truth_class": "Non_PII"},

            # enterprise.db:users
            {"source_type": "SQL", "dataset_name": "enterprise.db:users", "field_name": "id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:users", "field_name": "full_name", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:users", "field_name": "user_id_email", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:users", "field_name": "phone_number", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:users", "field_name": "password_hash", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:users", "field_name": "role", "ground_truth_class": "Non_PII"},

            # enterprise.db:billing_details
            {"source_type": "SQL", "dataset_name": "enterprise.db:billing_details", "field_name": "billing_id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:billing_details", "field_name": "user_id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:billing_details", "field_name": "credit_card_mask", "ground_truth_class": "Financial_Banking_Data"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:billing_details", "field_name": "billing_address", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:billing_details", "field_name": "billing_pincode", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:billing_details", "field_name": "currency", "ground_truth_class": "Non_PII"},

            # enterprise.db:patient_records
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "patient_id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "patient_name", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "dob", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "gender", "ground_truth_class": "Direct_Personal_Identifiers"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "emergency_contact_phone", "ground_truth_class": "Contact_Location_Data"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "blood_group", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:patient_records", "field_name": "admission_notes", "ground_truth_class": "Non_PII"},

            # enterprise.db:auth_sessions
            {"source_type": "SQL", "dataset_name": "enterprise.db:auth_sessions", "field_name": "session_id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:auth_sessions", "field_name": "user_id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:auth_sessions", "field_name": "client_ip_address", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:auth_sessions", "field_name": "user_agent_token", "ground_truth_class": "Authentication_Digital_Telemetry"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:auth_sessions", "field_name": "login_time", "ground_truth_class": "Non_PII"},

            # enterprise.db:inventory_products (Non-PII Control Table)
            {"source_type": "SQL", "dataset_name": "enterprise.db:inventory_products", "field_name": "product_id", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:inventory_products", "field_name": "sku_code", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:inventory_products", "field_name": "unit_price", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:inventory_products", "field_name": "stock_quantity", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:inventory_products", "field_name": "warehouse_bay", "ground_truth_class": "Non_PII"},
            {"source_type": "SQL", "dataset_name": "enterprise.db:inventory_products", "field_name": "reorder_threshold", "ground_truth_class": "Non_PII"}
        ]
    }

    gt_file = os.path.join(BENCHMARK_DIR, "ground_truth_labels.json")
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"    - Generated Benchmark Ground Truth: {gt_file} ({len(ground_truth['labels'])} evaluated columns)")
    print("[+] Synthetic environment preparation complete!\n")

if __name__ == "__main__":
    generate_all()
