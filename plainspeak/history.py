"""Saves past letters in a small local database (SQLite) so users can come back to them."""

import sqlite3
from datetime import datetime
from pathlib import Path

from .schema import LetterAnalysis

DB_PATH = Path(__file__).resolve().parent.parent / "plainspeak.db"


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS letters (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               saved_at TEXT NOT NULL,
               language TEXT NOT NULL,
               document_type TEXT NOT NULL,
               analysis_json TEXT NOT NULL)"""
    )
    return conn


def save(analysis: LetterAnalysis, language: str, db_path: Path = DB_PATH) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO letters (saved_at, language, document_type, analysis_json) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="minutes"), language, analysis.document_type,
             analysis.model_dump_json()),
        )
        return cur.lastrowid


def list_recent(limit: int = 10, db_path: Path = DB_PATH) -> list[tuple[int, str, str, str]]:
    with _connect(db_path) as conn:
        return conn.execute(
            "SELECT id, saved_at, language, document_type FROM letters ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def load(letter_id: int, db_path: Path = DB_PATH) -> tuple[LetterAnalysis, str] | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT analysis_json, language FROM letters WHERE id = ?", (letter_id,)).fetchone()
    return (LetterAnalysis.model_validate_json(row[0]), row[1]) if row else None


def delete(letter_id: int, db_path: Path = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM letters WHERE id = ?", (letter_id,))
