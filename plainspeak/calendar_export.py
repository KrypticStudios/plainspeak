"""Turns deadlines into a calendar file (.ics) that works with Google, Apple and Outlook calendars."""

from datetime import date, datetime, timedelta, timezone

from icalendar import Alarm, Calendar, Event

from .schema import Deadline


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def deadlines_to_ics(deadlines: list[Deadline], title_prefix: str = "PlainSpeak") -> bytes | None:
    """Return .ics file bytes, or None if no deadline has a real date."""
    cal = Calendar()
    cal.add("prodid", "-//PlainSpeak//EvoHacks//EN")
    cal.add("version", "2.0")

    count = 0
    for i, d in enumerate(deadlines):
        day = parse_date(d.date)
        if not day:
            continue
        event = Event()
        event.add("uid", f"plainspeak-{day.isoformat()}-{i}@plainspeak")
        event.add("summary", f"{title_prefix}: {d.what}")
        event.add("dtstart", day)                      # all-day event
        event.add("dtend", day + timedelta(days=1))
        event.add("dtstamp", datetime.now(timezone.utc))
        event.add("description", f'From your letter: "{d.source_quote}"')

        reminder = Alarm()                             # pop-up reminder 2 days before
        reminder.add("action", "DISPLAY")
        reminder.add("description", d.what)
        reminder.add("trigger", timedelta(days=-2))
        event.add_component(reminder)

        cal.add_component(event)
        count += 1

    return cal.to_ical() if count else None
