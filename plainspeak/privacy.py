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
MAX_PIXELS = 40_000_000  # about 4x a 12-megapixel phone photo


def pdf_page_count(data: bytes) -> int:
    """Roughly count the pages in a PDF without any extra library.

    PDFs list each page as "/Type /Page" and the total as "/Count N". We take the larger of the two,
    so a PDF can't hide extra pages from us.
    """
    pages = len(re.findall(rb"/Type\s*/Page(?!s)", data))
    counts = [int(n) for n in re.findall(rb"/Count\s+(\d+)", data)]
    return max([pages, *counts])


def check_upload(data: bytes, mime_type: str) -> str | None:
    """Return an error message if the file isn't a normal image or PDF, else None."""
    if len(data) > MAX_BYTES:
        return "That file is too big. Please use a file under 10 MB."
    if mime_type == "application/pdf":
        if data[:5] != b"%PDF-":
            return "That doesn't look like a real PDF file."
        if pdf_page_count(data) > MAX_PAGES:
            return f"That PDF has more than {MAX_PAGES} pages. Please upload only the pages of your letter."
        return None
    if mime_type.startswith("image/"):
        from io import BytesIO

        from PIL import Image, UnidentifiedImageError
        try:
            img = Image.open(BytesIO(data))
            if img.width * img.height > MAX_PIXELS:   # a tiny file can claim to be gigantic
                return "That picture is too large. Please use a normal phone photo."
            img.verify()                               # checks it's really an image, without running anything
            Image.open(BytesIO(data)).load()           # and that the whole picture is there (not cut off)
            return None
        except Image.DecompressionBombError:
            return "That picture is too large. Please use a normal phone photo."
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            return "We couldn't open that picture. Please try a JPG or PNG photo."
    return "Please upload a photo (JPG or PNG) or a PDF."
