import os
import re
import json
import sqlite3
import pandas as pd
from tabulate import tabulate

# ==========================================
# 1. PREDEFINED 5 DATA CLASSES & RULES
# ==========================================
PII_RULES = {
    "Direct Identifiers": {
        "headers": [r"name", r"full_name", r"first_name", r"last_name", r"aadhaar", r"passport", r"pan_card", r"ssn"],
        "regex": [
            r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",       # Indian PAN Card
            r"^[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}$" # Aadhaar Number
        ]
    },
    "Contact Data": {
        "headers": [r"email", r"mail", r"phone", r"mobile", r"contact", r"address", r"zip", r"pincode"],
        "regex": [
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", # Email Regex
            r"^(\+91[\-\s]?)?[0-9]{10}$"                          # Phone Regex
        ]
    },
    "Financial Data": {
        "headers": [r"bank", r"account_no", r"card", r"upi", r"credit", r"debit", r"cvv", r"routing"],
        "regex": [
            r"^[0-9]{9,18}$",                        # Generic Bank Acc Number
            r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$" # UPI ID format
        ]
    },
    "Biographic & Demographics": {
        "headers": [r"dob", r"birth", r"age", r"gender", r"sex", r"nationality", r"marital"],
        "regex": [
            r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
            r"^\d{2}/\d{2}/\d{4}$"   # DD/MM/YYYY
        ]
    },
    "Network & Telemetry": {
        "headers": [r"ip", r"ip_address", r"mac", r"device", r"user_agent", r"lat", r"long"],
        "regex": [
            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", # IPv4 Address
            r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$" # MAC Address
        ]
    }
}

class PIIPrivacyScanner:
    def __init__(self, registry_path="data/purpose_registry.json"):
        self.registry = self._load_json(registry_path)

    def _load_json(self, path):
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def classify_field(self, col_name, sample_values):
        """Rule engine inspecting header semantics and data values."""
        col_clean = col_name.strip().lower()
        
        for pii_class, rules in PII_RULES.items():
            # 1. Header Semantics Check
            for pattern in rules["headers"]:
                if re.search(pattern, col_clean):
                    return pii_class
            
            # 2. Value Pattern Match Check
            for val in sample_values.dropna().astype(str):
                val_clean = val.strip()
                for pattern in rules["regex"]:
                    if re.match(pattern, val_clean):
                        return pii_class
        return None

    def scan_dataframe(self, df, source_name):
        """Scans a dataframe and links discovered PII to purpose/retention metadata."""
        inventory = []
        source_registry = self.registry.get(source_name, {})

        for col in df.columns:
            pii_class = self.classify_field(col, df[col].head(20))
            if pii_class:
                meta = source_registry.get(col, {})
                purpose = meta.get("declared_purpose", None)
                retention = meta.get("retention_period_months", None)
                
                # Flag missing metadata gaps
                gap_flag = False
                missing_fields = []
                if not purpose:
                    gap_flag = True
                    missing_fields.append("Declared Purpose Missing")
                if not retention:
                    gap_flag = True
                    missing_fields.append("Retention Period Missing")

                inventory.append({
                    "Source": source_name,
                    "Field Name": col,
                    "Discovered Class": pii_class,
                    "Declared Purpose": purpose if purpose else "UNMAPPED",
                    "Retention (Months)": retention if retention else "UNMAPPED",
                    "Metadata Gap": "⚠️ " + ", ".join(missing_fields) if gap_flag else "✅ Complete"
                })
        return inventory

    def evaluate_performance(self, discovered_inventory, test_set_path="data/labeled_test_set.json"):
        """Evaluates per-class Precision and Recall against a ground-truth dataset."""
        ground_truth = self._load_json(test_set_path)
        if not ground_truth:
            print("No test set found for evaluation.")
            return

        # Map discovered results: key -> (source, field_name)
        discovered_map = {(item["Source"], item["Field Name"]): item["Discovered Class"] for item in discovered_inventory}
        
        metrics = {cls: {"TP": 0, "FP": 0, "FN": 0} for cls in PII_RULES.keys()}

        for item in ground_truth:
            src = item["source"]
            field = item["field_name"]
            true_cls = item["true_class"]
            pred_cls = discovered_map.get((src, field), None)

            if pred_cls == true_cls:
                metrics[true_cls]["TP"] += 1
            else:
                metrics[true_cls]["FN"] += 1
                if pred_cls in metrics:
                    metrics[pred_cls]["FP"] += 1

        print("\n" + "="*75)
        print("📊 ACCURACY EVALUATION REPORT (Per-Class Precision & Recall)")
        print("="*75)
        
        eval_table = []
        for cls, counts in metrics.items():
            tp, fp, fn = counts["TP"], counts["FP"], counts["FN"]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            eval_table.append([cls, tp, fp, fn, f"{precision:.2%}", f"{recall:.2%}"])

        print(tabulate(eval_table, headers=["PII Class", "TP", "FP", "FN", "Precision", "Recall"], tablefmt="grid"))


# ==========================================
# 5. DEMO EXECUTION PIPELINE
# ==========================================
def create_synthetic_data():
    """Generates synthetic CSV and SQLite Database files for demonstration."""
    os.makedirs("data/synthetic", exist_ok=True)

    # 1. Synthetic CSV
    users_df = pd.DataFrame({
        "user_id": [101, 102],
        "full_name": ["Alice Smith", "Bob Jones"],
        "email": ["alice@example.com", "bob@example.com"],
        "pan_card": ["ABCDE1234F", "XYZPG9876K"],
        "signup_ip": ["192.168.1.1", "10.0.0.1"]
    })
    users_df.to_csv("data/synthetic/users.csv", index=False)

    # 2. Synthetic SQLite DB
    conn = sqlite3.connect("data/synthetic/app_database.db")
    cust_df = pd.DataFrame({
        "cust_id": [1, 2],
        "customer_name": ["John Doe", "Jane Miller"],
        "phone": ["+919876543210", "+919123456789"],
        "bank_acc_no": ["123456789012", "987654321098"],
        "dob": ["1990-05-14", "1985-11-20"],
        "ip_address": ["172.16.0.45", "172.16.0.88"]
    })
    cust_df.to_sql("customers", conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    print("🚀 Initializing Synthetic Datasets...")
    create_synthetic_data()

    scanner = PIIPrivacyScanner()
    full_inventory = []

    # Process CSV Data Source
    csv_path = "data/synthetic/users.csv"
    csv_df = pd.read_csv(csv_path)
    full_inventory.extend(scanner.scan_dataframe(csv_df, source_name="users.csv"))

    # Process SQL Data Source
    conn = sqlite3.connect("data/synthetic/app_database.db")
    sql_df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    full_inventory.extend(scanner.scan_dataframe(sql_df, source_name="customers"))

    # Print Technical Evidence Inventory
    print("\n" + "="*75)
    print("🔍 TECHNICAL PRIVACY EVIDENCE & METADATA GAP INVENTORY")
    print("="*75)
    print(tabulate(full_inventory, headers="keys", tablefmt="grid"))

    # Run Benchmark Evaluation
    scanner.evaluate_performance(full_inventory)