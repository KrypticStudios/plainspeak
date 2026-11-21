"""PlainSpeak - understand any official letter.

Run with:  .venv/bin/streamlit run app.py
"""

import os
import uuid

import streamlit as st

from plainspeak import calendar_export, checks, demo, history
from plainspeak.analyzer import AnalyzerError, analyze_letter, ask_question, has_api_key
from plainspeak.export import next_deadline, summary_html
from plainspeak.images import prepare_image
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

# Who owns saved letters. On your own computer (PLAINSPEAK_LOCAL=1) they're kept between visits.
# On the public website each visitor gets a private random ID, so nobody sees anyone else's letters.
if "owner" not in st.session_state:
    st.session_state.owner = "local" if os.getenv("PLAINSPEAK_LOCAL") == "1" else uuid.uuid4().hex
OWNER = st.session_state.owner

# ---------- Sidebar: language, accessibility, history ----------
with st.sidebar:
    st.header("⚙️ Display")
    big_text = st.toggle("Larger text", value=False)
    high_contrast = st.toggle("High contrast", value=False)

    st.divider()
    st.header("🗂️ My letters")
    recent = history.list_recent(OWNER)
    if not recent:
        st.caption("Letters you save show up here. Only you can see them."
                   + ("" if OWNER == "local" else " They're cleared when you close this page."))
    for letter_id, saved_at, lang, doc_type in recent:
        col_open, col_del = st.columns([4, 1])
        if col_open.button(f"{doc_type} · {saved_at[:10]}", key=f"open-{letter_id}", use_container_width=True):
            loaded = history.load(letter_id, OWNER)
            if loaded:
                st.session_state.result, st.session_state.result_lang = loaded
                st.session_state.saved_id = letter_id
                st.session_state.pop("audio", None)
                st.session_state.pop("qa", None)
        if col_del.button("🗑️", key=f"del-{letter_id}", help="Delete this letter"):
            history.delete(letter_id, OWNER)
            st.rerun()

    st.divider()
    st.caption("⚠️ PlainSpeak explains letters. It is **not** legal or medical advice. "
               "For serious matters, talk to a lawyer, caseworker, or the office that sent the letter.")


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
                                   type=["png", "jpg", "jpeg", "webp", "heic", "pdf"])
        st.caption("📸 Tips: lay the letter flat, use good light, and get the whole page in the photo.")
        use_camera = st.toggle("Use my camera instead")
        snap = st.camera_input("Take a photo of your letter") if use_camera else None
        pages = ([snap] if snap else []) + list(uploads or [])
        if pages:
            images = [p for p in pages if p.type.startswith("image/")]
            if images:
                st.image(images, caption=[f"Page {i}" for i in range(1, len(images) + 1)], width=140)
            if st.button(f"Explain my letter ({len(pages)} page{'s' if len(pages) > 1 else ''})", type="primary",
                         key="go-photo", disabled=not has_api_key(), use_container_width=True):
                st.session_state.request = {"files": [prepare_image(p.getvalue(), p.type) for p in pages]}
                st.rerun()

    with tab_text:
        pasted = st.text_area("Paste the words from your letter", height=180,
                              placeholder="Copy and paste the text of the letter here…")
        if st.button("Explain my letter", type="primary", key="go-text", disabled=not has_api_key(),
                     use_container_width=True):
            if pasted.strip():
                st.session_state.request = {"text": pasted}
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
if "request" in st.session_state:
    req = st.session_state.pop("request")
    with st.spinner("Reading your letter… this takes about 10–20 seconds."):
        try:
            show_answer(analyze_letter(language, **req), language)
        except AnalyzerError as e:
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
    nxt = next_deadline(a)
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
            st.warning("Read-aloud needs an internet connection. Please try again.")
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
            when = friendly_date(d.date, code) or t["no_date"]
            ok = checks.quote_found(d.source_quote, a.original_text)
            if ok:
                verified.append(d)
            card(f"<b>{esc(when)}</b> — {esc(d.what)}{quote_html(d.source_quote, a.original_text, t)}",
                 "" if ok else "ps-high")
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
                    answer = ask_question(a.original_text, asked, lang_name)
                except AnalyzerError as e:
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
        st.session_state.saved_id = history.save(a, lang_name, OWNER)
        st.rerun()

    with st.expander(t["show_original"]):
        st.text(a.original_text)


if "result" in st.session_state:
    show_result(st.session_state.result, st.session_state.get("result_lang", language))
else:
    start_screen()
