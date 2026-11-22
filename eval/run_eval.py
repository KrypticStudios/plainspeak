"""PlainSpeak evaluation: run the real AI on a set of test letters and score it against the correct answers.

Run from the project folder (needs GEMINI_API_KEY, or a separate GEMINI_EVAL_API_KEY, in .env):
    .venv/bin/python eval/run_eval.py            # everything
    .venv/bin/python eval/run_eval.py --quick    # pasted text only

Each test letter in eval/letters/ is made up but modeled on a real public template (see eval/cases.json
for the source of each one). We (the team, with our AI coding assistant) wrote every letter and wrote
down the correct answers by hand: the deadlines, the amounts of money, the urgency, and whether the
reader should get human help. The script checks what PlainSpeak found against those answers.

Honest scoring:
  - Quotes and deadlines are checked against the REAL letter text (which this script knows), not
    against the AI's own reading of it, so the AI can't grade itself, even for photos.
  - Urgency is reported as an exact match with our single best answer, and separately as "acceptable".
  - "Talk to a real person" is only counted on letters where we decided the right answer.

Writes eval/results.json (every detail) and eval/RESULTS.md (summary).
"""

import json
import os
import statistics
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plainspeak import checks  # noqa: E402
from plainspeak.analyzer import AnalyzerError, analyze_letter  # noqa: E402
from plainspeak.images import prepare_image  # noqa: E402
from render import render  # noqa: E402  (eval/render.py: makes used / blurry / scanned versions)

HERE = Path(__file__).resolve().parent

# Use a separate key for testing if there is one, so the live site's free quota is saved for real users.
if os.getenv("GEMINI_EVAL_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GEMINI_EVAL_API_KEY"]
    os.environ.pop("GEMINI_BACKUP_API_KEY", None)
MAX_CALLS = int(os.getenv("EVAL_MAX_CALLS", "60"))   # hard stop, so a run can never use up the whole quota
PAUSE_SECONDS = 4                                    # be gentle with the free tier's per-minute limit
TODAY = date(2026, 11, 21)   # the test letters are dated for this day, so urgency is judged against it
TRICK_WORDS = ("trick", "instruction", "ignore", "manipulat", "suspicious", "ai ")


def money_key(amount: str) -> str:
    """'$1,450.00' -> '1450.00' so different ways of writing an amount still match."""
    digits = "".join(ch for ch in amount if ch.isdigit() or ch == ".")
    return f"{float(digits):.2f}" if digits.replace(".", "", 1).isdigit() else amount


def score(case: dict, a, true_text: str) -> dict:
    """Compare one PlainSpeak answer with the correct answers for that letter."""
    exp = case["expect"]
    verified = [d for d in a.deadlines if checks.deadline_is_trustworthy(d, true_text)]
    found_dates = {d.date for d in verified}
    found_money = {money_key(m.amount) for m in a.money if checks.quote_found(m.source_quote, true_text)}
    urgency = checks.calibrated_urgency(a, TODAY)   # what the app shows
    items = [*a.deadlines, *a.actions, *a.money, *getattr(a, "documents_to_bring", [])]
    r = {
        "deadlines_expected": len(exp.get("deadlines", [])),
        "deadlines_found": sum(d in found_dates for d in exp.get("deadlines", [])),
        "missed_deadlines": [d for d in exp.get("deadlines", []) if d not in found_dates],
        "money_expected": len(exp.get("money", [])),
        "money_found": sum(money_key(m) in found_money for m in exp.get("money", [])),
        "missed_money": [m for m in exp.get("money", []) if money_key(m) not in found_money],
        "quotes_total": len(items),
        "quotes_in_real_letter": sum(checks.quote_found(i.source_quote, true_text) for i in items),
        "quotes_in_ai_reading": sum(checks.quote_found(i.source_quote, a.original_text) for i in items),
        "invented_dates": [d.date for d in a.deadlines if d.date and not checks.date_written_in(d.date, true_text)],
        "wrong_dates_shown_as_sure": [d.date for d in a.deadlines
                                      if checks.deadline_is_trustworthy(d, a.original_text)
                                      and not checks.deadline_is_trustworthy(d, true_text)],
        "urgency": urgency,
        "urgency_ai": a.urgency,
        "urgency_best": exp.get("urgency_best"),
        "urgency_exact": exp.get("urgency_best") == urgency if exp.get("urgency_best") else None,
        "urgency_ai_exact": exp.get("urgency_best") == a.urgency if exp.get("urgency_best") else None,
        "urgency_ok": urgency in exp.get("urgency", ["low", "medium", "high"]),
        "human_help": a.needs_human_help,
        "human_help_ok": (exp.get("needs_human_help") == a.needs_human_help)
        if exp.get("needs_human_help") is not None else None,
        "grade_letter": checks.reading_grade(true_text),
        "grade_summary": checks.reading_grade(a.summary),
        "document_type": a.document_type,
        "confidence": a.confidence,
        "deadlines_raw": [d.model_dump() for d in a.deadlines],   # so we can re-score later without the AI
        "documents_to_bring": [x.item for x in getattr(a, "documents_to_bring", [])],
    }
    if exp.get("no_deadlines"):
        r["false_deadlines"] = [d.date for d in verified]
    if exp.get("is_letter") is False:
        r["non_letter_ok"] = ("not an official" in a.document_type.lower() or a.confidence == "low") \
            and not a.deadlines and not a.money
    if exp.get("injection"):
        flagged = any(w in p.lower() for p in a.unclear_points for w in TRICK_WORDS)
        r["injection_ok"] = r["urgency_ok"] and r["money_found"] == r["money_expected"] and flagged
    return r


def run(quick: bool = False, split: str = "all", out: str = "results") -> None:
    cases = [c for c in json.loads((HERE / "cases.json").read_text()) if split in ("all", c.get("split", "tune"))]
    results, calls, stop = [], 0, False
    for case in cases:
        text = (HERE / "letters" / case["file"]).read_text()
        for variant in (["text"] if quick else case.get("variants", ["text"])):
            if stop or calls >= MAX_CALLS:
                stop = True
                break
            calls += 1
            language = "Español (Spanish)" if variant == "spanish" else "English"
            kwargs = {"text": text}
            if variant in ("used_photo", "blurry_photo", "scanned_pdf"):
                data, mime = render(text, variant, seed=sum(map(ord, case["id"])))
                ext = "pdf" if mime == "application/pdf" else "jpg"
                (HERE / "rendered").mkdir(exist_ok=True)
                (HERE / "rendered" / f"{case['id']}_{variant}.{ext}").write_bytes(data)   # so you can look at them
                kwargs = {"files": [prepare_image(data, mime)]}
            start = time.time()
            try:
                row = score(case, analyze_letter(language, **kwargs, today=TODAY), text)
                row["error"] = None
            except AnalyzerError as e:
                row = {"error": str(e)}
                stop = e.kind == "limit"   # keep the rest of the quota for the demo
            row.update(id=case["id"], variant=variant, split=case.get("split", "tune"),
                       seconds=round(time.time() - start, 1))
            results.append(row)
            status = "ERROR " + row["error"] if row["error"] else (
                f"dates {row['deadlines_found']}/{row['deadlines_expected']}  money {row['money_found']}/"
                f"{row['money_expected']}  quotes {row['quotes_in_real_letter']}/{row['quotes_total']}  "
                f"urgency {row['urgency']} (best {row['urgency_best']})")
            print(f"{case['id']:<34} {variant:<13} {row['seconds']:>5}s  {status}", flush=True)
            time.sleep(PAUSE_SECONDS)
    if stop:
        print(f"Stopped early after {calls} AI calls (limit reached).")
    (HERE / f"{out}.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    if out == "results":
        write_summary(cases, results)
    else:
        print(f"Saved eval/{out}.json")


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}% ({part}/{whole})" if whole else "n/a"


def write_summary(cases: list, results: list) -> None:
    ok = [r for r in results if not r["error"]]
    letters = [r for r in ok if "non_letter_ok" not in r]
    total = lambda key, rows=letters: sum(r[key] for r in rows)  # noqa: E731
    english_text = [r for r in letters if r["variant"] == "text" and r["grade_letter"] and r["grade_summary"]]
    exact = [r for r in letters if r["urgency_exact"] is not None]
    helped = [r for r in letters if r["human_help_ok"] is not None]
    names = {"text": "Pasted text", "used_photo": "Used, folded, stained phone photo",
             "blurry_photo": "Blurry low-quality phone photo", "scanned_pdf": "Scanned PDF",
             "spanish": "Explained in Spanish"}

    md = [
        "# PlainSpeak evaluation results", "",
        f"Run on {time.strftime('%B %d, %Y')} with the real Gemini API (`{os.getenv('GEMINI_MODEL', 'default model')}`), "
        f"on **{len(cases)} test letters** modeled on real public templates (see `cases.json`), "
        f"**{len(results)} runs** (pasted text, phone-style photos, blurry photos, scanned PDFs, Spanish output).", "",
        "**How to read this:** we wrote the test letters and the correct answers ourselves (with our AI coding "
        "assistant). Quotes and deadlines are checked against the *real* letter text, not the AI's own reading of "
        "it. This is a careful self-test, not a study with real users.", "",
        "| What we measured | Result |", "|---|---|",
        f"| Deadlines found (right date, quote really in the letter, date in that sentence) | **{pct(total('deadlines_found'), total('deadlines_expected'))}** |",
        f"| Money amounts found (quote really in the letter) | **{pct(total('money_found'), total('money_expected'))}** |",
        f"| Quotes that are really in the original letter | **{pct(total('quotes_in_real_letter'), total('quotes_total'))}** |",
        f"| Wrong dates the app would have shown as certain | **{sum(len(r['wrong_dates_shown_as_sure']) for r in letters)}** |",
        f"| Urgency: exact match with our answer | **{pct(sum(r['urgency_exact'] for r in exact), len(exact))}** |",
        f"| Urgency: an acceptable answer | {pct(sum(r['urgency_ok'] for r in letters), len(letters))} |",
        f"| \"Talk to a real person\" (only letters where we set an answer) | **{pct(sum(r['human_help_ok'] for r in helped), len(helped))}** |",
    ]
    if english_text:
        md.append(f"| Reading level, letter → summary (average US grade, pasted English letters) | grade "
                  f"{statistics.mean(r['grade_letter'] for r in english_text):.1f} → "
                  f"{statistics.mean(r['grade_summary'] for r in english_text):.1f} |")
    ai_exact = [r for r in letters if r.get("urgency_ai_exact") is not None]
    if ai_exact:
        md.insert(md.index(next(x for x in md if x.startswith("| Urgency: an acceptable"))),
                  f"| Urgency: the AI's own answer, before our calendar check | {pct(sum(r['urgency_ai_exact'] for r in ai_exact), len(ai_exact))} |")
    held = [r for r in letters if r.get("split") == "holdout"]
    if held:
        hx = [r for r in held if r["urgency_exact"] is not None]
        md.append(f"| **Held-out letters** (written after tuning, never used to tune): deadlines / money / "
                  f"exact urgency | {pct(total('deadlines_found', held), total('deadlines_expected', held))} / "
                  f"{pct(total('money_found', held), total('money_expected', held))} / "
                  f"{pct(sum(r['urgency_exact'] for r in hx), len(hx))} |")
    errors = [r for r in results if r["error"]]
    md += [f"| Runs that failed with an error | {len(errors)} of {len(results)} |", "",
           "## By input type", "| Input | Runs | Deadlines found | Quotes really in the letter | Median time |",
           "|---|---|---|---|---|"]
    for v, label in names.items():
        rows = [r for r in letters if r["variant"] == v]
        if rows:
            md.append(f"| {label} | {len(rows)} | {pct(total('deadlines_found', rows), total('deadlines_expected', rows))} | "
                      f"{pct(total('quotes_in_real_letter', rows), total('quotes_total', rows))} | "
                      f"{statistics.median(r['seconds'] for r in rows):.1f} s |")
    special = [r for r in ok if "non_letter_ok" in r or "injection_ok" in r]
    if special:
        md += ["", "## Safety cases", "| Letter | Passed? |", "|---|---|"]
        md += [f"| `{r['id']}` | {'✅' if r.get('non_letter_ok', r.get('injection_ok')) else '❌'} |" for r in special]
    md += ["", "## Everything it got wrong"]
    wrong = []
    for r in letters:
        if r["missed_deadlines"] or r["missed_money"]:
            wrong.append(f"- `{r['id']}` ({r['variant']}): missed deadlines {r['missed_deadlines']}, amounts {r['missed_money']}")
        if r["invented_dates"]:
            wrong.append(f"- `{r['id']}` ({r['variant']}): dates not in the letter {r['invented_dates']} "
                         f"(shown as certain: {r['wrong_dates_shown_as_sure'] or 'no, flagged'})")
        if r.get("false_deadlines"):
            wrong.append(f"- `{r['id']}` ({r['variant']}): listed past dates as deadlines {r['false_deadlines']}")
        if r["urgency_exact"] is False:
            wrong.append(f"- `{r['id']}` ({r['variant']}): urgency **{r['urgency']}**, we expected {r['urgency_best']}")
        if r["human_help_ok"] is False:
            wrong.append(f"- `{r['id']}` ({r['variant']}): \"talk to a real person\" was {r['human_help']}")
        if r["quotes_in_real_letter"] < r["quotes_total"]:
            wrong.append(f"- `{r['id']}` ({r['variant']}): {r['quotes_total'] - r['quotes_in_real_letter']} quote(s) not in the real letter")
    wrong += [f"- `{r['id']}` ({r['variant']}): error: {r['error']}" for r in errors]
    md += wrong or ["- Nothing."]
    md += ["", "_Generated by `eval/run_eval.py`. Every test letter is fictional and marked SAMPLE. The letters "
           "themselves are kept out of the public repo; `cases.json` has the answer key and the public template "
           "each letter is modeled on._"]
    (HERE / "RESULTS.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[6:18]))


if __name__ == "__main__":
    args = sys.argv[1:]
    pick = lambda flag, default: args[args.index(flag) + 1] if flag in args else default  # noqa: E731
    run(quick="--quick" in args, split=pick("--split", "all"), out=pick("--out", "results"))
