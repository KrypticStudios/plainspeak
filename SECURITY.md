# Security and privacy in PlainSpeak

People upload eviction notices, hospital bills and benefits letters, which are some of the most private documents they have. This file explains how PlainSpeak protects that information and what the limits are.

## How it's built (the "backend")

```
 Visitor's browser                       Our server (Python + Streamlit)              Google Gemini
 ─────────────────                       ───────────────────────────────              ─────────────
 photo / text  ──── HTTPS ────▶  1. check the file is a real image/PDF
                                 2. hide ID numbers in typed text
                                 3. check usage limits
                                 4. add the secret API key  ──── HTTPS ────▶  reads the letter,
                                                                               returns JSON
                                 5. check every quote is really
 results  ◀──── HTTPS ─────────     in the letter (no AI)       ◀───────────
```

The Python program **is** the backend: all the code runs on the server, and the browser only receives the finished page. That means:
- **The API key never reaches the browser.** It's read from `.env` on our machine, or from Streamlit Cloud's encrypted "Secrets" settings, and never from code in the repo (`.gitignore` blocks `.env`).
- Visitors can't call Gemini directly or change our prompts.

### Why there's no database of letters
The safest data is data you never keep. On the public site, PlainSpeak stores **nothing on disk**:
- "My letters" lives only in the visitor's session memory and disappears when they close the page. There's also a **Delete all my letters** button.
- We don't log uploads or letter text.
- When you run PlainSpeak on your own computer (`PLAINSPEAK_LOCAL=1`), saved letters go into a local SQLite file, and every row is tagged with an owner.

A full account system (login plus an encrypted database) would let people keep letters across devices. We decided against it for now: storing fewer private letters is better than storing more, and our users shouldn't need an account to understand a letter.

## Protections in the code

| Risk | What we do | Where |
|---|---|---|
| AI makes something up | Every deadline, step and amount must quote the letter, and Python checks the quote exists. Anything unverified gets a ⚠ warning and is kept out of the calendar and the countdown. | `checks.py`, `export.py` |
| Sending ID numbers to the AI | Social Security, card, account and case numbers in typed or pasted text are replaced with `[number hidden]` before sending. For photos, the app asks people to cover ID numbers. | `privacy.py` → `redact()` |
| A letter that tries to trick the AI ("prompt injection") | The prompts tell the AI the letter is untrusted data. The answer must fit a fixed JSON shape, and quotes are checked. | `analyzer.py` |
| Malicious page content (XSS) | All AI and letter text is HTML-escaped before display. Phone links use digits only. | `app.py` → `esc()` |
| Fake or harmful uploads | Only real images (checked with Pillow) and PDFs (checked by file signature). Max 10 MB per file, 5 pages, 20,000 characters of text. Photos are re-encoded, which also strips hidden data like GPS location. | `privacy.py` → `check_upload()`, `images.py` |
| Someone using up the free AI quota | 6 AI requests per visitor per 10 minutes, and a daily cap for the whole site. | `privacy.py` → `RateLimiter` |
| Leaking technical details | Error details and stack traces are hidden from visitors. Usage statistics are off. Cross-site request (XSRF) protection is on. | `.streamlit/config.toml` |
| Leaked API key | The key is kept in `.env` or Cloud Secrets, which are git-ignored. | `.gitignore` |

## Honest limitations
- **The free Gemini tier is not private.** Under [Google's Gemini API terms](https://ai.google.dev/gemini-api/terms), content sent on the free tier may be used to improve Google's products and may be read by human reviewers, and Google advises against sending sensitive information. That's why the demo tells people to use the example letters or cover personal details. **A real launch would use Gemini's paid tier**, where Google doesn't use prompts or responses to improve its products, or an on-device model (see below).
- Redaction catches common ID formats in text. It can't read photos before they're sent, and it doesn't remove names or addresses, because explaining a letter needs some of that context.
- The usage limits are per server and in memory. They reset when the app restarts.
- PlainSpeak explains letters. It does not give legal advice.

## Ideas for the future
- An on-device "private mode" that reads the letter inside the user's own browser, so nothing leaves their phone. See the on-device notes in the README.
- Optional accounts with encrypted storage (sign-in through an auth provider such as MojoAuth).
