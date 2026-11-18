"""Enkel SQLite-lagring for firmaprofil og tilbud."""

import json
import sqlite3
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "tilbudsmaker.db"
LOGO_PATH = DATA_DIR / "logo.png"

COMPANY_FIELDS = [
    "navn", "orgnr", "adresse", "postnr_sted", "telefon", "epost",
    "kontonr", "standard_betingelser",
]


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS company (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL)"
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nummer INTEGER NOT NULL UNIQUE,
            opprettet TEXT NOT NULL,
            kunde TEXT NOT NULL,
            data TEXT NOT NULL,
            total REAL NOT NULL
        )"""
    )
    return conn


def get_company() -> dict:
    with _conn() as conn:
        row = conn.execute("SELECT data FROM company WHERE id = 1").fetchone()
    data = json.loads(row["data"]) if row else {}
    return {f: data.get(f, "") for f in COMPANY_FIELDS} | {"pro": data.get("pro", False)}


def save_company(data: dict) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO company (id, data) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET data = excluded.data",
            (json.dumps(data),),
        )


def next_quote_number() -> int:
    with _conn() as conn:
        row = conn.execute("SELECT MAX(nummer) AS n FROM quotes").fetchone()
    return (row["n"] or 1000) + 1


def save_quote(quote: dict) -> int:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO quotes (nummer, opprettet, kunde, data, total) VALUES (?, ?, ?, ?, ?)",
            (
                quote["nummer"],
                quote["dato"],
                quote["kunde"]["navn"],
                json.dumps(quote),
                quote["total"],
            ),
        )
    return quote["nummer"]


def list_quotes() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT data FROM quotes ORDER BY nummer DESC").fetchall()
    return [json.loads(r["data"]) for r in rows]


def quotes_this_month() -> int:
    prefix = date.today().strftime("%Y-%m")
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM quotes WHERE opprettet LIKE ?", (prefix + "%",)
        ).fetchone()
    return row["c"]
