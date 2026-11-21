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
            if len(self._hits) > 5000:   # forget visitors who haven't been back for a while
                for k in [k for k, h in self._hits.items() if not h or now - h[-1] > self.window]:
                    del self._hits[k]
            return True


MAX_PAGES = 5                     # pages per letter, counting every page of every file
MAX_BYTES = 10 * 1024 * 1024      # 10 MB per file
MAX_TOTAL_BYTES = 20 * 1024 * 1024  # 20 MB for the whole letter (Google's limit for files sent this way)
MAX_TEXT_CHARS = 20_000
MAX_PIXELS = 40_000_000           # about 4x a 12-megapixel phone photo

# Every upload problem has a short code. The app shows it in the reader's language (ui_start.py "up_*").
UPLOAD_PROBLEMS = {
    "too_big": "That file is too big. Please use a file under 10 MB.",
    "not_pdf": "That doesn't look like a real PDF file.",
    "pdf_unreadable": "We couldn't open that PDF. Please try a photo instead.",
    "too_large": "That picture is too large. Please use a normal phone photo.",
    "bad_image": "We couldn't open that picture. Please try a JPG or PNG photo.",
    "wrong_type": "Please upload a photo (JPG or PNG) or a PDF.",
    "too_many_pages": f"Please add at most {MAX_PAGES} pages at a time (this counts every page of every file).",
    "too_much_data": "These files are too big together. Please use fewer or smaller files.",
}


def pdf_page_count(data: bytes) -> int | None:
    """How many pages a PDF has (using the pypdf library), or None if it can't be read."""
    from io import BytesIO

    from pypdf import PdfReader
    try:
        return len(PdfReader(BytesIO(data)).pages)
    except Exception:   # broken, encrypted or fake PDF
        return None


def check_upload(data: bytes, mime_type: str) -> str | None:
    """Return a problem code (see UPLOAD_PROBLEMS) if the file isn't a normal image or PDF, else None."""
    if len(data) > MAX_BYTES:
        return "too_big"
    if mime_type == "application/pdf":
        if data[:5] != b"%PDF-":
            return "not_pdf"
        pages = pdf_page_count(data)
        if pages is None:
            return "pdf_unreadable"
        return "too_many_pages" if pages > MAX_PAGES else None
    if mime_type.startswith("image/"):
        from io import BytesIO

        from PIL import Image, UnidentifiedImageError
        try:
            img = Image.open(BytesIO(data))
            if img.width * img.height > MAX_PIXELS:   # a tiny file can claim to be gigantic
                return "too_large"
            img.verify()                               # checks it's really an image, without running anything
            Image.open(BytesIO(data)).load()           # and that the whole picture is there (not cut off)
            return None
        except Image.DecompressionBombError:
            return "too_large"
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            return "bad_image"
    return "wrong_type"


def check_letter(files: list[tuple[bytes, str]]) -> list[str]:
    """Problems with the letter as a whole: too many pages in total, or too much data in total."""
    problems = []
    pages = sum((pdf_page_count(d) or 0) if m == "application/pdf" else 1 for d, m in files)
    if pages > MAX_PAGES:
        problems.append("too_many_pages")
    if sum(len(d) for d, _ in files) > MAX_TOTAL_BYTES:
        problems.append("too_much_data")
    return problems
