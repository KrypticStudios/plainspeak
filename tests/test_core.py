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
    letter_id = history.save(a, "English", owner="alice", db_path=db)
    loaded, lang = history.load(letter_id, owner="alice", db_path=db)
    assert loaded == a and lang == "English"
    history.delete(letter_id, owner="alice", db_path=db)
    assert history.load(letter_id, owner="alice", db_path=db) is None


def test_visitors_cannot_see_each_others_letters(tmp_path):
    db = tmp_path / "t.db"
    a = demo.demo_analysis("Hospital bill", "English")
    letter_id = history.save(a, "English", owner="alice", db_path=db)
    assert history.list_recent(owner="bob", db_path=db) == []
    assert history.load(letter_id, owner="bob", db_path=db) is None
    history.delete(letter_id, owner="bob", db_path=db)            # bob can't delete it either
    assert history.load(letter_id, owner="alice", db_path=db) is not None


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


def test_countdown_and_next_deadline():
    from datetime import date
    from plainspeak.export import days_left, next_deadline
    a = demo.demo_analysis("Food benefits renewal", "English")
    days, d = next_deadline(a, today=date(2026, 11, 21))
    assert d.date == "2026-12-09" and days == 18
    days, d = next_deadline(a, today=date(2026, 12, 10))   # interview passed -> next is the form
    assert d.date == "2026-12-15"
    assert days_left("nope") is None


def test_fake_deadline_never_becomes_next_deadline():
    from datetime import date
    from plainspeak.export import next_deadline
    a = demo.with_simulated_mistake(demo.demo_analysis("Eviction notice (rent)", "English"))
    _, d = next_deadline(a, today=date(2026, 11, 21))
    assert d.date == "2026-12-04"


def test_printable_summary_is_escaped_and_translated():
    from plainspeak.export import summary_html
    a = demo.demo_analysis("Eviction notice (rent)", "Español (Spanish)")
    page = summary_html(a.model_copy(update={"sender": "<script>x</script>"}), "es")
    assert "Qué hacer" in page and "<script>x" not in page


def test_photo_is_rotated_and_shrunk():
    from io import BytesIO
    from PIL import Image
    from plainspeak.images import prepare_image
    buf = BytesIO()
    Image.new("RGBA", (4000, 3000), "white").save(buf, format="PNG")
    data, mime = prepare_image(buf.getvalue(), "image/png")
    img = Image.open(BytesIO(data))
    assert mime == "image/jpeg" and max(img.size) == 2000
    assert prepare_image(b"%PDF-1.4", "application/pdf") == (b"%PDF-1.4", "application/pdf")


def test_demo_question_quotes_are_in_the_letter():
    for sample in demo.SAMPLES:
        for lang in demo.demo_languages(sample):
            a = demo.demo_analysis(sample, lang)
            for q in demo.suggested_questions(a):
                ans = demo.demo_answer(a, q)
                for quote in ans.source_quotes:
                    assert checks.quote_found(quote, a.original_text), quote
    assert demo.suggested_questions(demo.demo_analysis("Hospital bill", "English"))
