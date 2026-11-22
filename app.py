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
_MODULES = ["schema", "checks", "ui_text", "ui_start", "speech", "calendar_export", "export", "images",
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

from plainspeak import calendar_export, checks, demo, history, monitor  # noqa: E402
from plainspeak.analyzer import AnalyzerError, analyze_letter, ask_question, has_api_key  # noqa: E402
from plainspeak.export import next_deadline, share_links, share_text, summary_html  # noqa: E402
from plainspeak.images import prepare_image  # noqa: E402
from plainspeak.privacy import MAX_TEXT_CHARS, RateLimiter, check_letter, check_upload, redact  # noqa: E402
from plainspeak.schema import LetterAnalysis  # noqa: E402
from plainspeak.speech import LANGUAGES, RTL_LANGUAGES, text_to_mp3  # noqa: E402
from plainspeak.ui_start import ui  # noqa: E402
from plainspeak.ui_text import friendly_date, labels  # noqa: E402

st.set_page_config(page_title="PlainSpeak", page_icon="📬", layout="centered")

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

PRIVACY_NOTE = """
- **We don't keep your letters.** On this website, letters you save are kept in your session on our server's
  memory only, and are gone when you close the page. Nothing is written to our server's disk, and our code
  doesn't log what you upload. (Our hosting provider, Streamlit Cloud, keeps its own technical logs.)
- **ID numbers:** in pasted text we try to hide common ID formats (Social Security, card, account, case numbers)
  before it is sent to the AI. This is best-effort, and it does not work on photos or PDFs, so please cover
  ID numbers before taking a photo.
- **Read-aloud** sends the plain-language summary and steps (not your letter) to Google's text-to-speech
  service. It only happens when you press the 🔊 button.
- **The AI is Google Gemini.** This demo uses Gemini's *free* tier. Under Google's terms, free-tier content may be
  used to improve Google's products and may be read by human reviewers. So please **don't upload letters with
  private details** here. Cover names and numbers, or use the example letters. A real launch would use the paid
  tier, where Google doesn't use your data to improve its products.
- Your API key and the AI connection stay on our server. Your browser never sees them.
"""
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
            "tts": RateLimiter(limit=10, window=600)}             # read-aloud: 10 per 10 minutes


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
    for key in ("audio", "qa", "notice"):
        st.session_state.pop(key, None)
    if notice:
        st.session_state.notice = notice


def clear_answer() -> None:
    for key in ("result", "result_lang", "result_source", "saved_id", "audio", "qa", "notice"):
        st.session_state.pop(key, None)


# ---------- Sidebar: display settings, saved letters ----------
with st.sidebar:
    st.header(U["display"])
    big_text = st.toggle(U["larger_text"], value=LINK["bigtext"] == "1", key="big_text")
    high_contrast = st.toggle(U["high_contrast"], value=LINK["contrast"] == "1", key="high_contrast")

    st.divider()
    st.header(U["my_letters"])
    recent = store.list_recent()
    if not recent:
        st.caption(U["letters_note"] + ("" if LOCAL_MODE else " " + U["letters_note_session"]))
    for letter_id, saved_at, lang, doc_type in recent:
        col_open, col_del = st.columns([4, 1])
        if col_open.button(f"{doc_type} · {saved_at[:10]}", key=f"open-{letter_id}", use_container_width=True):
            loaded = store.load(letter_id)
            if loaded:
                show_answer(loaded[0], loaded[1], "saved")
                st.session_state.saved_id = letter_id
        if col_del.button("🗑️", key=f"del-{letter_id}", help="Delete this letter"):
            store.delete(letter_id)
            if st.session_state.get("saved_id") == letter_id:
                st.session_state.saved_id = None   # so "Save" comes back for the letter on screen
            st.rerun()
    if recent and st.button(U["delete_all"], use_container_width=True, key="delete_all"):
        store.delete_all()
        clear_answer()
        st.rerun()

    st.divider()
    st.caption(U["disclaimer"])
    with st.expander(U["privacy"]):
        st.markdown(PRIVACY_NOTE)


# ---------- Styles ----------
css = """
<style>
.block-container {padding-top: 2.2rem;}
.ps-card {border-radius: 12px; padding: 1rem 1.2rem; margin: .5rem 0; border: 2px solid #cbd5e1; background: #f8fafc;}
.ps-high {border-color: #b91c1c; background: #fef2f2;}
.ps-medium {border-color: #b45309; background: #fffbeb;}
.ps-low {border-color: #15803d; background: #f0fdf4;}
.ps-quote {font-size: .9em; color: #334155; border-left: 3px solid #94a3b8; padding-left: .6rem; margin-top: .2rem;}
.ps-warn {color: #b91c1c; font-weight: 600;}
.ps-ok {color: #166534; font-weight: 600;}
.ps-steps {display: flex; gap: .6rem; margin: .6rem 0 1rem;}
.ps-step {flex: 1; text-align: center; padding: .8rem .4rem; border-radius: 12px; border: 2px solid #cbd5e1;}
.ps-step .big {font-size: 1.8rem; display: block;}
.ps-countdown {font-size: 1.6rem; font-weight: 700;}
@media (max-width: 640px) {
  .block-container {padding-top: 1rem;}
  .ps-steps {gap: .3rem;}
  .ps-step {padding: .4rem .2rem; font-size: .8rem;}
  .ps-step .big {font-size: 1.2rem;}
}
</style>
"""
if big_text:
    # Body text only, so headings stay bigger than the text under them.
    css += """<style>
    .stMarkdown p, .stMarkdown li, .ps-card, label p, button p, .stCaption, [data-testid="stCaptionContainer"]
        {font-size: 1.3rem !important; line-height: 1.6 !important;}
    .ps-quote {font-size: 1.1rem !important;}
    .stMarkdown h2 {font-size: 2.2rem !important;} .stMarkdown h3 {font-size: 1.8rem !important;}
    </style>"""
if high_contrast:
    # Black background, white text, yellow outlines: the whole page, including the sidebar.
    css += """<style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"], .ps-card, .ps-high, .ps-medium, .ps-low,
    [data-testid="stSelectbox"] div, [data-baseweb="select"] div, [data-baseweb="select"] input,
    [data-baseweb="popover"] *, [role="listbox"] *,
    [data-testid="stAlert"], [data-testid="stAlertContainer"], [data-testid="stAlert"] *,
    textarea, [data-testid="stFileUploaderDropzone"], [data-testid="stExpander"] details
        {background: #000 !important; color: #fff !important;}
    [data-testid="stAlertContainer"] {border: 2px solid #ffff00 !important;}
    .stApp *, [data-testid="stSidebar"] * {color: #fff !important;}
    .ps-card, [data-baseweb="select"] > div, textarea, button, [data-testid="stFileUploaderDropzone"]
        {border: 2px solid #ffff00 !important;}
    button {background: #000 !important;}
    a, .stApp a {color: #00ffff !important; text-decoration: underline !important;}
    .ps-ok {color: #7CFC00 !important;} .ps-warn, .ps-warn * {color: #ffff00 !important;}
    .ps-quote {border-left-color: #ffff00 !important;}
    </style>"""
st.markdown(css, unsafe_allow_html=True)


# ---------- Header ----------
if "result" in st.session_state:
    # Results: keep the header small, so on a phone the answer is on the first screen.
    st.markdown('<h1 style="font-size:1.4rem;padding:0;margin:0 0 .3rem">📬 PlainSpeak</h1>', unsafe_allow_html=True)
else:
    st.title("📬 PlainSpeak")
    st.markdown(U["tagline"])
    st.selectbox("🌐 Explain my letter in / Idioma / 语言 / Ngôn ngữ / اللغة", list(LANGUAGES),
                 index=list(LANGUAGES).index(language), key="language",
                 help="The summary and steps will be in this language.")
    if st.session_state.language != language:   # picked a new language: redraw everything in it
        st.session_state.lang_pref = st.session_state.language
        st.rerun()

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
    st.markdown(f"""<div class="ps-steps"{rtl}>
      <div class="ps-step"><span class="big">📷</span><b>{esc(U["step1t"])}</b><br>{esc(U["step1d"])}</div>
      <div class="ps-step"><span class="big">💬</span><b>{esc(U["step2t"])}</b><br>{esc(U["step2d"])}</div>
      <div class="ps-step"><span class="big">✅</span><b>{esc(U["step3t"])}</b><br>{esc(U["step3d"])}</div>
    </div>""", unsafe_allow_html=True)

    if not has_api_key():
        st.info(U["demo_mode"], icon="ℹ️")
    st.caption(U["privacy_line"])   # visible BEFORE anyone uploads, not hidden in a menu

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
            if st.button(label, type="primary", key="go-photo", disabled=not has_api_key() or bool(problems),
                         use_container_width=True):
                # Check again here on the server: a disabled button in the browser is not a real lock.
                if not upload_problems(pages):
                    st.session_state.request = {"files": [prepare_image(p.getvalue(), p.type) for p in pages],
                                                "source": "photo"}
                    st.rerun()

    with tab_text:
        pasted = st.text_area(U["paste_label"], height=180, max_chars=MAX_TEXT_CHARS, key="pasted",
                              placeholder=U["paste_placeholder"])
        st.caption(U["ids_note"])
        if st.button(U["explain"], type="primary", key="go-text", disabled=not has_api_key(),
                     use_container_width=True):
            if pasted.strip():
                clean, hidden = redact(pasted[:MAX_TEXT_CHARS])
                if hidden:
                    monitor.record("ids_hidden")
                st.session_state.request = {"text": clean, "source": "text",
                                            "notice": U["ids_hidden"].format(n=hidden) if hidden else None}
                st.rerun()
            else:
                st.warning(U["empty_box"])

    # One-click examples
    st.markdown(f"#### {U['examples_title']}")
    st.caption(U["examples_caption"])
    fake_mistake = st.toggle(U["mistake_toggle"], key="fake_mistake", help=U["mistake_help"])
    for col, (short, name) in zip(st.columns(len(LINK_EXAMPLES)), LINK_EXAMPLES.items()):
        icon = {"eviction": "🏠", "benefits": "🍎", "hospital": "🏥"}[short]
        if col.button(f"{icon} {U['ex_' + short]}", key=f"ex-{name}", use_container_width=True):
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
req = st.session_state.pop("request", None)   # take it out first, so a blocked request isn't retried forever
if req is not None and ai_allowed():
    source, notice = req.pop("source", "text"), req.pop("notice", None)
    with st.spinner(U["spinner"]):
        try:
            show_answer(analyze_letter(language, **req), language, source, notice)
            monitor.record("letter_ok")
        except AnalyzerError as e:
            monitor.record(monitor.kind_of_error(e.kind))
            st.error(U.get("err_" + e.kind, U["err_other"]), icon="🚫")
    if "result" in st.session_state:
        st.rerun()   # redraw from the top, so the results page gets its compact header (answer on screen one)


# ---------- Results screen ----------
def quote_html(quote: str, letter: str, t: dict) -> str:
    """The exact words from the letter, with a check mark if we found them in the letter."""
    if checks.quote_found(quote, letter):
        found = t["found_photo"] if st.session_state.get("result_source") == "photo" else t["found"]
        badge = f'<span class="ps-ok">✓ {esc(found)}</span>'
    else:
        badge = f'<span class="ps-warn">⚠ {esc(t["not_found"])}</span>'
    return f'<div class="ps-quote" dir="auto">“{esc(quote)}” — {badge}</div>'   # "auto": Arabic letters too


def show_result(a: LetterAnalysis, lang_name: str) -> None:
    code = LANGUAGES.get(lang_name, "en")
    t = {**ui(code), **labels(code)}   # every label in the language of THIS answer
    direction = "rtl" if code in RTL_LANGUAGES else "ltr"
    letter = a.original_text
    today = visitor_today()
    key = st.session_state.get("letter_key", "x")

    def card(body: str, extra_class: str = "") -> None:
        st.markdown(f'<div class="ps-card {extra_class}" dir="{direction}">{body}</div>', unsafe_allow_html=True)

    def heading(icon: str, text: str) -> None:
        st.markdown(f'<h3 dir="{direction}">{icon} {esc(text)}</h3>', unsafe_allow_html=True)

    if st.session_state.get("scrolled_for") != key:
        # A new answer: jump to the top of the page, so the countdown is the first thing you see
        # (otherwise the browser stays scrolled down where you pressed "Explain").
        st.session_state.scrolled_for = key
        # (A fixed snippet of our own code, never anything from a letter or the AI.)
        st.iframe("<script>for (const el of [window.parent, ...window.parent.document.querySelectorAll("
                  "'[data-testid=stMain], section.main, .main')]) { try { el.scrollTo({top: 0}); } catch (e) {} }"
                  "</script>", height=1, tab_index=-1, alt="")

    if st.button(f"⬅️ {t['start_over']}", key="start-over"):
        clear_answer()
        st.query_params.clear()   # so a shared link doesn't keep reopening the example
        st.rerun()
    if st.session_state.get("notice"):
        st.info(st.session_state.notice, icon="ℹ️")

    # --- At a glance: urgency, countdown, first step (first, so it's on a phone's first screen) ---
    icon = {"high": f"🔴 {t['urgent']}", "medium": f"🟠 {t['soon']}", "low": f"🟢 {t['not_urgent']}"}[a.urgency]
    glance = f'<div style="font-size:1.15em;font-weight:700">📄 {esc(a.document_type)}</div>' \
             f'<hr style="margin:.5rem 0"><b>{icon}</b> — {esc(a.urgency_reason)}'
    nxt = next_deadline(a, today=today)
    if nxt:
        days, d = nxt
        count = (t["days_left"].format(n=days) if days > 1 else t["day_left_one"] if days == 1
                 else t["due_today"] if days == 0 else t["passed"])
        glance += (f'<hr style="margin:.6rem 0"><span class="ps-countdown">⏰ {esc(count)}</span><br>'
                   f'{esc(t["next_deadline"])}: <b>{esc(friendly_date(d.date, code))}</b> — {esc(d.what)}')
    if a.actions:
        glance += f'<hr style="margin:.6rem 0">👉 <b>{esc(t["first_step"])}:</b> {esc(a.actions[0].step)}'
    card(glance, f"ps-{a.urgency}")
    st.caption(f"{t['from']}: {md(a.sender)}")

    # --- Summary + read aloud ---
    heading("💬", t["means"])
    card(f'<span style="font-size:1.1em">{esc(a.summary)}</span>')
    if st.button(f"🔊 {t['read_aloud']}", key="tts"):
        # Read everything that matters, so someone who can't read at all still gets it.
        parts = [a.summary]
        if nxt and nxt[0] >= 0:
            parts.append(f"{t['next_deadline']}: {friendly_date(nxt[1].date, code)}. {nxt[1].what}.")
        parts += [f"{i}. {s.step}" for i, s in enumerate(a.actions, 1)]
        audio = text_to_mp3(" ".join(parts), code) if limiters()["tts"].allow(visitor_id()) else None
        if audio:
            st.session_state.audio = (a.summary, audio, True)  # keep it, so the player doesn't vanish
        else:
            monitor.record("tts_failed")
            st.warning(t["tts_failed"])
    saved_audio = st.session_state.get("audio")
    if saved_audio and saved_audio[0] == a.summary:
        st.audio(saved_audio[1], format="audio/mp3", autoplay=saved_audio[2])   # plays straight away, once
        st.session_state.audio = (saved_audio[0], saved_audio[1], False)

    before, after = checks.reading_grade(letter), checks.reading_grade(a.summary)
    if code == "en" and before is not None and after is not None:
        st.caption(f"📉 Reading level: the letter needs grade **{before:.0f}**; this summary needs grade **{after:.0f}**.")

    # --- Deadlines ---
    if a.deadlines:
        heading("📅", t["dates"])
        verified = []
        for d in a.deadlines:
            quote_ok = checks.quote_found(d.source_quote, letter)
            if checks.deadline_is_trustworthy(d, letter):
                verified.append(d)
                when = f"<b>{esc(friendly_date(d.date, code))}</b>"
            elif quote_ok and checks.date_written_in(d.date, letter):
                # The sentence is real, but its date is a DIFFERENT date from elsewhere in the letter.
                when = (f"<b>{esc(friendly_date(d.date, code))}</b><br>"
                        f'<span class="ps-warn">⚠ {esc(t["date_mismatch"])}</span>')
            elif quote_ok:
                # No date written in the letter (or the AI worked one out itself): don't show a date we can't back up.
                when = f'<b>{esc(t["no_date"])}</b><br><span class="ps-warn">⏳ {esc(t["estimated"])}</span>'
            else:
                when = f"<b>{esc(friendly_date(d.date, code) or t['no_date'])}</b>"
            card(f"{when} — {esc(d.what)}{quote_html(d.source_quote, letter, t)}",
                 "" if d in verified else "ps-high")
        # Only dates we could find in the letter, next to their sentence, and still ahead, go into the calendar.
        ics = calendar_export.deadlines_to_ics(verified, today=today)
        if ics:
            st.download_button(f"📆 {t['add_calendar']}", ics, file_name="plainspeak-deadlines.ics",
                               mime="text/calendar", key="ics", on_click="ignore",
                               help="Opens in Google, Apple or Outlook Calendar, with a reminder 2 days before.")

    # --- Steps ---
    if a.actions:
        heading("✅", t["todo"])
        for i, s in enumerate(a.actions):
            st.checkbox(md(s.step), key=f"step-{key}-{i}")
            st.markdown(quote_html(s.source_quote, letter, t), unsafe_allow_html=True)

    # --- Money ---
    if a.money:
        heading("💵", t["money"])
        for m in a.money:
            card(f"<b>{esc(m.amount)}</b> — {esc(m.what)}{quote_html(m.source_quote, letter, t)}",
                 "" if checks.quote_found(m.source_quote, letter) else "ps-high")

    # --- Contacts: a number is only tap-to-call if it's really in the letter ---
    if a.contacts:
        heading("☎️", t["contact"])
        for c in a.contacts:
            lines = [f"<b>{esc(c.name)}</b> — {esc(c.why)}"]
            if c.phone and checks.phone_in_letter(c.phone, letter):
                digits = "".join(ch for ch in c.phone if ch.isdigit() or ch == "+")
                lines.append(f'📞 <a href="tel:{digits}">{esc(c.phone)}</a>')
            elif c.phone:
                lines.append(f'📞 {esc(c.phone)} <span class="ps-warn">⚠ {esc(t["phone_unverified"])}</span>')
            if c.email:
                lines.append(f"✉️ {esc(c.email)}")
            if c.address:
                lines.append(f"📍 {esc(c.address)}")
            card("<br>".join(lines))

    if a.rights:
        heading("🛡️", t["rights"])
        card("<br>".join(f"• {esc(r)}" for r in a.rights))

    # --- Ask a question ---
    heading("🙋", t["ask_title"])
    suggestions = demo.suggested_questions(a) or ([t["q1"], t["q2"], t["q3"], t["q4"]] if has_api_key() else [])
    asked = None
    if suggestions:
        st.caption(t["suggested"])
        for i, q in enumerate(suggestions):
            if st.button(q, key=f"suggest-{key}-{i}"):
                asked = q
    with st.form("ask-form", clear_on_submit=True):
        typed = st.text_input(t["ask_title"], placeholder=t["ask_placeholder"], label_visibility="collapsed",
                              max_chars=500, disabled=not has_api_key())
        if st.form_submit_button(t["ask_button"], disabled=not has_api_key()) and typed:
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

    if a.confidence != "high" or a.unclear_points:
        sure = {"high": "", "medium": " (?)", "low": " (??)"}[a.confidence]
        heading("❓", t["not_sure"] + sure)
        card("<br>".join(f"• {esc(p)}" for p in a.unclear_points) or "—")

    # --- Human help ---
    if a.needs_human_help:
        st.warning(f"**{md(t['talk_person'])}** {md(a.help_reason)}", icon="🧑‍⚖️")
    else:
        st.success(md(a.help_reason), icon="👍")
    heading("🤝", t["free_help"])
    st.markdown(f"📞 {t['help_211']}\n\n⚖️ {t['help_law']}")

    # --- Keep it ---
    col_print, col_save = st.columns(2)
    col_print.download_button(f"🖨️ {t['print']}", summary_html(a, code), file_name="plainspeak-summary.html",
                              mime="text/html", use_container_width=True, key="print", on_click="ignore",
                              help="A simple page you can print, or send to someone who helps you.")
    if st.session_state.get("saved_id"):
        col_save.caption(f"✓ {t['saved']}")
    elif col_save.button(f"💾 {t['save']}", use_container_width=True, key="save"):
        st.session_state.saved_id = store.save(a, lang_name)
        st.rerun()

    # --- Send to family: opens the person's OWN WhatsApp / texts / email, only when they tap ---
    heading("👪", t["share"])
    links = share_links(share_text(a, code, today=today), subject=f"PlainSpeak: {a.document_type}")
    for col, (app_name, app_icon) in zip(st.columns(3), [("WhatsApp", "💬"), ("SMS", "📱"), ("Email", "✉️")]):
        col.link_button(f"{app_icon} {app_name}", links[app_name], use_container_width=True)

    with st.expander(t["show_original"]):
        if st.session_state.get("result_source") == "photo":
            st.caption("ℹ️ " + t["found_photo"])
        st.text(letter)


if "result" in st.session_state:
    show_result(st.session_state.result, st.session_state.get("result_lang", language))
else:
    start_screen()
