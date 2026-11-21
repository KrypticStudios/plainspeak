# EvoHacks 2.0 — Rules & Strategy Notes

Devpost: https://evohacks2.devpost.com · Site: https://evohacks.xyz · Discord: https://discord.gg/3rpq367BFJ

## Timeline (PST)
- Hacking: Sat 11/21 9:00 AM → **Submit by Sun 11/22 12:00 PM**
- Judging 12:00–2:30 PM · Winners 3:00 PM
- Internal target: feature freeze ~9 AM Sunday, then video + Devpost write-up

## Theme
**Projects for Social Good** — "build something that makes a real difference... tackle meaningful problems, and turn your ideas into impactful projects." (Discord announcement, 11/21 9 AM PST). Must be central to the project, not bolted on.

## Submission checklist
- [ ] Project name + clear description
- [ ] Problem + how it works
- [ ] Demo video ≤ 3 min — includes a short segment explaining our own code (AI policy)
- [ ] Working demo / install instructions
- [ ] Public source repo (no API keys — use `.env` + `.env.example`)
- [ ] Team members, tech used, sponsor tools integrated
- [ ] What was built during the event vs pre-existing; credit libraries, assets, AI assistance

## Judging criteria
1. Fit to the prompt (theme central)
2. Problem & impact (specific users, real improvement, backed by demo/testing)
3. Functionality & technical execution (**blend of technologies**, technical knowledge)
4. Usability & accessibility (clear workflow, helpful errors, a11y)
5. Appropriate use of technology (AI adds real value; show we know its limits)
6. Video/demo (problem, solution, team contribution, core workflow)

## Sponsor prizes worth targeting
- MojoAuth (5 winners) / SSOJet (5 winners) — auth providers; use one for login
- Agentboxd — best meaningful use
- Game & Visual Design award (if a game)

## EvoHacks I (theme "AI for Automation") winners
1. Emberline 3.0 — AI disaster response → coordinated relief plans
2. ClearMessage — phishing-awareness assistant
3. LookCast — outfits from wardrobe + local weather
- Organizer's fav: Foreman AI — bulk automation w/ confidence scores, traceable decisions
Pattern: specific real problem, clear user, AI doing a concrete job with trust/transparency built in.

## Team setup
- Team of 3 (third member joined Sat ~10:45 AM PST), all beginners, Python stack
- Split: Claude does the advanced code (backend, AI integration, auth, deploy); teammates do beginner-friendly work and must understand the code well enough to explain it in the video (AI policy)
- Teammate tasks: UI text/copy, test data & manual testing, small UI tweaks, Devpost write-up, demo video script/recording, slides/screenshots, reading + annotating key code files
- Budget: $0. No paid APIs or hosting.
- AI in the app: free-tier API (Google Gemini via AI Studio key, no card; fallback Groq free tier) or no AI if the idea doesn't need it. Claude (Max plan) builds the code but is NOT the app's runtime AI.
- Hosting: Streamlit Community Cloud (free) or run locally for the demo
