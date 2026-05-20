import pytest
from datetime import date
from src.models import Deliverable
from src.metrics import compute_story_points_coverage, compute_developer_metrics


def _make_deliverable(issue_key, story_points, resolved_date="2026-05-15"):
    return Deliverable(
        email="dev@cashflo.io",
        issue_key=issue_key,
        issue_type="Story",
        story_points=story_points,
        resolved_date=date.fromisoformat(resolved_date),
        sprint="Sprint 12",
        epic_key="CASH-EP1",
    )


def test_story_points_coverage_all_set():
    deliverables = [_make_deliverable("A", 5), _make_deliverable("B", 3)]
    assert compute_story_points_coverage(deliverables) == pytest.approx(1.0)


def test_story_points_coverage_half_set():
    deliverables = [_make_deliverable("A", 5), _make_deliverable("B", None)]
    assert compute_story_points_coverage(deliverables) == pytest.approx(0.5)


def test_story_points_coverage_empty():
    assert compute_story_points_coverage([]) == pytest.approx(0.0)


def test_compute_metrics_basic():
    deliverables = [
        _make_deliverable("A", 5),
        _make_deliverable("B", 3),
        _make_deliverable("C", 2),
    ]
    claude_data = {"spend_usd": 300.0, "lines_of_code": 30000}
    m = compute_developer_metrics(
        email="dev@cashflo.io",
        display_name="Dev",
        period="2026-05",
        claude_data=claude_data,
        deliverables=deliverables,
    )
    assert m.deliverables_count == 3
    assert m.story_points_delivered == 10
    assert m.cost_per_deliverable == pytest.approx(100.0)
    assert m.lines_per_deliverable == pytest.approx(10000.0)
    assert m.cost_per_line == pytest.approx(0.01)


def test_ai_efficiency_score_computed_when_coverage_above_80_percent():
    deliverables = [_make_deliverable("A", 5), _make_deliverable("B", 3)]
    claude_data = {"spend_usd": 100.0, "lines_of_code": 5000}
    m = compute_developer_metrics("dev@cashflo.io", "Dev", "2026-05", claude_data, deliverables)
    # 8 story_points / $100 = 0.08
    assert m.ai_efficiency_score == pytest.approx(0.08)


def test_ai_efficiency_score_is_none_when_coverage_below_80_percent():
    # Only 1 of 2 has story points = 50% coverage
    deliverables = [_make_deliverable("A", 5), _make_deliverable("B", None)]
    claude_data = {"spend_usd": 100.0, "lines_of_code": 5000}
    m = compute_developer_metrics("dev@cashflo.io", "Dev", "2026-05", claude_data, deliverables)
    assert m.ai_efficiency_score is None
    assert m.story_points_coverage == pytest.approx(0.5)


def test_cost_per_deliverable_is_none_when_no_deliverables():
    claude_data = {"spend_usd": 100.0, "lines_of_code": 5000}
    m = compute_developer_metrics("dev@cashflo.io", "Dev", "2026-05", claude_data, [])
    assert m.cost_per_deliverable is None
    assert m.ai_efficiency_score is None


def test_metrics_zero_spend():
    deliverables = [_make_deliverable("A", 5)]
    claude_data = {"spend_usd": 0.0, "lines_of_code": 0}
    m = compute_developer_metrics("dev@cashflo.io", "Dev", "2026-05", claude_data, deliverables)
    assert m.cost_per_deliverable == pytest.approx(0.0)
    assert m.cost_per_line is None
    assert m.ai_efficiency_score is None
