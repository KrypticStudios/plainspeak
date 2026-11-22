"""Every language has every piece of text, and keeps the same {placeholders} as English (i18n-sync check)."""

import re

import pytest

from plainspeak import ui_new, ui_start, ui_text
from plainspeak.speech import LANGUAGES

CODES = sorted(set(LANGUAGES.values()))
TABLES = {"UI": ui_start.UI, "MORE": ui_start.MORE, "NEW": ui_new.NEW}
LISTS = {"TEXT": (ui_text.TEXT, ui_text.KEYS), "EXTRA": (ui_text.EXTRA, ui_text.EXTRA_KEYS),
         "ASK": (ui_text.ASK, ui_text.ASK_KEYS)}


def holes(s: str) -> set[str]:
    return set(re.findall(r"\{\w*\}", s))


@pytest.mark.parametrize("code", CODES)
def test_every_key_is_translated(code):
    for name, table in TABLES.items():
        missing = set(table["en"]) - set(table.get(code, {}))
        assert not missing, f"{name}[{code}] is missing {sorted(missing)}"
    for name, (table, keys) in LISTS.items():
        assert len(table.get(code, [])) == len(keys), f"{name}[{code}] has the wrong number of labels"
    for name in ("ESTIMATED", "SHARE"):
        assert code in getattr(ui_text, name), f"{name} has no {code}"


@pytest.mark.parametrize("code", CODES)
def test_placeholders_match_english(code):
    for name, table in TABLES.items():
        for key, english in table["en"].items():
            if key in table.get(code, {}):
                assert holes(table[code][key]) == holes(english), f"{name}[{code}][{key}] placeholders differ"
    for name, (table, _) in LISTS.items():
        for en, other in zip(table["en"], table.get(code, [])):
            assert holes(other) == holes(en), f"{name}[{code}]: {other!r}"


@pytest.mark.parametrize("code", [c for c in CODES if c != "en"])
def test_new_feature_text_is_really_translated(code):
    """Buttons and headings must not just be English copied over (a missed translation)."""
    same = [k for k, v in ui_new.NEW[code].items() if v == ui_new.NEW["en"][k]]
    assert not same, f"NEW[{code}] still English: {same}"
