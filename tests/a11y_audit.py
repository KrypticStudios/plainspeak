"""Accessibility audit with axe-core (the standard automated WCAG checker) on PlainSpeak's real pages.

Run (app must be running):  .tools/bin/python tests/a11y_audit.py [base_url]
"""

import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
AXE = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
PAGES = {
    "start (English)": "/",
    "results (English)": "/?example=eviction",
    "results + AI-mistake demo": "/?example=eviction&mistake=1",
    "results (Arabic, right-to-left)": "/?example=eviction&lang=ar",
    "results (high contrast + large text)": "/?example=benefits&contrast=1&bigtext=1",
    "start (Spanish)": "/?lang=es",
    "basic check without AI": "/",
}

total = 0
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for name, path in PAGES.items():
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(BASE + path)
        page.wait_for_selector("h1", timeout=60_000)
        page.wait_for_timeout(2500)
        if name.startswith("basic check"):   # the no-AI check needs a few clicks to reach
            page.get_by_text("Don't send my letter to the AI").click()
            page.get_by_role("tab", name="Paste").click() if page.get_by_role("tab", name="Paste").count() else \
                page.locator("[role=tab]").nth(1).click()
            page.locator("textarea").first.fill(open("samples/eviction_notice.txt").read())
            page.locator("textarea").first.press("Control+Enter")
            page.wait_for_timeout(800)
            page.get_by_role("button", name="Explain").last.click()
            page.wait_for_selector("text=Basic check", timeout=30_000)
            page.wait_for_timeout(1500)
        page.add_script_tag(url=AXE)
        result = page.evaluate("""async () => {
            const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}});
            return r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, n: v.nodes.length,
                where: v.nodes.slice(0, 3).map(n => n.target.join(' ') + ' :: ' + (n.failureSummary || '').split('\\n')[1])}));
        }""")
        total += len(result)
        print(f"\n== {name}: {len(result)} problem type(s)")
        for v in result:
            print(f"  [{v['impact']}] {v['id']} x{v['n']}: {v['help']}")
            for w in v["where"]:
                print("      ", w[:170])
        page.close()
    browser.close()
print(f"\nTotal problem types across pages: {total}")
