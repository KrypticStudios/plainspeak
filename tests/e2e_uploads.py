"""End-to-end upload test: puts real files through PlainSpeak's actual upload button in Chrome.

Not part of the normal `pytest` run (it needs the app running, Chrome, Playwright and an API key).
Run:   .tools/bin/python tests/e2e_uploads.py [base_url]        (default http://localhost:8501)

Files tested (all made from the fictional sample letters):
  - a big phone photo (4000x3000, ~4 MB, used/folded/stained look)   -> should be explained
  - a scanned PDF                                                     -> should be explained
  - a PNG screenshot                                                  -> should be explained
  - a letter photographed as 2 separate pages                         -> should be explained as one letter
  - a 6-page PDF                                   -> should be refused before any AI call
  - a text file renamed to .jpg                    -> should be refused
  - 6 photos at once                               -> should be refused (max 5 pages)
  - half of a photo (download cut off)             -> should be refused, not crash
  - a 30,000 x 30,000 pixel image in a tiny file   -> should be refused, not crash
  - one good page plus one fake page               -> should be refused until the bad one is removed
"""

import sys
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from render import draw_page, make_scan, make_used  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
TMP = Path(tempfile.mkdtemp(prefix="plainspeak-e2e-"))
SAMPLES = ROOT / "samples"


def save(img: Image.Image, name: str, **kw) -> Path:
    path = TMP / name
    img.save(path, **kw)
    return path


def make_files() -> dict:
    eviction = (SAMPLES / "eviction_notice.txt").read_text()
    bill = (SAMPLES / "medical_bill.txt").read_text()
    benefits = (SAMPLES / "benefits_renewal.txt").read_text()
    files = {}
    big = make_used(draw_page(eviction), seed=7).resize((3000, 4000))
    files["big_phone_photo"] = [save(big, "IMG_4021.jpg", quality=92)]
    files["scanned_pdf"] = [save(make_scan(draw_page(bill), seed=3), "scan_0001.pdf", resolution=150)]
    files["png_screenshot"] = [save(draw_page(benefits), "Screenshot 2026-11-21.png")]
    lines = eviction.splitlines()
    half = len(lines) // 2
    files["two_pages"] = [save(make_used(draw_page("\n".join(lines[:half])), 1), "page1.jpg", quality=85),
                          save(make_used(draw_page("\n".join(lines[half:])), 2), "page2.jpg", quality=85)]
    pages = [draw_page(f"Page {i}") for i in range(6)]
    pdf6 = TMP / "six_pages.pdf"
    pages[0].save(pdf6, save_all=True, append_images=pages[1:])
    files["six_page_pdf"] = [pdf6]
    fake = TMP / "not_really_a_photo.jpg"
    fake.write_text("this is just text pretending to be a picture")
    files["fake_jpg"] = [fake]
    small = draw_page("tiny").resize((300, 400))
    files["six_photos"] = [save(small, f"p{i}.jpg") for i in range(6)]
    good = files["png_screenshot"][0].read_bytes()
    cut = TMP / "half_downloaded.png"
    cut.write_bytes(good[: len(good) // 2])
    files["truncated_photo"] = [cut]
    giant = TMP / "giant.png"
    Image.new("1", (30_000, 30_000)).save(giant)
    files["giant_dimensions"] = [giant]
    files["good_plus_bad"] = [files["png_screenshot"][0], fake]
    return files


EXPECT_OK = {"big_phone_photo", "scanned_pdf", "png_screenshot", "two_pages"}


def run() -> int:
    files = make_files()
    failures = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for case, paths in files.items():
            page = browser.new_page(viewport={"width": 1280, "height": 1000})
            page.goto(BASE + "/")
            page.wait_for_selector("h1", timeout=60_000)
            page.wait_for_timeout(1500)
            page.locator('input[type="file"]').first.set_input_files([str(x) for x in paths])
            page.wait_for_timeout(2500)
            body = page.inner_text("body")
            explain = page.get_by_role("button", name="Explain my letter (")
            enabled = explain.count() > 0 and explain.first.is_enabled()
            if case in EXPECT_OK:
                if not enabled:
                    print(f"FAIL {case}: button not enabled. Page says: {body[-300:]!r}")
                    failures += 1
                    continue
                explain.first.click()
                try:
                    page.wait_for_selector("text=What this letter means", timeout=90_000)
                except Exception:
                    print(f"FAIL {case}: no result. Page says: {page.inner_text('body')[-400:]!r}")
                    failures += 1
                    continue
                page.wait_for_timeout(1000)
                text = page.inner_text("body")
                ok = text.count("found in your letter") + text.count("found in what we read from your photo")
                bad = text.count("could not find these words")
                title = text.split("📄")[1].splitlines()[0].strip() if "📄" in text else "?"
                print(f"OK   {case}: '{title}' | quotes verified {ok}, not found {bad} | "
                      f"countdown: {'days left' in text}")
                if bad:
                    failures += 1
            else:
                crashed = page.locator('[data-testid="stException"]').count() > 0
                refused = (not enabled) and not crashed and any(
                    w in body for w in ("more than 5", "at most 5", "couldn't open", "doesn't look like",
                                        "Please upload", "too large"))
                print(f"{'OK  ' if refused else 'FAIL'} {case}: refused={refused}")
                failures += 0 if refused else 1
            page.close()
        browser.close()
    print(f"\n{len(files) - failures}/{len(files)} upload cases passed. Test files in {TMP}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
