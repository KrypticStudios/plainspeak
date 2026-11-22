"""Basic check, with no AI at all: find the dates, money amounts and phone numbers in a letter's own words.

Used when the AI can't be reached (free limit used up, service busy), and when someone chooses not to send
their letter to the AI. It is plain Python, so it can't invent anything: every line it shows is a sentence
copied from the letter. It also can't explain anything, and the page says so.
Works on pasted text and on PDFs that contain real text (not on photos: reading photos needs the AI).
"""

import re
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO

from .checks import dates_in

# Words that usually mean something serious can happen. Shown as a warning, not as a verdict.
SERIOUS_WORDS = ["evict", "eviction", "vacate", "court", "hearing", "summons", "judgment", "foreclos", "repossess",
                 "shut off", "shutoff", "disconnect", "termination", "terminate", "suspend", "suspension",
                 "default", "collection", "garnish", "deport", "removal", "benefits may stop", "will end",
                 "lose your", "penalty", "fine", "warrant", "or quit", "possession", "legal proceedings",
                 "forfeiture", "discontinued", "collection agency"]

_AMOUNT = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?")
_PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}(?!\d)")


@dataclass
class BasicReading:
    dates: list[tuple[date, str]] = field(default_factory=list)      # (date, the sentence it is in)
    money: list[tuple[str, str]] = field(default_factory=list)      # (amount, the sentence it is in)
    phones: list[str] = field(default_factory=list)
    serious_words: list[str] = field(default_factory=list)
    text: str = ""

    @property
    def found_anything(self) -> bool:
        return bool(self.dates or self.money or self.phones)


_ABBREVIATIONS = {"jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "dr", "mr",
                  "mrs", "ms", "no", "st", "vs", "inc", "co", "ave", "apt", "u.s", "e.g", "i.e"}


def sentences(text: str) -> list[str]:
    """Split a letter into sentences and lines (letters use both).

    A line that continues the one before (it starts with a small letter or a digit, and the line before
    doesn't end a sentence) is joined to it, because PDFs and photos wrap lines in the middle of a
    sentence ("reply by March" / "5, 2027"). "Jan. 5" and "Dr. Lee" are not split."""
    lines: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if not line:
            lines.append("")
            continue
        if lines and lines[-1] and lines[-1][-1] not in ".!?:" and (line[0].islower() or line[0].isdigit()):
            lines[-1] += " " + line
        else:
            lines.append(line)
    parts = []
    for line in filter(None, lines):
        pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])", line)
        for piece in pieces:
            last_word = parts[-1].rsplit(" ", 1)[-1].rstrip(".").lower() if parts else ""
            if parts and parts[-1].endswith(".") and last_word in _ABBREVIATIONS and piece is not pieces[0]:
                parts[-1] += " " + piece
            else:
                parts.append(piece)
    return parts


def read(text: str, today: date | None = None) -> BasicReading:
    """Find dates, amounts, phones and serious words in `text`. Dates that already passed come last."""
    r = BasicReading(text=text)
    seen_dates, seen_money = set(), set()
    for s in sentences(text):
        for d in sorted(dates_in(s)):
            if d not in seen_dates:
                seen_dates.add(d)
                r.dates.append((d, s))
        for m in _AMOUNT.findall(s):
            amount = m.replace(" ", "")
            if amount not in seen_money:
                seen_money.add(amount)
                r.money.append((amount, s))
    if today:
        r.dates.sort(key=lambda x: (x[0] < today, x[0] if x[0] >= today else -x[0].toordinal()))
    for p in _PHONE.findall(text):
        if re.sub(r"\D", "", p)[-10:] not in {re.sub(r"\D", "", q)[-10:] for q in r.phones}:
            r.phones.append(p.strip())
    low = text.lower()
    r.serious_words = [w for w in SERIOUS_WORDS if re.search(rf"\b{re.escape(w)}", low)]
    return r


def pdf_text(data: bytes, max_pages: int = 5) -> str:
    """The real text inside a PDF (empty for a scanned PDF, which is just pictures)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages[:max_pages]).strip()
    except Exception:
        return ""
