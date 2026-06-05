# TokenToTask

> **Turn Claude Code usage into delivery intelligence — per developer, per sprint.**  
> TokenToTask joins Claude Console token data with Jira delivery data to answer the question every engineering manager needs answered: *Is our AI investment actually paying off?*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[🚀 Live Demo](https://dashboard-poc.cashflo.io) &nbsp;·&nbsp; [📋 Problem PRD](./PRDs/Problem-PRD.pdf) &nbsp;·&nbsp; [📋 Web App PRD](./PRDs/WebApp-PRD.pdf) &nbsp;·&nbsp; [📋 Final PRD](./PRDs/Final-PRD.pdf) &nbsp;·&nbsp; [🐛 Report a Bug](https://github.com/navneetshukla17/TokenToTask/issues)

> ⚠️ **Honest disclaimer:** This is a Proof of Concept. It works. It produces real, useful metrics. But it is held together by manual CSV exports from two external systems — Claude Console and Jira — that we do not control. If either changes their export format, this breaks. We know. That's what v3 is for.

---

## The Problem

Cashflo's engineering team shifted to Claude Code as the daily driver for writing code. That shift was a deliberate bet. But after making it, we had no way to answer the questions that mattered:

| Question | Status Before TokenToTask |
|---|---|
| Is the team actually using Claude Code? | ❌ No visibility |
| Is AI usage translating into more deliverables? | ❌ No visibility |
| What is the cost per deliverable, per developer? | ❌ No visibility |
| Which developers are getting ROI, which need coaching? | ❌ No visibility |

The data existed. Claude Console tracked every token spent and every line of code written. Jira tracked every deliverable, story point, and bug. But they lived in separate systems, were never joined, and produced no shared insight.

**The result: management had a gut feeling about AI ROI, not a number.**

---

## 📋 PRD Documentation

We went through three rounds of product thinking to get here. Each document solved a real problem the previous one created:

| # | Document | Purpose |
|---|---|---|
| 1 | [**Problem PRD**](./PRDs/Problem-PRD.pdf) | Defines the business problem — AI adoption with no measurement layer. Scopes what data we have, what we need, and why joining Claude Console + Jira is the right move. |
| 2 | [**Web App PRD**](./PRDs/WebApp-PRD.pdf) | Translates the problem into a product spec. Covers the v1 CLI, its limitations, and the case for a web interface with CSV upload, weekly/monthly views, and per-developer profiles. |
| 3 | [**Final PRD (Unified MVP)**](./PRDs/Final-PRD.pdf) | The definitive spec. Resolves conflicts between the first two (web upload vs. server directory, weekly vs. monthly), introduces the weekly spend scaling fallback, and adds the settings/configuration layer. |

### Why three PRDs?

Because the product changed as we understood the data better. The first document was written before we knew Claude Console only exports monthly totals. The second assumed a simpler ingestion path. By the time we understood the full constraints — weekly approximation, identity mapping, dual ingestion modes — neither document was accurate. The third one is the honest one.

---

## System Architecture

### v1 — CLI ETL Pipeline

<img src="./images/cli_architecture.png" width="800" alt="CLI ETL Pipeline Architecture"/>

The CLI is the core engine. It takes four CSV files, runs metrics computation in-memory, and writes a single `output.csv` — one row per developer. No server, no database, no UI.

### v2 — React + FastAPI Web Application

<img src="./images/webapp_architecture.png" width="800" alt="Web Application Architecture"/>

The web app wraps the CLI pipeline in a proper product. The full stack: React SPA → HTTPS/JSON → FastAPI (Uvicorn) → pandas CSV engine → SQLite + filesystem.

---

## Key Features

### For Managers
- **Team Leaderboard** — all developers ranked by flag, sortable by any metric, with weekly/monthly toggle
- **Flag Filter** — one click to show only red/yellow developers who need attention
- **Team Summary Cards** — total spend, total deliverables, average efficiency score, flag distribution at a glance
- **Team Trends Page** — aggregate charts across all stored periods, AI adoption rate (who has zero token spend)

### For Developers
- **Personal Profile Page** — all your metrics in one place with a plain-language explanation of your flag status
- **Week-over-week Trend Chart** — track your short-term progress
- **Month-over-month Trend Chart** — understand longer-term patterns
- **Bug Attribution Log** — see which bugs were attributed to your work and exactly why

### For Admins
- **Dual Ingestion** — drag-and-drop CSV upload or server directory scan (`./data_drop/`)
- **Upload History Log** — timestamp, status, and error details for every data refresh
- **Settings Editor** — configure Jira base URL and edit developer identity mappings on the fly

---

## Output Metrics Per Developer

| Metric | Description |
|---|---|
| `spend_usd` | Total Claude Code spend this period |
| `lines_of_code` | Lines written via Claude Code |
| `deliverables_count` | Jira Stories + Tasks closed |
| `story_points_delivered` | Sum of story points on closed issues |
| `story_points_coverage` | % of deliverables that had story points set |
| `cost_per_deliverable` | spend ÷ deliverables |
| `lines_per_deliverable` | lines ÷ deliverables |
| `cost_per_line` | spend ÷ lines |
| `ai_efficiency_score` | story points ÷ spend (suppressed if coverage < 80%) |
| `bugs_attributed` | Bugs linked to this developer's work (same epic + sprint, within 30 days) |
| `bug_rate` | bugs ÷ deliverables |
| `flag` | 🟢 green / 🟡 yellow / 🔴 red / ⚫ gray — computed from relative efficiency + bug rate |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18 + Vite | Team leaderboard, developer profiles, trend charts |
| Backend | FastAPI + Uvicorn | REST API, file upload handler, pipeline orchestration |
| Pipeline | Python + pandas | CSV ingestion, metrics computation, bug attribution |
| Database | SQLite | Historical metrics persistence per period |
| Storage | Server filesystem `/uploads/` | Raw CSV file storage |
| Optional | gspread + Google Sheets API | Cloud sync for v1 CLI output |

---

## Getting Started

### v1 — Run the CLI

```bash
# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the pipeline
python merge.py \
  tests/fixtures/claude_export.csv \
  tests/fixtures/jira_deliverables.csv \
  tests/fixtures/jira_bugs.csv \
  tests/fixtures/developers.csv \
  --period 2026-05 \
  --output output.csv
```

### v2 — Run the Web App

```bash
# 1. Build the React frontend
cd frontend
npm install
npm run build
cd ..

# 2. Set up the Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Start the server
.venv/bin/uvicorn main:app --reload

# 4. Open http://127.0.0.1:8000
# Drop the files from tests/fixtures/ to see the dashboard populated
```

---

## ⚠️ Blunt Assessment: What This Is and What It Isn't

This is a POC. It proves the concept. The metrics are real, the logic is tested, and the dashboard works. But before you treat this as production infrastructure, read this section carefully.

### The fragility problem

This entire dashboard depends on two external CSV export formats we do not control:

**Claude Console export** — If Anthropic changes the column structure of their members CSV, `claude_loader.py` breaks immediately. Every loader is hardcoded to specific column names.

**Jira export** — If the Jira admin changes the export filter template, renames a column, or adds a custom field, `jira_loader.py` breaks. There is no schema validation layer that fails gracefully.

### The weekly data problem

Claude Console only exports totals at a **calendar-month level**. To support the weekly view, the app approximates weekly spend and lines of code by **dividing monthly totals by 4.3**. This is a proxy, not real data. A developer who did all their work in week 1 and took week 4 off will show identical weekly numbers across all four weeks.

### The identity problem

Developer identity is bridged via a `developers.csv` mapping file (display name → email). If a developer's Jira display name is inconsistent across sprints, they get split into two records and their metrics are distorted. v2 makes this editable via the Settings UI — but it is still a manual process.

### What this proves

- The data join between Claude Console and Jira produces meaningful, actionable metrics
- Token spend + deliverables + bug attribution together tell a real story about AI-assisted development ROI
- Managers and developers both want this visibility — the question was never *if*, it was *how well*

---

## Project Structure

```
TokenToTask/
├── merge.py                  # Core ETL pipeline (v1 CLI entrypoint)
├── main.py                   # FastAPI app entrypoint (v2)
├── requirements.txt
├── .env.example
├── src/
│   ├── loaders/
│   │   ├── claude_loader.py  # Parses Claude Console CSV
│   │   └── jira_loader.py    # Parses Jira deliverables + bugs CSVs
│   ├── metrics.py            # Efficiency score, cost, coverage calculations
│   ├── guardrail.py          # Bug attribution + traffic-light flag logic
│   ├── models.py             # Dataclasses: Deliverable, Bug, DeveloperMetrics
│   ├── output.py             # CSV writer
│   └── sheets.py             # Optional Google Sheets sync
├── frontend/                 # React SPA (Vite)
├── tests/
│   ├── fixtures/             # Sample CSVs for local testing
│   ├── test_metrics.py
│   ├── test_guardrail.py
│   ├── test_claude_loader.py
│   └── test_output.py
├── uploads/                  # Raw CSV storage (gitignored)
├── data_drop/                # Server directory scan path (gitignored)
└── docs/
    ├── cli_architecture.png
    └── webapp_architecture.png
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

All core logic — metrics computation, bug attribution, flag calculation, CSV parsing — is unit tested against fixture files in `tests/fixtures/`.

---

## 🗺️ Roadmap

| Version | Status | What it adds |
|---|---|---|
| v1 — CLI | ✅ Done | Core ETL pipeline, metrics engine, Google Sheets sync |
| v2 — Web App | ✅ Done (POC) | FastAPI + React UI, SQLite history, CSV upload, trend charts |
| v3 — API Integrations | 🔜 Planned | Jira OAuth REST API, Anthropic Usage API, real weekly data, auth layer |

---

## 🤝 Contributing

This is an internal POC open-sourced for the community. If you are running Claude Code across an engineering team and want the same visibility, the fixture files in `tests/fixtures/` show exactly what CSV format the loaders expect.

PRs welcome, especially for:
- Schema validation with graceful error handling
- Alternative data source adapters (Linear, GitHub Issues)
- Better weekly approximation logic

---

## Built by

**Navneet Shukla**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/navneet-shukla17/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat-square&logo=github&logoColor=white)](https://github.com/navneetshukla17)

---

*Built by the Cashflo engineering team · MIT License*