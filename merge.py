import argparse
from collections import defaultdict
from datetime import datetime

from src.loaders.claude_loader import load_claude_csv
from src.loaders.jira_loader import load_developer_map, load_deliverables_csv, load_bugs_csv
from src.metrics import compute_developer_metrics
from src.guardrail import attribute_bugs, apply_flags
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
        help="Reporting period YYYY-MM (default: current month)",
    )
    parser.add_argument("--output", default="output.csv", help="Output CSV path")
    parser.add_argument("--sheet-id", default=None, help="Google Sheets ID (optional)")
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Google service account JSON path (only needed with --sheet-id)",
    )
    args = parser.parse_args()

    developer_map = load_developer_map(args.developers_csv)
    claude_data = load_claude_csv(args.claude_csv)
    deliverables = load_deliverables_csv(args.jira_deliverables_csv, developer_map)
    bugs = load_bugs_csv(args.jira_bugs_csv, developer_map)

    deliverables_by_email = defaultdict(list)
    for d in deliverables:
        deliverables_by_email[d.email].append(d)

    # Reverse map: email -> display_name (title-case the key from developer_map)
    name_map = {email: name.title() for name, email in developer_map.items()}

    all_emails = sorted(set(claude_data.keys()) | set(deliverables_by_email.keys()))

    metrics = []
    for email in all_emails:
        m = compute_developer_metrics(
            email=email,
            display_name=name_map.get(email, email),
            period=args.period,
            claude_data=claude_data.get(email, {"spend_usd": 0.0, "lines_of_code": 0}),
            deliverables=deliverables_by_email.get(email, []),
        )
        metrics.append(m)

    metrics = attribute_bugs(metrics, dict(deliverables_by_email), bugs)
    metrics = apply_flags(metrics)

    write_output_csv(metrics, args.output)
    print(f"Output written to {args.output} ({len(metrics)} developers)")

    if args.sheet_id:
        from src.sheets import get_sheets_client, append_to_sheet
        client = get_sheets_client(args.credentials)
        append_to_sheet(client, args.sheet_id, "raw_data", metrics)
        print(f"Appended to Google Sheets: {args.sheet_id}")


if __name__ == "__main__":
    main()
