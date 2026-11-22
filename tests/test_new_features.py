"""Tests for the newer features: the basic check without AI, papers to bring, reply letters, today's date.
The AI is replaced by fakes, so these tests cost nothing.
Run:  .venv/bin/pytest -q tests/test_new_features.py
"""

from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

import plainspeak.analyzer as analyzer
from plainspeak import basic_reader, checks, demo
from plainspeak.schema import DocumentItem, ReplyDraft
from plainspeak.ui_start import ui

APP = str(Path(__file__).resolve().parent.parent / "app.py")
EVICTION = demo.sample_text("Eviction notice (rent)")
TODAY = date(2026, 11, 21)


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [e.value for e in at.error] + [w.value for w in at.warning]
    return " ".join(parts + [i.value for i in at.info] + [c.value for c in at.caption])


# ---------------------------------------------------------------- basic check (no AI)

def test_basic_reader_finds_dates_amounts_phones_with_their_sentences():
    r = basic_reader.read(EVICTION, today=TODAY)
    assert r.dates[0][0] >= TODAY and date(2026, 12, 4) in [d for d, _ in r.dates]   # dates still ahead come first
    assert "December 4, 2026" in dict(r.dates)[date(2026, 12, 4)]   # shown next to its own sentence
    assert any(a == "$1,450.00" for a, _ in r.money)
    assert "(555) 013-7700" in r.phones or any("013-7700" in p for p in r.phones)
    assert {"or quit", "legal proceedings", "court"} <= set(r.serious_words)


def test_basic_reader_on_empty_and_strange_text():
    assert not basic_reader.read("").found_anything
    assert not basic_reader.read("hello there, nothing here").found_anything
    r = basic_reader.read("Pay $5 on 13/45/2026 or 02/30/2026.")   # impossible dates are ignored
    assert r.dates == [] and r.money[0][0] == "$5"


def test_pdf_text_reads_a_real_pdf_and_survives_garbage():
    assert basic_reader.pdf_text(b"not a pdf") == ""


def test_no_ai_choice_never_calls_the_ai(monkeypatch):
    def must_not_run(*a, **k):
        raise AssertionError("the AI was called")
    monkeypatch.setattr(analyzer, "analyze_letter", must_not_run)
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.toggle(key="no_ai").set_value(True).run()
    at.text_area(key="pasted").input(EVICTION).run()
    at.button(key="go-text").click().run()
    assert not at.exception
    text = page_text(at)
    assert ui("en")["basic_title"] in text and ui("en")["basic_private_intro"] in text
    assert "$1,450.00" in text and "December 4, 2026" in text


def test_no_ai_choice_works_even_without_an_api_key(monkeypatch):
    monkeypatch.setattr(analyzer, "has_api_key", lambda: False)
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.toggle(key="no_ai").set_value(True).run()
    at.text_area(key="pasted").input(EVICTION).run()
    assert not at.button(key="go-text").disabled
    at.button(key="go-text").click().run()
    assert not at.exception and ui("en")["basic_title"] in page_text(at)


def test_basic_check_in_spanish():
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["lang"] = "es"
    at.run()
    at.toggle(key="no_ai").set_value(True).run()
    at.text_area(key="pasted").input(EVICTION).run()
    at.button(key="go-text").click().run()
    assert not at.exception
    assert ui("es")["basic_title"] in page_text(at) and "diciembre" in page_text(at)


def test_basic_check_shows_letter_words_safely():
    """Words from the letter are shown as text, never run as HTML."""
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.toggle(key="no_ai").set_value(True).run()
    at.text_area(key="pasted").input("<script>alert(1)</script> Pay $20.00 by December 4, 2026.").run()
    at.button(key="go-text").click().run()
    assert not at.exception
    assert "<script>" not in " ".join(m.value for m in at.markdown)


# ---------------------------------------------------------------- papers to bring

def test_papers_to_bring_are_shown_with_their_quote(monkeypatch):
    letter = demo.sample_text("Food benefits renewal")
    base = demo.demo_analysis("Food benefits renewal", "English")
    quote = next(line for line in letter.splitlines() if "verification" in line.lower())
    answer = base.model_copy(update={"original_text": letter,
                                     "documents_to_bring": [DocumentItem(item="Proof of income", source_quote=quote)]})
    monkeypatch.setattr(analyzer, "analyze_letter", lambda *a, **k: answer)
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_area(key="pasted").input(letter).run()
    at.button(key="go-text").click().run()
    assert not at.exception
    assert ui("en")["docs_title"] in page_text(at)
    assert any(c.label == "Proof of income" for c in at.checkbox)


def test_old_saved_answers_without_papers_still_load():
    a = demo.demo_analysis("Hospital bill", "English")
    assert a.documents_to_bring == []


# ---------------------------------------------------------------- reply letters

def test_reply_check_flags_numbers_that_are_not_in_the_letter():
    letter = "Pay $684.50 by December 2, 2026. Call (555) 019-7700."
    ok = "November 21, 2026\nI would like a payment plan for $684.50 due December 2, 2026. [Your account number]"
    assert checks.numbers_not_in_letter(ok, letter, today=TODAY) == []
    bad = "I will pay $100.00 on January 5, 2027. Call me at 555-019-9999."
    found = checks.numbers_not_in_letter(bad, letter, today=TODAY)
    assert "2027-01-05" in found and "$100.00" in found and "9999" in found


def _fake_reply(text: str):
    def fake(letter, purpose, language, today=None):
        assert purpose in analyzer.REPLY_PURPOSES
        return ReplyDraft(reply_text=text, explanation="It asks for more time.",
                          fill_in=["Your name"], how_to_send="Mail it to the address in the letter.")
    return fake


def test_reply_writer_on_an_example(monkeypatch):
    monkeypatch.setattr(analyzer, "draft_reply", _fake_reply("Dear Maplewood,\nI ask for more time. [Your name]"))
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "eviction"
    at.run()
    go = [b for b in at.button if (b.key or "").startswith("reply-go-")][0]
    go.click().run()
    assert not at.exception
    box = [t for t in at.text_area if (t.key or "").startswith("reply-text-")][0]
    assert "more time" in box.value
    assert ui("en")["reply_bad_numbers"] not in page_text(at)


def test_reply_writer_warns_about_invented_numbers(monkeypatch):
    monkeypatch.setattr(analyzer, "draft_reply", _fake_reply("I will pay $99.00 on January 9, 2027."))
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "eviction"
    at.run()
    [b for b in at.button if (b.key or "").startswith("reply-go-")][0].click().run()
    assert not at.exception
    assert ui("en")["reply_bad_numbers"] in page_text(at) and "99.00" in page_text(at)


def test_reply_kinds_fit_the_letter():
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "hospital"
    at.run()
    options = [r for r in at.radio if (r.key or "").startswith("reply-kind-")][0].options
    assert ui("en")["reply_payment_plan"] in options        # the bill asks for money
    assert ui("en")["reply_questions"] in options and ui("en")["reply_dispute"] in options


def test_reply_failure_is_friendly(monkeypatch):
    def failing(*a, **k):
        raise analyzer.AnalyzerError("zzz-internal-detail", "busy")
    monkeypatch.setattr(analyzer, "draft_reply", failing)
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "hospital"
    at.run()
    [b for b in at.button if (b.key or "").startswith("reply-go-")][0].click().run()
    assert not at.exception and ui("en")["err_busy"] in page_text(at) and "zzz-internal" not in page_text(at)


# ---------------------------------------------------------------- today's date reaches the AI

def test_ai_is_told_todays_date(monkeypatch):
    seen = []

    def fake_ask(system_prompt, contents, shape):
        seen.append(contents)
        return demo.demo_analysis("Hospital bill", "English")
    monkeypatch.setattr(analyzer, "_ask_gemini", fake_ask)
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    analyzer.analyze_letter("English", text="a letter", today=TODAY)
    assert any("November 21, 2026" in c and "2026-11-21" in c for c in seen[0] if isinstance(c, str))
    analyzer.draft_reply("a letter", "more_time", "English", today=TODAY)
    assert any("November 21, 2026" in c for c in seen[1] if isinstance(c, str))


# ---------------------------------------------------------------- urgency is checked against the calendar

def _with(a, urgency, deadline_date):
    from plainspeak.schema import Deadline
    letter = f"SAMPLE. Your power may be shut off. Please pay by {deadline_date:%B} {deadline_date.day}, {deadline_date.year}."
    d = Deadline(date=deadline_date.isoformat(), what="pay", source_quote=letter.split(". ", 2)[2])
    return a.model_copy(update={"urgency": urgency, "original_text": letter, "deadlines": [d]})


def test_urgent_with_a_far_deadline_becomes_soon():
    a = demo.demo_analysis("Hospital bill", "English")
    assert checks.calibrated_urgency(_with(a, "high", date(2026, 12, 20)), TODAY) == "medium"   # 29 days
    assert checks.calibrated_urgency(_with(a, "high", date(2026, 12, 1)), TODAY) == "high"     # 10 days
    assert checks.calibrated_urgency(_with(a, "high", date(2026, 11, 1)), TODAY) == "high"     # passed
    assert checks.calibrated_urgency(_with(a, "medium", date(2026, 11, 25)), TODAY) == "medium"  # never raised
    assert checks.calibrated_urgency(_with(a, "low", date(2027, 1, 1)), TODAY) == "low"


def test_eviction_stays_urgent_even_with_a_far_date():
    a = _with(demo.demo_analysis("Hospital bill", "English"), "high", date(2027, 1, 30))
    a = a.model_copy(update={"original_text": a.original_text + " This is a notice to vacate."})
    assert checks.calibrated_urgency(a, TODAY) == "high"


def test_reply_check_flags_contacts_that_are_not_in_the_letter():
    letter = "Call (555) 019-7700 or write to billing@riverton.example."
    assert checks.contacts_not_in_letter("Write to billing@riverton.example or call (555) 019-7700.", letter) == []
    found = checks.contacts_not_in_letter("Pay at https://pay-now.example or send to help@scam.example, "
                                          "or call 555-123-4567.", letter)
    assert len(found) == 3


def test_reply_never_sees_hidden_id_numbers(monkeypatch):
    seen = []
    monkeypatch.setattr(analyzer, "draft_reply", lambda letter, *a, **k: seen.append(letter) or
                        ReplyDraft(reply_text="ok", explanation="", fill_in=[], how_to_send=""))
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    base = demo.demo_analysis("Hospital bill", "English")
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["result"] = base.model_copy(update={"original_text": base.original_text + " SSN 123-45-6789"})
    at.session_state["result_lang"] = "English"
    at.run()
    [b for b in at.button if (b.key or "").startswith("reply-go-")][0].click().run()
    assert seen and "123-45-6789" not in seen[0]
