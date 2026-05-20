import csv
import os
import pytest
from src.models import DeveloperMetrics
from src.output import write_output_csv

OUTPUT_PATH = "tests/fixtures/test_output.csv"

METRICS = [
    DeveloperMetrics(
        email="navneet.shukla@cashflo.io",
        display_name="Navneet Shukla",
        period="2026-05",
        spend_usd=335.06,
        lines_of_code=42068,
        deliverables_count=2,
        story_points_delivered=5,
        story_points_coverage=0.5,
        cost_per_deliverable=167.53,
        lines_per_deliverable=21034.0,
        cost_per_line=0.00796,
        ai_efficiency_score=None,
        bugs_attributed=1,
        bug_rate=0.5,
        flag="gray",
    )
]


def test_creates_output_file():
    write_output_csv(METRICS, OUTPUT_PATH)
    assert os.path.exists(OUTPUT_PATH)


def test_output_has_correct_headers():
    write_output_csv(METRICS, OUTPUT_PATH)
    with open(OUTPUT_PATH, newline="") as f:
        reader = csv.DictReader(f)
        assert "email" in reader.fieldnames
        assert "ai_efficiency_score" in reader.fieldnames
        assert "flag" in reader.fieldnames
        assert "bug_rate" in reader.fieldnames


def test_none_efficiency_score_written_as_na():
    write_output_csv(METRICS, OUTPUT_PATH)
    with open(OUTPUT_PATH, newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row["ai_efficiency_score"] == "N/A"


def test_numeric_fields_rounded():
    write_output_csv(METRICS, OUTPUT_PATH)
    with open(OUTPUT_PATH, newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row["spend_usd"] == "335.06"
        assert row["bug_rate"] == "0.5"
