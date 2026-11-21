"""Read-aloud: turns text into an MP3 using Google Text-to-Speech (gTTS, free, needs internet)."""

from io import BytesIO

# Language names shown in the app -> gTTS language codes.
LANGUAGES = {
    "English": "en",
    "Español (Spanish)": "es",
    "中文 (Chinese)": "zh-CN",
    "Tiếng Việt (Vietnamese)": "vi",
    "العربية (Arabic)": "ar",
    "हिन्दी (Hindi)": "hi",
    "Tagalog": "tl",
    "Français (French)": "fr",
    "한국어 (Korean)": "ko",
    "Русский (Russian)": "ru",
    "Português (Portuguese)": "pt",
}

RTL_LANGUAGES = {"ar"}  # written right-to-left
MAX_CHARS = 3000       # read-aloud covers the summary, deadline and steps; never a whole letter


def text_to_mp3(text: str, lang_code: str) -> bytes | None:
    """Return MP3 bytes, or None if the speech service is unreachable."""
    from gtts import gTTS
    from gtts.tts import gTTSError

    text = " ".join(text.split())[:MAX_CHARS]
    if not text:
        return None
    try:
        buf = BytesIO()
        gTTS(text=text, lang=lang_code).write_to_fp(buf)
        return buf.getvalue()
    except (gTTSError, ValueError, OSError, AssertionError):
        return None
