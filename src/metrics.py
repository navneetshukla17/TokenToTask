from typing import List, Optional
from src.models import Deliverable, DeveloperMetrics

STORY_POINTS_COVERAGE_THRESHOLD = 0.8


def compute_story_points_coverage(deliverables: List[Deliverable]) -> float:
    if not deliverables:
        return 0.0
    with_points = sum(1 for d in deliverables if d.story_points is not None)
    return with_points / len(deliverables)


def compute_developer_metrics(
    email: str,
    display_name: str,
    period: str,
    claude_data: dict,
    deliverables: List[Deliverable],
) -> DeveloperMetrics:
    spend = claude_data.get("spend_usd", 0.0)
    lines = claude_data.get("lines_of_code", 0)
    count = len(deliverables)
    sp = sum(d.story_points or 0 for d in deliverables)
    coverage = compute_story_points_coverage(deliverables)

    cost_per_del: Optional[float] = spend / count if count > 0 else None
    lines_per_del: Optional[float] = lines / count if count > 0 else None
    cost_per_line: Optional[float] = spend / lines if lines > 0 else None

    efficiency: Optional[float] = None
    if coverage >= STORY_POINTS_COVERAGE_THRESHOLD and spend > 0 and sp > 0:
        efficiency = sp / spend

    return DeveloperMetrics(
        email=email,
        display_name=display_name,
        period=period,
        spend_usd=spend,
        lines_of_code=lines,
        deliverables_count=count,
        story_points_delivered=sp,
        story_points_coverage=coverage,
        cost_per_deliverable=cost_per_del,
        lines_per_deliverable=lines_per_del,
        cost_per_line=cost_per_line,
        ai_efficiency_score=efficiency,
        bugs_attributed=0,
        bug_rate=None,
        flag="",
    )
