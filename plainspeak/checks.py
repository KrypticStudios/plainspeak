"""Safety checks we run on the AI's answer with plain Python (no AI).

AI can "hallucinate" (make things up). So for every deadline, step and amount, the AI must quote the
letter, and this file checks that:
  1. the quote is really in the letter (small differences in wording are allowed, but every NUMBER
     in the quote must match exactly, so "$930" can't quietly become "$980"),
  2. a deadline's date is really written in the letter, right in or next to its own sentence
     (not calculated by the AI, and not borrowed from somewhere else in the letter),
  3. a phone number we show as tap-to-call is really in the letter.
"""

import re
from datetime import date
from difflib import SequenceMatcher
from functools import lru_cache

import textstat

# ---------------------------------------------------------------- quotes


def _normalize(s: str) -> str:
    """Lowercase and squash spaces/punctuation so small differences in a photo reading don't matter."""
    s = s.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^\w$%./,:-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _numbers(s: str) -> list[str]:
    """Every number in a piece of text, e.g. '$1,450.00 by 12/04' -> ['1450.00', '12', '04']."""
    return [n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)]


@lru_cache(maxsize=4096)
def quote_location(quote: str, letter_text: str, threshold: float = 0.85) -> tuple[int, int] | None:
    """Where `quote` is in the letter, as (first word, last word) positions, or None if it isn't there."""
    q, words = _normalize(quote), _normalize(letter_text).split()
    if not q:
        return None
    q_words = q.split()
    n = len(q_words)
    text = " ".join(words)
    if q in text:  # exact match: find which word it starts at
        start = len(text[: text.index(q)].split())
        return start, start + n
    needed = _numbers(q)
    for i in range(max(1, len(words) - n + 1)):
        window = " ".join(words[i:i + n])
        if SequenceMatcher(None, q, window).ratio() >= threshold and \
                all(num in _numbers(window) for num in needed):   # wording may differ a little; numbers may not
            return i, i + n
    return None


def quote_found(quote: str, letter_text: str) -> bool:
    """True if `quote` appears in `letter_text` (exactly, or almost exactly with every number the same)."""
    return quote_location(quote, letter_text) is not None


# ---------------------------------------------------------------- dates

MONTH_NAMES = {
    1: ["january", "jan", "enero", "janvier", "janeiro", "enero"],
    2: ["february", "feb", "febrero", "février", "fevrier", "fevereiro", "pebrero"],
    3: ["march", "mar", "marzo", "mars", "março", "marco", "marso"],
    4: ["april", "apr", "abril", "avril", "abril"],
    5: ["may", "mayo", "mai", "maio"],
    6: ["june", "jun", "junio", "juin", "junho", "hunyo"],
    7: ["july", "jul", "julio", "juillet", "julho", "hulyo"],
    8: ["august", "aug", "agosto", "août", "aout", "agosto"],
    9: ["september", "sept", "sep", "septiembre", "setiembre", "septembre", "setembro", "setyembre"],
    10: ["october", "oct", "octubre", "octobre", "outubro", "oktubre"],
    11: ["november", "nov", "noviembre", "novembre", "novembro", "nobyembre"],
    12: ["december", "dec", "diciembre", "décembre", "decembre", "dezembro", "disyembre"],
}
# Month names in the other app languages (Russian uses the "of December" form in dates).
_MORE_MONTHS = {
    1: ["января", "январь", "जनवरी", "يناير", "كانون الثاني"],
    2: ["февраля", "февраль", "फ़रवरी", "फरवरी", "فبراير", "شباط"],
    3: ["марта", "март", "मार्च", "مارس", "آذار"],
    4: ["апреля", "апрель", "अप्रैल", "أبريل", "ابريل", "نيسان"],
    5: ["мая", "май", "मई", "مايو", "أيار"],
    6: ["июня", "июнь", "जून", "يونيو", "حزيران"],
    7: ["июля", "июль", "जुलाई", "يوليو", "تموز"],
    8: ["августа", "август", "अगस्त", "أغسطس", "آب"],
    9: ["сентября", "сентябрь", "सितंबर", "सितम्बर", "سبتمبر", "أيلول"],
    10: ["октября", "октябрь", "अक्टूबर", "أكتوبر", "تشرين الأول"],
    11: ["ноября", "ноябрь", "नवंबर", "नवम्बर", "نوفمبر", "تشرين الثاني"],
    12: ["декабря", "декабрь", "दिसंबर", "दिसम्बर", "ديسمبر", "كانون الأول"],
}
for _num, _names in _MORE_MONTHS.items():
    MONTH_NAMES[_num] = MONTH_NAMES[_num] + _names
# Arabic-Indic and Devanagari digits -> 0-9, so "٤ ديسمبر ٢٠٢٦" and "४ दिसंबर २०२६" are understood too.
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹०१२३४५६७८९", "0123456789" * 3)
_MONTH = {name: num for num, names in MONTH_NAMES.items() for name in names}
_MONTH_RE = "|".join(sorted(map(re.escape, _MONTH), key=len, reverse=True))
_DAY = r"(\d{1,2})(?:st|nd|rd|th|er)?"
_DATE_PATTERNS = [
    # 2026-12-04
    (re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)"), "ymd"),
    # 12/04/2026, 12/4/26, 12-04-2026 (US order, as on US letters)
    (re.compile(r"(?<![\d/])(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})(?![\d/])"), "mdy"),
    # December 4, 2026 / Dec. 4th 2026
    (re.compile(rf"\b({_MONTH_RE})\.?\s+{_DAY},?\s+(\d{{4}})\b"), "Mdy"),
    # 4 December 2026 / 4 de diciembre de 2026 / 4 décembre 2026 / 4 декабря 2026 г. / 4 दिसंबर 2026 / 4 ديسمبر 2026
    (re.compile(rf"(?<!\d){_DAY}\s+(?:de\s+)?({_MONTH_RE})\.?,?\s+(?:de\s+|del\s+)?(\d{{4}})(?!\d)"), "dMy"),
    # Chinese / Japanese 2026年12月4日 and Korean 2026년 12월 4일
    (re.compile(r"(?<!\d)(\d{4})\s*[年년]\s*(\d{1,2})\s*[月월]\s*(\d{1,2})\s*[日일]?"), "ymd"),
    # Vietnamese: ngày 4 tháng 12 năm 2026 (or "4 tháng 12, 2026")
    (re.compile(r"(?<!\d)(\d{1,2})\s+tháng\s+(\d{1,2})(?:\s*,|\s+năm)?\s+(\d{4})(?!\d)"), "dmy"),
    # Day-first numbers, as written in many countries: 04.12.2026
    (re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4})(?![\d.])"), "dmy"),
]


@lru_cache(maxsize=4096)
def dates_in(text: str) -> frozenset[date]:
    """Every real calendar date written in `text`."""
    t = " ".join(text.lower().translate(_DIGITS).split())
    found = set()
    for pattern, order in _DATE_PATTERNS:
        for m in pattern.finditer(t):
            try:
                if order == "ymd":
                    y, mo, d = int(m[1]), int(m[2]), int(m[3])
                elif order == "mdy":
                    mo, d, y = int(m[1]), int(m[2]), int(m[3])
                    y += 2000 if y < 100 else 0
                elif order == "dmy":
                    d, mo, y = int(m[1]), int(m[2]), int(m[3])
                elif order == "Mdy":
                    mo, d, y = _MONTH[m[1]], int(m[2]), int(m[3])
                else:
                    d, mo, y = int(m[1]), _MONTH[m[2]], int(m[3])
                found.add(date(y, mo, d))
            except (ValueError, KeyError):
                continue   # not a real date (e.g. month 13), ignore it
    return frozenset(found)


def _parse_iso(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def date_written_in(iso: str, letter_text: str) -> bool:
    """True if the date (YYYY-MM-DD) is actually written in the letter, in any common format.

    Letters often say "within 14 days after service" instead of a date. The AI may then work out a
    date itself, but that guess can be wrong (it depends on when the person got the letter), so we
    never put a calculated date in the countdown or the calendar.
    """
    d = _parse_iso(iso)
    return d is not None and d in dates_in(letter_text)


def deadline_is_trustworthy(deadline, letter_text: str, nearby_words: int = 15) -> bool:
    """The quote is really in the letter AND the date is written in that quote or right next to it.

    "Next to it" matters: a letter has many dates (the date it was sent, the service date...). The
    AI could pair a real sentence with the wrong one of those dates; this catches that.
    """
    d = _parse_iso(deadline.date)
    where = quote_location(deadline.source_quote, letter_text)
    if d is None or where is None:
        return False
    quoted_dates = dates_in(deadline.source_quote)
    if quoted_dates:                 # the sentence has a date: the deadline must be THAT date
        return d in quoted_dates
    words = _normalize(letter_text).split()
    start, end = max(0, where[0] - nearby_words), where[1] + nearby_words
    return d in dates_in(" ".join(words[start:end]))


# ---------------------------------------------------------------- phone numbers


def phone_in_letter(phone: str, letter_text: str) -> bool:
    """True if this phone number (any formatting) is written in the letter."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 3:
        return False
    if len(digits) <= 4:            # short numbers like 211 or 711: must appear as a whole number
        return re.search(rf"(?<!\d){digits}(?!\d)", letter_text) is not None
    for candidate in re.findall(r"\+?\d[\d\s().-]{5,}\d", letter_text):
        if re.sub(r"\D", "", candidate).endswith(digits[-10:]):
            return True
    return False


# ---------------------------------------------------------------- reading level


def reading_grade(text: str) -> float | None:
    """US school grade level needed to read `text` (Flesch-Kincaid). English only."""
    if len(text.split()) < 10:
        return None
    return round(max(0.0, textstat.flesch_kincaid_grade(text)), 1)


# ---------------------------------------------------------------- reply letters


def numbers_not_in_letter(text: str, letter_text: str, today: date | None = None) -> list[str]:
    """Dates, amounts and long numbers in `text` (an AI-written reply) that are NOT in the letter.

    Anything inside [brackets] is for the reader to fill in, so it is skipped. Today's date is allowed
    (a reply starts with it). Small numbers (days, months) are only checked as part of a full date."""
    text = re.sub(r"\[[^\]]*\]", " ", text)
    problems = []
    allowed_dates = set(dates_in(letter_text)) | ({today} if today else set())
    problems += [d.isoformat() for d in sorted(dates_in(text) - allowed_dates)]

    def value(n: str) -> float | None:
        try:
            return round(float(n.replace(",", "")), 2)
        except ValueError:
            return None
    # Money: every amount must be an amount (or number) written in the letter, exactly.
    letter_values = {value(n) for n in _numbers(letter_text)}
    for amount in dict.fromkeys(re.findall(r"\$\s?(\d[\d,]*(?:\.\d+)?)", text)):
        if value(amount) not in letter_values:
            problems.append("$" + amount)
    text = re.sub(r"\$\s?\d[\d,]*(?:\.\d+)?", " ", text)
    # Other long numbers (phone numbers, account or case numbers) must be in the letter too.
    in_letter = {n.lstrip("0") for n in _numbers(letter_text)}
    if today:
        in_letter |= {str(today.year), str(today.day), str(today.month)}
    for n in dict.fromkeys(_numbers(text)):
        n = n.rstrip(".")
        whole = n.split(".")[0]
        is_year = len(n) == 4 and n.isdigit() and 1990 <= int(n) <= 2100
        if (("." in n) or len(whole) >= 3) and not is_year and n.lstrip("0") not in in_letter:
            problems.append(n)
    return problems


# ---------------------------------------------------------------- urgency

# Letters where "urgent" stays urgent whatever the date: losing a home, a court case, immigration.
ALWAYS_SERIOUS = re.compile(r"\b(summons|evict|vacate|or quit|foreclos|immigration|uscis|biometric|deport|"
                            r"removal proceedings|desalojo|corte\b)")


def calibrated_urgency(analysis, today: date) -> str:
    """The AI's urgency, checked against the calendar by plain code.

    Our tests showed the AI often calls a letter "urgent" when its deadline is 3-4 weeks away: it is
    not reliable at counting days. So when the AI says "high", but every deadline we could VERIFY in
    the letter is more than 14 days from today, we show "medium" ("soon") instead. Housing, court and
    immigration letters are left as the AI said, and a deadline that already passed stays urgent.
    We only ever LOWER urgency here, never raise it; the countdown shows how close a date is.
    """
    if analysis.urgency != "high":
        return analysis.urgency
    text = analysis.original_text.lower()
    if ALWAYS_SERIOUS.search(text):
        return "high"
    ahead = []
    for d in analysis.deadlines:
        day = _parse_iso(d.date)
        if day and deadline_is_trustworthy(d, analysis.original_text):
            if day < today:
                return "high"            # a deadline already passed: that is urgent
            ahead.append((day - today).days)
    return "medium" if ahead and min(ahead) > 14 else "high"


def contacts_not_in_letter(text: str, letter_text: str) -> list[str]:
    """Email addresses, web links and phone numbers in `text` that are NOT in the letter.
    (A tricky letter could try to get a reply sent to a scammer's address.)"""
    low = letter_text.lower()
    found = [e for e in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text) if e.lower().rstrip(".") not in low]
    found += [u for u in re.findall(r"(?:https?://|www\.)\S+", text) if u.lower().rstrip(".,)") not in low]
    found += [p for p in re.findall(r"\+?\d[\d\s().-]{8,}\d", text)
              if len(re.sub(r"\D", "", p)) >= 10 and not phone_in_letter(p, letter_text)]
    return found
