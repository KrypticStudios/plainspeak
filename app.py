"""PlainSpeak - understand any official letter.

Run with:  .venv/bin/streamlit run app.py
"""

import html
import importlib
import os
import re
import threading
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

import plainspeak.schema  # noqa: F401  (loaded first: the other files use it)

# Streamlit Cloud updates the app when we push to GitHub, but it can keep running OLD copies of our
# other files (plainspeak/*.py). That once crashed the live site. So: if ANY of our files changed on
# disk, reload ALL of them, in order (files that others import come first), one visitor at a time.
_MODULES = ["schema", "theme", "checks", "basic_reader", "ui_new", "ui_text", "ui_start", "speech", "calendar_export", "export", "images",
            "privacy", "history", "demo", "analyzer", "monitor"]
_reload_lock = getattr(importlib, "_plainspeak_lock", None) or threading.Lock()
importlib._plainspeak_lock = _reload_lock
with _reload_lock:
    _mods = [importlib.import_module(f"plainspeak.{n}") for n in _MODULES]
    _stamps = [os.path.getmtime(m.__file__) for m in _mods]
    for m, t in zip(_mods, _stamps):   # a file seen for the first time was just loaded fresh: just note its time
        if getattr(m, "_loaded_mtime", None) is None:
            m._loaded_mtime = t
    if any(m._loaded_mtime != t for m, t in zip(_mods, _stamps)):   # something changed since: reload them all
        for m, t in zip(_mods, _stamps):
            importlib.reload(m)._loaded_mtime = t

from babel.dates import format_date  # noqa: E402

from plainspeak import basic_reader, calendar_export, checks, demo, history, monitor, theme  # noqa: E402
from plainspeak.analyzer import AnalyzerError, analyze_letter, ask_question, draft_reply, has_api_key  # noqa: E402
from plainspeak.export import next_deadline, share_links, share_text, summary_html  # noqa: E402
from plainspeak.images import prepare_image  # noqa: E402
from plainspeak.privacy import MAX_TEXT_CHARS, RateLimiter, check_letter, check_upload, redact  # noqa: E402
from plainspeak.schema import LetterAnalysis  # noqa: E402
from plainspeak.theme import icon  # noqa: E402
from plainspeak.speech import LANGUAGES, RTL_LANGUAGES, text_to_mp3  # noqa: E402
from plainspeak.ui_start import ui  # noqa: E402
from plainspeak.ui_text import friendly_date, labels  # noqa: E402

st.set_page_config(page_title="PlainSpeak", page_icon="📬", layout="wide")

# On Streamlit Cloud the key lives in the app's private "Secrets" box, not in a .env file.
try:
    for name in ("GEMINI_API_KEY", "GEMINI_BACKUP_API_KEY", "GEMINI_MODEL"):
        if name in st.secrets and not os.getenv(name):
            os.environ[name] = st.secrets[name]
except FileNotFoundError:
    pass  # running locally with no secrets file: .env is used instead

# Where "My letters" are kept.
#  - On your own computer (PLAINSPEAK_LOCAL=1): in a file, so they're still there next time.
#  - On the public website: only in this visitor's session, in the server's memory, never on its disk.
LOCAL_MODE = os.getenv("PLAINSPEAK_LOCAL") == "1"

store = history.DiskStore() if LOCAL_MODE else history.SessionStore(st.session_state)


# ---------- Limits, so one person (or a bot) can't use up the free AI quota for everyone ----------
def visitor_id() -> str:
    """The visitor's internet address if the host tells us (so reloading the page doesn't reset their
    limit), otherwise a random ID for this browser session. Only used for counting, never stored."""
    forwarded = st.context.headers.get("X-Forwarded-For", "") if hasattr(st, "context") else ""
    if forwarded:
        return "ip:" + forwarded.split(",")[0].strip()
    if "visitor" not in st.session_state:
        st.session_state.visitor = uuid.uuid4().hex
    return st.session_state.visitor


@st.cache_resource
def limiters() -> dict[str, RateLimiter]:
    """Shared by every visitor (each request can make at most 4 AI calls, see analyzer.MAX_ATTEMPTS)."""
    return {"visitor": RateLimiter(limit=6, window=600),          # 6 letters/questions per 10 minutes
            "site": RateLimiter(limit=int(os.getenv("MAX_DAILY_AI_CALLS", "300")), window=86_400),
            "tts": RateLimiter(limit=10, window=600),             # read-aloud: 10 per 10 minutes
            "basic": RateLimiter(limit=30, window=600)}           # no-AI check: cheap, but not unlimited


def ai_allowed() -> bool:
    lim = limiters()
    if not lim["visitor"].allow(visitor_id()):
        monitor.record("rate_limited")
        st.warning(U["slow_down"], icon="⏳")
        return False
    if not lim["site"].allow("site"):
        monitor.record("ai_limit")
        st.warning(U["daily_limit"], icon="⏳")
        return False
    return True


# ---------- Shareable links ----------
# e.g. https://plainspeak.streamlit.app/?example=eviction&lang=es opens a finished example in Spanish,
# so a judge (or a screenshot) gets there in one click. Options: example=eviction|benefits|hospital,
# lang=<code like es, ar, zh-CN>, mistake=1 (show the catch-an-AI-mistake demo), contrast=1, bigtext=1.
LINK = {k: st.query_params.get(k, "") for k in ("example", "lang", "mistake", "contrast", "bigtext")}
LINK_EXAMPLES = {"eviction": "Eviction notice (rent)", "benefits": "Food benefits renewal", "hospital": "Hospital bill"}
CODES = list(LANGUAGES.values())

# The language the visitor picked. Kept in its own place so it survives the results screen (where the
# language box isn't shown) and so the sidebar, drawn first, already speaks the right language.
if "lang_pref" not in st.session_state:
    st.session_state.lang_pref = next((n for n, c in LANGUAGES.items() if c == LINK["lang"]), "English")
if st.session_state.get("language") in LANGUAGES:          # the language box changed on this click
    st.session_state.lang_pref = st.session_state.language
language = st.session_state.lang_pref
U = ui(LANGUAGES[language])


def esc(s: str) -> str:
    """Make text safe to put inside our HTML: no tags, no quotes, and no blank lines (a blank line would
    end the HTML block and let the rest be read as Markdown, e.g. links or images)."""
    return html.escape(str(s), quote=True).replace("\n", "<br>")


def md(s: str) -> str:
    """Make AI/letter text safe for places Streamlit reads as Markdown: no links, images, math or styling."""
    return re.sub(r"([\\`*_{}\[\]()#+\-!|$<>~])", r"\\\1", " ".join(str(s).split()))


def visitor_today() -> date:
    """Today's date where the VISITOR is. The server runs on UTC, so after ~4 PM in California
    its 'today' is already tomorrow, which would make the countdown one day short."""
    for tz in (st.context.timezone, "America/Los_Angeles"):   # the visitor's, else the hackathon's (PST)
        try:
            return datetime.now(ZoneInfo(tz)).date()
        except Exception:   # browser didn't say, or the server has no timezone data
            continue
    return date.today()


def show_answer(result: LetterAnalysis, lang_name: str, source: str, notice: str | None = None) -> None:
    """Put an answer on screen. `source` says what we checked quotes against: "text" (the words the
    person pasted), "photo" (our reading of their photo/PDF), "example" or "saved"."""
    st.session_state.result, st.session_state.result_lang = result, lang_name
    st.session_state.result_source = source
    st.session_state.letter_key = uuid.uuid4().hex[:8]   # fresh checkboxes for every letter
    st.session_state.saved_id = None
    for key in ("audio", "qa", "notice", "basic", "reply"):
        st.session_state.pop(key, None)
    if notice:
        st.session_state.notice = notice


def clear_answer() -> None:
    for key in ("result", "result_lang", "result_source", "saved_id", "audio", "qa", "notice", "basic", "reply"):
        st.session_state.pop(key, None)


# ---------- Styles ----------
# Display settings live in the top bar on every screen (phones hide sidebars), so the people who need
# larger text or high contrast can find them. Read them here, draw them below.
big_text = st.session_state.get("big_text", LINK["bigtext"] == "1")
high_contrast = st.session_state.get("high_contrast", LINK["contrast"] == "1")
_css = theme.CSS + (theme.BIG_TEXT if big_text else "") + (theme.HIGH_CONTRAST if high_contrast else "")
# No blank lines: a blank line would end the HTML block and show the rest as text.
st.markdown("\n".join(line for line in _css.splitlines() if line.strip()), unsafe_allow_html=True)


def plain(s: str) -> str:
    """A label without its leading emoji, e.g. '🗂️ My letters' -> 'My letters' (the design uses line icons)."""
    return re.sub(r"^[^\w]+", "", s).strip()


def bold(s: str) -> str:
    """Our own **bold** labels as HTML (escaped first, so nothing else in them becomes HTML)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))


def go_to(view: str) -> None:
    st.session_state.view = view


def go_start() -> None:
    st.session_state.view = ""
    clear_answer()


# ---------- Top bar: name, My letters, display settings ----------
on_letters = st.session_state.get("view") == "letters"
with st.container(key="ps-top", horizontal=True, vertical_alignment="center", gap="medium"):
    st.markdown('<p class="ps-brand">PlainSpeak</p>', unsafe_allow_html=True, width="content")
    st.space("stretch")
    st.button(plain(U["my_letters"]), key="nav-letters-on" if on_letters else "nav-letters", icon=":material/folder:",
              type="primary" if on_letters else "secondary", on_click=go_to, args=("" if on_letters else "letters",))
    st.toggle(U["larger_text"], value=LINK["bigtext"] == "1", key="big_text")
    st.toggle(U["high_contrast"], value=LINK["contrast"] == "1", key="high_contrast")


# ---------- My letters (saved letters, the disclaimer and privacy) ----------
PRIVACY_ITEMS = [
    ("We don't keep your letters.",
     "On this website, letters you save are kept in your session on our server's memory only, and are gone when "
     "you close the page. Nothing is written to our server's disk, and our code doesn't log what you upload. "
     "(Our hosting provider, Streamlit Cloud, keeps its own technical logs.)"),
    ("ID numbers",
     "In pasted text we try to hide common ID formats (Social Security, card, account, case numbers) before it is "
     "sent to the AI. This is best-effort, and it does not work on photos or PDFs, so please cover ID numbers "
     "before taking a photo."),
    ("Read-aloud",
     "Read-aloud sends the plain-language summary and steps (not your letter) to Google's text-to-speech service. "
     "It only happens when you press the read-aloud button."),
    ("The AI is Google Gemini.",
     "This demo uses Gemini's free tier. Under Google's terms, free-tier content may be used to improve Google's "
     "products and may be read by human reviewers. So please don't upload letters with private details here. Cover "
     "names and numbers, or use the example letters. A real launch would use the paid tier, where Google doesn't "
     "use your data to improve its products."),
    ("Your API key and the AI connection stay on our server.", "Your browser never sees them."),
]


def letters_page() -> None:
    with st.container(key="ps-narrow"):
        title = plain(U["my_letters"])
        first, _, last = title.rpartition(" ")
        title_html = f"{esc(first)} <em>{esc(last)}</em>" if first else f"<em>{esc(title)}</em>"
        note = esc(U["letters_note"]) + ("" if LOCAL_MODE else "<br>" + esc(U["letters_note_session"]))
        st.markdown(f'<div class="ps-center"><span class="ps-icotile">{icon("folder", 34)}</span>'
                    f'<h1 class="ps-bigtitle">{title_html}</h1><p class="ps-sub">{note}</p></div>',
                    unsafe_allow_html=True)
        recent = store.list_recent()
        if not recent:
            with st.container(key="ps-empty", horizontal_alignment="center"):
                st.markdown(f'<div class="ps-center"><span class="ps-icotile soft">{icon("folder", 26)}</span>'
                            f'<div class="ps-empty-t">{esc(U["no_letters"])}</div>'
                            f'<div class="ps-empty-s">{esc(U["no_letters_sub"])}</div></div>', unsafe_allow_html=True)
                st.button(U["add_letter"], key="add-letter", type="primary", icon=":material/add:", on_click=go_start)
        else:
            for letter_id, saved_at, lang, doc_type in recent:
                with st.container(horizontal=True, vertical_alignment="center"):
                    if st.button(f"{doc_type} · {saved_at[:10]}", key=f"open-{letter_id}", width="stretch",
                                 icon=":material/description:"):
                        loaded = store.load(letter_id)
                        if loaded:
                            show_answer(loaded[0], loaded[1], "saved")
                            st.session_state.saved_id = letter_id
                            st.session_state.view = ""
                            st.rerun()
                    if st.button("🗑️", key=f"del-{letter_id}", help="Delete this letter"):
                        store.delete(letter_id)
                        if st.session_state.get("saved_id") == letter_id:
                            st.session_state.saved_id = None   # so "Save" comes back for the letter on screen
                        st.rerun()
            with st.container(horizontal=True, horizontal_alignment="center"):
                st.button(U["add_letter"], key="add-letter", type="primary", icon=":material/add:", on_click=go_start)
                if st.button(plain(U["delete_all"]), key="delete_all", icon=":material/delete:"):
                    store.delete_all()
                    clear_answer()
                    st.rerun()
        st.markdown(f'<div class="ps-disc">{icon("alert", 22)}<span>{bold(plain(U["disclaimer"]))}</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f'<h2 class="ps-h2" style="border-bottom:1px solid var(--line);padding-bottom:.9rem !important">'
                    f'{icon("lock", 26)}<span>{esc(plain(U["privacy"]))}</span></h2>', unsafe_allow_html=True)
        for i, (title, body) in enumerate(PRIVACY_ITEMS):
            with st.expander(title, expanded=i == 0):
                st.markdown(body)


# Open the example from a shareable link (only once, so "Explain another letter" still works).
if LINK["example"] in LINK_EXAMPLES and not st.session_state.get("link_opened"):
    st.session_state.link_opened = True
    _name = LINK_EXAMPLES[LINK["example"]]
    _saved = demo.demo_analysis(_name, language)
    _notice = None
    if _saved is None:   # no saved answer in this language: show English and say so
        _saved, _lang = demo.demo_analysis(_name, "English"), "English"
        _notice = U["english_only"]
    else:
        _lang = language
    show_answer(demo.with_simulated_mistake(_saved) if LINK["mistake"] == "1" else _saved, _lang, "example", _notice)
    st.rerun()


# ---------- Start screen (shown when there is no answer yet) ----------
def upload_problems(pages) -> list[str]:
    """Every problem with the uploaded pages, in the reader's language. Each file's check is
    remembered, so a big photo isn't re-checked on every click."""
    checked = st.session_state.setdefault("upload_checks", {})
    problems = []
    for p in pages:
        if p.file_id not in checked:
            checked[p.file_id] = check_upload(p.getvalue(), p.type)
            if checked[p.file_id]:
                monitor.record("bad_upload")
        if checked[p.file_id]:
            problems.append(f"{p.name}: {U['up_' + checked[p.file_id]]}")
    if not problems:
        problems += [U["up_" + code] for code in check_letter([(p.getvalue(), p.type) for p in pages])]
    return problems


def start_screen() -> None:
    rtl = ' dir="rtl"' if LANGUAGES[language] in RTL_LANGUAGES else ""
    # The tagline is "**Big question?** The rest." -> a big heading (last word in italics) and a line under it.
    tag = re.match(r"\*\*(.+?)\*\*\s*(.*)", U["tagline"], re.S)
    big, rest = (tag[1], tag[2]) if tag else ("PlainSpeak", U["tagline"])
    first, _, last = big.rpartition(" ")
    big_html = f"{esc(first)} <em>{esc(last)}</em>" if first else esc(big)
    st.markdown(f'<div class="ps-center"{rtl}><h1 class="ps-bigtitle">{big_html}</h1>'
                f'<p class="ps-sub">{esc(rest)}</p></div>', unsafe_allow_html=True)
    st.selectbox("🌐 Explain my letter in / Idioma / 语言 / Ngôn ngữ / اللغة", list(LANGUAGES),
                 index=list(LANGUAGES).index(language), key="language",
                 help="The summary and steps will be in this language.")
    if st.session_state.language != language:   # picked a new language: redraw everything in it
        st.session_state.lang_pref = st.session_state.language
        st.rerun()
    steps = [("camera", "step1t", "step1d"), ("message", "step2t", "step2d"), ("check", "step3t", "step3d")]
    st.markdown(f'<div class="ps-steps"{rtl}>' + "".join(
        f'<div class="ps-step"><span class="ps-icotile soft">{icon(ico, 22)}</span><b>{esc(U[title])}</b>{esc(U[desc])}</div>'
        for ico, title, desc in steps) + "</div>", unsafe_allow_html=True)

    if not has_api_key():
        st.info(U["demo_mode"], icon="ℹ️")
    st.caption(U["privacy_line"])   # visible BEFORE anyone uploads, not hidden in a menu

    # Privacy choice: plain-Python check only, nothing goes to the AI (also works when there is no AI key).
    no_ai = st.toggle("🔐 " + U["no_ai_toggle"], key="no_ai", help=U["no_ai_help"])
    can_go = has_api_key() or no_ai
    tab_photo, tab_text = st.tabs([U["tab_photo"], U["tab_paste"]])

    with tab_photo:
        uploads = st.file_uploader(U["upload_label"], accept_multiple_files=True, key="uploads",
                                   type=["png", "jpg", "jpeg", "webp", "pdf"])
        st.caption(U["photo_tips"])
        use_camera = st.toggle(U["use_camera"], key="use_camera")
        snap = st.camera_input(U["camera_label"], key="camera") if use_camera else None
        pages = ([snap] if snap else []) + list(uploads or [])
        if pages:
            # Check every file FIRST. Only real, readable pictures get a preview (a broken file must
            # show a friendly message, not crash the page).
            problems = upload_problems(pages)
            checked = st.session_state["upload_checks"]
            images = [p for p in pages if p.type.startswith("image/") and not checked.get(p.file_id)]
            if images:
                st.image(images, caption=[f"{U['page']} {i}" for i in range(1, len(images) + 1)], width=140)
            for problem in problems:
                st.error(problem, icon="🚫")
            label = f"{U['explain']} ({len(pages)} {U['page'] if len(pages) == 1 else U['pages']})"
            if st.button(label, type="primary", key="go-photo", disabled=not can_go or bool(problems),
                         use_container_width=True):
                # Check again here on the server: a disabled button in the browser is not a real lock.
                if not upload_problems(pages):
                    st.session_state.request = {"files": [prepare_image(p.getvalue(), p.type) for p in pages],
                                                "source": "photo", "basic": no_ai}
                    st.rerun()

    with tab_text:
        # Streamlit forgets a text box's words while another screen is shown; put them back.
        if "pasted" not in st.session_state and st.session_state.get("pasted_keep"):
            st.session_state.pasted = st.session_state.pasted_keep
        pasted = st.text_area(U["paste_label"], height=180, max_chars=MAX_TEXT_CHARS, key="pasted",
                              placeholder=U["paste_placeholder"])
        st.caption(U["ids_note"])
        if st.button(U["explain"], type="primary", key="go-text", disabled=not can_go,
                     use_container_width=True):
            if pasted.strip():
                clean, hidden = redact(pasted[:MAX_TEXT_CHARS])
                if hidden:
                    monitor.record("ids_hidden")
                st.session_state.request = {"text": clean, "source": "text", "basic": no_ai,
                                            "notice": U["ids_hidden"].format(n=hidden) if hidden else None}
                st.rerun()
            else:
                st.warning(U["empty_box"])

    # One-click examples
    st.markdown(f"#### {U['examples_title']}")
    st.caption(U["examples_caption"])
    fake_mistake = st.toggle(U["mistake_toggle"], key="fake_mistake", help=U["mistake_help"])
    for col, (short, name) in zip(st.columns(len(LINK_EXAMPLES)), LINK_EXAMPLES.items()):
        emoji = {"eviction": "🏠", "benefits": "🍎", "hospital": "🏥"}[short]
        if col.button(f"{emoji} {U['ex_' + short]}", key=f"ex-{name}", use_container_width=True):
            saved = demo.demo_analysis(name, language)
            if saved is None and has_api_key():
                st.session_state.request = {"text": demo.sample_text(name), "source": "example"}   # ask the AI live
                st.rerun()
            notice = None
            if saved is None:  # no key and no saved answer in this language -> fall back to English
                saved, lang_shown, notice = demo.demo_analysis(name, "English"), "English", U["english_only"]
            else:
                lang_shown = language
            show_answer(demo.with_simulated_mistake(saved) if fake_mistake else saved, lang_shown, "example", notice)
            st.rerun()


# ---------- Run the AI ----------
def letter_words(req: dict) -> str:
    """The letter's own words, if we have them without the AI: pasted text, or the text inside a real PDF."""
    if req.get("text", "").strip():
        return req["text"]
    texts = [basic_reader.pdf_text(data) for data, mime in req.get("files", []) if mime == "application/pdf"]
    return redact("\n\n".join(t for t in texts if t)[:MAX_TEXT_CHARS])[0]


def show_basic(req: dict, reason: str, why: str | None = None) -> bool:
    """Switch to the basic (no-AI) check. False if there are no words to check (a photo)."""
    words = letter_words(req)
    if not words.strip():
        return False
    clear_answer()
    st.session_state.basic = {"text": words, "reason": reason, "why": why}
    monitor.record("basic_check")
    return True


if "pasted" in st.session_state:   # also when they empty the box, so a deleted letter never comes back
    st.session_state.pasted_keep = st.session_state.pasted
req = st.session_state.pop("request", None)   # take it out first, so a blocked request isn't retried forever
if req is not None and req.pop("basic", False):
    if not limiters()["basic"].allow(visitor_id()):
        st.warning(U["slow_down"], icon="⏳")
    elif not show_basic(req, "private"):
        st.warning(U["basic_photo"], icon="📷")
elif req is not None and not ai_allowed():
    if req.get("source") != "example":
        show_basic(req, "down", U["daily_limit"])   # over the limit: plain code still finds dates and amounts
elif req is not None:
    source, notice = req.pop("source", "text"), req.pop("notice", None)
    with st.spinner(U["spinner"]):
        try:
            show_answer(analyze_letter(language, **req, today=visitor_today()), language, source, notice)
            monitor.record("letter_ok")
        except AnalyzerError as e:
            monitor.record(monitor.kind_of_error(e.kind))
            st.error(U.get("err_" + e.kind, U["err_other"]), icon="🚫")
            # The AI is down or out of free uses: still show what plain code can find in the letter.
            if e.kind not in ("unreadable", "too_long", "empty") and source != "example" and \
                    not show_basic(req, "down", U.get("err_" + e.kind, U["err_other"])):
                st.caption("📷 " + U["basic_photo"])
    if "result" in st.session_state or "basic" in st.session_state:
        st.rerun()   # redraw from the top, so the results page gets its compact header (answer on screen one)


# ---------- Results screen ----------
def quote_html(quote: str, letter: str, t: dict) -> str:
    """The exact words from the letter, with a check mark if we found them in the letter."""
    if checks.quote_found(quote, letter):
        found = t["found_photo"] if st.session_state.get("result_source") == "photo" else t["found"]
        badge = f'<span class="ps-chip ok ps-ok">✓ {esc(found)}</span>'
    else:
        badge = f'<span class="ps-chip bad ps-warn">⚠ {esc(t["not_found"])}</span>'
    return f'<div class="ps-quote" dir="auto">“{esc(quote)}” {badge}</div>'   # "auto": Arabic letters too


def reply_purposes(a: LetterAnalysis) -> list[str]:
    """The kinds of reply that make sense for this letter."""
    words = a.original_text.lower()
    purposes = ["more_time"] if a.deadlines else []
    purposes += ["payment_plan"] if a.money else []
    purposes += ["hearing"] if any(w in words for w in ("hearing", "appeal", "reconsideration", "review",
                                                         "audiencia", "apelación")) else []
    return purposes + ["dispute", "questions"]


def show_reply_writer(a: LetterAnalysis, lang_name: str, t: dict, card, heading, today: date) -> None:
    """Write a reply the reader can send back: only facts from their letter, [brackets] for what they fill in."""
    heading("pencil", t["reply_title"])
    st.caption(t["reply_help"])
    key = st.session_state.get("letter_key", "x")
    purposes = reply_purposes(a)
    purpose = st.radio(t["reply_title"], purposes, format_func=lambda p: t["reply_" + p], key=f"reply-kind-{key}",
                       label_visibility="collapsed", horizontal=True)
    if st.button(t["reply_make"], key=f"reply-go-{key}", disabled=not has_api_key(), type="primary",
                 icon=":material/edit:"):
        if ai_allowed():
            with st.spinner("…"):
                try:
                    # ID numbers are hidden again first (a photo's reading may contain them)
                    draft = draft_reply(redact(a.original_text)[0], purpose, lang_name, today=today)
                    st.session_state.reply = (key, purpose, draft, uuid.uuid4().hex[:6])
                    monitor.record("reply_ok")
                except AnalyzerError as e:
                    monitor.record(monitor.kind_of_error(e.kind))
                    st.error(t.get("err_" + e.kind, t["err_other"]), icon="🚫")
    if not has_api_key():
        st.caption(t["type_needs_key"])
    saved = st.session_state.get("reply")
    if not saved or saved[0] != key:
        return
    _, purpose, draft, nonce = saved   # a new draft gets a new box (Streamlit would keep the old words)
    card(f"<b>💬 {esc(t['reply_explain'])}:</b> {esc(draft.explanation)}")
    # Editable, so they can fix it before they send it. Plain text: nothing in it is run as code.
    text = st.text_area(t["reply_title"], draft.reply_text, height=320, key=f"reply-text-{key}-{nonce}",
                        label_visibility="collapsed")
    unsupported = checks.numbers_not_in_letter(text, a.original_text, today=today)
    unsupported += checks.contacts_not_in_letter(text + "\n" + draft.how_to_send, a.original_text)
    if unsupported:
        st.warning(f"{t['reply_bad_numbers']} {md(', '.join(unsupported))}", icon="⚠️")
    if draft.fill_in:
        card(f"<b>📝 {esc(t['reply_fill'])}:</b><br>" + "<br>".join(f"• {esc(x)}" for x in draft.fill_in))
    if draft.how_to_send:
        card(f"<b>📬 {esc(t['reply_send'])}:</b> {esc(draft.how_to_send)}")
    st.download_button(t["reply_download"], text, icon=":material/download:", file_name="plainspeak-reply.txt", mime="text/plain",
                       key=f"reply-dl-{key}", on_click="ignore")
    st.caption("⚠️ " + t["reply_check"])


def show_basic_result(b: dict) -> None:
    """The no-AI check: dates, money and phone numbers found by plain code, each next to its own sentence."""
    code = LANGUAGES.get(language, "en")
    t = {**ui(code), **labels(code)}
    direction = "rtl" if code in RTL_LANGUAGES else "ltr"
    today = visitor_today()
    r = basic_reader.read(b["text"], today=today)
    shown = 30   # at most this many of each, so a strange file can't make a page with thousands of cards

    def card(body: str, extra_class: str = "") -> None:
        st.markdown(f'<div class="ps-card {extra_class}" dir="{direction}">{body}</div>', unsafe_allow_html=True)

    if st.button(t["start_over"], key="start-over", icon=":material/arrow_back:"):
        clear_answer()
        st.rerun()
    st.markdown(f'<h1 class="ps-h1" dir="{direction}">{icon("cog", 26)}<span>{esc(t["basic_title"])}</span></h1>',
                unsafe_allow_html=True)
    if b.get("why"):
        st.error(b["why"], icon="🚫")   # why the AI couldn't help (in the reader's language)
    st.info(t["basic_private_intro"] if b["reason"] == "private" else t["basic_intro"], icon="ℹ️")
    if r.serious_words:
        st.warning(f"**{md(t['basic_serious'])}** {md(', '.join(r.serious_words))}. {md(t['basic_serious_help'])}",
                   icon="⚠️")

    def sentence(s: str) -> str:
        return f'<div class="ps-quote" dir="auto">“{esc(s)}”</div>'

    if r.dates:
        st.markdown(f"### 📅 {esc(t['basic_dates'])}")
        for d, s in r.dates[:shown]:
            days = (d - today).days
            # Plain code can't tell which date is a deadline, so this only says how far away each date is.
            when = t["basic_in_days"].format(n=days) if days > 0 else t["basic_passed"] if days < 0 else "📍"
            card(f"<b>{esc(friendly_date(d.isoformat(), code))}</b> — {esc(when)}{sentence(s)}")
    if r.money:
        st.markdown(f"### 💵 {esc(t['basic_money'])}")
        for amount, s in r.money[:shown]:
            card(f"<b>{esc(amount)}</b>{sentence(s)}")
    if r.phones:
        st.markdown(f"### ☎️ {esc(t['basic_phones'])}")
        card("<br>".join(f'📞 <a href="tel:{"".join(ch for ch in p if ch.isdigit())}">{esc(p)}</a>'
                         for p in r.phones[:shown]))
    if not r.found_anything:
        st.info(t["basic_none"])
    st.markdown(f"### 🤝 {esc(t['free_help'])}")
    st.markdown(f"📞 {t['help_211']}\n\n⚖️ {t['help_law']}")
    with st.expander(t["show_original"]):
        st.text(b["text"])


def notice_period(letter: str, days: int) -> int | None:
    """The notice period the letter itself states (e.g. '14-day notice', 'within fourteen (14) days'),
    for the countdown ring. Only a period at least as long as the days left; None if the letter gives none."""
    periods = [int(n) for n in re.findall(r"(\d{1,3})\)?[\s-]*(?:calendar\s+|business\s+)?days?\b", letter, re.I)]
    fitting = sorted(n for n in periods if 0 < n and n >= days)
    return fitting[0] if fitting and days >= 0 else None


def date_tile(d: date | None, code: str, bad: bool = False) -> str:
    """A small calendar page: month, day, weekday (in the reader's language)."""
    if d is None:
        return f'<div class="ps-tile{" bad" if bad else ""}" aria-hidden="true"><div class="m">&nbsp;</div>' \
               f'<div class="d">?</div><div class="w">&nbsp;</div></div>'
    loc = code.replace("-", "_")
    month = format_date(d, "MMM", locale=loc).upper().rstrip(".")
    weekday = format_date(d, "EEEE", locale=loc)
    return (f'<div class="ps-tile{" bad" if bad else ""}" aria-hidden="true"><div class="m">{esc(month)}</div>'
            f'<div class="d">{d.day}</div><div class="w">{esc(weekday)}</div></div>')


def show_result(a: LetterAnalysis, lang_name: str) -> None:
    code = LANGUAGES.get(lang_name, "en")
    t = {**ui(code), **labels(code)}   # every label in the language of THIS answer
    direction = "rtl" if code in RTL_LANGUAGES else "ltr"
    letter = a.original_text
    today = visitor_today()
    key = st.session_state.get("letter_key", "x")
    attrs = f'dir="{direction}" lang="{code}"'   # lang= tells screen readers which voice to use

    def card(body: str, extra_class: str = "") -> None:
        st.markdown(f'<div class="ps-card {extra_class}" {attrs}>{body}</div>', unsafe_allow_html=True)

    def heading(name: str, text: str, level: int = 2, anchor: str = "") -> None:
        tag, size = ("h2", 24) if level == 2 else ("h3", 20)
        st.markdown(f'<{tag} class="ps-{tag}" {attrs}{anchor}>{icon(name, size)}<span>{esc(text)}</span></{tag}>',
                    unsafe_allow_html=True)

    def html_block(body: str) -> None:
        st.markdown(f'<div {attrs}>{body}</div>', unsafe_allow_html=True)

    if st.session_state.get("scrolled_for") != key:
        # A new answer: jump to the top of the page, so the countdown is the first thing you see
        # (otherwise the browser stays scrolled down where you pressed "Explain").
        st.session_state.scrolled_for = key
        # (A fixed snippet of our own code, never anything from a letter or the AI.)
        st.iframe("<script>for (const el of [window.parent, ...window.parent.document.querySelectorAll("
                  "'[data-testid=stMain], section.main, .main')]) { try { el.scrollTo({top: 0}); } catch (e) {} }"
                  "</script>", height=1, tab_index=-1, alt="(scrolls the page to the top)")

    if st.button(t["start_over"], key="start-over", icon=":material/arrow_back:"):
        clear_answer()
        st.query_params.clear()   # so a shared link doesn't keep reopening the example
        st.rerun()
    if st.session_state.get("notice"):
        st.info(st.session_state.notice, icon="ℹ️")

    # --- At a glance: urgency, countdown, first step (first, so it's on a phone's first screen) ---
    urgency = checks.calibrated_urgency(a, today)   # the AI's urgency, checked against the calendar
    level = {"high": t["urgent"], "medium": t["soon"], "low": t["not_urgent"]}[urgency]
    split = re.match(r"^(.*?)\s*(\([^)]*\))\s*$", a.document_type)
    doc_html = f"{esc(split[1])} <em>{esc(split[2])}</em>" if split and split[1] else esc(a.document_type)
    nxt = next_deadline(a, today=today)
    ring = next_line = ""
    if nxt:
        days, d = nxt
        count = (t["days_left"].format(n=days) if days > 1 else t["day_left_one"] if days == 1
                 else t["due_today"] if days == 0 else t["passed"])
        small = days < 0
        next_line = (f'<p class="ps-next">{esc(t["next_deadline"])}: <b>{esc(friendly_date(d.date, code))}</b>'
                     f' — {esc(d.what)}</p>')
        period = notice_period(letter, days)
        if period:
            circ = 2 * 3.14159 * 46
            ring = (f'<div class="ps-ring" aria-hidden="true"><svg viewBox="0 0 104 104">'
                    f'<circle cx="52" cy="52" r="46" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="7"/>'
                    f'<circle cx="52" cy="52" r="46" fill="none" stroke="#F2C46D" stroke-width="7" stroke-linecap="round"'
                    f' stroke-dasharray="{circ * days / period:.1f} {circ:.1f}"/></svg>'
                    f'<div class="num">{days}/{period}<small>{esc(t["days_word"])}</small></div></div>')
    else:
        count, small = t["no_date"], True
    right = f'<p class="ps-why">{icon("clock", 18)}<span><b>{esc(level)}</b> — {esc(a.urgency_reason)}</span></p>'
    if a.actions:
        first = a.actions[0]
        right += f'<p class="ps-label">{esc(t["first_step"])}</p><p class="ps-first">{esc(first.step)}</p>'
        # A call button only for a number that is really in the letter and belongs to this first step.
        step_digits = re.sub(r"\D", "", first.step + " " + first.source_quote)
        for c in a.contacts:
            digits = re.sub(r"\D", "", c.phone)
            named = c.name and c.name.lower() in first.step.lower()
            if c.phone and checks.phone_in_letter(c.phone, letter) and len(digits) >= 7 and \
                    (digits in step_digits or named):
                tel = "".join(ch for ch in c.phone if ch.isdigit() or ch == "+")
                right += (f'<a class="ps-pill" href="tel:{tel}">{icon("phone", 17)}'
                          f'<span>{esc(t["call"])} {esc(c.phone)}</span></a>')
                break
    st.markdown(
        f'<section class="ps-hero" {attrs}><div class="ps-hero-l">'
        f'<span class="ps-badge {urgency}">{icon("alert", 14)}{esc(level)}</span>{ring}'
        f'<h1 class="ps-doc">{doc_html}</h1><div class="ps-count{" small" if small else ""}">{esc(count)}</div>'
        f'{next_line}</div><div class="ps-hero-r">{right}</div></section>'
        f'<p class="ps-from">{esc(t["from"])}: {esc(a.sender)}</p>', unsafe_allow_html=True)

    main, side = st.columns([1.62, 1], gap="large")
    with main:
        # --- Summary + read aloud ---
        heading("message", t["means"])
        parts = re.split(r"(?<=[.!?。！？؟।])\s+", a.summary.strip())
        summary = esc(" ".join(parts[:-1])) + f" <mark>{esc(parts[-1])}</mark>" if len(parts) > 1 else esc(a.summary)
        html_block(f'<p class="ps-summary">{summary}</p><hr class="ps-divider">')
        col_tts, col_grade = st.columns([1, 1.15], vertical_alignment="center")
        if col_tts.button(t["read_aloud"], key="tts", type="primary", icon=":material/volume_up:"):
            # Read everything that matters, so someone who can't read at all still gets it.
            spoken = [a.summary]
            if nxt and nxt[0] >= 0:
                spoken.append(f"{t['next_deadline']}: {friendly_date(nxt[1].date, code)}. {nxt[1].what}.")
            spoken += [f"{i}. {s.step}" for i, s in enumerate(a.actions, 1)]
            audio = text_to_mp3(" ".join(spoken), code) if limiters()["tts"].allow(visitor_id()) else None
            if audio:
                st.session_state.audio = (a.summary, audio, True)  # keep it, so the player doesn't vanish
            else:
                monitor.record("tts_failed")
                st.warning(t["tts_failed"])
        before, after = checks.reading_grade(letter), checks.reading_grade(a.summary)
        if code == "en" and before is not None and after is not None:
            def bar(g: float, cls: str) -> str:
                return f'<span class="bar {cls}" style="width:{max(8, min(100, g / 16 * 100)):.0f}%"></span>'
            col_grade.markdown(
                f'<div class="ps-grade" role="img" aria-label="{esc(t["reading_level"])}: {esc(t["rl_letter"])} '
                f'{esc(t["grade"].format(n=f"{before:.0f}"))}, {esc(t["rl_summary"])} {esc(t["grade"].format(n=f"{after:.0f}"))}">'
                f'<span style="grid-column:1/4">{esc(t["reading_level"])}</span>'
                f'<span>{esc(t["rl_letter"])}</span><span class="track">{bar(before, "")}</span>'
                f'<b>{esc(t["grade"].format(n=f"{before:.0f}"))}</b>'
                f'<span>{esc(t["rl_summary"])}</span><span class="track">{bar(after, "sum")}</span>'
                f'<b>{esc(t["grade"].format(n=f"{after:.0f}"))}</b></div>', unsafe_allow_html=True)
        saved_audio = st.session_state.get("audio")
        if saved_audio and saved_audio[0] == a.summary:
            st.audio(saved_audio[1], format="audio/mp3", autoplay=saved_audio[2])   # plays straight away, once
            st.session_state.audio = (saved_audio[0], saved_audio[1], False)

        # --- Deadlines: each with the sentence it came from, checked by our own code ---
        if a.deadlines:
            heading("calendar", t["dates"])
            verified = []
            for d in a.deadlines:
                quote_ok = checks.quote_found(d.source_quote, letter)
                try:
                    day = date.fromisoformat(d.date.strip())
                except ValueError:
                    day = None
                note = ""
                if checks.deadline_is_trustworthy(d, letter):
                    verified.append(d)
                    title, bad = friendly_date(d.date, code), False
                elif quote_ok and checks.date_written_in(d.date, letter):
                    # The sentence is real, but its date is a DIFFERENT date from elsewhere in the letter.
                    title, bad = friendly_date(d.date, code), True
                    note = f'<div class="ps-chip bad ps-warn">⚠ {esc(t["date_mismatch"])}</div>'
                elif quote_ok:
                    # No date written in the letter (or the AI worked one out itself): don't show a date we can't back up.
                    title, bad, day = t["no_date"], True, None
                    note = f'<div class="ps-chip bad ps-warn">⏳ {esc(t["estimated"])}</div>'
                else:
                    title, bad = friendly_date(d.date, code) or t["no_date"], True
                html_block(f'<div class="ps-date">{date_tile(day, code, bad)}<div><div class="ps-date-t">'
                           f'{esc(title)}</div><div class="ps-date-w">{esc(d.what)}</div>{note}</div></div>'
                           f'{quote_html(d.source_quote, letter, t)}')
            # Only dates we could find in the letter, next to their sentence, and still ahead, go into the calendar.
            ics = calendar_export.deadlines_to_ics(verified, today=today)
            if ics:
                st.download_button(t["add_calendar"], ics, file_name="plainspeak-deadlines.ics", mime="text/calendar",
                                   key="ics", on_click="ignore", icon=":material/calendar_today:",
                                   help="Opens in Google, Apple or Outlook Calendar, with a reminder 2 days before.")

        # --- Steps ---
        if a.actions:
            heading("check", t["todo"])
            for i, s in enumerate(a.actions):
                st.checkbox(md(s.step), key=f"step-{key}-{i}")
                html_block(f'<div class="ps-step-q">{quote_html(s.source_quote, letter, t)}</div>')

        # --- Papers to bring or send ---
        if a.documents_to_bring:
            heading("clip", t["docs_title"])
            for i, doc in enumerate(a.documents_to_bring):
                st.checkbox(md(doc.item), key=f"doc-{key}-{i}")
                html_block(f'<div class="ps-step-q">{quote_html(doc.source_quote, letter, t)}</div>')

    with side, st.container(key="ps-side"):
        if a.rights:
            heading("shield", t["rights"], level=3)
            html_block('<ul class="ps-list">' + "".join(f"<li>{esc(r)}</li>" for r in a.rights) + "</ul>")
        if a.confidence != "high" or a.unclear_points:
            sure = {"high": "", "medium": " (?)", "low": " (??)"}[a.confidence]
            heading("help", t["not_sure"] + sure, level=3)
            html_block('<ul class="ps-list">' + ("".join(f"<li>{esc(p)}</li>" for p in a.unclear_points)
                                                 or "<li>—</li>") + "</ul>")
        # --- Human help ---
        if a.needs_human_help:
            html_block(f'<div class="ps-banner"><span class="ico">{icon("user", 20)}</span>'
                       f'<span><b>{esc(t["talk_person"])}</b> {esc(a.help_reason)}</span></div>')
        else:
            html_block(f'<div class="ps-banner calm"><span class="ico">{icon("check", 20)}</span>'
                       f'<span>{esc(a.help_reason)}</span></div>')
        heading("user", t["free_help"], level=3)
        html_block(f'<div class="ps-help">{icon("phone", 17)}<span>{bold(t["help_211"])}</span></div>'
                   f'<div class="ps-help">{icon("globe", 17)}<span>{bold(t["help_law"])}</span></div>')
        # --- Keep it ---
        st.download_button(t["print"], summary_html(a, code), file_name="plainspeak-summary.html", mime="text/html",
                           width="stretch", key="print", on_click="ignore", icon=":material/print:",
                           help="A simple page you can print, or send to someone who helps you.")
        if st.session_state.get("saved_id"):
            html_block(f'<div class="ps-help" style="justify-content:center">{icon("check", 17)}'
                       f'<b>{esc(t["saved"])}</b></div>')
        elif st.button(t["save"], width="stretch", key="save", type="primary", icon=":material/bookmark:"):
            st.session_state.saved_id = store.save(a, lang_name)
            st.rerun()
        # --- Send to family: opens the person's OWN WhatsApp / texts / email, only when they tap ---
        html_block('<hr class="ps-sep">')
        heading("mail", t["share"], level=3)
        links = share_links(share_text(a, code, today=today), subject=f"PlainSpeak: {a.document_type}")
        html_block('<div class="ps-share-btns">' + "".join(
            f'<a href="{esc(links[name])}" target="_blank" rel="noopener noreferrer">{icon(ico, 17)}{name}</a>'
            for name, ico in [("WhatsApp", "chat"), ("SMS", "sms"), ("Email", "mail")]) + "</div>")

    # --- Money ---
    if a.money:
        heading("money", t["money"])
        html_block('<div class="ps-grid">' + "".join(
            f'<div><div class="ps-amt{"" if checks.quote_found(m.source_quote, letter) else " bad"}">{esc(m.amount)}'
            f'</div><div class="ps-amt-w">{esc(m.what)}</div>{quote_html(m.source_quote, letter, t)}</div>'
            for m in a.money) + "</div>")

    # --- Contacts: a number is only tap-to-call if it's really in the letter ---
    if a.contacts:
        heading("phone", t["contact"])
        people = []
        for c in a.contacts:
            lines = [f'<div class="n">{esc(c.name)}</div><div class="y">{esc(c.why)}</div>']
            if c.phone and checks.phone_in_letter(c.phone, letter):
                digits = "".join(ch for ch in c.phone if ch.isdigit() or ch == "+")
                lines.append(f'<div class="l">{icon("phone", 16)}<a href="tel:{digits}">{esc(c.phone)}</a></div>')
            elif c.phone:
                lines.append(f'<div class="l">{icon("phone", 16)}<span>{esc(c.phone)} '
                             f'<span class="ps-warn">⚠ {esc(t["phone_unverified"])}</span></span></div>')
            if c.email:
                lines.append(f'<div class="l">{icon("mail", 16)}<span>{esc(c.email)}</span></div>')
            if c.address:
                lines.append(f'<div class="l">{icon("pin", 16)}<span>{esc(c.address)}</span></div>')
            people.append('<div class="ps-contact">' + "".join(lines) + "</div>")
        html_block('<div class="ps-grid">' + "".join(people) + "</div>")

    col_ask, col_reply = st.columns(2, gap="large")
    with col_ask:
        # --- Ask a question ---
        heading("user", t["ask_title"])
        suggestions = demo.suggested_questions(a) or ([t["q1"], t["q2"], t["q3"], t["q4"]] if has_api_key() else [])
        asked = None
        if suggestions:
            st.caption(t["suggested"])
            for i, q in enumerate(suggestions):
                if st.button(q, key=f"suggest-{key}-{i}"):
                    asked = q
        with st.form("ask-form", clear_on_submit=True), \
                st.container(horizontal=True, vertical_alignment="center"):
            typed = st.text_input(t["ask_title"], placeholder=t["ask_placeholder"], label_visibility="collapsed",
                                  max_chars=500, disabled=not has_api_key())
            if st.form_submit_button(t["ask_button"], disabled=not has_api_key(), type="primary") and typed:
                asked = typed
        if not has_api_key():
            st.caption(t["type_needs_key"])
        if asked:
            answer = demo.demo_answer(a, asked)
            if answer is None and ai_allowed():
                with st.spinner("…"):
                    try:
                        answer = ask_question(letter, redact(asked)[0], lang_name)
                        monitor.record("question_ok")
                    except AnalyzerError as e:
                        monitor.record(monitor.kind_of_error(e.kind))
                        st.error(t.get("err_" + e.kind, t["err_other"]), icon="🚫")
            if answer:
                st.session_state.qa = [(asked, answer)] + st.session_state.get("qa", [])[:4]
        for q, ans in st.session_state.get("qa", []):
            body = f"<b>❔ {esc(q)}</b><br>{esc(ans.answer)}"
            if not ans.answered_from_letter:
                body += f'<br><span class="ps-warn">ℹ️ {esc(t["not_in_letter"])}</span>'
            for quote in ans.source_quotes:
                body += quote_html(quote, letter, t)
            if ans.who_to_ask:
                body += f"<br>👤 <b>{esc(t['who_to_ask'])}:</b> {esc(ans.who_to_ask)}"
            card(body)
    with col_reply:
        show_reply_writer(a, lang_name, t, card, heading, today)

    st.write("")
    with st.expander(t["show_original"], icon=":material/description:"):
        if st.session_state.get("result_source") == "photo":
            st.caption("ℹ️ " + t["found_photo"])
        st.text(letter)


if st.session_state.get("view") == "letters":
    letters_page()
elif "result" in st.session_state:
    show_result(st.session_state.result, st.session_state.get("result_lang", language))
elif "basic" in st.session_state:
    with st.container(key="ps-narrow"):
        show_basic_result(st.session_state.basic)
else:
    with st.container(key="ps-narrow"):
        start_screen()
