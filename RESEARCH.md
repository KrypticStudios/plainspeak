# Research: what already exists, and why PlainSpeak is different

Collected on Nov 21, 2026 from web searches. Verify a stat's source before quoting it in the video.

## Similar tools
| Tool | What it does | Gap vs PlainSpeak |
|---|---|---|
| [Plain Letter](https://plain-letter-green.vercel.app/) | Photo of a letter → plain English, 53 languages, read-aloud. Free. | UK only. No deadlines, calendar, money list or quote verification advertised. |
| [xPlainly](https://xplainly.app/) | Summary, amount owed, deadlines, calendar, 26 languages | **Paid** (€3.99 per 5 letters). Aimed at expats, not low literacy. No quote verification. |
| [HelpMe UK LetterLens](https://migrationpartnership.org.uk/resource-of-the-week-new-free-tool-to-help-people-understand-official-letters-and-forms/) | Free letter explainer for migrants | UK only |
| [BuroBrain](https://burobrain.com/), [WhatLetter](https://www.whatletter.com/) | Letter scanning and translation | Freemium or paywalled |
| [Propel](https://www.propel.app/insights/using-ai-for-snap-notices/) | Prototyping an AI SNAP-notice explainer | Not confirmed as launched; SNAP only |
| Be My Eyes / Google Lens | Read aloud or translate | Don't pull out deadlines or actions |
| ChatGPT / Gemini / Claude | Can explain a photo of a letter | You have to know what to ask. Can hallucinate. No structure, calendar, verification or reading-level guarantee. |
| [DoNotPay](https://www.ftc.gov/legal-library/browse/cases-proceedings/donotpay) | Paid "robot lawyer" | **FTC order (2025)** over unsupported AI claims. This is the cautionary tale behind our verification. |

Similar hackathon projects: [Waive](https://devpost.com/software/waive), [FairNotice](https://devpost.com/software/fairnotice), [BillClarity](https://devpost.com/software/billclarity).

## Our differentiators (use these in the pitch)
1. **Verified, not just generated.** Every deadline, amount and step quotes the letter word for word, and our own Python code (not the AI) checks that the quote exists. Anything that can't be found gets a ⚠. We found no consumer letter explainer advertising this.
2. **Knows when to stop.** It shows confidence and lists what it's unsure about, and serious letters (eviction, court, losing benefits) say "talk to a real person".
3. **Built for the reader.** It shows the reading level dropping (grade 11 → grade 3), reads aloud in 11 languages including right-to-left Arabic, offers one-tap calendar reminders, and has large-text and high-contrast modes. It's free and needs no account.
4. **Focused on the US letters that cause real losses**: eviction, benefits renewals, medical bills.

**Answering "can't you just ask ChatGPT?":** ChatGPT gives you a paragraph and you have to trust it. PlainSpeak gives you a checklist, calendar reminders and audio in your language, and proves every claim against your letter.

## Stats for the problem slide
- **28%** of US adults scored at Level 1 or below in literacy (PIAAC 2023, up from 19% in 2017). [NCES](https://ies.ed.gov/learn/press-release/u-s-adults-score-par-international-average-literacy-skills-below-international-average-numeracy-and)
- **About 27 million** US residents have limited English proficiency. [Migration Policy Institute](https://www.migrationpolicy.org/article/language-diversity-and-english-proficiency-united-states)
- **69%** of people who lost Medicaid during the 2023–24 unwinding lost it for **paperwork or procedural reasons**, not because they were ineligible. [KFF](https://www.kff.org/medicaid/issue-brief/an-examination-of-medicaid-renewal-outcomes-and-enrollment-changes-at-the-end-of-the-unwinding)
- In one state's SNAP data, **81%** of recertification denials were procedural. [CBPP](https://www.cbpp.org/research/food-assistance/administrative-burden-and-procedural-denials-in-the-supplemental-nutrition) (single state, not national)
- **1.23 million** eviction filings in 2025 across the sites Eviction Lab tracks. [Eviction Lab](https://evictionlab.org/ets-report-2025/)
- In Philadelphia, **54%** of evictions came from default judgments, meaning the tenant didn't show up. [Temple CSJ](https://law.temple.edu/csj/wp-content/uploads/sites/3/2020/07/Reducing-Default-Judgments-in-Philadelphias-Landlord-Tenant-Court.pdf)
- **15 million** Americans had **$49B** in medical bills on their credit reports. [CFPB](https://www.consumerfinance.gov/archive/newsroom/cfpb-finds-15-million-americans-have-medical-bills-on-their-credit-reports/)
