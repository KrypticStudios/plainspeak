# Demo video script: PlainSpeak (target 2:45, hard limit 3:00)

**Speakers:** **A** = [teammate 1], **B** = [teammate 2]. About 400 spoken words, which is a relaxed pace. Say it in your own words: judges notice when someone is reading.

**Setup before recording**
- Open the live app in Chrome at a 1920×1080 window, zoomed to about 125% so text is readable.
- Print or display the **eviction sample letter** (`samples/eviction_notice.txt`) so you can photograph it. **Never show a real person's letter.**
- Have VS Code open with `plainspeak/schema.py`, `plainspeak/checks.py` and `plainspeak/analyzer.py` in tabs, font size 18 or larger.
- Record the screen with **Cmd+Shift+5** (Mac) or **OBS**. Record your voice in a quiet room, and add your webcam in a corner if you can.
- Record the sections separately and join them in iMovie/CapCut. That's much easier than one perfect take.

---

### 0:00–0:20 · The problem (HOOK)
**Show:** A holding up the printed eviction letter, then a quick zoom on the dense legal paragraph.

**A:** "This is a real-looking eviction notice. *'Pursuant to the terms of your rental agreement… deliver up possession of the premises.'* If English isn't your first language, or reading is hard for you, what does this even mean? And how many days do you have?"

**B (on-screen text with the stats):** "Twenty-eight percent of US adults read at the lowest literacy level. Twenty-seven million people have limited English. And most people who lost Medicaid in 2023–24 lost it over *paperwork*, not eligibility."

### 0:20–0:30 · The solution
**Show:** the PlainSpeak start screen.

**A:** "So we built **PlainSpeak**. Take a photo of any official letter, and it tells you what it means, what to do and by when, in plain words and in your language."

### 0:30–1:30 · Live demo (the core workflow)
**Show and do, in this order:**
1. *(0:30)* Choose **Español**, take or upload the photo, then click **Explain my letter**. If the live AI is slow, cut the wait in editing. If the AI key isn't working, click the **🏠 Eviction notice** example button instead. It shows the same results.
   **B:** "I'll pick Spanish, like my [parent/neighbor] would, and take a photo."
2. *(0:45)* The results appear: the red **Urgente** card, the **"Quedan … días"** countdown, and **"Haga esto primero"**. The number of days depends on the day you record, so say whatever number is on screen.
   **B:** "Right at the top: it's urgent, there are [N] days left, and the first thing to do is call the housing help line, which the letter mentions in tiny print."
3. *(0:55)* Click **🔊 Leer en voz alta** and let 3 seconds play. **A:** "It can read everything out loud."
4. *(1:00)* Scroll to the dates and click **Add to calendar**. **A:** "One tap adds the deadline to your phone with a reminder."
5. *(1:08)* Point at a quote with **✓ found in your letter**. **A:** "And notice this: every date, step and dollar amount shows the exact words it came from."
6. *(1:15)* Ask: **"Will I have to go to court right away?"** **B:** "You can ask questions. When the letter doesn't say, PlainSpeak *tells* you it doesn't say, instead of making something up."
7. *(1:22)* Turn on **🧪 catch AI mistakes** and open the eviction example. **A:** "Here we've planted a fake deadline, the kind of thing AI invents. Our checker flags it in red and keeps it out of the calendar."

### 1:30–2:15 · How it works: our code (required by the rules)
**Show:** VS Code. Highlight each part as you talk about it.

**A (`schema.py`, the `Deadline` class):** "First, we don't let the AI answer however it wants. We designed this form, a Pydantic schema, and Gemini has to fill it in as JSON. Every deadline needs a date, what to do, and a `source_quote`."

**B (`checks.py`, `quote_found`):** "Second, we don't trust the AI. This function is plain Python, no AI. It searches the letter for each quote, using `difflib` so a tiny photo-reading error still matches. If the quote isn't there, the user sees a warning."

**A (`analyzer.py`, `SYSTEM_PROMPT`):** "Third, these are our rules for the AI: write at a 5th-grade level, never invent phone numbers, recommend a real person for eviction or court. The API key stays on our server, and the browser never sees it."

**B:** "We have 22 automated tests, like this one that checks a made-up quote gets caught." *(Show `pytest` output: 22 passed.)*

### 2:15–2:35 · Built for real people
**Show:** quick clips of high contrast plus large text, the phone layout, and the 🔒 Privacy box.

**B:** "It works on phones, has large-text and high-contrast modes, and works in 11 languages, including the headings and dates."
**A:** "For privacy: we store nothing on our server, ID numbers are hidden before anything reaches the AI, and we're honest that this demo uses Gemini's free tier."

### 2:35–2:50 · Impact and next steps
**Show:** the results page, then the GitHub repo and the live link.

**A:** "Next, we want to test PlainSpeak at a library or legal-aid clinic and add a text-a-photo option over SMS."
**B:** "Because nobody should lose their home or their food benefits over a letter they couldn't read. This is PlainSpeak."

---

## Checklist before uploading
- [ ] Under 3:00 (aim for 2:45)
- [ ] Shows the problem, the solution, the **core workflow**, and **your explanation of the code**
- [ ] Both teammates speak
- [ ] No real personal information on screen (use the sample letters only)
- [ ] No API key visible anywhere: don't open `.env` or the Streamlit Secrets page while recording
- [ ] Captions on (YouTube auto-captions are fine, or add them in CapCut), since that's accessibility in your own video
- [ ] Upload to YouTube as **Unlisted** or **Public**, and paste the link into Devpost
