# Developer Productivity Dashboard (Proof of Concept)

A unified dashboard correlating developer-specific Claude Code AI utilization (costs, code lines) with JIRA deliverables (story points, resolved items, and quality bugs).

---

## 📢 Blunt Product Reality & Scope Statement

Let's be completely transparent: **this dashboard is a Proof of Concept (POC) validating metrics, not a production-hardened platform.** 

The dashboard suffers from high fragility due to its **heavy reliance on manual CSV exports** from third-party tools (platform.claude.com and JIRA filters). Specifically:
1. **Schema Vulnerability**: If JIRA column headers change or Anthropic updates the Claude Console members CSV structure, the loaders *will* break and require manual hotfixes.
2. **Weekly Fallback Approximation**: Claude Console only exports totals at a calendar-month level. Because we require weekly granularity, the system approximates weekly Claude spend and lines of code by evenly dividing the monthly totals by 4.3. This is an educated proxy, not raw token data.
3. **Identity Mapping**: Bridging JIRA display names to Claude emails requires keeping `developers.csv` manually updated. Mismatched names default to usernames, split developer history, and distort quality calculations.

This MVP exists to prove value before we invest capital into Phase 2 (direct REST API syncs with JIRA OAuth and Anthropic's daily Usage API).

---

## 🛠️ The Problem & Our Solution

### The Problem
Cashflo's engineering team adopted Claude Code to speed up delivery. However, management had zero visibility into whether this investment was paying off or compromising code quality.
* Claude Console spend and JIRA deliverables lived in separate silos.
* Sharing developer performance was slow, manual, and occurred via flat CSV files.
* Developers had no self-service dashboard to review their flags or efficiency scores.
* Historical trends were lost because outputs were overwritten on each CLI execution.

### The Solution
We designed and implemented a dual-stage metrics compilation engine that cleanses, joins, and aggregates data, surfacing it in two formats:
1. **Stage 1 (CLI)**: A lightweight Python command-line utility for raw CSV merges and Google Sheets syncs.
2. **Stage 2 (Web App)**: A modern web interface running a FastAPI service and SQLite database to persist historical metrics and display them in an interactive React frontend.

---

## 🔍 Solution Evolution

### v1: Command-Line Interface (CLI)

The CLI script `merge.py` serves as the initial ETL pipeline. It accepts four input CSV files, runs the metrics joining in-memory, creates a flat `output.csv`, and optionally pushes data to a Google Sheet.

#### CLI In-Memory ETL Flow
![CLI In-Memory ETL Flow](/Users/tusharshukla/.gemini/antigravity/brain/1eaf88a9-f8c6-446b-8a98-d23facf8cb49/cli_architecture_diagram_1780652509931.png)

#### Running the CLI
```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Execute the CLI pipeline
python merge.py \
  tests/fixtures/claude_export.csv \
  tests/fixtures/jira_deliverables.csv \
  tests/fixtures/jira_bugs.csv \
  tests/fixtures/developers.csv \
  --period 2026-05 \
  --output output.csv
```

---

### v2: React + FastAPI Web Application (MVP)

The Web Application wraps the core Python calculations, housing them in a FastAPI backend backed by a persistent SQLite database. This allows historical trends to accumulate over months and weeks, and serves the views directly to a responsive React SPA frontend.

#### Web Application System Architecture
![Web Application System Architecture](/Users/tusharshukla/.gemini/antigravity/brain/1eaf88a9-f8c6-446b-8a98-d23facf8cb49/webapp_architecture_diagram_1780652531520.png)

#### App Features
* **Interactive Leaderboard**: Sortable developer grid, toggleable monthly/weekly periods, and multi-select flag checkboxes.
* **Developer Profiles**: Individual metric cards, interactive trend lines, and attributed bug logs that hyperlink straight to JIRA.
* **Team Trends**: Visual graphs monitoring total spend, deliverables, bugs, and AI adoption rates (tracking zero-spend developers).
* **Dual Ingestion**: Drag-and-drop file uploader and server directory scan (`./data_drop/`).
* **Settings & Mapping**: UI configuration editors to save the JIRA link prefix and edit user mappings on the fly.

---

## 📋 The Product Requirement Documents (PRDs)

We progressed through three distinct documentation stages to align stakeholders and refine features. **Click the links below to view the exact specifications:**

1. **[AI Developer Dashboard Design Spec](file:///Users/tusharshukla/Desktop/Developer-Dashboard/docs/superpowers/specs/2026-05-20-ai-developer-dashboard-design.md)**
   * *Purpose*: Defines initial metrics formulas, bug attribution limits (sprint + epic + 30 days window), and flag calculations based on team-wide medians.
2. **[The Problem PRD](file:///Users/tusharshukla/Desktop/Developer-Dashboard/The%20problem_%20Developer-Productivity-Dashboard-PRD.pdf)**
   * *Purpose*: Outlined the initial business goals of migrating from the CLI, proposing a **web-based file upload screen** and supporting both **weekly and monthly** granularities.
3. **[Web App PRD](file:///Users/tusharshukla/Desktop/Developer-Dashboard/WebApp_%20Developer-Dashboard-PRD.pdf)**
   * *Purpose*: Drafted a simpler alternative focused on **server filesystem directory ingestion** (running via monthly cron or a button click) rather than browser uploads, using **monthly granularity only**.
4. **[Unified Web App MVP PRD (Finalized)](file:///Users/tusharshukla/Desktop/Developer-Dashboard/docs/superpowers/specs/AI-Developer-Dashboard-PRD.md)**
   * *Purpose*: The definitive spec combining both ingestion paths (manual web upload + server directory), supporting weekly/monthly toggles, introducing the weekly spend scaling fallback, and incorporating editable settings.

### Why did we need separate documents?
* The **Design Spec** focused entirely on the raw mathematical formulas and CLI rules.
* **The Problem PRD** and **Web App PRD** presented conflicting product requirements (web upload vs. server folder ingestion, weekly vs. monthly support).
* The **Unified PRD** resolved these discrepancies, creating a hybrid MVP that combines the ease of manual browser uploads with server execution triggers, and maps out the custom JIRA configuration settings.

---

## 🚀 Deployment & Demo

* **Live Demo URL**: [https://dashboard-poc.cashflo.io](https://dashboard-poc.cashflo.io) *(Placeholder — Update once deployed)*

### Local Quickstart
1. Compile the React frontend:
   ```bash
   cd frontend
   npm run build
   cd ..
   ```
2. Start the FastAPI backend:
   ```bash
   .venv/bin/uvicorn main:app --reload
   ```
3. Open your browser to **`http://127.0.0.1:8000`** and drag-and-drop the files in `tests/fixtures/` to see the dashboard populated!
