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
