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


def test_redaction_hides_ids_but_keeps_what_we_need():
    from plainspeak.privacy import HIDDEN, redact
    text = ("SSN 123-45-6789, card 4111 1111 1111 1111, Account Number: RGH-123456, Case #00-1234567. "
            "Call (555) 014-2290. Pay $1,450.00 by December 4, 2026. A caseworker from Customer Service will call.")
    out, n = redact(text)
    assert n == 4
    for secret in ("123-45-6789", "4111", "RGH-123456", "00-1234567"):
        assert secret not in out
    for keep in ("(555) 014-2290", "$1,450.00", "December 4, 2026", "caseworker", "Customer Service"):
        assert keep in out
    assert out.count(HIDDEN) == 4


def test_rate_limiter():
    from plainspeak.privacy import RateLimiter
    rl = RateLimiter(limit=2, window=60)
    assert rl.allow("a", now=0) and rl.allow("a", now=1)
    assert not rl.allow("a", now=2)          # third try within a minute is blocked
    assert rl.allow("b", now=2)              # other visitors aren't affected
    assert rl.allow("a", now=62)             # allowed again after the window


def test_upload_checks():
    from io import BytesIO
    from PIL import Image
    from plainspeak.privacy import check_upload
    buf = BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="PNG")
    assert check_upload(buf.getvalue(), "image/png") is None
    assert check_upload(b"%PDF-1.7 ...", "application/pdf") == "pdf_unreadable"
    assert check_upload(b"<script>evil</script>", "image/png") == "bad_image"
    assert check_upload(b"MZ\x90\x00", "application/pdf") == "not_pdf"
    assert check_upload(b"x" * (11 * 1024 * 1024), "image/png") == "too_big"


def test_session_store_is_per_visitor_and_deletable():
    a = demo.demo_analysis("Hospital bill", "English")
    alice, bob = history.SessionStore({}), history.SessionStore({})
    i = alice.save(a, "English")
    assert alice.load(i) == (a, "English") and bob.list_recent() == []
    alice.delete_all()
    assert alice.list_recent() == []


def test_calculated_dates_are_not_trusted():
    from plainspeak.checks import date_written_in, deadline_is_trustworthy
    from plainspeak.export import next_deadline
    letter = "You must pay within fourteen (14) days after service. Date of notice: November 17, 2026."
    assert date_written_in("2026-11-17", letter)
    assert not date_written_in("2026-12-01", letter)            # 14 days later: worked out, not written
    assert date_written_in("2026-12-03", "Cita: 3 de diciembre de 2026 a las 2:00 p. m.")
    assert date_written_in("2026-12-21", "NO LATER THAN 12/21/2026.")
    guessed = Deadline(date="2026-12-01", what="Pay or move out",
                       source_quote="You must pay within fourteen (14) days after service.")
    assert not deadline_is_trustworthy(guessed, letter)
    a = demo.demo_analysis("Eviction notice (rent)", "English")
    fake = a.model_copy(update={"deadlines": [guessed], "original_text": letter})
    assert next_deadline(fake) is None                           # no countdown for a guessed date
    assert calendar_export.deadlines_to_ics([d for d in fake.deadlines
                                             if deadline_is_trustworthy(d, letter)]) is None


def test_pdf_page_limit():
    from io import BytesIO
    from PIL import Image
    from plainspeak.privacy import check_upload, pdf_page_count

    def pdf(n):
        buf = BytesIO()
        pages = [Image.new("RGB", (50, 50), "white") for _ in range(n)]
        pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
        return buf.getvalue()

    assert pdf_page_count(pdf(1)) == 1 and pdf_page_count(pdf(3)) == 3
    assert check_upload(pdf(5), "application/pdf") is None
    assert check_upload(pdf(6), "application/pdf") == "too_many_pages"


def test_monitor_records_kinds_not_content(caplog):
    import logging
    from plainspeak import monitor
    with caplog.at_level(logging.INFO, logger="plainspeak"):
        monitor.record("letter_ok")
        monitor.record("Maria Lopez owes $1,450")        # anything unexpected is stored as a fixed word
    assert "Maria" not in caplog.text and "1,450" not in caplog.text
    assert monitor.counts()["ai_other"] >= 1
    assert monitor.kind_of_error("busy") == "ai_busy" and monitor.kind_of_error("limit") == "ai_limit"
    assert monitor.kind_of_error("setup") == "ai_key" and monitor.kind_of_error("unreadable") == "ai_other"


def test_broken_and_giant_pictures_are_refused():
    from io import BytesIO
    from PIL import Image
    from plainspeak.privacy import check_upload
    buf = BytesIO()
    Image.new("RGB", (800, 600), "white").save(buf, format="JPEG")
    good = buf.getvalue()
    assert check_upload(good, "image/jpeg") is None
    assert check_upload(good[: len(good) // 2], "image/jpeg")         # half a photo (download cut off)
    giant = BytesIO()
    Image.new("1", (30_000, 30_000)).save(giant, format="PNG")        # small file, huge picture
    assert check_upload(giant.getvalue(), "image/png") == "too_large"


def test_start_screen_text_complete_in_every_language():
    from plainspeak.speech import LANGUAGES
    from plainspeak.ui_start import UI, ui
    for code in LANGUAGES.values():
        missing = set(UI["en"]) - set(UI[code])
        assert not missing, (code, missing)
        assert "{n}" in ui(code)["ids_hidden"]


class _FakeModels:
    """Pretends to be Google: the main key is out of quota, the backup key works."""
    def __init__(self, key, calls):
        self.key, self.calls = key, calls

    def generate_content(self, model, contents, config):
        from google.genai import errors
        self.calls.append((self.key, model))
        if self.key == "MAIN":
            raise errors.ClientError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}})
        answer = demo.demo_analysis("Hospital bill", "English")
        return type("R", (), {"parsed": answer, "text": answer.model_dump_json()})()


def _fake_google(monkeypatch, calls):
    from google import genai

    class FakeClient:
        def __init__(self, api_key, http_options=None):
            self.models = _FakeModels(api_key, calls)
    monkeypatch.setattr(genai, "Client", FakeClient)


def test_backup_key_takes_over_when_main_key_is_out_of_quota(monkeypatch):
    calls = []
    _fake_google(monkeypatch, calls)
    monkeypatch.setenv("GEMINI_API_KEY", "MAIN")
    monkeypatch.setenv("GEMINI_BACKUP_API_KEY", "BACKUP")
    result = analyze_letter("English", text="some letter")
    assert result.document_type.startswith("Hospital bill")
    assert calls[-1][0] == "BACKUP" and any(k == "MAIN" for k, _ in calls)


def test_without_backup_key_the_limit_message_is_friendly(monkeypatch):
    calls = []
    _fake_google(monkeypatch, calls)
    monkeypatch.setenv("GEMINI_API_KEY", "MAIN")
    monkeypatch.delenv("GEMINI_BACKUP_API_KEY", raising=False)
    with pytest.raises(AnalyzerError, match="free AI limit"):
        analyze_letter("English", text="some letter")


def test_share_message_and_links():
    from datetime import date
    from urllib.parse import unquote
    from plainspeak.export import share_links, share_text
    a = demo.demo_analysis("Eviction notice (rent)", "Español (Spanish)")
    msg = share_text(a, "es", today=date(2026, 11, 21))
    assert "viernes, 4 de diciembre de 2026" in msg and "(555) 013-7700" in msg
    assert "Maria" not in msg                       # the person's name from the letter isn't sent
    links = share_links(msg, "PlainSpeak")
    assert links["WhatsApp"].startswith("https://wa.me/?text=") and unquote(links["WhatsApp"]).endswith(
        "https://plainspeak.streamlit.app)")
    assert links["SMS"].startswith("sms:") and links["Email"].startswith("mailto:?subject=")


def test_whole_letter_limits():
    from io import BytesIO
    from PIL import Image
    from plainspeak.privacy import check_letter

    def pdf(n):
        buf = BytesIO()
        pages = [Image.new("RGB", (50, 50), "white") for _ in range(n)]
        pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
        return buf.getvalue()
    assert check_letter([(pdf(3), "application/pdf"), (b"img", "image/jpeg")]) == []
    assert check_letter([(pdf(3), "application/pdf"), (pdf(3), "application/pdf")]) == ["too_many_pages"]


def test_pdf_with_bookmarks_is_not_miscounted():
    from io import BytesIO
    from PIL import Image
    from pypdf import PdfWriter
    from plainspeak.privacy import pdf_page_count
    buf = BytesIO()
    Image.new("RGB", (50, 50), "white").save(buf, format="PDF")
    w = PdfWriter(clone_from=BytesIO(buf.getvalue()))
    parent = w.add_outline_item("Chapter", 0)
    for i in range(9):
        w.add_outline_item(f"Part {i}", 0, parent=parent)   # adds "/Count 9" to the outline
    out = BytesIO()
    w.write(out)
    assert pdf_page_count(out.getvalue()) == 1


def test_new_checks_catch_subtle_mistakes():
    from plainspeak.checks import date_written_in, deadline_is_trustworthy, phone_in_letter, quote_found
    letter = demo.sample_text("Eviction notice (rent)")
    assert not date_written_in("2026-12-04", "pay by 14 december 2026")      # 14 is not 4
    assert not date_written_in("2026-01-04", "due 11/4/2026")
    assert not date_written_in("2026-13-01", "anything")                       # no crash on a bad month
    assert date_written_in("2026-12-04", "Dec. 4th, 2026") and date_written_in("2026-12-04", "le 4 décembre 2026")
    real_sentence_wrong_date = Deadline(date="2026-11-20", what="Pay",
                                        source_quote="Payment must be made on or before December 4, 2026.")
    assert not deadline_is_trustworthy(real_sentence_wrong_date, letter)
    assert not quote_found("TOTAL AMOUNT DUE: $1,950.00", letter)              # a changed number is caught
    assert phone_in_letter("555.013.7700", letter) and not phone_in_letter("(555) 999-0000", letter)
    for sample in demo.SAMPLES:                                                # both demo mistakes are caught
        a = demo.with_simulated_mistake(demo.demo_analysis(sample, "English"))
        assert [deadline_is_trustworthy(d, a.original_text) for d in a.deadlines[:2]] == [False, False]


def test_transparent_png_becomes_white_not_black():
    from io import BytesIO
    from PIL import Image, ImageDraw
    from plainspeak.images import prepare_image
    im = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 40), "HELLO", fill=(0, 0, 0, 255))
    buf = BytesIO()
    im.save(buf, "PNG")
    out, _ = prepare_image(buf.getvalue(), "image/png")
    assert Image.open(BytesIO(out)).convert("L").getextrema()[1] > 200   # there is white paper


def test_read_aloud_with_nothing_to_say_does_not_crash():
    from plainspeak.speech import text_to_mp3
    assert text_to_mp3("   ", "en") is None


@pytest.mark.parametrize("iso,text", [
    ("2026-12-10", "请于2026年12月10日上午10点到本办公室"), ("2026-12-10", "2026년 12월 10일까지"),
    ("2026-12-12", "trước ngày 12 tháng 12 năm 2026"), ("2026-12-15", "оплатите до 15 декабря 2026 г."),
    ("2026-12-04", "भुगतान 4 दिसंबर 2026 तक"), ("2026-12-04", "الدفع قبل ٤ ديسمبر ٢٠٢٦"),
    ("2026-12-04", "bago ang Disyembre 4, 2026"), ("2026-12-04", "le 4 décembre 2026"), ("2026-12-04", "04.12.2026"),
])
def test_dates_in_every_app_language(iso, text):
    from plainspeak.checks import date_written_in
    assert date_written_in(iso, text)


def test_similar_dates_in_other_languages_are_not_confused():
    from plainspeak.checks import date_written_in
    assert not date_written_in("2026-12-04", "14 декабря 2026")
    assert not date_written_in("2026-12-04", "2026年12月14日")
    assert not date_written_in("2026-12-04", "ngày 14 tháng 12 năm 2026")
