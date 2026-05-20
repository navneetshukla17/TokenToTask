from unittest.mock import MagicMock, patch
from src.models import DeveloperMetrics
from src.sheets import append_to_sheet

METRICS = [
    DeveloperMetrics(
        email="dev@cashflo.io", display_name="Dev", period="2026-05",
        spend_usd=100.0, lines_of_code=5000, deliverables_count=2,
        story_points_delivered=8, story_points_coverage=1.0,
        cost_per_deliverable=50.0, lines_per_deliverable=2500.0,
        cost_per_line=0.02, ai_efficiency_score=0.08,
        bugs_attributed=0, bug_rate=0.0, flag="green",
    )
]


def test_append_to_sheet_calls_append_rows():
    mock_client = MagicMock()
    mock_ws = MagicMock()
    mock_client.open_by_key.return_value.worksheet.return_value = mock_ws

    append_to_sheet(mock_client, "SHEET_ID_123", "raw_data", METRICS)

    mock_client.open_by_key.assert_called_once_with("SHEET_ID_123")
    mock_client.open_by_key.return_value.worksheet.assert_called_once_with("raw_data")
    mock_ws.append_rows.assert_called_once()
    rows_written = mock_ws.append_rows.call_args[0][0]
    assert len(rows_written) == 1
    assert rows_written[0][0] == "dev@cashflo.io"
    assert rows_written[0][11] == 0.08  # ai_efficiency_score at index 11


def test_none_efficiency_score_written_as_na_string():
    mock_client = MagicMock()
    mock_ws = MagicMock()
    mock_client.open_by_key.return_value.worksheet.return_value = mock_ws

    metrics_with_none = [
        DeveloperMetrics(
            email="dev@cashflo.io", display_name="Dev", period="2026-05",
            spend_usd=100.0, lines_of_code=5000, deliverables_count=2,
            story_points_delivered=8, story_points_coverage=0.5,
            cost_per_deliverable=50.0, lines_per_deliverable=2500.0,
            cost_per_line=0.02, ai_efficiency_score=None,
            bugs_attributed=0, bug_rate=0.0, flag="yellow",
        )
    ]
    append_to_sheet(mock_client, "SHEET_ID_123", "raw_data", metrics_with_none)

    rows_written = mock_ws.append_rows.call_args[0][0]
    assert rows_written[0][11] == "N/A"
