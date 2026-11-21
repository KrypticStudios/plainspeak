"""Turns a test letter into realistic, imperfect pictures, like the ones real people take.

Real letters arrive folded, coffee-stained and photographed at an angle under a lamp. To test
PlainSpeak fairly, we draw each letter on paper and then make it look used:

  used_photo    yellowed paper, fold creases, a stain, uneven light, tilted phone angle, grain
  blurry_photo  the same, plus camera blur and low resolution
  scanned_pdf   a grey, slightly crooked office-scanner copy, saved as a PDF

Only uses Pillow, no extra libraries.
"""

import random
import textwrap
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FONT_PATHS = ["/System/Library/Fonts/Supplemental/Times New Roman.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf", "DejaVuSerif.ttf"]


def _font(size: int, bold: bool = False):
    paths = ["/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"] if bold else []
    for path in paths + FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_page(text: str) -> Image.Image:
    """Typeset the letter on a clean white US-letter page (about 150 dpi)."""
    body, bold = _font(24), _font(28, bold=True)
    lines = []
    for raw in text.splitlines():
        for part in textwrap.wrap(raw, 88) or [""]:
            lines.append((part, raw.isupper() and len(raw) > 3))   # ALL-CAPS lines look like headings
    page = Image.new("RGB", (1275, max(1650, 120 + 34 * len(lines))), "white")
    d = ImageDraw.Draw(page)
    y = 90
    for line, heading in lines:
        d.text((110, y), line, fill=(20, 20, 25), font=bold if heading else body)
        y += 34
    return page


def _perspective(img: Image.Image, strength: float, rng: random.Random) -> Image.Image:
    """Make it look like the phone wasn't held perfectly flat over the page."""
    w, h = img.size
    j = lambda: rng.uniform(0, strength) * w  # noqa: E731
    src = [(j(), j()), (w - j(), j()), (w - j(), h - j()), (j(), h - j())]
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    # Solve for the 8 perspective coefficients (standard formula).
    matrix, vec = [], []
    for (x, y), (u, v) in zip(dst, src):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); vec.append(u)
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y]); vec.append(v)
    coeffs = _solve(matrix, vec)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC,
                         fillcolor=(70, 62, 55))   # the table under the paper


def _solve(a: list, b: list) -> list:
    """Tiny Gaussian elimination, so we don't need numpy."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c])]
    return [m[i][n] / m[i][i] for i in range(n)]


def make_used(page: Image.Image, seed: int) -> Image.Image:
    rng = random.Random(seed)
    w, h = page.size
    # 1. Old, slightly yellow paper.
    paper = Image.new("RGB", (w, h), (243, 236, 218))
    img = ImageChops.multiply(page, paper)
    d = ImageDraw.Draw(img, "RGBA")
    # 2. Fold creases (the letter was folded in three for the envelope).
    for fy in (h // 3, 2 * h // 3):
        fy += rng.randint(-15, 15)
        d.line([(0, fy), (w, fy + rng.randint(-8, 8))], fill=(120, 110, 95, 90), width=3)
        d.rectangle([0, fy + 2, w, fy + 14], fill=(0, 0, 0, 18))
    # 3. A coffee ring somewhere.
    cx, cy, r = rng.randint(200, w - 200), rng.randint(300, h - 300), rng.randint(70, 110)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(150, 105, 60, 110), width=9)
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=(160, 120, 70, 25))
    # 4. A pen mark and a sticky smudge, like real mail.
    d.line([(w * 0.62, h * 0.12), (w * 0.85, h * 0.10)], fill=(30, 40, 140, 160), width=4)
    # 5. Uneven light: a lamp on one side, the phone's shadow on the other.
    light = Image.linear_gradient("L").rotate(rng.choice([90, -90, 180]), expand=True).resize((w, h))
    light = light.point(lambda v: 150 + v * 105 // 255)
    img = ImageChops.multiply(img, Image.merge("RGB", [light] * 3))
    # 6. Taken at an angle, then a bit of camera grain.
    img = img.rotate(rng.uniform(-4, 4), expand=True, fillcolor=(70, 62, 55))
    img = _perspective(img, 0.035, rng)
    noise = Image.effect_noise(img.size, 18).convert("RGB")
    img = Image.blend(img, ImageChops.multiply(img, ImageChops.invert(noise).point(lambda v: 200 + v // 5)), 0.5)
    return ImageEnhance.Contrast(img).enhance(0.9)


def make_blurry(page: Image.Image, seed: int) -> Image.Image:
    img = make_used(page, seed)
    w, h = img.size
    img = img.resize((int(w * 0.55), int(h * 0.55)), Image.Resampling.BILINEAR)   # low-quality camera
    return img.filter(ImageFilter.GaussianBlur(1.3))                                   # shaky hands


def make_scan(page: Image.Image, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = page.convert("L")
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = img.rotate(rng.uniform(-1.5, 1.5), expand=True, fillcolor=235)
    speckle = Image.effect_noise(img.size, 40).point(lambda v: 0 if v < 25 else 255)   # scanner dust
    img = ImageChops.darker(img, speckle)
    return img.filter(ImageFilter.GaussianBlur(0.5)).convert("RGB")


def to_jpeg(img: Image.Image, quality: int = 70) -> bytes:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def to_pdf(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PDF", resolution=150)
    return buf.getvalue()


def render(text: str, kind: str, seed: int = 0) -> tuple[bytes, str]:
    """Return (file bytes, mime type) for one realistic version of the letter."""
    page = draw_page(text)
    if kind == "used_photo":
        return to_jpeg(make_used(page, seed)), "image/jpeg"
    if kind == "blurry_photo":
        return to_jpeg(make_blurry(page, seed), quality=55), "image/jpeg"
    if kind == "scanned_pdf":
        return to_pdf(make_scan(page, seed)), "application/pdf"
    raise ValueError(kind)
