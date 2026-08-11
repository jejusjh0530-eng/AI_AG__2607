"""Build a styled .pptx briefing deck from the same structured JSON input
used by build_docx_report.py.

Both scripts read one JSON file so the report and the deck stay in sync —
you analyze the scraped articles once, and both outputs are just different
renderings of the same "sections" list. A section that should appear in
only one of the two outputs (e.g. a long "Sources" list that suits the
report but clutters a deck) can be excluded with "include_in".

Usage:
    python build_pptx_deck.py --input briefing.json --output briefing.pptx [--color "#2E86AB"]

JSON input schema: see build_docx_report.py's module docstring. Relevant
per-section keys for the deck:
  - "heading"   -> slide title
  - "paragraphs" + "bullets" -> slide body bullets (paragraphs become
    bullets too; a deck has no separate prose flow like a document does)
  - "image"     -> picture placed on the right half of the slide
  - "source"    -> small caption under the title
  - "include_in": ["pptx"] / ["docx"] -> restrict which output renders it
"""

import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from image_utils import fit_within_box, prepare_image_for_embed, resolve_image_path

FONT_NAME = "맑은 고딕"
TITLE_SLIDE_TITLE_SIZE = Pt(40)
TITLE_SLIDE_SUBTITLE_SIZE = Pt(20)
SLIDE_TITLE_SIZE = Pt(30)
CAPTION_SIZE = Pt(12)
BODY_SIZE = Pt(18)
DEFAULT_COLOR = "1F4E79"

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
MARGIN = Inches(0.5)
IMAGE_MAX_WIDTH_IN = 5.6
IMAGE_MAX_HEIGHT_IN = 5.7
IMAGE_WIDTH = Inches(IMAGE_MAX_WIDTH_IN)

HEX_LENGTH = 6


def parse_color(value: str) -> RGBColor:
    hex_value = value.lstrip("#")
    if len(hex_value) != HEX_LENGTH or any(
        c not in "0123456789ABCDEFabcdef" for c in hex_value
    ):
        raise ValueError(
            f"'{value}' is not a valid hex color (expected format: RRGGBB or #RRGGBB)"
        )
    return RGBColor.from_string(hex_value.upper())


def set_font(run, size=None, color: RGBColor = None, bold: bool = None, italic: bool = None):
    run.font.name = FONT_NAME
    if size is not None:
        run.font.size = size
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    return run


def blank_slide(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])  # blank layout


def add_textbox(slide, left, top, width, height):
    box = slide.shapes.add_textbox(left, top, width, height)
    box.text_frame.word_wrap = True
    return box.text_frame


def add_title_slide(prs: Presentation, title_text: str, subtitle_text: str, color: RGBColor):
    slide = blank_slide(prs)

    tf = add_textbox(slide, MARGIN, Inches(2.6), SLIDE_WIDTH - 2 * MARGIN, Inches(1.6))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title_text
    set_font(run, size=TITLE_SLIDE_TITLE_SIZE, color=color, bold=True)

    if subtitle_text:
        sub_tf = add_textbox(slide, MARGIN, Inches(4.2), SLIDE_WIDTH - 2 * MARGIN, Inches(0.8))
        sp = sub_tf.paragraphs[0]
        sp.alignment = PP_ALIGN.CENTER
        srun = sp.add_run()
        srun.text = subtitle_text
        set_font(srun, size=TITLE_SLIDE_SUBTITLE_SIZE, color=RGBColor(0x59, 0x59, 0x59), italic=True)

    return slide


def add_content_slide(prs: Presentation, section: dict, color: RGBColor, base_dir: Path):
    slide = blank_slide(prs)
    has_image = bool(section.get("image"))
    body_width = (IMAGE_WIDTH and (SLIDE_WIDTH - 3 * MARGIN - IMAGE_WIDTH)) if has_image else (SLIDE_WIDTH - 2 * MARGIN)

    # Title
    title_tf = add_textbox(slide, MARGIN, Inches(0.4), SLIDE_WIDTH - 2 * MARGIN, Inches(1.0))
    tp = title_tf.paragraphs[0]
    trun = tp.add_run()
    trun.text = section.get("heading", "")
    set_font(trun, size=SLIDE_TITLE_SIZE, color=color, bold=True)

    top = Inches(1.3)

    source = section.get("source")
    if source:
        cap_tf = add_textbox(slide, MARGIN, top, body_width, Inches(0.4))
        cp = cap_tf.paragraphs[0]
        crun = cp.add_run()
        crun.text = source
        set_font(crun, size=CAPTION_SIZE, color=RGBColor(0x80, 0x80, 0x80), italic=True)
        top = top + Inches(0.45)

    body_lines = list(section.get("paragraphs", [])) + list(section.get("bullets", []))
    if body_lines:
        body_tf = add_textbox(slide, MARGIN, top, body_width, SLIDE_HEIGHT - top - MARGIN)
        for i, line in enumerate(body_lines):
            p = body_tf.paragraphs[0] if i == 0 else body_tf.add_paragraph()
            p.text = f"• {line}"
            for run in p.runs:
                set_font(run, size=BODY_SIZE)
            p.space_after = Pt(10)

    if has_image:
        image_path = section["image"]
        resolved = resolve_image_path(image_path, base_dir)
        image_left = SLIDE_WIDTH - MARGIN - IMAGE_WIDTH
        if resolved.exists():
            embed_path, width_px, height_px = prepare_image_for_embed(resolved, base_dir)
            width_in, height_in = fit_within_box(width_px, height_px, IMAGE_MAX_WIDTH_IN, IMAGE_MAX_HEIGHT_IN)
            slide.shapes.add_picture(
                str(embed_path), image_left, Inches(1.3), width=Inches(width_in), height=Inches(height_in)
            )
        else:
            warn_tf = add_textbox(slide, image_left, Inches(1.3), IMAGE_WIDTH, Inches(0.6))
            wp = warn_tf.paragraphs[0]
            wrun = wp.add_run()
            wrun.text = f"[Screenshot not found: {image_path}]"
            set_font(wrun, size=CAPTION_SIZE, italic=True)

    return slide


def section_applies(section: dict, output: str) -> bool:
    include_in = section.get("include_in")
    return include_in is None or output in include_in


def build_deck(data: dict, base_dir: Path, color_override: RGBColor = None) -> Presentation:
    title_text = data.get("title", "Untitled Briefing")
    subtitle_text = data.get("subtitle", "")
    main_color = color_override or parse_color(data.get("color", DEFAULT_COLOR))

    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    add_title_slide(prs, title_text, subtitle_text, main_color)

    for section in data.get("sections", []):
        if not section_applies(section, "pptx"):
            continue
        add_content_slide(prs, section, main_color, base_dir)

    return prs


def parse_args():
    parser = argparse.ArgumentParser(description="Build a styled .pptx briefing deck from a JSON summary.")
    parser.add_argument("--input", type=Path, required=True, help="Path to the input JSON file")
    parser.add_argument("--output", type=Path, default=Path("briefing.pptx"), help="Output .pptx path")
    parser.add_argument(
        "--color",
        type=parse_color,
        default=None,
        help="Main color as hex code, e.g. #2E86AB (overrides the JSON's 'color' field)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    presentation = build_deck(data, base_dir=args.input.parent, color_override=args.color)
    presentation.save(args.output)
    print(f"Deck saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
