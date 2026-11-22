"""Hard, real-world inputs through the real AI: sideways, upside-down and dark photos, a PDF with real text,
letters in Chinese, Vietnamese and Russian, and a court letter full of dates.

Run:  .venv/bin/python tests/hard_letters.py     (uses the test key GEMINI_EVAL_API_KEY if set; ~9 AI calls)
"""

import os
import sys
import time
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval"))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
if os.getenv("GEMINI_EVAL_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GEMINI_EVAL_API_KEY"]
    os.environ.pop("GEMINI_BACKUP_API_KEY", None)

from plainspeak import checks  # noqa: E402
from plainspeak.analyzer import analyze_letter  # noqa: E402
from plainspeak.export import next_deadline  # noqa: E402
from plainspeak.images import prepare_image  # noqa: E402
from render import draw_page, make_used  # noqa: E402

TODAY = __import__("datetime").date(2026, 11, 21)
EVICTION = (ROOT / "samples" / "eviction_notice.txt").read_text()

CHINESE = """样本信件 - 虚构 - 仅供测试
河景市住房管理局
地址：中央大道200号  电话：(555) 014-2500
日期：2026年11月18日
尊敬的王丽女士：
您的租房补助需要每年重新认证。请于2026年12月10日上午10点到本办公室参加面谈。
请携带过去60天的收入证明。如果您不能参加，请在2026年12月8日之前致电 (555) 014-2500 改约。
如果您不参加面谈，您的补助可能会被终止。
"""
VIETNAMESE = """THƯ MẪU - HƯ CẤU - CHỈ ĐỂ THỬ NGHIỆM
CÔNG TY ĐIỆN RIVERTON
Điện thoại: (555) 012-4000
Ngày 19 tháng 11 năm 2026
Kính gửi ông Trần Văn Nam,
Hóa đơn tiền điện của ông đã quá hạn. Số tiền còn nợ: $245.80.
Nếu chúng tôi không nhận được thanh toán trước ngày 12 tháng 12 năm 2026, điện có thể bị cắt.
Vui lòng gọi (555) 012-4000 để lập kế hoạch thanh toán.
"""
RUSSIAN = """ОБРАЗЕЦ ПИСЬМА - ВЫМЫШЛЕННОЕ - ТОЛЬКО ДЛЯ ТЕСТА
Больница Ривертон, отдел оплаты. Телефон: (555) 017-3300
Дата: 15 ноября 2026 г.
Уважаемая Анна Петрова,
Ваш долг за лечение составляет $640.00. Пожалуйста, оплатите до 15 декабря 2026 г.,
иначе счёт может быть передан в коллекторское агентство. Вы можете подать заявление на финансовую помощь.
"""
COURT = """SAMPLE LETTER - FICTIONAL - FOR TESTING ONLY
RIVERTON COUNTY HOUSING COURT
NOTICE OF HEARING   Case No. 26-UD-1188   Notice date: November 16, 2026
Tenant: Maria Lopez   Landlord: Maplewood Property Management LLC
Your eviction case was filed on November 12, 2026. A hearing is set for December 7, 2026 at 9:00 AM in Courtroom 3B.
You must file your written answer no later than December 2, 2026.
A free legal clinic is available on November 30, 2026 and December 1, 2026 from 1:00 PM to 4:00 PM.
If you do not attend the hearing on December 7, 2026, the court may enter a default judgment against you.
Your lease began on March 1, 2025. Rent was last paid on September 3, 2026.
"""
EXPECT = {   # (letter text, deadlines that must be found, deadlines that must NOT be shown as upcoming)
    "Chinese housing letter": (CHINESE, {"2026-12-10", "2026-12-08"}, set()),
    "Vietnamese electric bill": (VIETNAMESE, {"2026-12-12"}, set()),
    "Russian hospital bill": (RUSSIAN, {"2026-12-15"}, set()),
    "court letter full of dates": (COURT, {"2026-12-07", "2026-12-02"}, {"2026-11-12", "2025-03-01", "2026-09-03"}),
}


def photo(img: Image.Image) -> list:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return [prepare_image(buf.getvalue(), "image/jpeg")]


def report(name: str, a, letter: str, must: set, must_not: set) -> bool:
    trusted = {d.date for d in a.deadlines if checks.deadline_is_trustworthy(d, a.original_text)}
    really = {d.date for d in a.deadlines if checks.deadline_is_trustworthy(d, letter)}
    nxt = next_deadline(a, today=TODAY)
    ok = must <= trusted and not (must_not & trusted) and trusted <= really
    print(f"{'PASS' if ok else 'FAIL'}  {name}: type={a.document_type!r} urgency={a.urgency} "
          f"| shown as sure: {sorted(trusted)} | expected: {sorted(must)} | countdown: {nxt[1].date if nxt else None}")
    if not ok:
        print("      all deadlines the AI gave:", [(d.date, d.source_quote[:60]) for d in a.deadlines])
    return ok


results = []
for name, (text, must, must_not) in EXPECT.items():
    language = "English"
    results.append(report(name, analyze_letter(language, text=text), text, must, must_not))
    time.sleep(4)

page = make_used(draw_page(EVICTION), seed=11)
for name, img in {"sideways photo (90°)": page.rotate(90, expand=True),
                  "upside-down photo": page.rotate(180),
                  "dark, underexposed photo": ImageEnhance.Brightness(page).enhance(0.35)}.items():
    results.append(report(name, analyze_letter("English", files=photo(img)), EVICTION, {"2026-12-04"}, set()))
    time.sleep(4)

# A PDF with real, selectable text (made by printing an HTML page with Chrome)
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page()
    pg.set_content("<pre style='font:14px Times; white-space: pre-wrap'>" + EVICTION.replace("<", "&lt;") + "</pre>")
    pdf = pg.pdf(format="Letter")
    b.close()
results.append(report("PDF with real text", analyze_letter("English", files=[(pdf, "application/pdf")]),
                      EVICTION, {"2026-12-04"}, set()))
print(f"\n{sum(results)}/{len(results)} hard letters passed")
