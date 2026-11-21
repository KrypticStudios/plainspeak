"""PlainSpeak - understand any official letter.

Run with:  .venv/bin/streamlit run app.py
"""

import streamlit as st

from plainspeak import calendar_export, checks, demo, history
from plainspeak.analyzer import AnalyzerError, analyze_letter, has_api_key
from plainspeak.schema import LetterAnalysis
from plainspeak.speech import LANGUAGES, RTL_LANGUAGES, text_to_mp3

st.set_page_config(page_title="PlainSpeak", page_icon="📬", layout="centered")

# ---------- Sidebar: language, accessibility, history ----------
with st.sidebar:
    st.header("⚙️ Settings")
    language = st.selectbox("Explain my letter in", list(LANGUAGES), help="The summary and steps will be in this language.")
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

lang_code = LANGUAGES[language]

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
    css += "<style>html, body, [class*='st-'], p, li, label, .ps-card {font-size: 1.25rem !important;}</style>"
if high_contrast:
    css += """<style>
    .stApp, .ps-card, .ps-high, .ps-medium, .ps-low {background: #000 !important; color: #fff !important;}
    .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .ps-quote {color: #fff !important;}
    .ps-card {border-color: #ffff00 !important;}
    .ps-ok {color: #7CFC00 !important;} .ps-warn {color: #ffff00 !important;}
    </style>"""
st.markdown(css, unsafe_allow_html=True)

# ---------- Header ----------
st.title("📬 PlainSpeak")
st.markdown("**Got a confusing letter?** Take a photo. We'll tell you what it means, what to do, and by when, "
            "in plain words and in your language.")

if not has_api_key():
    st.info("Demo mode: no AI key is set up, so you can try the **sample letters** below. "
            "To read your own letters, add a free Gemini key (see README).", icon="ℹ️")

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
    if st.button("Explain this sample", type="primary", key="go-sample"):
        if use_instant:
            st.session_state.result, st.session_state.result_lang = instant, language
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


def quote_html(quote: str, letter: str) -> str:
    """The exact words from the letter, with a check mark if we found them in the letter."""
    if checks.quote_found(quote, letter):
        badge = '<span class="ps-ok">✓ found in your letter</span>'
    else:
        badge = '<span class="ps-warn">⚠ we could not find these words in your letter. Please double-check.</span>'
    return f'<div class="ps-quote">“{esc(quote)}” — {badge}</div>'


def show_result(a: LetterAnalysis, lang_name: str) -> None:
    code = LANGUAGES.get(lang_name, "en")
    direction = "rtl" if code in RTL_LANGUAGES else "ltr"
    st.divider()
    st.subheader(f"📄 {a.document_type}")
    st.caption(f"From: {a.sender}")

    icon = {"high": "🔴 Urgent", "medium": "🟠 Soon", "low": "🟢 Not urgent"}[a.urgency]
    st.markdown(f'<div class="ps-card ps-{a.urgency}" dir="{direction}"><b>{icon}</b> — {esc(a.urgency_reason)}</div>',
                unsafe_allow_html=True)

    # Summary + read aloud
    st.markdown("### 💬 What this letter means")
    st.markdown(f'<div class="ps-card" dir="{direction}" style="font-size:1.1em">{esc(a.summary)}</div>',
                unsafe_allow_html=True)
    if st.button("🔊 Read this out loud", key="tts"):
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
        label = {"high": "", "medium": " (we're fairly sure, but check the details)",
                 "low": " (the letter was hard to read, so please double-check)"}[a.confidence]
        st.markdown(f"### ❓ Things we're not sure about{label}")
        for p in a.unclear_points:
            st.markdown(f"- {p}")

    # Deadlines
    if a.deadlines:
        st.markdown("### 📅 Important dates")
        for d in a.deadlines:
            when = d.date or "No exact date given"
            st.markdown(f'<div class="ps-card" dir="{direction}"><b>{esc(when)}</b> — {esc(d.what)}'
                        f'{quote_html(d.source_quote, a.original_text)}</div>', unsafe_allow_html=True)
        ics = calendar_export.deadlines_to_ics(a.deadlines)
        if ics:
            st.download_button("📆 Add these dates to my calendar", ics, file_name="plainspeak-deadlines.ics",
                               mime="text/calendar", help="Opens in Google, Apple or Outlook Calendar, with a reminder 2 days before.")

    # Steps
    if a.actions:
        st.markdown("### ✅ What to do")
        for i, s in enumerate(a.actions):
            st.checkbox(s.step, key=f"step-{i}")
            st.markdown(quote_html(s.source_quote, a.original_text), unsafe_allow_html=True)

    # Money
    if a.money:
        st.markdown("### 💵 Money")
        for m in a.money:
            st.markdown(f'<div class="ps-card" dir="{direction}"><b>{esc(m.amount)}</b> — {esc(m.what)}'
                        f'{quote_html(m.source_quote, a.original_text)}</div>', unsafe_allow_html=True)

    # Contacts
    if a.contacts:
        st.markdown("### ☎️ Who to contact")
        for c in a.contacts:
            lines = [f"**{c.name}** — {c.why}"]
            if c.phone:
                digits = "".join(ch for ch in c.phone if ch.isdigit() or ch == "+")
                lines.append(f"📞 [{c.phone}](tel:{digits})")
            if c.email:
                lines.append(f"✉️ {c.email}")
            if c.address:
                lines.append(f"📍 {c.address}")
            st.markdown("  \n".join(lines))

    if a.rights:
        st.markdown("### 🛡️ Your rights (from the letter)")
        for r in a.rights:
            st.markdown(f"- {r}")

    if a.needs_human_help:
        st.warning(f"**Talk to a real person about this.** {a.help_reason}", icon="🧑‍⚖️")
    else:
        st.success(a.help_reason, icon="👍")

    with st.expander("Show the full original letter"):
        st.text(a.original_text)

    # Save
    if st.session_state.get("saved_id"):
        st.caption("✓ Saved to My letters.")
    elif st.button("💾 Save to My letters"):
        st.session_state.saved_id = history.save(a, lang_name)
        st.rerun()


if "result" in st.session_state:
    show_result(st.session_state.result, st.session_state.get("result_lang", language))
