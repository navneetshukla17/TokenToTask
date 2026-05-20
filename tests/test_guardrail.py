import pytest
from datetime import date
from src.models import Deliverable, Bug, DeveloperMetrics
from src.guardrail import attribute_bugs, apply_flags


def _make_metric(email, deliverables_count=2, efficiency=0.1, bug_rate=None):
    return DeveloperMetrics(
        email=email, display_name=email, period="2026-05",
        spend_usd=100.0, lines_of_code=5000,
        deliverables_count=deliverables_count, story_points_delivered=10,
        story_points_coverage=1.0, cost_per_deliverable=50.0,
        lines_per_deliverable=2500.0, cost_per_line=0.02,
        ai_efficiency_score=efficiency,
        bugs_attributed=0, bug_rate=bug_rate, flag="",
    )


def _make_deliverable(email, resolved, sprint, epic):
    return Deliverable(
        email=email, issue_key="CASH-1", issue_type="Story",
        story_points=5, resolved_date=date.fromisoformat(resolved),
        sprint=sprint, epic_key=epic,
    )


def _make_bug(email, created, sprint, epic):
    return Bug(
        email=email, issue_key="BUG-1",
        created_date=date.fromisoformat(created),
        sprint=sprint, epic_key=epic,
    )


def test_bug_attributed_within_30_days_same_epic():
    metrics = [_make_metric("dev@cashflo.io")]
    deliverables_by_email = {
        "dev@cashflo.io": [_make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 1", "EP-1")]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-05-20", "Sprint 1", "EP-1")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 1


def test_bug_attributed_within_30_days_same_sprint_and_epic():
    metrics = [_make_metric("dev@cashflo.io")]
    deliverables_by_email = {
        "dev@cashflo.io": [_make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 12", "EP-1")]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-05-20", "Sprint 12", "EP-1")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 1


def test_bug_not_attributed_same_sprint_different_epic():
    metrics = [_make_metric("dev@cashflo.io")]
    deliverables_by_email = {
        "dev@cashflo.io": [_make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 12", "EP-1")]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-05-20", "Sprint 12", "EP-DIFFERENT")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 0


def test_bug_not_attributed_outside_30_days():
    metrics = [_make_metric("dev@cashflo.io")]
    deliverables_by_email = {
        "dev@cashflo.io": [_make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 1", "EP-1")]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-07-01", "Sprint 1", "EP-1")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 0


def test_bug_not_attributed_different_epic_and_sprint():
    metrics = [_make_metric("dev@cashflo.io")]
    deliverables_by_email = {
        "dev@cashflo.io": [_make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 1", "EP-1")]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-05-20", "Sprint 99", "EP-99")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 0


def test_bug_counted_once_per_developer_even_if_matches_multiple_stories():
    metrics = [_make_metric("dev@cashflo.io", deliverables_count=2)]
    deliverables_by_email = {
        "dev@cashflo.io": [
            _make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 1", "EP-1"),
            _make_deliverable("dev@cashflo.io", "2026-05-05", "Sprint 1", "EP-1"),
        ]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-05-20", "Sprint 1", "EP-1")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 1


def test_flag_green_high_efficiency_low_bugs():
    metrics = [
        _make_metric("a@c.io", efficiency=0.2),
        _make_metric("b@c.io", efficiency=0.05),
    ]
    metrics[0].bug_rate = 0.1
    metrics[1].bug_rate = 0.5
    result = apply_flags(metrics)
    assert result[0].flag == "green"


def test_flag_red_high_efficiency_high_bugs():
    metrics = [
        _make_metric("a@c.io", efficiency=0.2),
        _make_metric("b@c.io", efficiency=0.05),
    ]
    metrics[0].bug_rate = 0.5
    metrics[1].bug_rate = 0.1
    result = apply_flags(metrics)
    assert result[0].flag == "red"


def test_flag_yellow_low_efficiency_low_bugs():
    metrics = [
        _make_metric("a@c.io", efficiency=0.2),
        _make_metric("b@c.io", efficiency=0.05),
    ]
    metrics[0].bug_rate = 0.1
    metrics[1].bug_rate = 0.05
    result = apply_flags(metrics)
    assert result[1].flag == "yellow"
