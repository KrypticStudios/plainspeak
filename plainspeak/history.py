"""Saves past letters in a small database (SQLite) so users can come back to them.

On the public website we use SessionStore: letters live only in that visitor's session, in the
server's memory, and are gone when they close the page. DiskStore (a file) is only for running
PlainSpeak on your own computer, where you are the only user.
"""

import sqlite3
from contextlib import closing
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
               analysis_json TEXT NOT NULL,
               owner TEXT NOT NULL DEFAULT 'local')"""
    )
    columns = [row[1] for row in conn.execute("PRAGMA table_info(letters)")]
    if "owner" not in columns:   # older databases were made before the owner column existed
        conn.execute("ALTER TABLE letters ADD COLUMN owner TEXT NOT NULL DEFAULT 'local'")
    return conn


def save(analysis: LetterAnalysis, language: str, owner: str, db_path: Path = DB_PATH) -> int:
    with closing(_connect(db_path)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO letters (saved_at, language, document_type, analysis_json, owner) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="minutes"), language, analysis.document_type,
             analysis.model_dump_json(), owner),
        )
        return cur.lastrowid


def list_recent(owner: str, limit: int = 10, db_path: Path = DB_PATH) -> list[tuple[int, str, str, str]]:
    with closing(_connect(db_path)) as conn:
        return conn.execute(
            "SELECT id, saved_at, language, document_type FROM letters WHERE owner = ? ORDER BY id DESC LIMIT ?",
            (owner, limit),
        ).fetchall()


def load(letter_id: int, owner: str, db_path: Path = DB_PATH) -> tuple[LetterAnalysis, str] | None:
    with closing(_connect(db_path)) as conn:
        row = conn.execute("SELECT analysis_json, language FROM letters WHERE id = ? AND owner = ?",
                           (letter_id, owner)).fetchone()
    if not row:
        return None
    try:
        return LetterAnalysis.model_validate_json(row[0]), row[1]
    except ValueError:   # saved by an older version of PlainSpeak whose format has changed
        return None


def delete(letter_id: int, owner: str, db_path: Path = DB_PATH) -> None:
    with closing(_connect(db_path)) as conn, conn:
        conn.execute("DELETE FROM letters WHERE id = ? AND owner = ?", (letter_id, owner))


class SessionStore:
    """'My letters' kept only in this visitor's browser session (in memory), never written to disk.

    Used on the public website: when the visitor closes the page, their letters are gone from our server.
    """

    def __init__(self, session: dict):
        self.letters = session.setdefault("my_letters", {})   # id -> (saved_at, language, LetterAnalysis)

    def save(self, analysis: LetterAnalysis, language: str) -> int:
        letter_id = max(self.letters, default=0) + 1
        self.letters[letter_id] = (datetime.now().isoformat(timespec="minutes"), language, analysis)
        return letter_id

    def list_recent(self, limit: int = 10) -> list[tuple[int, str, str, str]]:
        rows = [(i, at, lang, a.document_type) for i, (at, lang, a) in self.letters.items()]
        return sorted(rows, reverse=True)[:limit]

    def load(self, letter_id: int) -> tuple[LetterAnalysis, str] | None:
        if letter_id not in self.letters:
            return None
        _, lang, a = self.letters[letter_id]
        return a, lang

    def delete(self, letter_id: int) -> None:
        self.letters.pop(letter_id, None)

    def delete_all(self) -> None:
        self.letters.clear()


class DiskStore:
    """'My letters' saved in the SQLite file on this computer (for running PlainSpeak on your own machine)."""

    def __init__(self, owner: str = "local", db_path: Path = DB_PATH):
        self.owner, self.db_path = owner, db_path

    def save(self, analysis: LetterAnalysis, language: str) -> int:
        return save(analysis, language, self.owner, self.db_path)

    def list_recent(self, limit: int = 10):
        return list_recent(self.owner, limit, self.db_path)

    def load(self, letter_id: int):
        return load(letter_id, self.owner, self.db_path)

    def delete(self, letter_id: int) -> None:
        delete(letter_id, self.owner, self.db_path)

    def delete_all(self) -> None:
        with closing(_connect(self.db_path)) as conn, conn:
            conn.execute("DELETE FROM letters WHERE owner = ?", (self.owner,))
