from datetime import date
from src.models import Deliverable, Bug, DeveloperMetrics


def test_deliverable_instantiation():
    d = Deliverable(
        email="dev@cashflo.io",
        issue_key="CASH-101",
        issue_type="Story",
        story_points=5,
        resolved_date=date(2026, 5, 15),
        sprint="Sprint 12",
        epic_key="CASH-EP1",
    )
    assert d.email == "dev@cashflo.io"
    assert d.story_points == 5


def test_deliverable_no_story_points():
    d = Deliverable(
        email="dev@cashflo.io",
        issue_key="CASH-102",
        issue_type="Task",
        story_points=None,
        resolved_date=date(2026, 5, 15),
        sprint="Sprint 12",
        epic_key="",
    )
    assert d.story_points is None


def test_bug_instantiation():
    b = Bug(
        email="dev@cashflo.io",
        issue_key="BUG-201",
        created_date=date(2026, 5, 20),
        sprint="Sprint 12",
        epic_key="CASH-EP1",
    )
    assert b.issue_key == "BUG-201"


def test_developer_metrics_instantiation():
    m = DeveloperMetrics(
        email="dev@cashflo.io",
        display_name="Dev User",
        period="2026-05",
        spend_usd=335.06,
        lines_of_code=42068,
        deliverables_count=10,
        story_points_delivered=50,
        story_points_coverage=1.0,
        cost_per_deliverable=33.5,
        lines_per_deliverable=4206.8,
        cost_per_line=0.008,
        ai_efficiency_score=0.149,
        bugs_attributed=2,
        bug_rate=0.2,
        flag="green",
    )
    assert m.flag == "green"
    assert m.ai_efficiency_score == 0.149
