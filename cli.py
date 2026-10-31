"""
Command-Line Interface for PS-019 Personal-Data Discovery Scanner.
Provides rich terminal reporting for discovery scans, metadata linking,
and per-class precision/recall benchmark evaluations.
"""

import os
import sys
import json
import argparse
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core.scanner import PersonalDataScanner
from core.evaluator import BenchmarkEvaluator

console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "enterprise.db")
DEFAULT_OUTPUT_JSON = os.path.join(BASE_DIR, "privacy_evidence_inventory.json")

def print_banner():
    banner_text = (
        "[bold cyan]PS-019: Personal-Data Discovery & Privacy Evidence Inventory[/bold cyan]\n"
        "[dim]Cybersecurity & Privacy Engineering Suite | MeitY DPDPA 2023 Aligned[/dim]\n"
        "[bold yellow]DISCLAIMER: Technical Evidence Inventory Only. Not Legal Advice.[/bold yellow]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))

def cmd_scan(args):
    print_banner()
    console.print(f"[green][*] Initializing Discovery Scanner...[/green]")
    console.print(f"[dim]    Scanning CSV Directory: {args.csv_dir}[/dim]")
    console.print(f"[dim]    Scanning SQL Database: {args.sql_db}[/dim]\n")

    scanner = PersonalDataScanner()
    report = scanner.run_full_scan(
        csv_dir_or_files=args.csv_dir,
        sql_db_path=args.sql_db if os.path.exists(args.sql_db) else None
    )

    metrics = report["summary_metrics"]
    inventory = report["evidence_inventory"]

    # Summary Panel
    summary_msg = (
        f"[bold]Total Inspected Columns:[/bold] {metrics['total_columns_inspected']}\n"
        f"[bold cyan]Candidate PII Fields Discovered:[/bold cyan] {metrics['candidate_personal_data_fields']}\n"
        f"[bold green]Documented Inventory Fields:[/bold green] {metrics['documented_personal_fields']}\n"
        f"[bold red]Shadow Data (Evidence Gaps):[/bold red] {metrics['shadow_pii_with_evidence_gaps']} "
        f"({metrics['evidence_gap_rate_percent']}% Gap Rate)\n"
        f"[bold yellow]Missing Purpose Flags:[/bold yellow] {metrics['missing_purpose_count']} | "
        f"[bold yellow]Missing Retention Flags:[/bold yellow] {metrics['missing_retention_count']}\n"
        f"[dim]Scan Execution Time: {report['scan_metadata']['duration_seconds']}s[/dim]"
    )
    console.print(Panel(summary_msg, title="[bold]Scan Execution Summary[/bold]", border_style="blue"))

    # Table of Discovered Personal Data
    table = Table(title="[bold magenta]Discovered Personal Data Fields & Governance Linkage[/bold magenta]")
    table.add_column("Dataset / Source", style="cyan", no_wrap=True)
    table.add_column("Field Name", style="bold white")
    table.add_column("Predicted Class", style="magenta")
    table.add_column("Conf.", justify="center", style="yellow")
    table.add_column("Declared Purpose", style="green")
    table.add_column("Retention Schedule", style="cyan")
    table.add_column("Evidence Status", justify="center")

    for f in inventory:
        if f["is_personal_data"]:
            status_style = "[bold green]DOCUMENTED[/bold green]" if f["audit_status"] == "DOCUMENTED_INVENTORY" else "[bold red]GAP FLAGGED[/bold red]"
            purpose_text = f["governance_metadata"]["declared_purpose"]
            if "GAP" in purpose_text:
                purpose_text = f"[red]{purpose_text}[/red]"
            
            retention_text = f["governance_metadata"]["retention_period"]
            if "GAP" in retention_text:
                retention_text = f"[red]{retention_text}[/red]"

            table.add_row(
                f["dataset_name"],
                f["field_name"],
                f["predicted_class"].replace("_", " "),
                f"{int(f['confidence_score'] * 100)}%",
                purpose_text,
                retention_text,
                status_style
            )

    console.print(table)

    # Save to JSON
    with open(args.output, "w", encoding="utf-8") as out_f:
        json.dump(report, out_f, indent=2)
    console.print(f"\n[bold green][+] Technical Evidence Inventory written to:[/bold green] [underline]{args.output}[/underline]\n")

def cmd_evaluate(args):
    print_banner()
    console.print("[green][*] Executing Precision and Recall Evaluation against Ground Truth Benchmark...[/green]\n")

    scanner = PersonalDataScanner()
    report = scanner.run_full_scan(
        csv_dir_or_files=args.csv_dir,
        sql_db_path=args.sql_db if os.path.exists(args.sql_db) else None
    )

    evaluator = BenchmarkEvaluator()
    eval_res = evaluator.evaluate(report["evidence_inventory"])

    summary = eval_res["evaluation_summary"]
    per_class = eval_res["per_class_metrics"]

    # Per-Class Metrics Table
    table = Table(title="[bold cyan]Per-Class Precision, Recall, and F1-Score (5 Data Classes)[/bold cyan]")
    table.add_column("Data Class", style="bold white")
    table.add_column("TP", justify="center", style="green")
    table.add_column("FP", justify="center", style="red")
    table.add_column("FN", justify="center", style="red")
    table.add_column("Support", justify="center", style="cyan")
    table.add_column("Precision", justify="right", style="yellow")
    table.add_column("Recall", justify="right", style="magenta")
    table.add_column("F1-Score", justify="right", style="bold green")

    for cls_name, m in per_class.items():
        table.add_row(
            m["display_name"],
            str(m["true_positives"]),
            str(m["false_positives"]),
            str(m["false_negatives"]),
            str(m["support"]),
            f"{m['precision_percent']}%",
            f"{m['recall_percent']}%",
            f"{m['f1_percent']}%"
        )

    console.print(table)

    # Macro Summary Panel
    macro_msg = (
        f"[bold]Total Benchmark Columns Evaluated:[/bold] {summary['matched_evaluated_samples']}\n"
        f"[bold green]Macro Precision:[/bold green] {summary['macro_precision_percent']}%\n"
        f"[bold green]Macro Recall:[/bold green] {summary['macro_recall_percent']}%\n"
        f"[bold green]Macro F1-Score:[/bold green] {summary['macro_f1_percent']}%\n"
        f"[bold cyan]Non-PII Negative Specificity:[/bold cyan] {summary['non_pii_specificity_percent']}%\n"
        f"[bold blue]Binary PII Detection F1:[/bold blue] {round(summary['micro_f1_score'] * 100, 2)}%"
    )
    console.print(Panel(macro_msg, title="[bold]Evaluation Benchmark Summary[/bold]", border_style="green"))

    # Save evaluation report
    eval_out_path = os.path.join(BASE_DIR, "evaluation_benchmark_results.json")
    with open(eval_out_path, "w", encoding="utf-8") as f:
        json.dump(eval_res, f, indent=2)
    console.print(f"[bold green][+] Benchmark evaluation results written to:[/bold green] [underline]{eval_out_path}[/underline]\n")

def main():
    parser = argparse.ArgumentParser(
        description="PS-019 Personal-Data Discovery and Privacy Evidence Inventory CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan CSV datasets and SQL database")
    scan_parser.add_argument("--csv-dir", default=DEFAULT_DATA_DIR, help="Path to CSV folder or file")
    scan_parser.add_argument("--sql-db", default=DEFAULT_DB_PATH, help="Path to SQLite database")
    scan_parser.add_argument("--output", default=DEFAULT_OUTPUT_JSON, help="Path to output JSON inventory")

    # evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate scanner precision and recall")
    eval_parser.add_argument("--csv-dir", default=DEFAULT_DATA_DIR, help="Path to CSV folder or file")
    eval_parser.add_argument("--sql-db", default=DEFAULT_DB_PATH, help="Path to SQLite database")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    else:
        # Default run both scan and evaluate if no arg given
        parser.print_help()
        console.print("\n[yellow]Running default full scan & evaluation demonstration...[/yellow]\n")
        class DefaultArgs:
            csv_dir = DEFAULT_DATA_DIR
            sql_db = DEFAULT_DB_PATH
            output = DEFAULT_OUTPUT_JSON
        cmd_scan(DefaultArgs)
        cmd_evaluate(DefaultArgs)

if __name__ == "__main__":
    main()
