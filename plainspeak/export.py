"""Makes a one-page summary file people can print, or send to a family member or caseworker."""

from datetime import date
from html import escape

from .checks import deadline_is_trustworthy, quote_found
from .schema import LetterAnalysis
from .ui_text import friendly_date, labels


def days_left(value: str, today: date | None = None) -> int | None:
    """Days from today until a YYYY-MM-DD date (negative if it has passed). None if not a date."""
    try:
        d = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return (d - (today or date.today())).days


def next_deadline(a: LetterAnalysis, today: date | None = None):
    """The soonest verified deadline that hasn't passed yet (or the latest passed one), with days left."""
    dated = [(days_left(d.date, today), d) for d in a.deadlines
             if days_left(d.date, today) is not None and deadline_is_trustworthy(d, a.original_text)]
    if not dated:
        return None
    upcoming = sorted([x for x in dated if x[0] >= 0], key=lambda x: x[0])
    return upcoming[0] if upcoming else max(dated, key=lambda x: x[0])


def summary_html(a: LetterAnalysis, lang_code: str) -> str:
    """A simple, printable HTML page with the summary, dates, steps and contacts."""
    t = labels(lang_code)
    direction = "rtl" if lang_code == "ar" else "ltr"
    deadlines = "".join(
        f"<li><b>{escape(friendly_date(d.date, lang_code) or t['no_date'])}</b> — {escape(d.what)}</li>"
        if deadline_is_trustworthy(d, a.original_text)
        else f"<li>{escape(d.what)} ({escape(t['estimated'])})</li>"
        for d in a.deadlines if quote_found(d.source_quote, a.original_text))
    steps = "".join(f"<li>☐ {escape(s.step)}</li>" for s in a.actions)
    money = "".join(f"<li><b>{escape(m.amount)}</b> — {escape(m.what)}</li>" for m in a.money)
    contacts = "".join(
        f"<li><b>{escape(c.name)}</b> — {escape(c.why)}"
        + (f"<br>📞 {escape(c.phone)}" if c.phone else "")
        + (f"<br>✉️ {escape(c.email)}" if c.email else "")
        + (f"<br>📍 {escape(c.address)}" if c.address else "") + "</li>"
        for c in a.contacts)

    def section(title: str, items: str) -> str:
        return f"<h2>{escape(title)}</h2><ul>{items}</ul>" if items else ""

    help_line = f"<p class='help'><b>{escape(t['talk_person'])}</b> {escape(a.help_reason)}</p>" if a.needs_human_help else ""
    return f"""<!DOCTYPE html>
<html lang="{lang_code}" dir="{direction}"><head><meta charset="utf-8">
<title>PlainSpeak — {escape(a.document_type)}</title>
<style>
 body {{font-family: system-ui, sans-serif; font-size: 18px; line-height: 1.6; max-width: 720px; margin: 2rem auto; padding: 0 1rem; color: #111;}}
 h1 {{font-size: 1.6rem;}} h2 {{font-size: 1.25rem; margin-top: 1.5rem; border-bottom: 2px solid #ccc;}}
 ul {{padding-inline-start: 1.2rem;}} li {{margin: .4rem 0;}}
 .summary {{background: #f3f4f6; padding: 1rem; border-radius: 8px;}}
 .help {{border: 2px solid #b91c1c; padding: .8rem; border-radius: 8px;}}
 small {{color: #555;}}
</style></head><body>
<h1>📬 {escape(a.document_type)}</h1>
<p><small>{escape(t['from'])}: {escape(a.sender)}</small></p>
<h2>{escape(t['means'])}</h2><p class="summary">{escape(a.summary)}</p>
{section(t['dates'], deadlines)}{section(t['todo'], steps)}{section(t['money'], money)}{section(t['contact'], contacts)}
{help_line}
<p><small>Made with PlainSpeak. This explains a letter; it is not legal or medical advice.</small></p>
</body></html>"""
