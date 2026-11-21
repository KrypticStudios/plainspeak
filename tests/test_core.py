"""Run with:  .venv/bin/pytest -q"""

import pytest

from plainspeak import calendar_export, checks, demo, history
from plainspeak.analyzer import AnalyzerError, analyze_letter
from plainspeak.schema import Deadline


@pytest.mark.parametrize("sample", list(demo.SAMPLES))
def test_demo_quotes_are_really_in_the_letter(sample):
    """Every quote in our demo answers must appear in the sample letter."""
    for lang in demo.demo_languages(sample):
        a = demo.demo_analysis(sample, lang)
        for item in [*a.deadlines, *a.actions, *a.money]:
            assert checks.quote_found(item.source_quote, a.original_text), item.source_quote


def test_made_up_quote_is_caught():
    letter = demo.sample_text("Hospital bill")
    assert not checks.quote_found("You owe $9,999 by tomorrow", letter)
    assert not checks.quote_found("", letter)


def test_small_ocr_differences_still_match():
    assert checks.quote_found("PATIENT RESPONSIBILITY:  $930.00", "patient responsibility: $930.00 due")


def test_summary_is_easier_to_read_than_letter():
    a = demo.demo_analysis("Eviction notice (rent)", "English")
    assert checks.reading_grade(a.summary) < checks.reading_grade(a.original_text)


def test_calendar_has_one_event_per_real_date():
    ics = calendar_export.deadlines_to_ics([
        Deadline(date="2026-12-04", what="Pay rent", source_quote="q"),
        Deadline(date="", what="No date", source_quote="q"),
        Deadline(date="soon", what="Bad date", source_quote="q"),
    ])
    assert ics.count(b"BEGIN:VEVENT") == 1
    assert b"20261204" in ics


def test_calendar_with_no_dates_returns_none():
    assert calendar_export.deadlines_to_ics([]) is None


def test_history_save_load_delete(tmp_path):
    db = tmp_path / "t.db"
    a = demo.demo_analysis("Hospital bill", "English")
    letter_id = history.save(a, "English", db_path=db)
    loaded, lang = history.load(letter_id, db_path=db)
    assert loaded == a and lang == "English"
    history.delete(letter_id, db_path=db)
    assert history.load(letter_id, db_path=db) is None


def test_no_api_key_gives_friendly_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(AnalyzerError, match="API key"):
        analyze_letter("English", text="hello")


def test_every_language_has_every_label():
    from plainspeak.speech import LANGUAGES
    from plainspeak.ui_text import KEYS, TEXT, friendly_date
    for code in LANGUAGES.values():
        assert len(TEXT[code]) == len(KEYS), code
        assert friendly_date("2026-12-04", code)
    assert friendly_date("not a date", "en") is None


def test_simulated_mistake_is_flagged():
    a = demo.with_simulated_mistake(demo.demo_analysis("Eviction notice (rent)", "English"))
    assert not checks.quote_found(a.deadlines[0].source_quote, a.original_text)
    assert all(checks.quote_found(d.source_quote, a.original_text) for d in a.deadlines[1:])
