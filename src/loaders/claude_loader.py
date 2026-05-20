import pandas as pd
from typing import Dict


def load_claude_csv(path: str) -> Dict[str, dict]:
    """Load Claude Console export CSV.
    Returns {email_lower: {spend_usd: float, lines_of_code: int}}.
    Excludes API key rows (rows where email has no @).
    """
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "members": "email",
        "spend this month": "spend_raw",
        "lines this month": "lines_raw",
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
