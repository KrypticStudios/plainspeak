"""Tiny privacy-safe monitoring: counts what KIND of thing happened, never what was in a letter.

Each event is one short word, like "letter_ok" or "ai_busy". The counts go to the server log, which
only the app's owner can see (Streamlit Cloud: Manage app -> Logs), so we can tell during judging
whether the AI is struggling, without ever recording anyone's letter, question or answer.
"""

import logging
import threading
from collections import Counter

EVENTS = {
    "letter_ok": "a letter was explained",
    "question_ok": "a question was answered",
    "reply_ok": "a reply letter was drafted",
    "basic_check": "a letter was checked without the AI",
    "ai_busy": "Google's AI was overloaded or too slow",
    "ai_limit": "the free AI limit was reached",
    "ai_key": "the API key was rejected",
    "ai_other": "another AI error",
    "bad_upload": "an upload was refused (wrong type, too big, too many pages)",
    "rate_limited": "a visitor hit our usage limit",
    "ids_hidden": "ID numbers were hidden before sending",
    "tts_failed": "read-aloud failed",
}

_counts: Counter = Counter()
_lock = threading.Lock()
log = logging.getLogger("plainspeak")
if not log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s PLAINSPEAK %(message)s"))
    log.addHandler(_handler)
    log.setLevel(logging.INFO)


def record(event: str) -> None:
    """Count one event (a fixed word from EVENTS) and write a one-line, content-free log entry."""
    if event not in EVENTS:
        event = "ai_other"
    with _lock:
        _counts[event] += 1
        total = _counts[event]
    log.info("%s (total %d)", event, total)


def counts() -> dict[str, int]:
    with _lock:
        return dict(_counts)


def kind_of_error(kind: str) -> str:
    """Turn an AnalyzerError's kind ("busy", "limit", ...) into an event word."""
    return {"busy": "ai_busy", "limit": "ai_limit", "setup": "ai_key"}.get(kind, "ai_other")
