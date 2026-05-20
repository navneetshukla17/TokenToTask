# AI Developer Dashboard — Design Spec

**Date:** 2026-05-20  
**Status:** Approved  
**Team:** Cashflo Engineering  

---

## Problem

The engineering team has shifted from manual coding to using Claude Code as a daily driver. There is no unified view of how much AI each developer is consuming versus how many deliverables they are shipping. Managers need per-developer visibility across AI spend, output volume, and quality — without relying on gut feel.

---

## Goal

A dashboard that shows, per developer per week/month/year:
- How much AI they used (spend, tokens, lines of code)
- How many deliverables they completed (JIRA stories/tasks)
- How efficient that usage was (derived ratios)
- Whether speed is coming at the cost of quality (guardrail flag)

Audience: managers see all developers; developers see the full team leaderboard.

---

## Data Sources

### Claude Console (platform.claude.com/claude-code)
- Central Anthropic team account with 18 members, all `@cashflo.io` emails
- **Phase 1:** Manual CSV export via the Export button on the team page
- **Phase 2:** Anthropic Usage API (daily automated pull)
- Fields available: `email`, `spend_usd`, `lines_of_code`, `tokens_input`, `tokens_output`
- **Exclusions:** API key entries (`claude_key`, `aditya-sales-key`) are not human developers and are excluded

### JIRA
- Deliverables = issues of specific types (Story, Task, Bug) with status Done/Deployed
- **Phase 1:** Two manual CSV exports via saved JIRA filters
- **Phase 2:** JIRA REST API (daily automated pull)
- Export 1 — Deliverables filter: `issuetype in (Story, Task) AND status in (Done, Deployed) AND resolved >= startOfMonth()`
  - Fields: `Assignee (email)`, `Issue Key`, `Issue Type`, `Story Points`, `Resolved Date`, `Sprint`, `Epic Link`
- Export 2 — Bugs filter: `issuetype = Bug AND created >= startOfMonth()`
  - Fields: `Assignee (email)`, `Issue Key`, `Created Date`, `Sprint`, `Epic Link`

### Join Key
Claude Console email = JIRA assignee email (both `@cashflo.io`). Direct match, no fuzzy mapping needed.

---

## Metrics

### Raw Inputs (per developer, per period)
| Metric | Source |
|--------|--------|
| `spend_usd` | Claude Console |
| `lines_of_code` | Claude Console |
| `tokens_consumed` | Anthropic API (Phase 2 only) — not available in Phase 1 |
| `deliverables_count` | JIRA — count of closed Stories/Tasks |
| `story_points_delivered` | JIRA — sum of Story Points on closed Stories/Tasks |
| `story_points_coverage` | JIRA — % of closed tickets that have Story Points set |

### Derived Efficiency Metrics
| Metric | Formula | Direction |
|--------|---------|-----------|
| `deliverables_per_month` | count of closed Stories/Tasks | higher = better |
| `cost_per_deliverable` | `spend_usd ÷ deliverables_count` | lower = better |
| `lines_per_deliverable` | `lines_of_code ÷ deliverables_count` | context-dependent |
| `cost_per_line` | `spend_usd ÷ lines_of_code` | lower = better |
| `ai_efficiency_score` | Phase 1: `story_points_delivered ÷ spend_usd` (SP per $). Phase 2: `story_points_delivered ÷ tokens_consumed` | higher = better |

**AI Efficiency Score notes:**
- Phase 1 uses `spend_usd` as the denominator (story points per dollar spent) since the Claude Console export does not expose raw token counts. Using a per-model token price approximation was rejected — mixed Opus/Sonnet/Haiku usage makes it unreliable. Phase 2 switches to true `tokens_consumed` from the Anthropic API.
- If `story_points_coverage < 80%` for a developer, their `ai_efficiency_score` is shown as `N/A ⚠️` with a note: "Story points missing on X% of tickets — score unreliable." This surfaces JIRA hygiene issues without silently producing misleading numbers.

### Guardrail Metric: Bug Rate
- **Definition:** A bug is attributed to a developer if a Bug ticket was created in the **same Epic or Sprint** within **30 days** of one of their Stories closing.
- **Formula:** `bug_rate = bugs_attributed ÷ stories_closed` (per developer, per period)
- **Threshold:** Flag if `bug_rate > team average bug_rate`

### Developer Flag States
| Flag | Condition | Meaning |
|------|-----------|---------|
| 🟢 On Track | High efficiency + Low bug rate | Target state |
| 🔴 Quality Risk | High efficiency + High bug rate | Shipping fast but carelessly — review quality |
| 🟡 Coaching Opportunity | Low efficiency + Low bug rate | Underutilising AI — needs guidance |
| ⚪ Needs Attention | Low efficiency + High bug rate | Both dimensions off |

"High" = above team median. "Low" = below team median.

---

## Phase 1: CSV + Google Sheets

### Overview
Manual monthly process. Zero infrastructure. Validates which metrics the team actually cares about before building automation.

### Process (monthly, ~20 minutes)
1. Export Claude Console CSV from `platform.claude.com/claude-code` (Export button)
2. Export JIRA deliverables CSV using saved filter
3. Export JIRA bugs CSV using saved filter
4. Run: `python merge.py claude_export.csv jira_deliverables.csv jira_bugs.csv`
5. Script writes output to Google Sheets via Sheets API (or manual paste on first run)

### Script: `merge.py`
**Inputs:** Three CSVs  
**Logic:**
1. Load and normalise all emails to lowercase
2. Exclude API key rows from Claude Console (rows where email doesn't contain `@`)
3. Join Claude data + JIRA deliverables on `email`
4. Compute story points coverage per developer
5. Match bugs to developers via Epic/Sprint within 30-day window
6. Compute all derived metrics
7. Apply flag states based on team medians
8. Write to output CSV / Google Sheets

**Output columns:**
```
email, display_name, period, spend_usd, lines_of_code, tokens_consumed,
deliverables_count, story_points_delivered, story_points_coverage,
cost_per_deliverable, lines_per_deliverable, cost_per_line,
ai_efficiency_score, bugs_attributed, bug_rate, flag
```

### Google Sheets Layout
- **`raw_data` tab** — script writes here (one row per developer per month, append-only)
- **`dashboard` tab** — charts auto-update from `raw_data`:
  - Leaderboard table: all developers, sortable by any column
  - Bar chart: deliverables this month per developer
  - Bar chart: spend this month per developer
  - Scatter chart: spend ($) vs story points delivered (efficiency view)
  - Flag summary: count of 🔴/🟡/⚪ flags this month
  - Month selector dropdown (filters all charts)
- **`data_quality` tab** — lists developers with `story_points_coverage < 80%`

Shared link readable by the whole team.

---

## Phase 2: Automated Pipeline + Metabase

Triggered once Phase 1 has validated the metrics (estimated: after 2–3 months of manual runs).

### Architecture
```
Anthropic Usage API ──┐
                      ├──► Python pipeline (daily cron) ──► PostgreSQL ──► Metabase
JIRA REST API ────────┘
```

### PostgreSQL Schema
```sql
-- One row per developer per day
claude_usage (
  email          TEXT,
  date           DATE,
  spend_usd      NUMERIC,
  lines_of_code  INTEGER,
  tokens_input   BIGINT,
  tokens_output  BIGINT
)

-- One row per resolved issue
jira_issues (
  email          TEXT,
  issue_key      TEXT PRIMARY KEY,
  issue_type     TEXT,  -- Story, Task, Bug
  story_points   INTEGER,
  resolved_date  DATE,
  sprint_name    TEXT,
  epic_key       TEXT
)

-- Static lookup, manually maintained
developers (
  email          TEXT PRIMARY KEY,
  display_name   TEXT
)
```

### Pipeline Jobs
- **Job A (daily 2am):** Anthropic Usage API → upsert into `claude_usage`
- **Job B (daily 2am):** JIRA REST API paginated query → upsert into `jira_issues`
- **Job C (daily 3am):** Materialise derived metrics into a `developer_metrics` summary table (pre-computed for Metabase query performance)

### Metabase Dashboard
Self-hosted (free), connected to PostgreSQL. Provides:
- Time period filter: week / month / year (no code changes needed to add new views)
- Team leaderboard with all metrics and flag states
- Per-developer drill-down: trend lines over time for each metric
- Data quality panel: story points coverage per developer
- Export to CSV for any view

### Hosting
Single VM: AWS EC2 `t3.small` (~$15/month) or equivalent internal server running:
- Python pipeline service
- PostgreSQL
- Metabase (Docker)

---

## Out of Scope
- Authentication / access control (dashboard is open to the whole team by design)
- Real-time streaming (daily refresh is sufficient)
- Git commit analysis (lines of code from Claude Console is the source of truth)
- Integration with tools other than JIRA and Claude Console

---

## Open Questions (for Phase 2 setup)
1. Confirm JIRA instance URL and whether REST API access requires a service account
2. Confirm Anthropic Usage API access level for the org admin account
3. Decide hosting: AWS vs internal server
