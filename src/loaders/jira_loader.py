import pandas as pd
from typing import Dict, List
from src.models import Deliverable, Bug


def load_developer_map(path: str) -> Dict[str, str]:
    """Load developers.csv. Returns {display_name_lower: email_lower}."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return {
        row["display_name"].strip().lower(): row["email"].strip().lower()
        for _, row in df.iterrows()
    }


def _resolve_email(assignee: str, developer_map: Dict[str, str]) -> str:
    """Map JIRA display name to email. Falls back to assignee lowercased."""
    return developer_map.get(assignee.strip().lower(), assignee.strip().lower())


def load_deliverables_csv(path: str, developer_map: Dict[str, str]) -> List[Deliverable]:
    """Load JIRA closed Stories/Tasks CSV. Returns list of Deliverable."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    sp_col = next(
        (c for c in df.columns if "story point" in c.lower()),
        None,
    )

    records = []
    for _, row in df.iterrows():
        resolved_raw = row.get("Resolved", "")
        if pd.isna(resolved_raw) or str(resolved_raw).strip() == "":
            continue

        resolved_date = pd.to_datetime(resolved_raw).date()

        sp = None
        if sp_col and pd.notna(row[sp_col]) and str(row[sp_col]).strip() != "":
            try:
                sp = int(float(row[sp_col]))
            except (ValueError, TypeError):
                sp = None

        records.append(Deliverable(
            email=_resolve_email(str(row.get("Assignee", "")), developer_map),
            issue_key=str(row["Issue key"]).strip(),
            issue_type=str(row.get("Issue Type", "")).strip(),
            story_points=sp,
            resolved_date=resolved_date,
            sprint=str(row.get("Sprint", "")).strip(),
            epic_key=str(row.get("Epic Link", "")).strip(),
        ))
    return records


def load_bugs_csv(path: str, developer_map: Dict[str, str]) -> List[Bug]:
    """Load JIRA Bugs CSV. Returns list of Bug."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    records = []
    for _, row in df.iterrows():
        created_raw = row.get("Created", "")
        if pd.isna(created_raw) or str(created_raw).strip() == "":
            continue

        created_date = pd.to_datetime(created_raw).date()

        records.append(Bug(
            email=_resolve_email(str(row.get("Assignee", "")), developer_map),
            issue_key=str(row["Issue key"]).strip(),
            created_date=created_date,
            sprint=str(row.get("Sprint", "")).strip(),
            epic_key=str(row.get("Epic Link", "")).strip(),
        ))
    return records
