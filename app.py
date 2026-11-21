"""PlainSpeak - understand any official letter.

Run with:  .venv/bin/streamlit run app.py
"""

import importlib
import os
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

import plainspeak.schema  # noqa: E402  (loaded first: the other files use it)

# Streamlit Cloud updates the app when we push to GitHub, but it can keep running OLD copies of our
# other files (plainspeak/*.py). That once crashed the live site. So: if any of our files changed on
# disk since it was loaded, reload it. This costs nothing when nothing has changed.
for _name in ["schema", "checks", "ui_text", "calendar_export", "export", "images", "privacy", "speech",
              "history", "demo", "analyzer", "monitor"]:
    _mod = importlib.import_module(f"plainspeak.{_name}")
    _mtime = os.path.getmtime(_mod.__file__)
    if getattr(_mod, "_loaded_mtime", None) != _mtime:   # changed, or an old copy from before this check
        _mod = importlib.reload(_mod)
    _mod._loaded_mtime = _mtime

from plainspeak import calendar_export, checks, demo, history, monitor  # noqa: E402
from plainspeak.analyzer import AnalyzerError, analyze_letter, ask_question, has_api_key
from plainspeak.export import next_deadline, summary_html
from plainspeak.images import prepare_image
from plainspeak.privacy import MAX_PAGES, MAX_TEXT_CHARS, RateLimiter, check_upload, redact
from plainspeak.schema import LetterAnalysis
from plainspeak.speech import LANGUAGES, RTL_LANGUAGES, text_to_mp3
from plainspeak.ui_text import GENERIC_QUESTIONS, friendly_date, labels

st.set_page_config(page_title="PlainSpeak", page_icon="📬", layout="centered")

# On Streamlit Cloud the key lives in the app's private "Secrets" box, not in a .env file.
try:
    for name in ("GEMINI_API_KEY", "GEMINI_MODEL"):
        if name in st.secrets and not os.getenv(name):
            os.environ[name] = st.secrets[name]
except FileNotFoundError:
    pass  # running locally with no secrets file: .env is used instead

# Where "My letters" are kept.
#  - On your own computer (PLAINSPEAK_LOCAL=1): in a file, so they're still there next time.
#  - On the public website: only in this visitor's session memory, never written to the server's disk.
LOCAL_MODE = os.getenv("PLAINSPEAK_LOCAL") == "1"

PRIVACY_NOTE = """
- **We don't keep your letters.** On this website, letters you save stay in your browser session only and are
  deleted when you close the page. Nothing is written to our server's disk, and we don't log what you upload.
- **ID numbers are hidden** in typed or pasted text before it's sent to the AI.
- **Read-aloud** sends the plain-language summary and steps (not your letter) to Google's text-to-speech
  service to turn them into audio. It only happens when you press the 🔊 button.
- **The AI is Google Gemini.** This demo uses Gemini's *free* tier. Under Google's terms, free-tier content may be
  used to improve Google's products and may be read by human reviewers. So please **don't upload letters with
  sensitive details** here. Cover ID numbers, or use the example letters. A real launch would use the paid tier,
  where Google doesn't use your data to improve its products.
- Your API key and the AI connection stay on our server. Your browser never sees them.
"""
store = history.DiskStore() if LOCAL_MODE else history.SessionStore(st.session_state)

# Limits so one person (or a bot) can't use up the free AI quota for everyone.
if "visitor" not in st.session_state:
    st.session_state.visitor = uuid.uuid4().hex


@st.cache_resource
def limiters() -> tuple[RateLimiter, RateLimiter]:
    """Shared by every visitor: 6 AI requests per visitor per 10 minutes, 300 per day for the whole site."""
    return RateLimiter(limit=6, window=600), RateLimiter(limit=int(os.getenv("MAX_DAILY_AI_CALLS", "300")),
                                                          window=86_400)


def ai_allowed() -> bool:
    per_visitor, whole_site = limiters()
    if not per_visitor.allow(st.session_state.visitor):
        monitor.record("rate_limited")
        st.warning("You've asked a lot in a short time. Please wait a few minutes and try again.", icon="⏳")
        return False
    if not whole_site.allow("site"):
        monitor.record("ai_limit")
        st.warning("PlainSpeak has reached its free daily limit. Please try again tomorrow, "
                   "or call 211 for help with your letter.", icon="⏳")
        return False
    return True

# ---------- Sidebar: language, accessibility, history ----------
with st.sidebar:
    st.header("⚙️ Display")
    big_text = st.toggle("Larger text", value=False)
    high_contrast = st.toggle("High contrast", value=False)

    st.divider()
    st.header("🗂️ My letters")
    recent = store.list_recent()
    if not recent:
        st.caption("Letters you save show up here. Only you can see them."
                   + ("" if LOCAL_MODE else " They're deleted when you close this page."))
    for letter_id, saved_at, lang, doc_type in recent:
        col_open, col_del = st.columns([4, 1])
        if col_open.button(f"{doc_type} · {saved_at[:10]}", key=f"open-{letter_id}", use_container_width=True):
            loaded = store.load(letter_id)
            if loaded:
                st.session_state.result, st.session_state.result_lang = loaded
                st.session_state.saved_id = letter_id
                st.session_state.pop("audio", None)
                st.session_state.pop("qa", None)
        if col_del.button("🗑️", key=f"del-{letter_id}", help="Delete this letter"):
            store.delete(letter_id)
            st.rerun()
    if recent and st.button("🗑️ Delete all my letters", use_container_width=True):
        store.delete_all()
        for key in ("result", "result_lang", "saved_id", "audio", "qa"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.caption("⚠️ PlainSpeak explains letters. It is **not** legal or medical advice. "
               "For serious matters, talk to a lawyer, caseworker, or the office that sent the letter.")
    with st.expander("🔒 Privacy"):
        st.markdown(PRIVACY_NOTE)


# ---------- Accessibility styles ----------
css = """
<style>
.ps-card {border-radius: 12px; padding: 1rem 1.2rem; margin: .5rem 0; border: 2px solid #cbd5e1; background: #f8fafc;}
.ps-high {border-color: #b91c1c; background: #fef2f2;}
.ps-medium {border-color: #b45309; background: #fffbeb;}
.ps-low {border-color: #15803d; background: #f0fdf4;}
.ps-quote {font-size: .9em; color: #334155; border-left: 3px solid #94a3b8; padding-left: .6rem; margin-top: .2rem;}
.ps-warn {color: #b91c1c; font-weight: 600;}
.ps-ok {color: #15803d; font-weight: 600;}
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
    [data-testid="stSelectbox"] div, [data-baseweb="select"] div, [data-baseweb="select"] input, [data-baseweb="popover"] *, [role="listbox"] *,
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
st.markdown("""<style>
.ps-steps {display: flex; gap: .6rem; margin: .6rem 0 1rem;}
.ps-step {flex: 1; text-align: center; padding: .8rem .4rem; border-radius: 12px; border: 2px solid #cbd5e1;}
.ps-step .big {font-size: 1.8rem; display: block;}
.ps-countdown {font-size: 1.6rem; font-weight: 700;}
@media (max-width: 640px) {.ps-steps {flex-direction: column;}}
</style>""", unsafe_allow_html=True)


def visitor_today() -> date:
    """Today's date where the VISITOR is. The server runs on UTC, so after ~4 PM in California
    its 'today' is already tomorrow, which would make the countdown one day short."""
    for tz in (st.context.timezone, "America/Los_Angeles"):   # the visitor's, else the hackathon's (PST)
        try:
            return datetime.now(ZoneInfo(tz)).date()
        except Exception:   # browser didn't say, or the server has no timezone data
            continue
    return date.today()


def esc(s: str) -> str:
    """Make text safe to put inside HTML (so a letter can't inject code into the page)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def show_answer(result: LetterAnalysis, lang_name: str) -> None:
    """Put an answer on screen and switch to the results view."""
    st.session_state.result, st.session_state.result_lang = result, lang_name
    st.session_state.saved_id = None
    st.session_state.pop("audio", None)
    st.session_state.pop("qa", None)


# ---------- Header ----------
st.title("📬 PlainSpeak")
st.markdown("**Got a confusing letter?** We'll tell you what it means, what to do, and by when, "
            "in plain words and in your language.")

language = st.selectbox("🌐 Explain my letter in / Idioma / 语言 / Ngôn ngữ / اللغة", list(LANGUAGES),
                        help="The summary and steps will be in this language.")


# ---------- Start screen (shown when there is no answer yet) ----------
def start_screen() -> None:
    st.markdown("""<div class="ps-steps">
      <div class="ps-step"><span class="big">📷</span><b>1. Add your letter</b><br>Photo, PDF, or paste the words</div>
      <div class="ps-step"><span class="big">💬</span><b>2. Read it in plain words</b><br>In your language, or listen</div>
      <div class="ps-step"><span class="big">✅</span><b>3. Know what to do</b><br>Steps, dates and who to call</div>
    </div>""", unsafe_allow_html=True)

    if not has_api_key():
        st.info("**Demo mode:** reading your own letters needs a free AI key (see README). "
                "You can still try the example letters below.", icon="ℹ️")

    tab_photo, tab_text = st.tabs(["📷 Photo or PDF", "⌨️ Paste the words"])

    with tab_photo:
        uploads = st.file_uploader("Add a photo of each page (or one PDF)", accept_multiple_files=True,
                                   type=["png", "jpg", "jpeg", "webp", "pdf"])
        st.caption("📸 Tips: lay the letter flat, use good light, and get the whole page in the photo. "
                   "🔒 Cover ID numbers (like a Social Security or account number) with a finger or paper. "
                   "PlainSpeak doesn't need them.")
        use_camera = st.toggle("Use my camera instead")
        snap = st.camera_input("Take a photo of your letter") if use_camera else None
        pages = ([snap] if snap else []) + list(uploads or [])
        if pages:
            images = [p for p in pages if p.type.startswith("image/")]
            if images:
                st.image(images, caption=[f"Page {i}" for i in range(1, len(images) + 1)], width=140)
            problems = [f"{p.name}: {err}" for p in pages if (err := check_upload(p.getvalue(), p.type))]
            if len(pages) > MAX_PAGES:
                problems.append(f"Please add at most {MAX_PAGES} pages at a time.")
            for problem in problems:
                st.error(problem, icon="🚫")
            reported = st.session_state.setdefault("reported_uploads", set())
            for p in pages:   # count each refused file once, not on every page refresh
                if p.file_id not in reported and check_upload(p.getvalue(), p.type):
                    reported.add(p.file_id)
                    monitor.record("bad_upload")
            if st.button(f"Explain my letter ({len(pages)} page{'s' if len(pages) > 1 else ''})", type="primary",
                         key="go-photo", disabled=not has_api_key() or bool(problems), use_container_width=True):
                st.session_state.request = {"files": [prepare_image(p.getvalue(), p.type) for p in pages]}
                st.rerun()

    with tab_text:
        pasted = st.text_area("Paste the words from your letter", height=180, max_chars=MAX_TEXT_CHARS,
                              placeholder="Copy and paste the text of the letter here…")
        st.caption("🔒 ID numbers (Social Security, card, account and case numbers) are hidden automatically "
                   "before your letter is sent to the AI.")
        if st.button("Explain my letter", type="primary", key="go-text", disabled=not has_api_key(),
                     use_container_width=True):
            if pasted.strip():
                clean, hidden = redact(pasted)
                if hidden:
                    monitor.record("ids_hidden")
                    st.session_state.notice = f"🔒 We hid {hidden} ID number(s) before sending your letter to the AI."
                st.session_state.request = {"text": clean}
                st.rerun()
            else:
                st.warning("The box is empty. Paste the words from your letter first.")

    # One-click examples
    st.markdown("#### No letter handy? See an example")
    st.caption("These letters are **made up**, so you can try PlainSpeak without sharing anything personal.")
    fake_mistake = st.toggle("🧪 Show how PlainSpeak catches AI mistakes",
                             help="Adds one made-up deadline, the kind of thing an AI might invent, "
                                  "so you can see our check flag it.")
    cols = st.columns(len(demo.SAMPLES))
    for col, (name, icon) in zip(cols, [("Eviction notice (rent)", "🏠"), ("Food benefits renewal", "🍎"),
                                        ("Hospital bill", "🏥")]):
        if col.button(f"{icon} {name}", key=f"ex-{name}", use_container_width=True):
            saved = demo.demo_analysis(name, language)
            if saved is None and has_api_key():
                st.session_state.request = {"text": demo.sample_text(name)}   # ask the AI live
                st.rerun()
            else:
                if saved is None:  # no key and no saved answer in this language -> fall back to English
                    saved, lang_shown = demo.demo_analysis(name, "English"), "English"
                    st.session_state.notice = (f"This example is saved in English only. "
                                               f"Add an AI key to see it in {language}.")
                else:
                    lang_shown = language
                show_answer(demo.with_simulated_mistake(saved) if fake_mistake else saved, lang_shown)
                st.rerun()


# ---------- Run the AI ----------
req = st.session_state.pop("request", None)   # take it out first, so a blocked request isn't retried forever
if req is not None and ai_allowed():
    with st.spinner("Reading your letter… this usually takes a few seconds."):
        try:
            show_answer(analyze_letter(language, **req), language)
            monitor.record("letter_ok")
        except AnalyzerError as e:
            monitor.record(monitor.kind_of_error(str(e)))
            st.error(str(e), icon="🚫")


# ---------- Results screen ----------
def quote_html(quote: str, letter: str, t: dict) -> str:
    """The exact words from the letter, with a check mark if we found them in the letter."""
    if checks.quote_found(quote, letter):
        badge = f'<span class="ps-ok">✓ {t["found"]}</span>'
    else:
        badge = f'<span class="ps-warn">⚠ {t["not_found"]}</span>'
    return f'<div class="ps-quote" dir="ltr">“{esc(quote)}” — {badge}</div>'


def show_result(a: LetterAnalysis, lang_name: str) -> None:
    code = LANGUAGES.get(lang_name, "en")
    t = labels(code)  # headings in the reader's language
    direction = "rtl" if code in RTL_LANGUAGES else "ltr"

    def card(html: str, extra_class: str = "") -> None:
        st.markdown(f'<div class="ps-card {extra_class}" dir="{direction}">{html}</div>', unsafe_allow_html=True)

    def heading(icon: str, text: str) -> None:
        st.markdown(f'<h3 dir="{direction}">{icon} {esc(text)}</h3>', unsafe_allow_html=True)

    if st.button(f"⬅️ {t['start_over']}", key="start-over"):
        for key in ("result", "result_lang", "saved_id", "audio", "qa"):
            st.session_state.pop(key, None)
        st.rerun()
    if "notice" in st.session_state:
        st.info(st.session_state.pop("notice"), icon="ℹ️")

    st.markdown(f'<h2 dir="{direction}">📄 {esc(a.document_type)}</h2>', unsafe_allow_html=True)
    st.caption(f"{t['from']}: {a.sender}")

    # --- At a glance: urgency, countdown, first step ---
    icon = {"high": f"🔴 {t['urgent']}", "medium": f"🟠 {t['soon']}", "low": f"🟢 {t['not_urgent']}"}[a.urgency]
    glance = f"<b>{icon}</b> — {esc(a.urgency_reason)}"
    nxt = next_deadline(a, today=visitor_today())
    if nxt:
        days, d = nxt
        if days > 0:
            count = t["days_left"].format(n=days)
        elif days == 0:
            count = t["due_today"]
        else:
            count = t["passed"]
        when = friendly_date(d.date, code)
        glance += (f'<hr style="margin:.6rem 0"><span class="ps-countdown">⏰ {esc(count)}</span><br>'
                   f'{esc(t["next_deadline"])}: <b>{esc(when)}</b> — {esc(d.what)}')
    if a.actions:
        glance += f'<hr style="margin:.6rem 0">👉 <b>{esc(t["first_step"])}:</b> {esc(a.actions[0].step)}'
    card(glance, f"ps-{a.urgency}")

    # --- Summary + read aloud ---
    heading("💬", t["means"])
    card(f'<span style="font-size:1.1em">{esc(a.summary)}</span>')
    if st.button(f"🔊 {t['read_aloud']}", key="tts"):
        # Read the summary, then the steps, so someone who can't read at all still gets everything.
        script = a.summary + " " + " ".join(f"{i}. {s.step}" for i, s in enumerate(a.actions, 1))
        audio = text_to_mp3(script, code)
        if audio:
            st.session_state.audio = (a.summary, audio)  # keep it so the player doesn't vanish on the next click
        else:
            monitor.record("tts_failed")
            st.warning("Read-aloud isn't working right now. Please try again in a moment.")
    saved_audio = st.session_state.get("audio")
    if saved_audio and saved_audio[0] == a.summary:
        st.audio(saved_audio[1], format="audio/mp3")

    before, after = checks.reading_grade(a.original_text), checks.reading_grade(a.summary)
    if before and after and code == "en":
        st.caption(f"📉 Reading level: the letter needs grade **{before:.0f}**; this summary needs grade **{after:.0f}**.")

    # --- Deadlines ---
    if a.deadlines:
        heading("📅", t["dates"])
        verified = []
        for d in a.deadlines:
            quote_ok = checks.quote_found(d.source_quote, a.original_text)
            if checks.deadline_is_trustworthy(d, a.original_text):
                verified.append(d)
                when = f"<b>{esc(friendly_date(d.date, code))}</b>"
            else:
                # No date written in the letter (or the AI worked one out itself): don't show a date we can't back up.
                when = f'<b>{esc(t["no_date"])}</b><br><span class="ps-warn">⏳ {esc(t["estimated"])}</span>' \
                    if quote_ok else f"<b>{esc(friendly_date(d.date, code) or t['no_date'])}</b>"
            card(f"{when} — {esc(d.what)}{quote_html(d.source_quote, a.original_text, t)}",
                 "" if quote_ok else "ps-high")
        # Only dates we could find in the letter go into the calendar.
        ics = calendar_export.deadlines_to_ics(verified)
        if ics:
            st.download_button(f"📆 {t['add_calendar']}", ics, file_name="plainspeak-deadlines.ics",
                               mime="text/calendar",
                               help="Opens in Google, Apple or Outlook Calendar, with a reminder 2 days before.")

    # --- Steps ---
    if a.actions:
        heading("✅", t["todo"])
        for i, s in enumerate(a.actions):
            st.checkbox(s.step, key=f"step-{i}")
            st.markdown(quote_html(s.source_quote, a.original_text, t), unsafe_allow_html=True)

    # --- Money ---
    if a.money:
        heading("💵", t["money"])
        for m in a.money:
            card(f"<b>{esc(m.amount)}</b> — {esc(m.what)}{quote_html(m.source_quote, a.original_text, t)}")

    # --- Contacts ---
    if a.contacts:
        heading("☎️", t["contact"])
        for c in a.contacts:
            lines = [f"<b>{esc(c.name)}</b> — {esc(c.why)}"]
            if c.phone:
                digits = "".join(ch for ch in c.phone if ch.isdigit() or ch == "+")
                lines.append(f'📞 <a href="tel:{digits}">{esc(c.phone)}</a>')
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
    suggestions = demo.suggested_questions(a) or (GENERIC_QUESTIONS if has_api_key() else [])
    asked = None
    if suggestions:
        st.caption(t["suggested"])
        for i, q in enumerate(suggestions):
            if st.button(q, key=f"suggest-{i}"):
                asked = q
    with st.form("ask-form", clear_on_submit=True):
        typed = st.text_input(t["ask_title"], placeholder=t["ask_placeholder"], label_visibility="collapsed",
                              max_chars=500, disabled=not has_api_key())
        if st.form_submit_button(t["ask_button"], disabled=not has_api_key()) and typed:
            asked = typed
    if not has_api_key():
        st.caption("Typing your own question needs an AI key. Try a common question above.")
    if asked:
        answer = demo.demo_answer(a, asked)
        if answer is None:
            with st.spinner("…"):
                try:
                    answer = ask_question(a.original_text, redact(asked)[0], lang_name) if ai_allowed() else None
                    if answer:
                        monitor.record("question_ok")
                except AnalyzerError as e:
                    monitor.record(monitor.kind_of_error(str(e)))
                    st.error(str(e), icon="🚫")
        if answer:
            st.session_state.qa = [(asked, answer)] + st.session_state.get("qa", [])[:4]
    for q, ans in st.session_state.get("qa", []):
        body = f"<b>❔ {esc(q)}</b><br>{esc(ans.answer)}"
        if not ans.answered_from_letter:
            body += f'<br><span class="ps-warn">ℹ️ {esc(t["not_in_letter"])}</span>'
        for quote in ans.source_quotes:
            body += quote_html(quote, a.original_text, t)
        if ans.who_to_ask:
            body += f"<br>👤 <b>{esc(t['who_to_ask'])}:</b> {esc(ans.who_to_ask)}"
        card(body)

    if a.confidence != "high" or a.unclear_points:
        sure = {"high": "", "medium": " (?)", "low": " (??)"}[a.confidence]
        heading("❓", t["not_sure"] + sure)
        card("<br>".join(f"• {esc(p)}" for p in a.unclear_points) or "—")

    # --- Human help ---
    if a.needs_human_help:
        st.warning(f"**{t['talk_person']}** {a.help_reason}", icon="🧑‍⚖️")
    else:
        st.success(a.help_reason, icon="👍")
    heading("🤝", t["free_help"])
    card('📞 <b><a href="tel:211">211</a></b> — free, confidential help finding local services (housing, food, bills), '
         '24/7, in many languages · <a href="https://www.211.org" target="_blank">211.org</a><br>'
         '⚖️ <b><a href="https://www.lawhelp.org" target="_blank">LawHelp.org</a></b> — find free legal aid in your state')

    # --- Keep it ---
    col_print, col_save = st.columns(2)
    col_print.download_button(f"🖨️ {t['print']}", summary_html(a, code), file_name="plainspeak-summary.html",
                              mime="text/html", use_container_width=True,
                              help="A simple page you can print, or send to someone who helps you.")
    if st.session_state.get("saved_id"):
        col_save.caption(f"✓ {t['saved']}")
    elif col_save.button(f"💾 {t['save']}", use_container_width=True):
        st.session_state.saved_id = store.save(a, lang_name)
        st.rerun()

    with st.expander(t["show_original"]):
        st.text(a.original_text)


if "result" in st.session_state:
    show_result(st.session_state.result, st.session_state.get("result_lang", language))
else:
    start_screen()
