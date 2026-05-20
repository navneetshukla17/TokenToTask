import gspread
from google.oauth2.service_account import Credentials
from typing import List
from src.models import DeveloperMetrics

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_client(credentials_path: str) -> gspread.Client:
    creds = Credentials.from_service_account_file(credentials_path, scopes=_SCOPES)
    return gspread.authorize(creds)


def append_to_sheet(
    client: gspread.Client,
    sheet_id: str,
    worksheet_name: str,
    metrics: List[DeveloperMetrics],
) -> None:
    ws = client.open_by_key(sheet_id).worksheet(worksheet_name)
    rows = []
    for m in metrics:
        rows.append([
            m.email,
            m.display_name,
            m.period,
            round(m.spend_usd, 2),
            m.lines_of_code,
            m.deliverables_count,
            m.story_points_delivered,
            round(m.story_points_coverage, 2),
            round(m.cost_per_deliverable, 2) if m.cost_per_deliverable is not None else "",
            round(m.lines_per_deliverable, 1) if m.lines_per_deliverable is not None else "",
            round(m.cost_per_line, 5) if m.cost_per_line is not None else "",
            round(m.ai_efficiency_score, 3) if m.ai_efficiency_score is not None else "N/A",
            m.bugs_attributed,
            round(m.bug_rate, 2) if m.bug_rate is not None else "",
            m.flag,
        ])
    ws.append_rows(rows, value_input_option="USER_ENTERED")
