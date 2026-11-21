# Devpost write-up draft: PlainSpeak

> Copy each section into the matching Devpost box. Fill in everything in **[brackets]** with your own words. Judges can tell a real story from a generic one, so add one sentence about *why you* care (a family member, a friend, something you've seen).

---

**Project name:** PlainSpeak

**Tagline (short description):** Take a photo of a confusing official letter. Get what it means, what to do and by when, in plain words and in your language, with every fact checked against the letter.

---

## Inspiration
[Optional personal line, e.g. "One of us has translated letters for a parent who is still learning English…"]

Official letters decide whether people keep their homes, their food benefits and their health coverage, and they're written in legal language most people can't easily read:
- **28%** of US adults read at the lowest literacy levels (PIAAC 2023, NCES).
- **About 27 million** people in the US have limited English proficiency (Migration Policy Institute).
- When Medicaid renewals restarted in 2023–24, **69%** of the people who lost coverage lost it for **paperwork reasons**, not because they were ineligible (KFF).
- In Philadelphia, **more than half** of evictions came from default judgments, meaning the tenant never showed up to court (Temple CSJ).

Often the help people needed was written in the same letter (rental assistance, financial aid, how to reschedule). They just couldn't tell what it said, or how urgent it was. The theme was *Projects for Social Good*, and we wanted to make that information readable for everyone.

## What it does
1. **Add your letter.** Take a photo of each page, upload a PDF, or paste the text.
2. **Read it in plain words.** You get a 2–4 sentence summary at about a 5th-grade reading level, in 11 languages, with **read-aloud**. Right-to-left text works for Arabic.
3. **Know what to do.** The top of the page shows how urgent the letter is, a **countdown** ("18 days left"), and the **first thing to do**. Below that are all the deadlines (with one-tap **add to calendar** and a 2-day reminder), a checklist of steps, the money involved, who to call (tap-to-call), and your rights as the letter states them.
4. **Ask follow-up questions** like "What if I can't pay?". Answers come only from the letter. When the letter doesn't say, PlainSpeak says *"The letter doesn't say this"* and tells you who to ask.
5. **Get human help.** Serious letters (eviction, court, losing benefits) are flagged "talk to a real person", and every answer links to **211** and **LawHelp.org**.
6. **Keep it.** Save it to *My letters*, or download a one-page summary to print or send to a family member or caseworker.

### What makes it different: checked, not just generated
Anyone can paste a letter into a chatbot, but a chatbot gives you a paragraph you have to trust. PlainSpeak makes the AI **quote the exact words from the letter** for every deadline, step and amount. Then **our own Python code, not the AI, checks that those words really appear in the letter.** Anything that can't be found gets a ⚠ warning and is **kept out of the calendar and the countdown**. You can watch this happen with the 🧪 "catch an AI mistake" demo.

## How we built it
- **Python + Streamlit** for the whole web app. The server is the backend, so the API key never reaches the browser.
- **Google Gemini API (free tier)** reads the photo and explains the letter. We use **structured output**: the AI must fill in a fixed JSON shape, which we define and validate with **Pydantic**.
- **Our verification layer** (`difflib` fuzzy matching) checks every quote against the letter. **textstat** measures the reading level ("the letter needs grade 11, our summary needs grade 3").
- **gTTS** for read-aloud, **icalendar** for calendar files, **Babel** for dates in each language, **Pillow** to straighten and shrink phone photos, and **SQLite** for local saved letters.
- **Accessibility:** large-text and high-contrast modes, a layout that works on phones, urgency shown with icons and words (not only color), and plain-language error messages.
- **Privacy and security:** the public site stores no letters on disk. ID numbers (SSN, card, account and case numbers) are hidden before text goes to the AI. We added rate limits, file checks and prompt-injection rules. The full write-up is in `SECURITY.md`.
- **Testing:** 22 automated tests (pytest), including "a made-up quote gets caught", "visitors can't see each other's letters" and "ID numbers are hidden but phone numbers aren't".

## Challenges we ran into
- **AI hallucinations on high-stakes letters.** A wrong date on an eviction notice could cost someone their home. We solved this by forcing the AI to quote its sources and checking those quotes in code.
- **Privacy on a free AI tier.** Google's free tier terms allow using submitted content to improve their products. We were upfront about this in the app, added ID-number hiding, and stored nothing on the server.
- **On-device AI.** We researched running the AI entirely in the browser, but in 2026 that still needs a powerful desktop and a multi-GB download, which doesn't fit people on older phones with limited data.
- [Add one of your own: something that confused or blocked you and how you got past it.]

## Accomplishments that we're proud of
- The quote checker: you can *see* PlainSpeak catch an invented deadline.
- It works in 11 languages, including the headings, buttons and dates, not just the AI's text.
- [Your own: e.g. "As first-time hackers, we shipped a working, deployed app with tests."]

## What we learned
- [In your own words, e.g. what structured output is, why AI output needs checking, how an API key is kept secret, what accessibility means in practice.]

## What's next for PlainSpeak
- Test with real users at a library, legal-aid clinic or community center.
- Move to Gemini's **paid tier** or an on-device model, so letters are never used to improve anyone's products.
- An optional on-device "private mode" for capable computers.
- SMS / WhatsApp: text a photo of a letter and get the explanation back.
- Partnerships with 211 and legal-aid groups to send people to the right local help.

---

## Built with
`python` `streamlit` `google-gemini` `pydantic` `sqlite` `gtts` `icalendar` `babel` `pillow` `textstat` `pytest`

## Try it out
- Live app: **[Streamlit link after deploying]**
- Code: https://github.com/KrypticStudios/plainspeak
- No key needed to try it: the three **example letters** work right away.

## What we built during the event / AI disclosure
Everything was built during EvoHacks 2.0 (Nov 21–22, 2026). There was no code before the event. The sample letters are made up, with fictional names, addresses and numbers. We used **Claude (Anthropic) as an AI coding assistant** to help write and review code. [Describe your own contributions honestly: e.g. "We designed the features and user flow, wrote and tested the sample letters, chose the button text, tested the app, and wrote this write-up and the video."] We can explain how every part works. See `CODE_GUIDE.md`. The app itself uses Google Gemini at runtime. Libraries are listed above.

## Team
- [Name]: [what you did]
- [Name]: [what you did]
