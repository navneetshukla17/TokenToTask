import csv
import subprocess
import sys

OUTPUT_PATH = "tests/fixtures/integration_output.csv"

CMD = [
    sys.executable, "merge.py",
    "tests/fixtures/claude_export.csv",
    "tests/fixtures/jira_deliverables.csv",
    "tests/fixtures/jira_bugs.csv",
    "tests/fixtures/developers.csv",
    "--period", "2026-05",
    "--output", OUTPUT_PATH,
]


def test_pipeline_runs_without_error():
    result = subprocess.run(CMD, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_output_has_three_developer_rows():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3


def test_navneet_has_correct_spend():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = {r["email"]: r for r in csv.DictReader(f)}
    assert float(rows["navneet.shukla@cashflo.io"]["spend_usd"]) == 335.06


def test_navneet_has_1_bug_attributed():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = {r["email"]: r for r in csv.DictReader(f)}
    # BUG-201: created 2026-05-20, Navneet's CASH-101 resolved 2026-05-15
    # Same sprint (Sprint 12) + same epic (CASH-EP1), within 30 days
    assert rows["navneet.shukla@cashflo.io"]["bugs_attributed"] == "1"


def test_chetan_has_0_bugs_attributed():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = {r["email"]: r for r in csv.DictReader(f)}
    # BUG-203: created 2026-08-01, 78 days after CASH-105, different sprint/epic
    assert rows["chetan.nikam@cashflo.io"]["bugs_attributed"] == "0"


def test_navneet_efficiency_score_is_na_due_to_low_coverage():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = {r["email"]: r for r in csv.DictReader(f)}
    # Navneet: CASH-101 has 5 pts, CASH-102 has None -> 50% coverage < 80%
    assert rows["navneet.shukla@cashflo.io"]["ai_efficiency_score"] == "N/A"


def test_shiva_efficiency_score_computed():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = {r["email"]: r for r in csv.DictReader(f)}
    # Shiva: CASH-103 (8pts) + CASH-104 (3pts) = 11pts, both have points -> 100% coverage
    # efficiency = 11 / 181.46 ~= 0.0606
    score = float(rows["shivakumar.swami@cashflo.io"]["ai_efficiency_score"])
    assert 0.06 < score < 0.07
