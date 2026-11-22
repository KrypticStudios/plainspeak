"""What does a user see when things go wrong? Every failure must give a friendly message in their language,
never a crash or a technical error. The AI is replaced by fakes, so these tests cost nothing.
Run:  .venv/bin/pytest -q tests/test_failures.py
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import plainspeak.analyzer as analyzer
from plainspeak import demo
from plainspeak.schema import QuestionAnswer
from plainspeak.ui_start import ui
from plainspeak.ui_text import labels

APP = str(Path(__file__).resolve().parent.parent / "app.py")
LETTER = demo.sample_text("Eviction notice (rent)")


def paste_and_explain(at: AppTest, text: str = LETTER) -> AppTest:
    at.text_area(key="pasted").input(text).run()
    at.button(key="go-text").click().run()
    return at


def shown(at: AppTest) -> str:
    return " ".join([e.value for e in at.error] + [w.value for w in at.warning] + [i.value for i in at.info])


@pytest.mark.parametrize("kind", ["busy", "limit", "setup", "unreadable", "too_long", "empty", "other", "something_new"])
@pytest.mark.parametrize("lang", ["en", "es", "ar"])
def test_ai_failures_show_a_friendly_translated_message(monkeypatch, kind, lang):
    def failing(*args, **kwargs):
        raise analyzer.AnalyzerError("technical detail the user should never see", kind)
    monkeypatch.setattr(analyzer, "analyze_letter", failing)
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["lang"] = lang
    at.run()
    paste_and_explain(at)
    text = shown(at)
    assert not at.exception
    assert "technical detail" not in text and "GEMINI" not in text
    expected = ui(lang).get("err_" + kind, ui(lang)["err_other"])
    assert expected in text
    if kind in ("limit", "busy", "setup", "other", "something_new"):
        # The AI can't help right now: plain code still shows the dates and amounts from the pasted letter
        assert any(ui(lang)["basic_title"] in m.value for m in at.markdown)
        assert any("December" in m.value or "2026" in m.value for m in at.markdown)
        [b for b in at.button if b.key == "start-over"][0].click().run()
    assert at.text_area(key="pasted").value.startswith("SAMPLE LETTER")   # what they pasted is not lost


def test_too_many_questions_are_slowed_down_politely(monkeypatch):
    calls = []

    def fake_ask(letter, question, language):
        calls.append(question)
        return QuestionAnswer(answer="The letter doesn't say.", answered_from_letter=False, source_quotes=[], who_to_ask="")
    monkeypatch.setattr(analyzer, "ask_question", fake_ask)
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "eviction"
    at.run()
    for i in range(8):
        at.text_input[0].input(f"Question number {i}?")            # typed text is sent together with "Ask"
        [b for b in at.button if b.label == "Ask"][0].click().run()
    assert not at.exception
    assert len(calls) == 6                                   # the limit is 6 per 10 minutes
    assert ui("en")["slow_down"] in shown(at)


def test_question_failure_is_friendly(monkeypatch):
    def failing(*a, **k):
        raise analyzer.AnalyzerError("boom", "busy")
    monkeypatch.setattr(analyzer, "ask_question", failing)
    monkeypatch.setattr(analyzer, "has_api_key", lambda: True)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "eviction"
    at.query_params["lang"] = "es"
    at.run()
    at.text_input[0].input("¿Algo?")
    [b for b in at.button if b.label == labels("es")["ask_button"]][0].click().run()
    assert not at.exception and ui("es")["err_busy"] in shown(at) and "boom" not in shown(at)


def test_read_aloud_failure_is_friendly(monkeypatch):
    import plainspeak.speech as speech
    monkeypatch.setattr(speech, "text_to_mp3", lambda text, lang: None)   # e.g. the speech service is down
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["example"] = "eviction"
    at.run()
    at.button(key="tts").click().run()
    assert not at.exception and ui("en")["tts_failed"] in shown(at)
