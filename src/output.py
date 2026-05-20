import csv
from typing import List
from src.models import DeveloperMetrics

FIELDNAMES = [
    "email", "display_name", "period", "spend_usd", "lines_of_code",
    "deliverables_count", "story_points_delivered", "story_points_coverage",
    "cost_per_deliverable", "lines_per_deliverable", "cost_per_line",
    "ai_efficiency_score", "bugs_attributed", "bug_rate", "flag",
]


def write_output_csv(metrics: List[DeveloperMetrics], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for m in metrics:
            writer.writerow({
                "email": m.email,
                "display_name": m.display_name,
                "period": m.period,
                "spend_usd": round(m.spend_usd, 2),
                "lines_of_code": m.lines_of_code,
                "deliverables_count": m.deliverables_count,
                "story_points_delivered": m.story_points_delivered,
                "story_points_coverage": round(m.story_points_coverage, 2),
                "cost_per_deliverable": round(m.cost_per_deliverable, 2) if m.cost_per_deliverable is not None else "",
                "lines_per_deliverable": round(m.lines_per_deliverable, 1) if m.lines_per_deliverable is not None else "",
                "cost_per_line": round(m.cost_per_line, 5) if m.cost_per_line is not None else "",
                "ai_efficiency_score": round(m.ai_efficiency_score, 3) if m.ai_efficiency_score is not None else "N/A",
                "bugs_attributed": m.bugs_attributed,
                "bug_rate": round(m.bug_rate, 2) if m.bug_rate is not None else "",
                "flag": m.flag,
            })
