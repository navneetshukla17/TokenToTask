import os
import shutil
import csv
import re
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.db import (
    init_db,
    get_latest_metrics_for_period,
    get_periods,
    get_developer_profile,
    get_developer_history,
    get_developer_attributed_bugs,
    get_team_history,
    get_runs,
    get_setting,
    set_setting,
)
from src.pipeline import run_pipeline

app = FastAPI(title="Developer Productivity Dashboard API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database at startup
init_db()

TEMP_DIR = "./temp_uploads"
DATA_DROP_DIR = "./data_drop"
DEV_MAP_PATH = "./developers.csv"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DATA_DROP_DIR, exist_ok=True)


class SettingsUpdate(BaseModel):
    jira_base_url: str


class DeveloperMapping(BaseModel):
    display_name: str
    email: str


# Helper to check if fallback logic applies (e.g. show warning in UI if weekly view uses monthly Claude data)
def check_weekly_fallback_applies(period: str) -> bool:
    return bool(re.match(r"^\d{4}-W\d{2}$", period))


@app.get("/api/periods")
def api_get_periods():
    """Retrieve all periods with successfully computed dashboard data."""
    try:
        return {"periods": get_periods()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs")
def api_get_runs(limit: int = 20):
    """Retrieve pipeline run logs (success/failed runs)."""
    try:
        return {"runs": get_runs(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
def api_get_settings():
    """Retrieve configuration settings (Jira base URL)."""
    try:
        return {
            "jira_base_url": get_setting("jira_base_url")
            or "https://cashflo.atlassian.net/browse/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
def api_update_settings(settings: SettingsUpdate):
    """Update configurations."""
    try:
        set_setting("jira_base_url", settings.jira_base_url)
        return {"status": "success", "jira_base_url": settings.jira_base_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/developers")
def api_get_developers():
    """Retrieve display_name -> email developer mapping from developers.csv."""
    try:
        if not os.path.exists(DEV_MAP_PATH):
            return {"developers": []}

        devs = []
        with open(DEV_MAP_PATH, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                devs.append(
                    {
                        "display_name": row.get("display_name", "").strip(),
                        "email": row.get("email", "").strip(),
                    }
                )
        return {"developers": devs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/developers")
def api_update_developers(devs: List[DeveloperMapping]):
    """Update developers.csv mapping list."""
    try:
        with open(DEV_MAP_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["display_name", "email"])
            writer.writeheader()
            for dev in devs:
                writer.writerow(
                    {
                        "display_name": dev.display_name.strip(),
                        "email": dev.email.strip(),
                    }
                )
        return {"status": "success", "count": len(devs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard")
def api_get_leaderboard(period: str):
    """Retrieve the sorted developer leaderboard for a specific period."""
    if not period:
        raise HTTPException(status_code=400, detail="Period parameter is required.")

    try:
        metrics = get_latest_metrics_for_period(period)
        fallback_warning = check_weekly_fallback_applies(period)
        return {
            "period": period,
            "metrics": metrics,
            "weekly_spend_approximated": fallback_warning,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/developer/{email}")
def api_get_developer_profile(email: str, period: str):
    """Retrieve full metrics history and period details for a single developer."""
    if not email or not period:
        raise HTTPException(
            status_code=400, detail="Email and period parameters are required."
        )

    try:
        profile = get_developer_profile(email, period)
        history = get_developer_history(email)
        bugs = get_developer_attributed_bugs(email, period)

        # Flag explanation logic
        flag = profile.get("flag", "gray") if profile else "gray"
        explanation = ""
        if flag == "green":
            explanation = "You are currently On Track. Your AI efficiency score is above team median, and your bug rate is below team median. Keep doing what you're doing!"
        elif flag == "red":
            explanation = "Your flag is Quality Risk. While your AI productivity/efficiency score is high, you have a higher-than-average bug rate. Focus more on testing and review."
        elif flag == "yellow":
            explanation = "Your flag is Coaching Opportunity. You have a low bug rate, but your AI efficiency score is below average. You may benefit from coaching to leverage Claude Code more effectively."
        elif flag == "gray":
            explanation = "Your flag is Needs Attention. Your AI efficiency is below average, and your bug rate is above team average. Consider reviewing code patterns and pairing with colleagues."

        return {
            "email": email,
            "period": period,
            "profile": profile,
            "explanation": explanation,
            "history": history,
            "bugs": bugs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/team/trends")
def api_get_team_trends():
    """Retrieve historical team aggregate stats."""
    try:
        return {"trends": get_team_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def api_upload_csv(
    period: str = Form(...),
    claude_file: UploadFile = File(...),
    jira_deliverables_file: UploadFile = File(...),
    jira_bugs_file: UploadFile = File(...),
):
    """Handles manual CSV ingestion via web form upload."""
    if not re.match(r"^\d{4}-W\d{2}$", period) and not re.match(
        r"^\d{4}-\d{2}$", period
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid period format. Must be YYYY-MM or YYYY-Www.",
        )

    # Save to temp paths
    claude_path = os.path.join(TEMP_DIR, f"claude_{period}.csv")
    deliv_path = os.path.join(TEMP_DIR, f"deliverables_{period}.csv")
    bugs_path = os.path.join(TEMP_DIR, f"bugs_{period}.csv")

    try:
        with open(claude_path, "wb") as buffer:
            shutil.copyfileobj(claude_file.file, buffer)
        with open(deliv_path, "wb") as buffer:
            shutil.copyfileobj(jira_deliverables_file.file, buffer)
        with open(bugs_path, "wb") as buffer:
            shutil.copyfileobj(jira_bugs_file.file, buffer)

        # We assume the default developers.csv in the root is our developer map.
        # If it doesn't exist, create an empty file with headers.
        if not os.path.exists(DEV_MAP_PATH):
            with open(DEV_MAP_PATH, "w", encoding="utf-8") as f:
                f.write("display_name,email\n")

        # Run pipeline
        run_id, metrics = run_pipeline(
            claude_csv_path=claude_path,
            jira_deliverables_path=deliv_path,
            jira_bugs_path=bugs_path,
            developers_csv_path=DEV_MAP_PATH,
            period=period,
            trigger_type="web_upload",
        )

        return {
            "status": "success",
            "run_id": run_id,
            "period": period,
            "developers_count": len(metrics),
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Pipeline processing failed: {str(e)}"
        )
    finally:
        # Cleanup temp files
        for path in [claude_path, deliv_path, bugs_path]:
            if os.path.exists(path):
                os.remove(path)


@app.post("/api/run-server")
def api_run_server_files(period: str):
    """Triggers pipeline execution using CSV files located in `./data_drop` folder."""
    if not re.match(r"^\d{4}-W\d{2}$", period) and not re.match(
        r"^\d{4}-\d{2}$", period
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid period format. Must be YYYY-MM or YYYY-Www.",
        )

    claude_path = os.path.join(DATA_DROP_DIR, "claude_export.csv")
    deliv_path = os.path.join(DATA_DROP_DIR, "jira_deliverables.csv")
    bugs_path = os.path.join(DATA_DROP_DIR, "jira_bugs.csv")
    dev_map_path = os.path.join(DATA_DROP_DIR, "developers.csv")

    # Fallback to root developers.csv if not found in data_drop
    if not os.path.exists(dev_map_path):
        dev_map_path = DEV_MAP_PATH

    missing_files = []
    for name, path in [
        ("claude_export.csv", claude_path),
        ("jira_deliverables.csv", deliv_path),
        ("jira_bugs.csv", bugs_path),
        ("developers.csv", dev_map_path),
    ]:
        if not os.path.exists(path):
            missing_files.append(name)

    if missing_files:
        raise HTTPException(
            status_code=400,
            detail=f"Incomplete files in server directory. Missing: {', '.join(missing_files)}. Please place them in './data_drop/'",
        )

    try:
        run_id, metrics = run_pipeline(
            claude_csv_path=claude_path,
            jira_deliverables_path=deliv_path,
            jira_bugs_path=bugs_path,
            developers_csv_path=dev_map_path,
            period=period,
            trigger_type="server_directory",
        )
        return {
            "status": "success",
            "run_id": run_id,
            "period": period,
            "developers_count": len(metrics),
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Pipeline processing failed: {str(e)}"
        )


# Serve frontend static assets if available (Production deployment support)
FRONTEND_DIST = "./frontend/dist"
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
