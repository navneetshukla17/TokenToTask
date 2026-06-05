import argparse
from datetime import datetime

from src.db import init_db
from src.pipeline import run_pipeline
from src.output import write_output_csv


def main():
    parser = argparse.ArgumentParser(
        description="Merge Claude Console + JIRA exports into developer metrics CSV"
    )
    parser.add_argument("claude_csv", help="Claude Console export CSV")
    parser.add_argument("jira_deliverables_csv", help="JIRA closed Stories/Tasks CSV")
    parser.add_argument("jira_bugs_csv", help="JIRA Bug tickets CSV")
    parser.add_argument("developers_csv", help="Developer display_name->email mapping CSV")
    parser.add_argument(
        "--period",
        default=datetime.now().strftime("%Y-%m"),
        help="Reporting period YYYY-MM or YYYY-Www (default: current month)",
    )
    parser.add_argument("--output", default="output.csv", help="Output CSV path")
    parser.add_argument("--sheet-id", default=None, help="Google Sheets ID (optional)")
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Google service account JSON path (only needed with --sheet-id)",
    )
    args = parser.parse_args()

    # Initialize database
    init_db()

    # Run the pipeline (logging it as CLI trigger type)
    _, metrics = run_pipeline(
        claude_csv_path=args.claude_csv,
        jira_deliverables_path=args.jira_deliverables_csv,
        jira_bugs_path=args.jira_bugs_csv,
        developers_csv_path=args.developers_csv,
        period=args.period,
        trigger_type="cli",
    )

    write_output_csv(metrics, args.output)
    print(f"Output written to {args.output} ({len(metrics)} developers)")

    if args.sheet_id:
        from src.sheets import get_sheets_client, append_to_sheet
        client = get_sheets_client(args.credentials)
        append_to_sheet(client, args.sheet_id, "raw_data", metrics)
        print(f"Appended to Google Sheets: {args.sheet_id}")


if __name__ == "__main__":
    main()
