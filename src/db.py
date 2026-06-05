import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from src.models import DeveloperMetrics

DB_PATH = "dashboard.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Settings table (for Jira base URL, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # Pipeline runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        period TEXT NOT NULL,
        trigger_type TEXT NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT
    )
    """)

    # Developer metrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS developer_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        email TEXT NOT NULL,
        display_name TEXT,
        period TEXT NOT NULL,
        spend_usd REAL,
        lines_of_code INTEGER,
        deliverables_count INTEGER,
        story_points_delivered INTEGER,
        story_points_coverage REAL,
        cost_per_deliverable REAL,
        lines_per_deliverable REAL,
        cost_per_line REAL,
        ai_efficiency_score REAL,
        bugs_attributed INTEGER,
        bug_rate REAL,
        flag TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE
    )
    """)

    # Attributed bugs detail table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attributed_bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        email TEXT NOT NULL,
        bug_key TEXT NOT NULL,
        epic_key TEXT,
        sprint TEXT,
        created_date TEXT,
        resolved_date TEXT,
        story_key TEXT,
        FOREIGN KEY (run_id) REFERENCES runs (id) ON DELETE CASCADE
    )
    """)

    # Default settings
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        ("jira_base_url", "https://cashflo.atlassian.net/browse/"),
    )

    conn.commit()
    conn.close()


def set_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()


def get_setting(key: str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None


def add_run(period: str, trigger_type: str, status: str, error_message: str = None) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO runs (timestamp, period, trigger_type, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    """,
        (timestamp, period, trigger_type, status, error_message),
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def get_runs(limit: int = 20) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, period, trigger_type, status, error_message FROM runs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_metrics(run_id: int, metrics: List[DeveloperMetrics]):
    conn = get_db_connection()
    cursor = conn.cursor()
    for m in metrics:
        cursor.execute(
            """
            INSERT INTO developer_metrics (
                run_id, email, display_name, period, spend_usd, lines_of_code,
                deliverables_count, story_points_delivered, story_points_coverage,
                cost_per_deliverable, lines_per_deliverable, cost_per_line,
                ai_efficiency_score, bugs_attributed, bug_rate, flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run_id,
                m.email,
                m.display_name,
                m.period,
                m.spend_usd,
                m.lines_of_code,
                m.deliverables_count,
                m.story_points_delivered,
                m.story_points_coverage,
                m.cost_per_deliverable,
                m.lines_per_deliverable,
                m.cost_per_line,
                m.ai_efficiency_score,
                m.bugs_attributed,
                m.bug_rate,
                m.flag,
            ),
        )
    conn.commit()
    conn.close()


def save_attributed_bugs(run_id: int, email: str, bug_list: List[dict]):
    conn = get_db_connection()
    cursor = conn.cursor()
    for b in bug_list:
        cursor.execute(
            """
            INSERT INTO attributed_bugs (
                run_id, email, bug_key, epic_key, sprint, created_date, resolved_date, story_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run_id,
                email,
                b["bug_key"],
                b.get("epic_key"),
                b.get("sprint"),
                b.get("created_date"),
                b.get("resolved_date"),
                b.get("story_key"),
            ),
        )
    conn.commit()
    conn.close()


def get_latest_metrics_for_period(period: str) -> List[Dict]:
    """Retrieve the metrics associated with the most recent SUCCESSFUL run of a period."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM runs 
        WHERE period = ? AND status = 'success' 
        ORDER BY id DESC LIMIT 1
    """,
        (period,),
    )
    run_row = cursor.fetchone()
    if not run_row:
        conn.close()
        return []

    run_id = run_row["id"]
    cursor.execute(
        "SELECT * FROM developer_metrics WHERE run_id = ?",
        (run_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_periods() -> List[str]:
    """Get all periods that have at least one successful run, sorted chronologically."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT period FROM runs WHERE status = 'success' ORDER BY period ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [row["period"] for row in rows]


def get_developer_profile(email: str, period: str) -> Optional[Dict]:
    """Get metrics for a specific developer in a period."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT dm.* FROM developer_metrics dm
        JOIN runs r ON dm.run_id = r.id
        WHERE dm.email = ? AND dm.period = ? AND r.status = 'success'
        ORDER BY r.id DESC LIMIT 1
    """,
        (email, period),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_developer_history(email: str) -> List[Dict]:
    """Get historical metrics for a developer, sorted chronologically."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Find the latest successful metrics for each period
    cursor.execute(
        """
        SELECT dm.* FROM developer_metrics dm
        JOIN (
            SELECT period, MAX(id) as latest_run_id FROM runs 
            WHERE status = 'success' 
            GROUP BY period
        ) r ON dm.run_id = r.latest_run_id
        WHERE dm.email = ?
        ORDER BY dm.period ASC
    """,
        (email,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_developer_attributed_bugs(email: str, period: str) -> List[Dict]:
    """Get the details of bugs attributed to a developer in a period."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Find latest successful run for the period
    cursor.execute(
        """
        SELECT id FROM runs 
        WHERE period = ? AND status = 'success' 
        ORDER BY id DESC LIMIT 1
    """,
        (period,),
    )
    run_row = cursor.fetchone()
    if not run_row:
        conn.close()
        return []

    run_id = run_row["id"]
    cursor.execute(
        "SELECT * FROM attributed_bugs WHERE run_id = ? AND email = ?",
        (run_id, email),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_team_history() -> List[Dict]:
    """Get aggregate team metrics per period (sum/avg across developers)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the latest run IDs for each period
    cursor.execute(
        """
        SELECT latest_run_id, period FROM (
            SELECT period, MAX(id) as latest_run_id FROM runs 
            WHERE status = 'success' 
            GROUP BY period
        )
    """
    )
    periods_runs = cursor.fetchall()
    if not periods_runs:
        conn.close()
        return []

    results = []
    for pr in periods_runs:
        run_id = pr["latest_run_id"]
        period = pr["period"]

        # Sum and averages
        cursor.execute(
            """
            SELECT 
                SUM(spend_usd) as total_spend,
                SUM(lines_of_code) as total_lines,
                SUM(deliverables_count) as total_deliverables,
                SUM(story_points_delivered) as total_story_points,
                AVG(ai_efficiency_score) as avg_efficiency,
                SUM(bugs_attributed) as total_bugs,
                COUNT(email) as total_developers,
                SUM(CASE WHEN spend_usd > 0 THEN 1 ELSE 0 END) as active_developers
            FROM developer_metrics 
            WHERE run_id = ?
        """,
            (run_id,),
        )
        agg = cursor.fetchone()

        # Count flags
        cursor.execute(
            """
            SELECT flag, COUNT(*) as count 
            FROM developer_metrics 
            WHERE run_id = ? 
            GROUP BY flag
        """,
            (run_id,),
        )
        flag_rows = cursor.fetchall()
        flags = {"green": 0, "red": 0, "yellow": 0, "gray": 0}
        for f in flag_rows:
            if f["flag"] in flags:
                flags[f["flag"]] = f["count"]

        results.append(
            {
                "period": period,
                "total_spend": agg["total_spend"] or 0.0,
                "total_lines": agg["total_lines"] or 0,
                "total_deliverables": agg["total_deliverables"] or 0,
                "total_story_points": agg["total_story_points"] or 0,
                "avg_efficiency": agg["avg_efficiency"],
                "total_bugs": agg["total_bugs"] or 0,
                "total_developers": agg["total_developers"] or 0,
                "active_developers": agg["active_developers"] or 0,
                "flags": flags,
            }
        )

    conn.close()
    # Sort chronologically by period
    results.sort(key=lambda x: x["period"])
    return results
