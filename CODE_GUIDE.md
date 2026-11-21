# How PlainSpeak works: a guide for the team

Read this before recording the video. The rules require us to explain our code, so each of you should be able to talk through **the 3 key ideas** below in your own words.

---

## The big picture (say this in the video)

```
 photo / text ──▶ analyzer.py ──▶ Gemini AI ──▶ JSON answer ──▶ checks.py ──▶ app.py shows it
                  (adds our rules)               (fixed shape)    (verifies       (cards, calendar,
                                                                   quotes)         read-aloud)
```

---

## Key idea 1: We make the AI answer in a fixed shape (`plainspeak/schema.py`)

Normally an AI replies with a paragraph of text. We need specific pieces instead: the summary, each deadline, each step. So in `schema.py` we describe the exact fields we want (`summary`, `deadlines`, `actions`, `money`, ...) using **Pydantic** classes. We pass this shape to Gemini, and Gemini has to return JSON that matches it.

**How to say it:** "Instead of a chat answer, we force the AI to fill in a form we designed. That way our app always knows where the deadline is, and Pydantic checks that the answer has the right shape."

Look at: the `Deadline` class has a `date`, a `what`, and a `source_quote`.

## Key idea 2: We don't blindly trust the AI (`plainspeak/checks.py`)

AI can make things up ("hallucinate"). For every deadline, step and amount, the AI has to copy the **exact words** from the letter into `source_quote`. Then `quote_found()`, which is ordinary Python with no AI, searches the letter for those words.
- If it finds them: **✓ found in your letter**
- If it doesn't: **⚠ please double-check**

It uses `difflib.SequenceMatcher` so tiny differences, like an extra space when reading a photo, still count as a match.

**How to say it:** "The AI is only used for reading and explaining. Checking is done by our own code, so if the AI invents a date, the user sees a warning."

Also in this file: `reading_grade()` measures how hard text is to read (the Flesch-Kincaid grade). That's how we can show "the letter needs grade 11, our summary needs grade 3".

## Key idea 3: The prompt is our safety rules (`plainspeak/analyzer.py`)

`SYSTEM_PROMPT` is the set of instructions we give the AI: write at a 5th-grade level, never invent phone numbers, always quote the letter, say when you're unsure, and recommend a real person for eviction or court letters. `analyze_letter()` sends the photo or text plus these rules to Gemini.

Other details worth knowing:
- The **API key** is read from `.env` on the server, so it's never sent to the browser and never pushed to GitHub (`.gitignore`).
- If one Gemini model is unavailable, it tries the next one in `DEFAULT_MODELS`.
- Errors are turned into friendly messages, for example "The free AI limit was reached. Wait a minute…"
- `temperature=0.2` makes the AI careful and consistent instead of creative.

---

## The smaller files
| File | What it does | One-line explanation |
|---|---|---|
| `app.py` | The whole web page | Streamlit turns Python into a website. Each `st.something` draws something on the page. |
| `calendar_export.py` | Makes a `.ics` file | `.ics` is the standard calendar format. Each deadline becomes an all-day event with a reminder 2 days before. |
| `speech.py` | Read-aloud | Sends the summary to Google Text-to-Speech and gets an MP3 back. |
| `history.py` | My letters | Saves answers in a SQLite database file on the computer. |
| `export.py` | Countdown and printable page | Works out how many days are left until the next *verified* deadline, and builds a simple HTML page to print. |
| `images.py` | Prepares photos | Turns sideways phone photos the right way up and shrinks them so the AI is faster. |
| `ui_text.py` | Translations | Every heading and button on the results page in 11 languages, plus dates written the local way. |
| `demo.py` | Sample answers | Answers we wrote ahead of time for the sample letters, so the demo works with no internet. |
| `tests/test_core.py` | Automated tests | Checks things like "a made-up quote gets caught" and "the calendar file has the right dates". |

## Words you might get asked about
- **API**: a way for our program to talk to another service (Gemini).
- **JSON**: a text format for structured data, like `{"date": "2026-12-04"}`.
- **Hallucination**: when AI states something false with confidence.
- **Structured output**: making the AI fill in a fixed format instead of free text.
- **SQLite**: a tiny database stored in a single file.
- **Streamlit**: a Python library that turns scripts into web apps.
