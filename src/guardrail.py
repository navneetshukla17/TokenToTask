import statistics
from typing import Dict, List, Optional
from src.models import Bug, Deliverable, DeveloperMetrics

BUG_WINDOW_DAYS = 30


def attribute_bugs(
    metrics: List[DeveloperMetrics],
    deliverables_by_email: Dict[str, List[Deliverable]],
    bugs: List[Bug],
) -> List[DeveloperMetrics]:
    for metric in metrics:
        dev_deliverables = deliverables_by_email.get(metric.email, [])
        attributed = 0
        for bug in bugs:
            for story in dev_deliverables:
                days_diff = (bug.created_date - story.resolved_date).days
                if 0 <= days_diff <= BUG_WINDOW_DAYS:
                    same_epic = bool(story.epic_key and bug.epic_key and story.epic_key == bug.epic_key)
                    same_sprint = bool(story.sprint and bug.sprint and story.sprint == bug.sprint)
                    if same_epic or same_sprint:
                        attributed += 1
                        break  # count each bug once per developer
        metric.bugs_attributed = attributed
        metric.bug_rate = attributed / metric.deliverables_count if metric.deliverables_count > 0 else None
    return metrics


def apply_flags(metrics: List[DeveloperMetrics]) -> List[DeveloperMetrics]:
    efficiency_scores = [m.ai_efficiency_score for m in metrics if m.ai_efficiency_score is not None]
    bug_rates = [m.bug_rate for m in metrics if m.bug_rate is not None]

    median_efficiency: Optional[float] = statistics.median(efficiency_scores) if efficiency_scores else None
    median_bug_rate: Optional[float] = statistics.median(bug_rates) if bug_rates else None

    for m in metrics:
        high_eff = (
            m.ai_efficiency_score is not None
            and median_efficiency is not None
            and m.ai_efficiency_score >= median_efficiency
        )
        high_bug = (
            m.bug_rate is not None
            and median_bug_rate is not None
            and m.bug_rate > median_bug_rate
        )

        if high_eff and not high_bug:
            m.flag = "green"
        elif high_eff and high_bug:
            m.flag = "red"
        elif not high_eff and not high_bug:
            m.flag = "yellow"
        else:
            m.flag = "gray"

    return metrics
