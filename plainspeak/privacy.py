"""Privacy and safety helpers, all plain Python and run on our server.

1. redact(): hides ID numbers (Social Security, card, account and case numbers)
   in typed or pasted text BEFORE it is sent to the AI. Explaining a letter
   never needs them.
2. RateLimiter: stops one person (or a bot) from using up the free AI quota.
3. check_upload(): only lets real images and PDFs through, at a sensible size.
"""

import re
import threading
import time
from collections import deque

HIDDEN = "[number hidden]"

# Social Security numbers: 123-45-6789 or 123 45 6789
_SSN = re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b")
# Card numbers: 13-19 digits, optionally in groups of 4
_CARD = re.compile(r"\b(?:\d{4}[- ]?){3}\d{1,7}\b")
# A label like "Account Number:", "Case #", "Member ID" followed by the number itself
_LABELLED = re.compile(
    r"(?i)\b((?:account|acct|case|member|policy|patient|client|customer|reference|ref|claim|medicaid|medicare|"
    r"ebt|snap|ssn|social security|id|identification)\s*(?:no\.?|number|num|#|id)?\s*[:#]?\s*)"
    r"(?=[A-Z0-9-]*\d)([A-Z0-9][A-Z0-9-]{4,})\b")  # the value must contain at least one digit
# Any long run of digits (9+) that isn't a phone number written with separators
_LONG_DIGITS = re.compile(r"\b\d{9,}\b")


def redact(text: str) -> tuple[str, int]:
    """Return (text with ID numbers hidden, how many were hidden)."""
    count = 0

    def hide(_match) -> str:
        nonlocal count
        count += 1
        return HIDDEN

    def hide_value(match) -> str:
        nonlocal count
        count += 1
        return match.group(1) + HIDDEN

    text = _SSN.sub(hide, text)
    text = _CARD.sub(hide, text)
    text = _LABELLED.sub(hide_value, text)
    text = _LONG_DIGITS.sub(hide, text)
    return text, count


class RateLimiter:
    """Allows at most `limit` uses per `window` seconds for each key. Safe to share between visitors."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True


MAX_PAGES = 5
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
MAX_TEXT_CHARS = 20_000


def check_upload(data: bytes, mime_type: str) -> str | None:
    """Return an error message if the file isn't a normal image or PDF, else None."""
    if len(data) > MAX_BYTES:
        return "That file is too big. Please use a file under 10 MB."
    if mime_type == "application/pdf":
        return None if data[:5] == b"%PDF-" else "That doesn't look like a real PDF file."
    if mime_type.startswith("image/"):
        from io import BytesIO

        from PIL import Image, UnidentifiedImageError
        try:
            Image.open(BytesIO(data)).verify()   # checks it's really an image, without running anything
            return None
        except (UnidentifiedImageError, OSError, SyntaxError):
            return "We couldn't open that picture. Please try a JPG or PNG photo."
    return "Please upload a photo (JPG or PNG) or a PDF."
