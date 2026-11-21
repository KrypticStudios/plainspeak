"""PlainSpeak - understand any official letter.

Run with:  .venv/bin/streamlit run app.py
"""

import streamlit as st

from plainspeak import calendar_export, checks, demo, history
from plainspeak.analyzer import AnalyzerError, analyze_letter, has_api_key
from plainspeak.schema import LetterAnalysis
from plainspeak.speech import LANGUAGES, RTL_LANGUAGES, text_to_mp3
from plainspeak.ui_text import friendly_date, labels

st.set_page_config(page_title="PlainSpeak", page_icon="📬", layout="centered")

# ---------- Sidebar: language, accessibility, history ----------
with st.sidebar:
    st.header("⚙️ Display")
    big_text = st.toggle("Larger text", value=False)
    high_contrast = st.toggle("High contrast", value=False)

    st.divider()
    st.header("🗂️ My letters")
    recent = history.list_recent()
    if not recent:
        st.caption("Letters you save will show up here. They stay on this computer.")
    for letter_id, saved_at, lang, doc_type in recent:
        col_open, col_del = st.columns([4, 1])
        if col_open.button(f"{doc_type} · {saved_at[:10]}", key=f"open-{letter_id}", use_container_width=True):
            loaded = history.load(letter_id)
            if loaded:
                st.session_state.result, st.session_state.result_lang = loaded
                st.session_state.saved_id = letter_id
        if col_del.button("🗑️", key=f"del-{letter_id}", help="Delete this letter"):
            history.delete(letter_id)
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

# ---------- Header ----------
st.title("📬 PlainSpeak")
st.markdown("**Got a confusing letter?** Take a photo. We'll tell you what it means, what to do, and by when, "
            "in plain words and in your language.")

if not has_api_key():
    st.info("Demo mode: no AI key is set up, so you can try the **sample letters** below. "
            "To read your own letters, add a free Gemini key (see README).", icon="ℹ️")

language = st.selectbox("🌐 Explain my letter in / Idioma / 语言 / Ngôn ngữ / اللغة", list(LANGUAGES),
                        help="The summary and steps will be in this language.")

# ---------- Input ----------
tab_photo, tab_text, tab_sample = st.tabs(["📷 Photo or file", "⌨️ Paste text", "📄 Try a sample"])

with tab_photo:
    upload = st.file_uploader("Upload a photo or PDF of your letter", type=["png", "jpg", "jpeg", "webp", "pdf"],
                              help="Make sure the whole page is in the photo and the words are sharp.")
    use_camera = st.toggle("Use my camera instead")
    snap = st.camera_input("Take a photo of your letter") if use_camera else None
    photo = snap or upload
    if photo:
        if photo.type.startswith("image/"):
            st.image(photo, caption="Your letter", width=300)
        if st.button("Explain my letter", type="primary", key="go-photo", disabled=not has_api_key()):
            st.session_state.request = {"file_bytes": photo.getvalue(), "mime_type": photo.type}

with tab_text:
    pasted = st.text_area("Paste the words from your letter", height=200,
                          placeholder="Copy and paste the text of the letter here…")
    if st.button("Explain my letter", type="primary", key="go-text", disabled=not has_api_key()):
        if pasted.strip():
            st.session_state.request = {"text": pasted}
        else:
            st.warning("The box is empty. Paste the text of your letter first.")

with tab_sample:
    st.caption("These are **made-up** letters, so you can see how PlainSpeak works without sharing anything personal.")
    sample = st.selectbox("Pick a sample letter", list(demo.SAMPLES))
    with st.expander("Read the original sample letter"):
        st.text(demo.sample_text(sample))
    instant = demo.demo_analysis(sample, language)
    use_instant = instant is not None and (not has_api_key() or st.toggle(
        "Use the saved demo answer (works offline)", value=True))
    fake_mistake = use_instant and st.toggle(
        "🧪 Show how PlainSpeak catches AI mistakes",
        help="Adds one made-up deadline, the kind of thing an AI might invent, so you can see our check flag it.")
    if st.button("Explain this sample", type="primary", key="go-sample"):
        if use_instant:
            st.session_state.result = demo.with_simulated_mistake(instant) if fake_mistake else instant
            st.session_state.result_lang = language
            st.session_state.saved_id = None
        elif has_api_key():
            st.session_state.request = {"text": demo.sample_text(sample)}
        else:
            langs = ", ".join(demo.demo_languages(sample))
            st.warning(f"In demo mode this sample is available in: {langs}. Change the language in Settings, "
                       "or add an AI key to use any language.")

# ---------- Run the AI ----------
if "request" in st.session_state:
    req = st.session_state.pop("request")
    with st.spinner("Reading your letter… this takes about 10–20 seconds."):
        try:
            st.session_state.result = analyze_letter(language, **req)
            st.session_state.result_lang = language
            st.session_state.saved_id = None
        except AnalyzerError as e:
            st.error(str(e), icon="🚫")


# ---------- Show the result ----------
def esc(s: str) -> str:
    """Make text safe to put inside HTML (so a letter can't inject code into the page)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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

    st.divider()
    st.markdown(f'<h2 dir="{direction}">📄 {esc(a.document_type)}</h2>', unsafe_allow_html=True)
    st.caption(f"{t['from']}: {a.sender}")

    icon = {"high": f"🔴 {t['urgent']}", "medium": f"🟠 {t['soon']}", "low": f"🟢 {t['not_urgent']}"}[a.urgency]
    card(f"<b>{icon}</b> — {esc(a.urgency_reason)}", f"ps-{a.urgency}")

    # Summary + read aloud
    heading("💬", t["means"])
    card(f'<span style="font-size:1.1em">{esc(a.summary)}</span>')
    if st.button(f"🔊 {t['read_aloud']}", key="tts"):
        audio = text_to_mp3(a.summary, code)
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

    if a.confidence != "high" or a.unclear_points:
        sure = {"high": "", "medium": " (?)", "low": " (??)"}[a.confidence]
        heading("❓", t["not_sure"] + sure)
        card("<br>".join(f"• {esc(p)}" for p in a.unclear_points) or "—")

    # Deadlines
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

    # Steps
    if a.actions:
        heading("✅", t["todo"])
        for i, s in enumerate(a.actions):
            st.checkbox(s.step, key=f"step-{i}")
            st.markdown(quote_html(s.source_quote, a.original_text, t), unsafe_allow_html=True)

    # Money
    if a.money:
        heading("💵", t["money"])
        for m in a.money:
            card(f"<b>{esc(m.amount)}</b> — {esc(m.what)}{quote_html(m.source_quote, a.original_text, t)}")

    # Contacts
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

    if a.needs_human_help:
        st.warning(f"**{t['talk_person']}** {a.help_reason}", icon="🧑‍⚖️")
    else:
        st.success(a.help_reason, icon="👍")

    with st.expander(t["show_original"]):
        st.text(a.original_text)

    # Save
    if st.session_state.get("saved_id"):
        st.caption(f"✓ {t['saved']}")
    elif st.button(f"💾 {t['save']}"):
        st.session_state.saved_id = history.save(a, lang_name)
        st.rerun()


if "result" in st.session_state:
    show_result(st.session_state.result, st.session_state.get("result_lang", language))
