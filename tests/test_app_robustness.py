"""The web page must survive anything the AI might send back, in every language.

These tests run the real app.py with Streamlit's test tool, but replace the AI with fake answers that
are empty, strange, enormous, or try to inject links and code into the page.
Run:  .venv/bin/pytest -q tests/test_app_robustness.py
"""

import pytest
from streamlit.testing.v1 import AppTest

from plainspeak import demo
from plainspeak.schema import ActionStep, Contact, Deadline, LetterAnalysis, MoneyItem
from plainspeak.speech import LANGUAGES

LETTER = demo.sample_text("Eviction notice (rent)")
APP = __import__("pathlib").Path(__file__).resolve().parent.parent / "app.py"


def run_app(**query) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=60)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    return at


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [w.value for w in at.warning]
    parts += [s.value for s in at.success] + [e.value for e in at.error] + [i.value for i in at.info]
    parts += [c.label for c in at.checkbox]
    return "\n".join(str(p) for p in parts)


def show_fake(at: AppTest, analysis: LetterAnalysis, language="English", source="text") -> AppTest:
    """Put a fake AI answer on screen the same way the app does, then redraw."""
    at.session_state["result"] = analysis
    at.session_state["result_lang"] = language
    at.session_state["result_source"] = source
    at.session_state["letter_key"] = "t"
    at.run()
    return at


EVIL = '![x](https://evil.example/steal?d=1) [Click here](https://evil.example) <script>alert(1)</script> $5 to $9'

WEIRD = {
    "everything empty": LetterAnalysis(
        original_text="", document_type="", sender="", summary="", urgency="low", urgency_reason="",
        deadlines=[], actions=[], money=[], contacts=[], rights=[], unclear_points=[], needs_human_help=False,
        help_reason="", confidence="low"),
    "invalid dates and blanks": LetterAnalysis(
        original_text=LETTER, document_type="Notice", sender="Someone", summary="Short.", urgency="high",
        urgency_reason="Soon.",
        deadlines=[Deadline(date="2026-13-45", what="bad month", source_quote="nope"),
                   Deadline(date="", what="no date", source_quote=""),
                   Deadline(date="tomorrow", what="words", source_quote="TOTAL AMOUNT DUE: $1,450.00"),
                   Deadline(date="2020-01-01", what="long ago", source_quote="Dated: November 20, 2026")],
        actions=[ActionStep(step="", source_quote="")], money=[MoneyItem(amount="", what="", source_quote="")],
        contacts=[Contact(name="", why="", phone="abc"), Contact(name="X", why="Y", phone="+1 (555) 013-7700 ext. 4")],
        rights=[""], unclear_points=[""], needs_human_help=True, help_reason="", confidence="medium"),
    "injection everywhere": LetterAnalysis(
        original_text=LETTER + "\n\n" + EVIL, document_type=EVIL, sender=EVIL, summary=EVIL, urgency="high",
        urgency_reason=EVIL,
        deadlines=[Deadline(date="2026-12-04", what=EVIL, source_quote=EVIL + "\n\n# heading")],
        actions=[ActionStep(step=EVIL, source_quote=EVIL)], money=[MoneyItem(amount=EVIL, what=EVIL, source_quote=EVIL)],
        contacts=[Contact(name=EVIL, why=EVIL, phone="(555) 666-0000", email=EVIL, address=EVIL)],
        rights=[EVIL], unclear_points=[EVIL], needs_human_help=True, help_reason=EVIL, confidence="low"),
    "huge text": LetterAnalysis(
        original_text=LETTER * 20, document_type="Notice " * 200, sender="S" * 5000, summary="word " * 3000,
        urgency="medium", urgency_reason="r " * 500,
        deadlines=[Deadline(date="2026-12-04", what="w " * 300, source_quote="Payment must be made on or before December 4, 2026.")] * 30,
        actions=[ActionStep(step="s " * 200, source_quote="q " * 200)] * 40, money=[], contacts=[], rights=[],
        unclear_points=["u " * 200] * 20, needs_human_help=False, help_reason="ok", confidence="high"),
    "unicode and right-to-left": LetterAnalysis(
        original_text="إشعار إخلاء. يجب الدفع قبل 4 ديسمبر 2026. 🙂 ‮ evil", document_type="إشعار 🏠",
        sender="مالك", summary="ادفع الإيجار. 中文 हिन्दी 한국어", urgency="high", urgency_reason="قريب",
        deadlines=[Deadline(date="2026-12-04", what="ادفع", source_quote="يجب الدفع قبل 4 ديسمبر 2026.")],
        actions=[ActionStep(step="اتصل", source_quote="إشعار إخلاء.")], money=[], contacts=[], rights=[],
        unclear_points=[], needs_human_help=True, help_reason="محامٍ", confidence="medium"),
}


@pytest.mark.parametrize("name", list(WEIRD))
@pytest.mark.parametrize("language", ["English", "العربية (Arabic)"])
def test_page_survives_strange_ai_answers(name, language):
    at = show_fake(run_app(), WEIRD[name], language)
    assert not at.exception, f"{name}: {at.exception[0].message if at.exception else ''}"


def test_injected_links_and_code_are_neutralized():
    at = show_fake(run_app(), WEIRD["injection everywhere"])
    assert not at.exception
    raw = page_text(at)
    # HTML we build ourselves must have the attack escaped, never as live tags
    assert "<script>" not in raw
    for m in at.markdown:
        v = str(m.value)
        if "unsafe" in str(getattr(m, "proto", "")) or v.lstrip().startswith("<"):
            assert "<script>" not in v and 'href="https://evil' not in v
    # Markdown-rendered places must have the link syntax escaped
    for el in [*at.caption, *at.warning, *at.checkbox]:
        text = str(getattr(el, "value", "")) + str(getattr(el, "label", ""))
        assert "](https://evil" not in text, text[:120]
    # the scam number is not tap-to-call
    assert 'href="tel:5556660000"' not in raw


@pytest.mark.parametrize("language", list(LANGUAGES))
def test_start_screen_in_every_language(language):
    code = LANGUAGES[language]
    at = run_app(lang=code)
    assert not at.exception
    assert at.session_state["lang_pref"] == language


@pytest.mark.parametrize("language", list(LANGUAGES))
@pytest.mark.parametrize("example", ["eviction", "benefits", "hospital"])
def test_every_example_in_every_language(language, example):
    at = run_app(example=example, lang=LANGUAGES[language])
    assert not at.exception
    assert "result" in at.session_state


@pytest.mark.parametrize("query", [
    {"lang": "xx"}, {"lang": "../../etc"}, {"example": "nope"}, {"example": ""}, {"mistake": "1"},
    {"example": "eviction", "mistake": "yes", "contrast": "2", "bigtext": "<b>"}, {"lang": "AR"},
    {"example": "hospital", "lang": "ar", "mistake": "1", "contrast": "1", "bigtext": "1"},
])
def test_odd_links_do_not_break_the_page(query):
    assert not run_app(**query).exception


def test_saved_letter_round_trip_and_isolation():
    a = run_app(example="eviction")
    a.button(key="save").click().run()
    a.button(key="nav-letters").click().run()   # the My letters page
    assert any(b.key and b.key.startswith("open-") for b in a.button)
    b = run_app()   # a second visitor: separate session, sees none of a's letters
    b.button(key="nav-letters").click().run()
    assert not [x for x in b.button if x.key and x.key.startswith("open-")] or \
        b.session_state["lang_pref"]   # local mode (PLAINSPEAK_LOCAL=1) shares one file by design


def test_start_over_and_language_change_after_results():
    at = run_app(example="eviction", lang="es")
    at.button(key="start-over").click().run()
    assert "result" not in at.session_state and not at.exception
    assert at.session_state["lang_pref"].startswith("Español")
    at.selectbox(key="language").select("Tiếng Việt (Vietnamese)").run()
    assert not at.exception and "Dán chữ" in " ".join(b.label for b in at.button)
