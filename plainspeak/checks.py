"""Safety checks we run on the AI's answer with plain Python (no AI).

AI can "hallucinate" (make things up). So for every deadline, step and amount,
we check that its quote really appears in the letter. If it doesn't, the app
shows a warning instead of trusting it.
"""

import re
from difflib import SequenceMatcher

import textstat


def _normalize(s: str) -> str:
    """Lowercase and squash spaces/punctuation so small OCR differences don't matter."""
    s = s.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^\w$%./,:-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def quote_found(quote: str, letter_text: str, threshold: float = 0.85) -> bool:
    """True if `quote` appears in `letter_text` (exactly, or almost exactly)."""
    q, text = _normalize(quote), _normalize(letter_text)
    if not q:
        return False
    if q in text:
        return True
    # Slide a window the size of the quote across the letter and keep the best match.
    words, q_len = text.split(), len(q.split())
    best = 0.0
    for i in range(max(1, len(words) - q_len + 1)):
        window = " ".join(words[i:i + q_len])
        best = max(best, SequenceMatcher(None, q, window).ratio())
        if best >= threshold:
            return True
    return False


def reading_grade(text: str) -> float | None:
    """US school grade level needed to read `text` (Flesch-Kincaid). English only."""
    if len(text.split()) < 10:
        return None
    return round(max(0.0, textstat.flesch_kincaid_grade(text)), 1)


MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def date_written_in(iso: str, letter_text: str) -> bool:
    """True if the date (YYYY-MM-DD) is actually written in the letter, in any common format.

    Letters often say "within 14 days after service" instead of a date. The AI may then work out a
    date itself, but that guess can be wrong (it depends on when the person got the letter), so we
    never put a calculated date in the countdown or the calendar.
    """
    try:
        y, m, d = (int(x) for x in iso.strip().split("-"))
    except ValueError:
        return False
    t = " ".join(letter_text.lower().split())
    forms = [f"{y}-{m:02d}-{d:02d}", f"{m:02d}/{d:02d}/{y}", f"{m}/{d}/{y}", f"{m:02d}/{d:02d}/{y % 100:02d}",
             f"{MONTHS[m - 1]} {d}, {y}", f"{MONTHS[m - 1]} {d} {y}", f"{d} {MONTHS[m - 1]} {y}",
             f"{d} de {MESES[m - 1]} de {y}", f"{d} de {MESES[m - 1]} del {y}"]
    return any(f in t for f in forms)


def deadline_is_trustworthy(deadline, letter_text: str) -> bool:
    """Its quote is really in the letter AND its date is written in the letter (not calculated)."""
    return quote_found(deadline.source_quote, letter_text) and date_written_in(deadline.date, letter_text)
