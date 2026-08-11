"""Shared helper for build_docx_report.py and build_pptx_deck.py.

Full-page Playwright screenshots of a real news article can be several
thousand pixels tall (headline + body + related-article rails + comment
section, all in one capture) and multiple megabytes each. Two problems
follow if such an image is embedded naively:

  1. File size — embedding at native resolution bloats the resulting
     .docx/.pptx into the tens of megabytes for no visual benefit, since
     the document only ever displays the image a few inches wide.
  2. Layout — an image that's, say, 1:11 wide:tall would render 60+
     inches tall if simply scaled to a fixed *width*. In a .docx that
     spills across dozens of pages; in a .pptx it overflows the slide
     entirely and is effectively invisible.

`prepare_image_for_embed` fixes (1) by downscaling and re-encoding as
JPEG. `fit_within_box` fixes (2) by computing dimensions that respect
*both* a max width and a max height (whichever is more constraining wins),
the same "contain" logic as CSS `object-fit: contain`.
"""

from pathlib import Path

from PIL import Image

MAX_WIDTH_PX = 1600
JPEG_QUALITY = 82
CACHE_DIRNAME = ".embed_cache"


def prepare_image_for_embed(path: Path, base_dir: Path) -> tuple[Path, int, int]:
    """Return (embeddable_path, width_px, height_px) for the image at
    `path`, downscaled to MAX_WIDTH_PX and re-encoded as JPEG. Falls back
    to the original path (and its native size, if readable) for files
    Pillow can't open, so the caller's existing not-found/error handling
    still applies.
    """
    try:
        img = Image.open(path)
        img.load()
    except Exception:
        return path, 0, 0

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    if img.width > MAX_WIDTH_PX:
        ratio = MAX_WIDTH_PX / img.width
        img = img.resize((MAX_WIDTH_PX, max(1, round(img.height * ratio))), Image.LANCZOS)

    cache_dir = base_dir / CACHE_DIRNAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_path = cache_dir / (path.stem + ".jpg")
    img.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return out_path, img.width, img.height


def resolve_image_path(image_path: str, base_dir: Path) -> Path:
    return (base_dir / image_path).resolve() if not Path(image_path).is_absolute() else Path(image_path)


def fit_within_box(width_px: int, height_px: int, max_width_in: float, max_height_in: float):
    """Compute (width_in, height_in) that fit `width_px`x`height_px` inside
    a max_width_in x max_height_in box, preserving aspect ratio — whichever
    dimension is more constraining determines the final size. Falls back to
    the box's full width (square-ish) if pixel dimensions are unknown.
    """
    if not width_px or not height_px:
        return max_width_in, max_width_in

    aspect = height_px / width_px
    width_in = max_width_in
    height_in = width_in * aspect
    if height_in > max_height_in:
        height_in = max_height_in
        width_in = height_in / aspect
    return width_in, height_in
