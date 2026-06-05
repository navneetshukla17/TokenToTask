# Developer Dashboard

Python CLI that merges Claude Console + JIRA exports into a developer metrics CSV.

## Commands

```sh
# run the pipeline
python merge.py claude_export.csv jira_deliverables.csv jira_bugs.csv developers.csv --period 2026-05

# run all tests
python -m pytest tests/ -v

# run focused tests
python -m pytest tests/test_metrics.py -v
python -m pytest tests/test_integration.py -v
```

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

Env vars (optional, only for Google Sheets upload): `GOOGLE_CREDENTIALS_PATH`, `SHEET_ID` — see `.env.example`.

## Architecture

- **`merge.py`** — CLI entrypoint, orchestrates loading → compute → output
- **`src/models.py`** — dataclasses: `Deliverable`, `Bug`, `DeveloperMetrics`
- **`src/loaders/`** — `claude_loader.py` (pandas CSV), `jira_loader.py` (pandas CSV + developer name→email mapping)
- **`src/metrics.py`** — AI efficiency, cost-per-deliverable, story points coverage
- **`src/guardrail.py`** — bug attribution (30-day window, same epic+sprint), flag states (green/red/yellow/gray)
- **`src/output.py`** — CSV writer with rounding and null handling
- **`src/sheets.py`** — optional Google Sheets append via `gspread`

## Key behaviors

- Claude loader strips `$` and commas from spend/lines, excludes API key rows (no `@` in email)
- JIRA loader maps display names to emails via `developers.csv`; falls back to lowercased assignee
- `ai_efficiency_score` = story_points / spend_usd; `N/A` if story_points_coverage < 80%
- Bug attribution requires same epic + same sprint, bug created ≤30 days after story resolved
- All emails lowercased throughout

## Testing

- **Fixtures**: `tests/fixtures/` — `claude_export.csv`, `jira_deliverables.csv`, `jira_bugs.csv`, `developers.csv`
- Integration test (`test_integration.py`) runs `merge.py` as subprocess against fixtures
- No CI config found — run tests manually before committing
- `.venv/` directory exists but is Windows-format; recreate with `python3 -m venv` on macOS
