# AI Developer Dashboard — Phase 1: CSV Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI (`merge.py`) that merges three CSV exports (Claude Console, JIRA deliverables, JIRA bugs) into a per-developer metrics report written to CSV and optionally appended to Google Sheets.

**Architecture:** Five focused modules handle loading, metrics, guardrail logic, and output. A developer name→email mapping CSV bridges the gap between JIRA display names and Claude Console emails. The Google Sheets writer is an optional final step; CSV output is always produced.

**Tech Stack:** Python 3.10+, pandas 2.2, pytest 8.2, gspread 6.1, google-auth 2.29, python-dotenv 1.0

---

## Scope Note

This plan covers **Phase 1 only** (CSV pipeline). Phase 2 (Anthropic Usage API + JIRA REST API + PostgreSQL + Metabase) is a separate plan written after Phase 1 validates which metrics the team actually uses.

---

## File Map

| File | Responsibility |
|------|----------------|
| `merge.py` | CLI entry point — orchestrates the full pipeline |
| `src/__init__.py` | Empty marker |
| `src/models.py` | Dataclasses: `Deliverable`, `Bug`, `DeveloperMetrics` |
| `src/loaders/__init__.py` | Empty marker |
| `src/loaders/claude_loader.py` | Parses Claude Console CSV → `{email: {spend_usd, lines_of_code}}` |
| `src/loaders/jira_loader.py` | Parses developer map CSV, JIRA deliverables CSV, JIRA bugs CSV |
| `src/metrics.py` | Computes per-developer derived metrics |
| `src/guardrail.py` | Bug attribution (30-day window, same Epic/Sprint) + flag state logic |
| `src/output.py` | Writes `DeveloperMetrics` list to output CSV |
| `src/sheets.py` | Appends `DeveloperMetrics` to Google Sheets `raw_data` tab |
| `tests/__init__.py` | Empty marker |
| `tests/fixtures/claude_export.csv` | Test fixture |
| `tests/fixtures/jira_deliverables.csv` | Test fixture |
| `tests/fixtures/jira_bugs.csv` | Test fixture |
| `tests/fixtures/developers.csv` | Test fixture |
| `tests/test_claude_loader.py` | Unit tests |
| `tests/test_jira_loader.py` | Unit tests |
| `tests/test_metrics.py` | Unit tests |
| `tests/test_guardrail.py` | Unit tests |
| `tests/test_integration.py` | End-to-end pipeline test |
| `requirements.txt` | Python dependencies |
| `.env.example` | Env var template |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py`, `src/loaders/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Verify Python version**

Run: `python --version`
Expected: `Python 3.10.x` or higher. If lower, install Python 3.10+ before continuing.

- [ ] **Step 2: Create directory structure**

Run:
```powershell
mkdir src, src\loaders, tests, tests\fixtures
New-Item src\__init__.py, src\loaders\__init__.py, tests\__init__.py -ItemType File
```

- [ ] **Step 3: Create requirements.txt**

```
pandas==2.2.2
gspread==6.1.2
google-auth==2.29.0
python-dotenv==1.0.1
pytest==8.2.0
```

- [ ] **Step 4: Create .env.example**

```
# Path to Google service account credentials JSON (only needed for Sheets upload)
GOOGLE_CREDENTIALS_PATH=credentials.json

# Google Sheets ID from the URL: docs.google.com/spreadsheets/d/<SHEET_ID>/
SHEET_ID=
```

- [ ] **Step 5: Install dependencies**

Run:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Expected: No errors. `pip show pandas` should show version 2.2.x.

- [ ] **Step 6: Init git and commit**

Run:
```powershell
git init
git add requirements.txt .env.example src\__init__.py src\loaders\__init__.py tests\__init__.py
git commit -m "chore: project setup"
```

---

## Task 2: Data Models

**Files:**
- Create: `src/models.py`

- [ ] **Step 1: Write the test first**

Create `tests/test_models.py`:
```python
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
```

- [ ] **Step 2: Run test — confirm it fails**

Run: `pytest tests/test_models.py -v`
Expected: `ImportError: cannot import name 'Deliverable' from 'src.models'`

- [ ] **Step 3: Implement models**

Create `src/models.py`:
```python
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
```

- [ ] **Step 4: Run test — confirm it passes**

Run: `pytest tests/test_models.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\models.py tests\test_models.py
git commit -m "feat: add data models"
```

---

## Task 3: Test Fixtures

**Files:**
- Create: `tests/fixtures/developers.csv`
- Create: `tests/fixtures/claude_export.csv`
- Create: `tests/fixtures/jira_deliverables.csv`
- Create: `tests/fixtures/jira_bugs.csv`

These fixtures are shared by all unit and integration tests.

- [ ] **Step 1: Create developers.csv**

`tests/fixtures/developers.csv`:
```
display_name,email
Navneet Shukla,navneet.shukla@cashflo.io
Shiva Kumar Swami,shivakumar.swami@cashflo.io
Chetan Nikam,chetan.nikam@cashflo.io
```

- [ ] **Step 2: Create claude_export.csv**

`tests/fixtures/claude_export.csv`:
```
Members,Spend this month,Lines this month
navneet.shukla@cashflo.io,$335.06,"42,068"
shivakumar.swami@cashflo.io,$181.46,"86,203"
chetan.nikam@cashflo.io,$608.37,"33,019"
claude_key [API KEY],$380.08,"19,305"
aditya-sales-key [API KEY],$122.45,"16,134"
```

- [ ] **Step 3: Create jira_deliverables.csv**

`tests/fixtures/jira_deliverables.csv`:
```
Issue key,Summary,Issue Type,Status,Assignee,Story Points,Resolved,Sprint,Epic Link
CASH-101,Feature A,Story,Done,Navneet Shukla,5,2026-05-15,Sprint 12,CASH-EP1
CASH-102,Feature B,Task,Done,Navneet Shukla,,2026-05-18,Sprint 12,CASH-EP1
CASH-103,Feature C,Story,Done,Shiva Kumar Swami,8,2026-05-10,Sprint 12,CASH-EP2
CASH-104,Feature D,Story,Done,Shiva Kumar Swami,3,2026-05-12,Sprint 12,CASH-EP2
CASH-105,Feature E,Story,Done,Chetan Nikam,13,2026-05-14,Sprint 12,CASH-EP3
```

- [ ] **Step 4: Create jira_bugs.csv**

`tests/fixtures/jira_bugs.csv`:
```
Issue key,Summary,Issue Type,Status,Assignee,Created,Sprint,Epic Link
BUG-201,Bug in Feature A,Bug,Open,Navneet Shukla,2026-05-20,Sprint 12,CASH-EP1
BUG-202,Bug in Feature C,Bug,Open,Shiva Kumar Swami,2026-06-01,Sprint 12,CASH-EP2
BUG-203,Unrelated bug,Bug,Open,Chetan Nikam,2026-08-01,Sprint 13,CASH-EP9
```

Note: BUG-201 is within 30 days of CASH-101 (same epic+sprint) → attributed to Navneet.
BUG-202 is 22 days after CASH-103 (same epic+sprint) → attributed to Shiva.
BUG-203 is 78 days after CASH-105 and different sprint/epic → NOT attributed to Chetan.

- [ ] **Step 5: Commit**

```powershell
git add tests\fixtures\
git commit -m "test: add CSV fixtures"
```

---

## Task 4: Claude Console CSV Loader

**Files:**
- Create: `src/loaders/claude_loader.py`
- Create: `tests/test_claude_loader.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_claude_loader.py`:
```python
import pytest
from src.loaders.claude_loader import load_claude_csv

FIXTURE = "tests/fixtures/claude_export.csv"


def test_loads_three_developers():
    result = load_claude_csv(FIXTURE)
    assert len(result) == 3


def test_excludes_api_keys():
    result = load_claude_csv(FIXTURE)
    assert "claude_key [api key]" not in result
    assert "aditya-sales-key [api key]" not in result


def test_parses_spend_correctly():
    result = load_claude_csv(FIXTURE)
    assert result["navneet.shukla@cashflo.io"]["spend_usd"] == pytest.approx(335.06)
    assert result["chetan.nikam@cashflo.io"]["spend_usd"] == pytest.approx(608.37)


def test_parses_lines_with_comma_separator():
    result = load_claude_csv(FIXTURE)
    assert result["navneet.shukla@cashflo.io"]["lines_of_code"] == 42068
    assert result["shivakumar.swami@cashflo.io"]["lines_of_code"] == 86203


def test_emails_are_lowercased():
    result = load_claude_csv(FIXTURE)
    for email in result:
        assert email == email.lower()
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_claude_loader.py -v`
Expected: `ImportError: cannot import name 'load_claude_csv'`

- [ ] **Step 3: Implement Claude loader**

Create `src/loaders/claude_loader.py`:
```python
import pandas as pd
from typing import Dict


def load_claude_csv(path: str) -> Dict[str, dict]:
    """Load Claude Console export CSV.
    Returns {email_lower: {spend_usd: float, lines_of_code: int}}.
    Excludes API key rows (rows where email has no @).
    """
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Members": "email",
        "Spend this month": "spend_raw",
        "Lines this month": "lines_raw",
    })
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df[df["email"].str.contains("@", na=False)]
    df["spend_usd"] = (
        df["spend_raw"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )
    df["lines_of_code"] = (
        df["lines_raw"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(int)
    )
    return {
        row["email"]: {
            "spend_usd": row["spend_usd"],
            "lines_of_code": row["lines_of_code"],
        }
        for _, row in df.iterrows()
    }
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_claude_loader.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\loaders\claude_loader.py tests\test_claude_loader.py
git commit -m "feat: add Claude Console CSV loader"
```

---

## Task 5: JIRA Loaders

**Files:**
- Create: `src/loaders/jira_loader.py`
- Create: `tests/test_jira_loader.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_jira_loader.py`:
```python
from datetime import date
from src.loaders.jira_loader import load_developer_map, load_deliverables_csv, load_bugs_csv

DEV_MAP_FIXTURE = "tests/fixtures/developers.csv"
DELIVERABLES_FIXTURE = "tests/fixtures/jira_deliverables.csv"
BUGS_FIXTURE = "tests/fixtures/jira_bugs.csv"


def test_developer_map_keys_are_lowercase():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    for key in dm:
        assert key == key.lower()


def test_developer_map_values_are_emails():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    assert dm["navneet shukla"] == "navneet.shukla@cashflo.io"
    assert dm["shiva kumar swami"] == "shivakumar.swami@cashflo.io"


def test_loads_five_deliverables():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    assert len(records) == 5


def test_deliverable_email_resolved_from_display_name():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    navneet_records = [r for r in records if r.email == "navneet.shukla@cashflo.io"]
    assert len(navneet_records) == 2


def test_deliverable_missing_story_points_is_none():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    cash_102 = next(r for r in records if r.issue_key == "CASH-102")
    assert cash_102.story_points is None


def test_deliverable_resolved_date_parsed():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    records = load_deliverables_csv(DELIVERABLES_FIXTURE, dm)
    cash_101 = next(r for r in records if r.issue_key == "CASH-101")
    assert cash_101.resolved_date == date(2026, 5, 15)


def test_loads_three_bugs():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    bugs = load_bugs_csv(BUGS_FIXTURE, dm)
    assert len(bugs) == 3


def test_bug_email_resolved_from_display_name():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    bugs = load_bugs_csv(BUGS_FIXTURE, dm)
    navneet_bugs = [b for b in bugs if b.email == "navneet.shukla@cashflo.io"]
    assert len(navneet_bugs) == 1


def test_bug_created_date_parsed():
    dm = load_developer_map(DEV_MAP_FIXTURE)
    bugs = load_bugs_csv(BUGS_FIXTURE, dm)
    bug_201 = next(b for b in bugs if b.issue_key == "BUG-201")
    assert bug_201.created_date == date(2026, 5, 20)
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_jira_loader.py -v`
Expected: `ImportError: cannot import name 'load_developer_map'`

- [ ] **Step 3: Implement JIRA loaders**

Create `src/loaders/jira_loader.py`:
```python
import pandas as pd
from typing import Dict, List
from src.models import Deliverable, Bug


def load_developer_map(path: str) -> Dict[str, str]:
    """Load developers.csv. Returns {display_name_lower: email_lower}."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return {
        row["display_name"].strip().lower(): row["email"].strip().lower()
        for _, row in df.iterrows()
    }


def _resolve_email(assignee: str, developer_map: Dict[str, str]) -> str:
    """Map JIRA display name to email. Falls back to assignee lowercased."""
    return developer_map.get(assignee.strip().lower(), assignee.strip().lower())


def load_deliverables_csv(path: str, developer_map: Dict[str, str]) -> List[Deliverable]:
    """Load JIRA closed Stories/Tasks CSV. Returns list of Deliverable."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    sp_col = next(
        (c for c in df.columns if "story point" in c.lower()),
        None,
    )

    records = []
    for _, row in df.iterrows():
        resolved_raw = row.get("Resolved", "")
        if pd.isna(resolved_raw) or str(resolved_raw).strip() == "":
            continue

        resolved_date = pd.to_datetime(resolved_raw).date()

        sp = None
        if sp_col and pd.notna(row[sp_col]) and str(row[sp_col]).strip() != "":
            try:
                sp = int(float(row[sp_col]))
            except (ValueError, TypeError):
                sp = None

        records.append(Deliverable(
            email=_resolve_email(str(row.get("Assignee", "")), developer_map),
            issue_key=str(row["Issue key"]).strip(),
            issue_type=str(row.get("Issue Type", "")).strip(),
            story_points=sp,
            resolved_date=resolved_date,
            sprint=str(row.get("Sprint", "")).strip(),
            epic_key=str(row.get("Epic Link", "")).strip(),
        ))
    return records


def load_bugs_csv(path: str, developer_map: Dict[str, str]) -> List[Bug]:
    """Load JIRA Bugs CSV. Returns list of Bug."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    records = []
    for _, row in df.iterrows():
        created_raw = row.get("Created", "")
        if pd.isna(created_raw) or str(created_raw).strip() == "":
            continue

        created_date = pd.to_datetime(created_raw).date()

        records.append(Bug(
            email=_resolve_email(str(row.get("Assignee", "")), developer_map),
            issue_key=str(row["Issue key"]).strip(),
            created_date=created_date,
            sprint=str(row.get("Sprint", "")).strip(),
            epic_key=str(row.get("Epic Link", "")).strip(),
        ))
    return records
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_jira_loader.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\loaders\jira_loader.py tests\test_jira_loader.py
git commit -m "feat: add JIRA CSV loaders"
```

---

## Task 6: Metrics Computation

**Files:**
- Create: `src/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_metrics.py`:
```python
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
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_metrics.py -v`
Expected: `ImportError: cannot import name 'compute_story_points_coverage'`

- [ ] **Step 3: Implement metrics**

Create `src/metrics.py`:
```python
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
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_metrics.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\metrics.py tests\test_metrics.py
git commit -m "feat: add metrics computation"
```

---

## Task 7: Bug Attribution and Flag States

**Files:**
- Create: `src/guardrail.py`
- Create: `tests/test_guardrail.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_guardrail.py`:
```python
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


def test_bug_attributed_within_30_days_same_sprint():
    metrics = [_make_metric("dev@cashflo.io")]
    deliverables_by_email = {
        "dev@cashflo.io": [_make_deliverable("dev@cashflo.io", "2026-05-01", "Sprint 12", "EP-1")]
    }
    bugs = [_make_bug("other@cashflo.io", "2026-05-20", "Sprint 12", "EP-DIFFERENT")]
    result = attribute_bugs(metrics, deliverables_by_email, bugs)
    assert result[0].bugs_attributed == 1


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
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_guardrail.py -v`
Expected: `ImportError: cannot import name 'attribute_bugs'`

- [ ] **Step 3: Implement guardrail**

Create `src/guardrail.py`:
```python
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
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_guardrail.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\guardrail.py tests\test_guardrail.py
git commit -m "feat: add bug attribution and flag states"
```

---

## Task 8: CSV Output

**Files:**
- Create: `src/output.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_output.py`:
```python
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
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_output.py -v`
Expected: `ImportError: cannot import name 'write_output_csv'`

- [ ] **Step 3: Implement CSV output**

Create `src/output.py`:
```python
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
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_output.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\output.py tests\test_output.py
git commit -m "feat: add CSV output writer"
```

---

## Task 9: CLI Entry Point + Integration Test

**Files:**
- Create: `merge.py`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write failing integration test**

Create `tests/test_integration.py`:
```python
import csv
import subprocess
import sys
import os

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
    # Navneet: CASH-101 has 5 pts, CASH-102 has None → 50% coverage < 80%
    assert rows["navneet.shukla@cashflo.io"]["ai_efficiency_score"] == "N/A"


def test_shiva_efficiency_score_computed():
    subprocess.run(CMD, capture_output=True)
    with open(OUTPUT_PATH, newline="") as f:
        rows = {r["email"]: r for r in csv.DictReader(f)}
    # Shiva: CASH-103 (8pts) + CASH-104 (3pts) = 11pts, both have points → 100% coverage
    # efficiency = 11 / 181.46 ≈ 0.0606
    score = float(rows["shivakumar.swami@cashflo.io"]["ai_efficiency_score"])
    assert 0.06 < score < 0.07
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_integration.py -v`
Expected: `FileNotFoundError` or `ModuleNotFoundError` since `merge.py` doesn't exist yet.

- [ ] **Step 3: Implement CLI entry point**

Create `merge.py`:
```python
import argparse
from collections import defaultdict
from datetime import datetime

from src.loaders.claude_loader import load_claude_csv
from src.loaders.jira_loader import load_developer_map, load_deliverables_csv, load_bugs_csv
from src.metrics import compute_developer_metrics
from src.guardrail import attribute_bugs, apply_flags
from src.output import write_output_csv


def main():
    parser = argparse.ArgumentParser(
        description="Merge Claude Console + JIRA exports into developer metrics CSV"
    )
    parser.add_argument("claude_csv", help="Claude Console export CSV")
    parser.add_argument("jira_deliverables_csv", help="JIRA closed Stories/Tasks CSV")
    parser.add_argument("jira_bugs_csv", help="JIRA Bug tickets CSV")
    parser.add_argument("developers_csv", help="Developer display_name→email mapping CSV")
    parser.add_argument(
        "--period",
        default=datetime.now().strftime("%Y-%m"),
        help="Reporting period YYYY-MM (default: current month)",
    )
    parser.add_argument("--output", default="output.csv", help="Output CSV path")
    parser.add_argument("--sheet-id", default=None, help="Google Sheets ID (optional)")
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Google service account JSON path (only needed with --sheet-id)",
    )
    args = parser.parse_args()

    developer_map = load_developer_map(args.developers_csv)
    claude_data = load_claude_csv(args.claude_csv)
    deliverables = load_deliverables_csv(args.jira_deliverables_csv, developer_map)
    bugs = load_bugs_csv(args.jira_bugs_csv, developer_map)

    deliverables_by_email = defaultdict(list)
    for d in deliverables:
        deliverables_by_email[d.email].append(d)

    # Reverse map: email → display_name (title-case the key from developer_map)
    name_map = {email: name.title() for name, email in developer_map.items()}

    all_emails = sorted(set(claude_data.keys()) | set(deliverables_by_email.keys()))

    metrics = []
    for email in all_emails:
        m = compute_developer_metrics(
            email=email,
            display_name=name_map.get(email, email),
            period=args.period,
            claude_data=claude_data.get(email, {"spend_usd": 0.0, "lines_of_code": 0}),
            deliverables=deliverables_by_email.get(email, []),
        )
        metrics.append(m)

    metrics = attribute_bugs(metrics, dict(deliverables_by_email), bugs)
    metrics = apply_flags(metrics)

    write_output_csv(metrics, args.output)
    print(f"Output written to {args.output} ({len(metrics)} developers)")

    if args.sheet_id:
        from src.sheets import get_sheets_client, append_to_sheet
        client = get_sheets_client(args.credentials)
        append_to_sheet(client, args.sheet_id, "raw_data", metrics)
        print(f"Appended to Google Sheets: {args.sheet_id}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_integration.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS. Note the exact count.

- [ ] **Step 6: Commit**

```powershell
git add merge.py tests\test_integration.py
git commit -m "feat: add CLI entry point and integration test"
```

---

## Task 10: Google Sheets Writer (Optional)

**Files:**
- Create: `src/sheets.py`
- Create: `tests/test_sheets.py`

Skip this task if you want to use CSV-only output for the first monthly run. Come back to it when you're ready to connect Google Sheets.

- [ ] **Step 1: Write failing test with mocked gspread**

Create `tests/test_sheets.py`:
```python
from unittest.mock import MagicMock, patch
from src.models import DeveloperMetrics
from src.sheets import append_to_sheet

METRICS = [
    DeveloperMetrics(
        email="dev@cashflo.io", display_name="Dev", period="2026-05",
        spend_usd=100.0, lines_of_code=5000, deliverables_count=2,
        story_points_delivered=8, story_points_coverage=1.0,
        cost_per_deliverable=50.0, lines_per_deliverable=2500.0,
        cost_per_line=0.02, ai_efficiency_score=0.08,
        bugs_attributed=0, bug_rate=0.0, flag="green",
    )
]


def test_append_to_sheet_calls_append_rows():
    mock_client = MagicMock()
    mock_ws = MagicMock()
    mock_client.open_by_key.return_value.worksheet.return_value = mock_ws

    append_to_sheet(mock_client, "SHEET_ID_123", "raw_data", METRICS)

    mock_client.open_by_key.assert_called_once_with("SHEET_ID_123")
    mock_client.open_by_key.return_value.worksheet.assert_called_once_with("raw_data")
    mock_ws.append_rows.assert_called_once()
    rows_written = mock_ws.append_rows.call_args[0][0]
    assert len(rows_written) == 1
    assert rows_written[0][0] == "dev@cashflo.io"
    assert rows_written[0][11] == 0.08  # ai_efficiency_score


def test_none_efficiency_score_written_as_na_string():
    mock_client = MagicMock()
    mock_ws = MagicMock()
    mock_client.open_by_key.return_value.worksheet.return_value = mock_ws

    m = METRICS[0]
    m.ai_efficiency_score = None
    append_to_sheet(mock_client, "SHEET_ID_123", "raw_data", [m])

    rows_written = mock_ws.append_rows.call_args[0][0]
    assert rows_written[0][11] == "N/A"
```

- [ ] **Step 2: Run — confirm failure**

Run: `pytest tests/test_sheets.py -v`
Expected: `ImportError: cannot import name 'append_to_sheet'`

- [ ] **Step 3: Implement Sheets writer**

Create `src/sheets.py`:
```python
import gspread
from google.oauth2.service_account import Credentials
from typing import List
from src.models import DeveloperMetrics

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_client(credentials_path: str) -> gspread.Client:
    creds = Credentials.from_service_account_file(credentials_path, scopes=_SCOPES)
    return gspread.authorize(creds)


def append_to_sheet(
    client: gspread.Client,
    sheet_id: str,
    worksheet_name: str,
    metrics: List[DeveloperMetrics],
) -> None:
    ws = client.open_by_key(sheet_id).worksheet(worksheet_name)
    rows = []
    for m in metrics:
        rows.append([
            m.email,
            m.display_name,
            m.period,
            round(m.spend_usd, 2),
            m.lines_of_code,
            m.deliverables_count,
            m.story_points_delivered,
            round(m.story_points_coverage, 2),
            round(m.cost_per_deliverable, 2) if m.cost_per_deliverable is not None else "",
            round(m.lines_per_deliverable, 1) if m.lines_per_deliverable is not None else "",
            round(m.cost_per_line, 5) if m.cost_per_line is not None else "",
            round(m.ai_efficiency_score, 3) if m.ai_efficiency_score is not None else "N/A",
            m.bugs_attributed,
            round(m.bug_rate, 2) if m.bug_rate is not None else "",
            m.flag,
        ])
    ws.append_rows(rows, value_input_option="USER_ENTERED")
```

- [ ] **Step 4: Run — confirm passing**

Run: `pytest tests/test_sheets.py -v`
Expected: Both tests PASS.

- [ ] **Step 5: Set up Google Sheets credentials (one-time)**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **Google Sheets API**
3. Create a **Service Account** → Download JSON credentials → save as `credentials.json` in project root
4. Share your Google Sheet with the service account email (editor access)
5. Copy the Sheet ID from the URL: `docs.google.com/spreadsheets/d/<SHEET_ID>/`

- [ ] **Step 6: Smoke test with real Sheets (manual)**

Run:
```powershell
python merge.py `
  tests/fixtures/claude_export.csv `
  tests/fixtures/jira_deliverables.csv `
  tests/fixtures/jira_bugs.csv `
  tests/fixtures/developers.csv `
  --period 2026-05 `
  --output output.csv `
  --sheet-id YOUR_SHEET_ID
```
Expected: `Appended to Google Sheets: YOUR_SHEET_ID` and 3 rows appear in the `raw_data` tab.

- [ ] **Step 7: Commit**

```powershell
git add src\sheets.py tests\test_sheets.py
git commit -m "feat: add Google Sheets writer"
```

---

## Usage Reference

### Monthly run (CSV only)
```powershell
python merge.py `
  exports\claude_export.csv `
  exports\jira_deliverables.csv `
  exports\jira_bugs.csv `
  developers.csv `
  --period 2026-05 `
  --output exports\2026-05-metrics.csv
```

### Monthly run (CSV + push to Sheets)
```powershell
python merge.py `
  exports\claude_export.csv `
  exports\jira_deliverables.csv `
  exports\jira_bugs.csv `
  developers.csv `
  --period 2026-05 `
  --output exports\2026-05-metrics.csv `
  --sheet-id YOUR_SHEET_ID
```

### JIRA filter to use for deliverables export
```
issuetype in (Story, Task) AND status in (Done, Deployed) AND resolved >= startOfMonth() AND resolved <= endOfMonth()
```
Export fields to include: `Issue key, Summary, Issue Type, Status, Assignee, Story Points, Resolved, Sprint, Epic Link`

### JIRA filter for bugs export
```
issuetype = Bug AND created >= startOfMonth() AND created <= endOfMonth()
```
Export fields: `Issue key, Summary, Issue Type, Status, Assignee, Created, Sprint, Epic Link`

### developers.csv format (maintain this manually)
```
display_name,email
Navneet Shukla,navneet.shukla@cashflo.io
Shiva Kumar Swami,shivakumar.swami@cashflo.io
```
Add a row for each team member. The display name must match exactly what JIRA shows in the Assignee column.
