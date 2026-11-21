"""Gets phone photos ready before sending them to the AI.

Phone photos are often sideways (the phone stores the rotation separately) and
very large (5-10 MB). We turn them the right way up and shrink them, which makes
the AI faster and more accurate, and keeps us within the free limits.
"""

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SIDE = 2000  # pixels: plenty for reading text, much smaller than a raw phone photo


def prepare_image(data: bytes, mime_type: str) -> tuple[bytes, str]:
    """Return (bytes, mime_type) ready for the AI. PDFs and unreadable files pass through unchanged."""
    if not mime_type.startswith("image/"):
        return data, mime_type
    try:
        img = Image.open(BytesIO(data))
        img = ImageOps.exif_transpose(img)        # fix sideways phone photos
        img = img.convert("RGB")                  # JPEG has no transparency
        img.thumbnail((MAX_SIDE, MAX_SIDE))       # shrink, keeping the shape
        out = BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue(), "image/jpeg"
    except (UnidentifiedImageError, OSError):
        return data, mime_type
