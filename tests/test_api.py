import os
import pytest
from fastapi.testclient import TestClient
from main import app
from src.db import DB_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup - let database initialize
    yield
    # Teardown - we keep db for manual tests but can clean up runs if we want.
    # To isolate tests, we could delete dashboard.db, but since init_db runs at import,
    # keeping the database is fine.


def test_api_settings():
    # Test GET settings
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "jira_base_url" in data

    # Test POST settings
    payload = {"jira_base_url": "https://test.jira.com/browse/"}
    response = client.post("/api/settings", json=payload)
    assert response.status_code == 200
    assert response.json()["jira_base_url"] == "https://test.jira.com/browse/"

    # Test GET updates
    response = client.get("/api/settings")
    assert response.json()["jira_base_url"] == "https://test.jira.com/browse/"


def test_api_developers_map():
    # Test GET developers
    response = client.get("/api/developers")
    assert response.status_code == 200
    assert "developers" in response.json()

    # Test POST developers mapping update
    payload = [
        {"display_name": "Test Dev", "email": "test.dev@cashflo.io"},
        {"display_name": "Second Dev", "email": "second.dev@cashflo.io"},
    ]
    response = client.post("/api/developers", json=payload)
    assert response.status_code == 200
    assert response.json()["count"] == 2

    # Verify update
    response = client.get("/api/developers")
    devs = response.json()["developers"]
    assert len(devs) == 2
    assert devs[0]["display_name"] == "Test Dev"
    assert devs[0]["email"] == "test.dev@cashflo.io"


def test_api_upload_flow():
    # 1. First set up developers map fixture in developers.csv for mapping to pass
    # (since developers.csv is read in upload flow)
    devs_payload = [
        {"display_name": "Navneet Shukla", "email": "navneet.shukla@cashflo.io"},
        {"display_name": "Shiva Kumar Swami", "email": "shivakumar.swami@cashflo.io"},
        {"display_name": "Chetan Nikam", "email": "chetan.nikam@cashflo.io"},
    ]
    client.post("/api/developers", json=devs_payload)

    # 2. Upload three CSV files
    claude_path = "tests/fixtures/claude_export.csv"
    jira_deliv_path = "tests/fixtures/jira_deliverables.csv"
    jira_bugs_path = "tests/fixtures/jira_bugs.csv"

    with open(claude_path, "rb") as f_claude, \
         open(jira_deliv_path, "rb") as f_deliv, \
         open(jira_bugs_path, "rb") as f_bugs:
        
        response = client.post(
            "/api/upload",
            data={"period": "2026-05"},
            files={
                "claude_file": ("claude.csv", f_claude, "text/csv"),
                "jira_deliverables_file": ("jira_deliv.csv", f_deliv, "text/csv"),
                "jira_bugs_file": ("jira_bugs.csv", f_bugs, "text/csv"),
            }
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["period"] == "2026-05"

    # 3. Retrieve periods
    response = client.get("/api/periods")
    assert response.status_code == 200
    assert "2026-05" in response.json()["periods"]

    # 4. Retrieve leaderboard for 2026-05
    response = client.get("/api/leaderboard?period=2026-05")
    assert response.status_code == 200
    leaderboard = response.json()
    assert leaderboard["period"] == "2026-05"
    assert len(leaderboard["metrics"]) == 3  # Navneet, Shiva, Chetan

    # Sort checks
    metrics = leaderboard["metrics"]
    # Verify Navneet is present
    navneet_row = next(m for m in metrics if m["email"] == "navneet.shukla@cashflo.io")
    assert navneet_row["spend_usd"] == 335.06
    assert navneet_row["bugs_attributed"] == 1
    assert navneet_row["flag"] == "yellow"

    # 5. Retrieve developer profile
    response = client.get("/api/developer/navneet.shukla@cashflo.io?period=2026-05")
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == "navneet.shukla@cashflo.io"
    assert profile_data["profile"]["spend_usd"] == 335.06
    assert len(profile_data["bugs"]) == 1
    assert profile_data["bugs"][0]["bug_key"] == "BUG-201"
    assert len(profile_data["history"]) >= 1

    # 6. Retrieve team trends
    response = client.get("/api/team/trends")
    assert response.status_code == 200
    trends = response.json()["trends"]
    assert len(trends) >= 1
    assert trends[0]["period"] == "2026-05"
    assert trends[0]["total_deliverables"] == 5
    assert trends[0]["total_bugs"] == 2
