# 📬 PlainSpeak

**Take a photo of a confusing official letter and find out what it means, what to do, and by when, in plain words and in your own language.**

Built for **EvoHacks 2.0**, whose theme is *Projects for Social Good*.

## The problem
Eviction notices, hospital bills and benefits renewals are written in legal, bureaucratic language. People who are still learning English, elderly people and people who struggle with reading often can't tell what the letter is asking for, or how urgent it is. When they miss a deadline, they can lose their home, their food benefits, or end up with a bill in collections, even though help was often offered in the same letter.

## What PlainSpeak does
1. **Read**: you upload a photo of each page, a PDF, or the pasted text. Photos are straightened and shrunk automatically.
2. **Explain**: the app gives a 2–4 sentence summary at a 5th-grade reading level and tells you how urgent the letter is.
3. **Act**: it lists the deadlines, a checklist of what to do, the money involved, and who to call (phone numbers you can tap).
4. **Your language**: the explanation comes in 11 languages, with read-aloud. Right-to-left text is supported for Arabic.
5. **At a glance**: the top of the results shows how urgent the letter is, a countdown (e.g. "18 days left") to the next deadline, and the first thing to do.
6. **Remember**: you can add the deadlines to Google, Apple or Outlook Calendar with a reminder 2 days before, save letters to *My letters*, or download a summary page to print or send to someone who helps you.
7. **Get help**: every answer links to 211 (free local help) and LawHelp.org (free legal aid).

### Why you can trust it
AI can make things up. PlainSpeak protects against that:
- **Every deadline, step and amount quotes the exact words from the letter.** Ordinary Python code, not the AI, then checks that those words really appear in the letter. If they don't, the item gets a ⚠ warning so you know to double-check it.
- Only dates that pass this check go into the calendar file.
- In the sample tab, the **🧪 "Show how PlainSpeak catches AI mistakes"** switch adds a fake deadline so you can watch the check flag it.
- The AI has to list **what it's unsure about** and give a **confidence** level.
- Serious letters (eviction, court, debt, losing benefits) get a **"talk to a real person"** warning. PlainSpeak explains letters. It does not give legal advice.
- It shows how hard the original letter is to read compared with the summary, measured as a school grade level (Flesch-Kincaid).

### Accessibility
The app has options for larger text and high contrast, can read the summary aloud, explains in 11 languages including right-to-left Arabic, and uses plain wording throughout, including in its error messages. Urgency is shown with an icon and words as well as color, so it doesn't rely on color alone.

## Tech
| Part | Tool |
|---|---|
| Web app | Python and [Streamlit](https://streamlit.io) |
| Reading photos and explaining letters | Google Gemini API (free tier), using structured JSON output checked by Pydantic |
| Quote checking and reading level | Python's `difflib` and [`textstat`](https://github.com/textstat/textstat) |
| Read-aloud | [gTTS](https://github.com/pndurette/gTTS) |
| Calendar | [`icalendar`](https://github.com/collective/icalendar), which makes `.ics` files |
| Saved letters | SQLite |

## Run it yourself
```bash
git clone <this repo>
cd Evohacks
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then paste a free key from https://aistudio.google.com into .env
streamlit run app.py
```
**No key?** The app runs in demo mode with three made-up sample letters, so you can try it without signing up for anything.

Run the tests with `pytest -q`.

## Project structure
```
app.py                       the web page (everything you see)
plainspeak/schema.py         the shape of the AI's answer
plainspeak/analyzer.py       sends the letter to Gemini
plainspeak/checks.py         quote checker and reading level (no AI)
plainspeak/calendar_export.py  deadlines -> .ics calendar file
plainspeak/speech.py         read-aloud and language list
plainspeak/history.py        My letters (SQLite)
plainspeak/demo.py           saved answers for the sample letters
plainspeak/export.py         countdown and printable summary page
plainspeak/images.py         straightens and shrinks phone photos
plainspeak/ui_text.py        labels and dates in 11 languages
samples/                     made-up letters for testing and the demo
tests/                       automated tests
```

## Built during EvoHacks 2.0
Everything in this repo was written during the event (Nov 21–22, 2026). There was no code before the event. The sample letters are made up: every name, address, phone number and case number in them is fictional.

**AI assistance:** we used Claude (Anthropic) as a coding assistant to help write and review code. The app itself uses Google Gemini at runtime. We can explain every part of the code, and `CODE_GUIDE.md` is our own walkthrough of how it works.

**Libraries used:** Streamlit, google-genai, Pydantic, gTTS, icalendar, textstat, python-dotenv, Pillow, pytest.

## Disclaimer
PlainSpeak helps you understand a letter. It is not legal, medical or financial advice. For anything serious, contact a lawyer, a caseworker, or the office that sent the letter.
