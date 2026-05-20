from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Deliverable:
    email: str
    issue_key: str
    issue_type: str
    story_points: Optional[int]
    resolved_date: date
    sprint: str
    epic_key: str


@dataclass
class Bug:
    email: str
    issue_key: str
    created_date: date
    sprint: str
    epic_key: str


@dataclass
class DeveloperMetrics:
    email: str
    display_name: str
    period: str
    spend_usd: float
    lines_of_code: int
    deliverables_count: int
    story_points_delivered: int
    story_points_coverage: float
    cost_per_deliverable: Optional[float]
    lines_per_deliverable: Optional[float]
    cost_per_line: Optional[float]
    ai_efficiency_score: Optional[float]
    bugs_attributed: int
    bug_rate: Optional[float]
    flag: str
