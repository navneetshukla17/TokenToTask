import re
from typing import List, Dict, Tuple
from collections import defaultdict

from src.loaders.claude_loader import load_claude_csv
from src.loaders.jira_loader import load_developer_map, load_deliverables_csv, load_bugs_csv
from src.metrics import compute_developer_metrics
from src.guardrail import attribute_bugs_detailed, apply_flags
from src.models import DeveloperMetrics
from src.db import add_run, save_metrics, save_attributed_bugs, get_db_connection


def run_pipeline(
    claude_csv_path: str,
    jira_deliverables_path: str,
    jira_bugs_path: str,
    developers_csv_path: str,
    period: str,
    trigger_type: str,
) -> Tuple[int, List[DeveloperMetrics]]:
    """Runs the metrics pipeline for a period, saves to SQLite, and updates the run status."""
    # 1. Create running log entry in DB
    run_id = add_run(period, trigger_type, "running")

    try:
        # 2. Load inputs
        developer_map = load_developer_map(developers_csv_path)
        claude_data = load_claude_csv(claude_csv_path)
        deliverables = load_deliverables_csv(jira_deliverables_path, developer_map)
        bugs = load_bugs_csv(jira_bugs_path, developer_map)

        # 3. Filter deliverables and apply weekly fallback if needed
        is_weekly = bool(re.match(r"^\d{4}-W\d{2}$", period))
        is_monthly = bool(re.match(r"^\d{4}-\d{2}$", period))

        if not is_weekly and not is_monthly:
            raise ValueError(
                f"Invalid period format: '{period}'. Must be YYYY-MM or YYYY-Www."
            )

        if is_weekly:
            # Filter deliverables by ISO week resolved date
            filtered_deliverables = []
            for d in deliverables:
                iso_yr, iso_wk, _ = d.resolved_date.isocalendar()
                d_week = f"{iso_yr}-W{iso_wk:02d}"
                if d_week == period:
                    filtered_deliverables.append(d)
            deliverables = filtered_deliverables

            # Scale Claude monthly spend and lines of code by dividing by 4.3
            for email in claude_data:
                claude_data[email]["spend_usd"] = round(
                    claude_data[email]["spend_usd"] / 4.3, 2
                )
                claude_data[email]["lines_of_code"] = int(
                    claude_data[email]["lines_of_code"] / 4.3
                )
        else:
            # Filter deliverables by monthly resolved date
            deliverables = [
                d
                for d in deliverables
                if d.resolved_date.strftime("%Y-%m") == period
            ]

        # 4. Group deliverables by email
        deliverables_by_email = defaultdict(list)
        for d in deliverables:
            deliverables_by_email[d.email].append(d)

        # Map name for output
        name_map = {email: name.title() for name, email in developer_map.items()}

        all_emails = sorted(set(claude_data.keys()) | set(deliverables_by_email.keys()))

        # 5. Compute metrics
        metrics = []
        for email in all_emails:
            m = compute_developer_metrics(
                email=email,
                display_name=name_map.get(email, email),
                period=period,
                claude_data=claude_data.get(
                    email, {"spend_usd": 0.0, "lines_of_code": 0}
                ),
                deliverables=deliverables_by_email.get(email, []),
            )
            metrics.append(m)

        # 6. Bug attribution & Flags
        metrics, attributed_bugs = attribute_bugs_detailed(
            metrics, dict(deliverables_by_email), bugs
        )
        metrics = apply_flags(metrics)

        # 7. Save to Database
        save_metrics(run_id, metrics)

        # Group attributed bugs by developer email
        bugs_by_email = defaultdict(list)
        for b in attributed_bugs:
            bugs_by_email[b["email"]].append(b)

        for email, dev_bugs in bugs_by_email.items():
            save_attributed_bugs(run_id, email, dev_bugs)

        # Update run status to success
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET status = 'success' WHERE id = ?", (run_id,)
        )
        conn.commit()
        conn.close()

        return run_id, metrics

    except Exception as e:
        # Update run status to failed with error message
        error_msg = str(e)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET status = 'failed', error_message = ? WHERE id = ?",
            (error_msg, run_id),
        )
        conn.commit()
        conn.close()
        raise e
