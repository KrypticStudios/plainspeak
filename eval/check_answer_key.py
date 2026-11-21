"""Sanity check for the answer key: every expected date and dollar amount must really be in its letter.

Run:  .venv/bin/python eval/check_answer_key.py
"""

import json
import re
from pathlib import Path

from run_eval import money_key
from plainspeak.checks import date_written_in as date_in_letter

HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / "cases.json").read_text())
problems = 0
for c in cases:
    text = (HERE / "letters" / c["file"]).read_text()
    amounts = {money_key(a) for a in re.findall(r"\$[\d,]+\.\d\d", text)}
    for d in c["expect"].get("deadlines", []):
        if not date_in_letter(d, text):
            print("date not in letter:", c["id"], d); problems += 1
    for m in c["expect"].get("money", []):
        if m not in amounts:
            print("amount not in letter:", c["id"], m); problems += 1
print(f"{len(cases)} letters, {sum(len(c['variants']) for c in cases)} runs planned, {problems} problems in the answer key")
