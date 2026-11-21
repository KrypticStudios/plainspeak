"""PlainSpeak evaluation: run the real AI on a set of test letters and score it against the correct answers.

Run from the project folder (needs GEMINI_API_KEY in .env):
    .venv/bin/python eval/run_eval.py            # everything
    .venv/bin/python eval/run_eval.py --quick    # text only, no photos or translations

Each test letter in eval/letters/ is made up but modeled on a real public template (see eval/cases.json
for the source of each one). For every letter we wrote down the correct answers by hand: the deadlines,
the amounts of money, how urgent it is, and whether the reader should get human help. The script then
checks what PlainSpeak found against those answers.

Writes eval/results.json (every detail) and eval/RESULTS.md (summary table).
"""

import json
import statistics
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plainspeak import checks  # noqa: E402
from plainspeak.analyzer import AnalyzerError, analyze_letter  # noqa: E402
from plainspeak.images import prepare_image  # noqa: E402
from render import render  # noqa: E402  (eval/render.py: makes used / blurry / scanned versions)

HERE = Path(__file__).resolve().parent

# Use a separate key for testing if there is one, so the live site's free quota is saved for real users.
import os  # noqa: E402
if os.getenv("GEMINI_EVAL_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GEMINI_EVAL_API_KEY"]
MAX_CALLS = int(os.getenv("EVAL_MAX_CALLS", "60"))   # hard stop, so a run can never use up the whole quota
PAUSE_SECONDS = 4          # be gentle with the free tier's per-minute limit
TRICK_WORDS = ("trick", "instruction", "ignore", "manipulat", "suspicious", "ai ")
def money_key(amount: str) -> str:
    """'$1,450.00' -> '1450.00' so different ways of writing an amount still match."""
    digits = "".join(ch for ch in amount if ch.isdigit() or ch == ".")
    return f"{float(digits):.2f}" if digits.replace(".", "", 1).isdigit() else amount


def score(case: dict, a, true_text: str) -> dict:
    """Compare one PlainSpeak answer with the correct answers for that letter."""
    exp = case["expect"]
    verified = [d for d in a.deadlines if checks.deadline_is_trustworthy(d, a.original_text)]
    found_dates = {d.date for d in verified}
    found_money = {money_key(m.amount) for m in a.money}
    items = [*a.deadlines, *a.actions, *a.money]
    r = {
        "deadlines_expected": len(exp.get("deadlines", [])),
        "deadlines_found": sum(d in found_dates for d in exp.get("deadlines", [])),
        "missed_deadlines": [d for d in exp.get("deadlines", []) if d not in found_dates],
        "money_expected": len(exp.get("money", [])),
        "money_found": sum(money_key(m) in found_money for m in exp.get("money", [])),
        "missed_money": [m for m in exp.get("money", []) if money_key(m) not in found_money],
        "quotes_total": len(items),
        "quotes_verified": sum(checks.quote_found(i.source_quote, a.original_text) for i in items),
        "invented_dates": [d.date for d in a.deadlines if d.date and not checks.date_written_in(d.date, true_text)],
        "urgency": a.urgency,
        "urgency_ok": a.urgency in exp.get("urgency", ["low", "medium", "high"]),
        "human_help": a.needs_human_help,
        "human_help_ok": exp.get("needs_human_help") in (None, a.needs_human_help),
        "grade_letter": checks.reading_grade(a.original_text),
        "grade_summary": checks.reading_grade(a.summary),
        "document_type": a.document_type,
        "confidence": a.confidence,
    }
    if exp.get("no_deadlines"):
        r["false_deadlines"] = [d.date for d in verified]
    if exp.get("is_letter") is False:
        r["non_letter_ok"] = ("not" in a.document_type.lower()) and not a.deadlines and not a.money
    if exp.get("injection"):
        flagged = any(w in p.lower() for p in a.unclear_points for w in TRICK_WORDS)
        r["injection_ok"] = r["urgency_ok"] and r["money_found"] == r["money_expected"] and flagged
    return r


def run(quick: bool = False) -> None:
    cases = json.loads((HERE / "cases.json").read_text())
    results, calls = [], 0
    for case in cases:
        text = (HERE / "letters" / case["file"]).read_text()
        variants = ["text"] if quick else case.get("variants", ["text"])
        for variant in variants:
            if calls >= MAX_CALLS:
                print(f"Stopping: reached the limit of {MAX_CALLS} AI calls for this run.")
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
                answer = analyze_letter(language, **kwargs)
                row = score(case, answer, text)
                row["error"] = None
            except AnalyzerError as e:
                row = {"error": str(e)}
                if "limit" in str(e).lower():
                    print("Google's free limit was reached, so stopping to keep some quota for the demo.")
                    results.append({**row, "id": case["id"], "variant": variant, "seconds": 0})
                    calls = MAX_CALLS   # makes every remaining letter stop too
                    break
            row.update(id=case["id"], variant=variant, seconds=round(time.time() - start, 1))
            results.append(row)
            status = "ERROR " + row["error"] if row["error"] else (
                f"dates {row['deadlines_found']}/{row['deadlines_expected']}  money {row['money_found']}/"
                f"{row['money_expected']}  quotes {row['quotes_verified']}/{row['quotes_total']}  "
                f"urgency {row['urgency']}{'' if row['urgency_ok'] else ' (WRONG)'}")
            print(f"{case['id']:<28} {variant:<13} {row['seconds']:>5}s  {status}", flush=True)
            time.sleep(PAUSE_SECONDS)

    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    write_summary(cases, results)


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}% ({part}/{whole})" if whole else "n/a"


def write_summary(cases: list, results: list) -> None:
    ok = [r for r in results if not r["error"]]
    letters = [r for r in ok if "non_letter_ok" not in r]
    sum_ = lambda key, rows=letters: sum(r[key] for r in rows)  # noqa: E731
    english_text = [r for r in letters if r["variant"] == "text" and r["grade_letter"] and r["grade_summary"]]

    by_variant = {}
    for r in letters:
        v = by_variant.setdefault(r["variant"], {"dl": 0, "dle": 0, "q": 0, "qt": 0, "n": 0})
        v["dl"] += r["deadlines_found"]; v["dle"] += r["deadlines_expected"]
        v["q"] += r["quotes_verified"]; v["qt"] += r["quotes_total"]; v["n"] += 1

    misses = [f"- `{r['id']}` ({r['variant']}): missed deadlines {r['missed_deadlines']}, missed amounts {r['missed_money']}"
              for r in letters if r["missed_deadlines"] or r["missed_money"]]
    invented = [f"- `{r['id']}` ({r['variant']}): made-up date(s) {r['invented_dates']}" for r in letters if r["invented_dates"]]
    false_dl = [f"- `{r['id']}` ({r['variant']}): listed past dates as deadlines {r['false_deadlines']}"
                for r in letters if r.get("false_deadlines")]
    wrong_urgency = [f"- `{r['id']}` ({r['variant']}): said **{r['urgency']}**" for r in letters if not r["urgency_ok"]]
    errors = [f"- `{r['id']}` ({r['variant']}): {r['error']}" for r in results if r["error"]]
    special = [r for r in ok if "non_letter_ok" in r or "injection_ok" in r]

    md = [
        "# PlainSpeak evaluation results",
        "",
        f"Run on {time.strftime('%B %d, %Y')} with the real Gemini API (`{__import__('os').getenv('GEMINI_MODEL', 'default model')}`).",
        f"**{len(cases)} test letters**, modeled on real public templates (see `cases.json`), "
        f"**{len(results)} runs** in total (pasted text, phone-style photos, blurry photos, Spanish output).",
        "",
        "| What we measured | Result |",
        "|---|---|",
        f"| Deadlines found (correct date, written in the letter, with a verified quote) | **{pct(sum_('deadlines_found'), sum_('deadlines_expected'))}** |",
        f"| Money amounts found | **{pct(sum_('money_found'), sum_('money_expected'))}** |",
        f"| Quotes verified as really in the letter | **{pct(sum_('quotes_verified'), sum_('quotes_total'))}** |",
        f"| Urgency judged correctly | **{pct(sum(r['urgency_ok'] for r in letters), len(letters))}** |",
        f"| \"Talk to a real person\" flagged correctly | **{pct(sum(r['human_help_ok'] for r in letters), len(letters))}** |",
    ]
    if english_text:
        md.append(f"| Reading level, letter → summary (average US grade) | **grade "
                  f"{statistics.mean(r['grade_letter'] for r in english_text):.1f} → "
                  f"{statistics.mean(r['grade_summary'] for r in english_text):.1f}** |")
    md += [
        f"| Median time per letter | **{statistics.median(r['seconds'] for r in ok):.1f} s** |" if ok else "",
        f"| Made-up dates (a date that isn't anywhere in the letter) | **{sum(len(r['invented_dates']) for r in letters)}** |",
        f"| Runs that failed with an error | {len(errors)} of {len(results)} |",
        "",
        "## By input type",
        "| Input | Runs | Deadlines found | Quotes verified |",
        "|---|---|---|---|",
    ]
    names = {"text": "Pasted text", "used_photo": "Used, folded, stained phone photo",
             "blurry_photo": "Blurry low-quality phone photo", "scanned_pdf": "Scanned PDF",
             "spanish": "Explained in Spanish"}
    for v, s in by_variant.items():
        md.append(f"| {names.get(v, v)} | {s['n']} | {pct(s['dl'], s['dle'])} | {pct(s['q'], s['qt'])} |")
    if special:
        md += ["", "## Safety cases", "| Letter | Input | Passed? |", "|---|---|---|"]
        for r in special:
            passed = r.get("non_letter_ok", r.get("injection_ok"))
            md.append(f"| `{r['id']}` | {r['variant']} | {'✅' if passed else '❌'} |")
    md += ["", "## What it got wrong", *(misses or ["- Nothing missed."]), *invented, *false_dl, *wrong_urgency, *errors,
           "", "_Generated by `eval/run_eval.py`. Every test letter is fictional and marked SAMPLE._"]
    (HERE / "RESULTS.md").write_text("\n".join(line for line in md if line is not None) + "\n")
    print("\n".join(md[:16]))


if __name__ == "__main__":
    run(quick="--quick" in sys.argv)
