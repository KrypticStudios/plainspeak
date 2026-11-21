# Security and privacy in PlainSpeak

People upload eviction notices, hospital bills and benefits letters, which are some of the most private documents they have. This file explains how PlainSpeak protects that information and what the limits are.

## How it's built (the "backend")

```
 Visitor's browser                       Our server (Python + Streamlit)              Google Gemini
 ─────────────────                       ───────────────────────────────              ─────────────
 photo / text  ──── HTTPS ────▶  1. check the file is a real image/PDF
                                 2. try to hide ID numbers in pasted text
                                 3. check usage limits
                                 4. add the secret API key  ──── HTTPS ────▶  reads the letter,
                                                                               returns JSON
                                 5. check quotes, dates and phone
 results  ◀──── HTTPS ─────────     numbers (no AI)             ◀───────────
```

The Python program **is** the backend: all the code runs on the server, and the browser only receives the finished page. That means:
- **The API key never reaches the browser.** It's read from `.env` on our machine, or from Streamlit Cloud's encrypted "Secrets" settings, and never from code in the repo (`.gitignore` blocks `.env`).
- Visitors can't call Gemini directly or change our prompts.

### Why there's no database of letters
The safest data is data you never keep. On the public site, PlainSpeak stores **nothing on disk**:
- "My letters" lives only in the visitor's session, in the server's memory, and is gone when they close the page. There's also a **Delete all my letters** button.
- Our code doesn't log uploads or letter text. (Our host, Streamlit Cloud, keeps its own technical logs, which we don't control.)
- When you run PlainSpeak on your own computer (`PLAINSPEAK_LOCAL=1`), saved letters go into a local SQLite file. That mode is for a single user. **Never set it on a public server**, because every visitor would share one file.

A full account system (login plus an encrypted database) would let people keep letters across devices. We decided against it for now: storing fewer private letters is better than storing more, and our users shouldn't need an account to understand a letter.

## Protections in the code

| Risk | What we do | Where |
|---|---|---|
| AI makes something up | Every deadline, step and amount must quote the letter. Python checks the quote is there, with every number exact. For pasted text it checks against the text the person pasted. For photos it checks against the AI's own reading of the photo, and the app labels it that way. A deadline's date must be written in its own sentence. Anything unverified gets a ⚠ and stays out of the calendar, countdown and share message. | `checks.py`, `export.py` |
| AI gives a wrong or scam phone number | A number is only tap-to-call if it appears in the letter. Otherwise it's shown with a ⚠. | `checks.phone_in_letter` |
| Sending ID numbers to the AI | Best-effort: common formats of Social Security, card, account and case numbers in *pasted* text are replaced with `[number hidden]`. This can miss unusual formats, and it can't touch photos or PDFs, so the app asks people to cover numbers before taking a photo, and shows a privacy warning above the upload button. | `privacy.py` → `redact()` |
| A letter that tries to trick the AI ("prompt injection") | The prompts tell the AI the letter is untrusted data. The answer must fit a fixed JSON shape, and quotes are checked. | `analyzer.py` |
| Malicious page content (XSS, phishing links) | AI and letter text is HTML-escaped (`esc()`), or Markdown-escaped where Streamlit reads Markdown (`md()`), so a letter can't inject code, links or tracking images. Phone links use digits only. Share links are URL-encoded. | `app.py` |
| Fake or harmful uploads | Only real images (fully decoded with Pillow) and PDFs (opened with pypdf). Max 10 MB per file, 20 MB and 5 pages for the whole letter, 40 megapixels per image, 20,000 characters of text. Checked again on the server when "Explain" is pressed, because a greyed-out button isn't a real lock. Photos are re-encoded, which strips hidden data like GPS location. PDFs are sent as they are. | `privacy.py`, `images.py`, `app.py` |
| Someone using up the free AI quota | 6 requests per visitor per 10 minutes, keyed on the visitor's internet address when the host provides it, so reloading the page doesn't reset it. Read-aloud is limited separately. There's a daily cap for the whole site, and at most 4 AI calls per letter (including fallbacks to other models and a backup key). | `app.py`, `privacy.py`, `analyzer.py` |
| Not knowing when something breaks | We count event *types* only ("letter_ok", "ai_busy", "bad_upload"…), never letter content, in the server log that only the owner can see. | `monitor.py` |

| A library update breaking the live site | Every dependency is pinned to the exact version we tested. | `requirements.txt` |
| Leaking technical details | Error details and stack traces are hidden from visitors. Usage statistics are off. Cross-site request (XSRF) protection is on. | `.streamlit/config.toml` |
| Leaked API key | The key is kept in `.env` or Cloud Secrets, which are git-ignored. | `.gitignore` |

## Honest limitations
- **The free Gemini tier is not private.** Under [Google's Gemini API terms](https://ai.google.dev/gemini-api/terms), content sent on the free tier may be used to improve Google's products and may be read by human reviewers, and Google advises against sending sensitive information. That's why the demo tells people to use the example letters or cover personal details. **A real launch would use Gemini's paid tier**, where Google doesn't use prompts or responses to improve its products, or an on-device model (see below).
- Redaction catches common ID formats in text. It can't read photos before they're sent, and it doesn't remove names or addresses, because explaining a letter needs some of that context.
- The usage limits are kept in memory. They reset when the app restarts, and someone determined (e.g. using many internet addresses) could still get past them.
- **Photos:** our checks compare quotes with the AI's own reading of the photo, so if the AI misreads a photo, the check can't notice. The app shows "found in what we read from your photo" and lets people see the full text it read.
- Read-aloud sends the summary and steps (not the letter) to Google's text-to-speech service, and only when the user presses 🔊.
- PlainSpeak explains letters. It does not give legal advice.

## Ideas for the future
- An on-device "private mode" that reads the letter inside the user's own browser, so nothing leaves their device. In 2026 this still needs a powerful desktop (Chrome's built-in AI is desktop-only and needs a large one-time download), so it doesn't yet reach the older phones many of our users have.
- Optional accounts with encrypted storage (sign-in through an auth provider such as MojoAuth).
