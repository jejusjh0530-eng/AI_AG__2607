"""General-purpose .xlsx spreadsheet generator using openpyxl.

Usage:
    python create_spreadsheet.py [--output PATH] [--title TEXT] [--subtitle TEXT] [--color HEXCODE]

Example:
    python create_spreadsheet.py --title "Project Report" --color "#2E86AB" --output report.xlsx

Styling defaults (mirrors scripts/create_document.py):
    - Font: 맑은 고딕 (Malgun Gothic)
    - Title: 24pt bold, main color
    - Table header row: 12pt bold white text on main color fill
    - Body cells: 11pt
    - Main color customizable via --color
"""

import argparse
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

FONT_NAME = "맑은 고딕"
TITLE_SIZE = 24
SUBTITLE_SIZE = 11
HEADER_SIZE = 12
BODY_SIZE = 11
DEFAULT_COLOR = "1F4E79"

HEX_LENGTH = 6


def parse_color(value: str) -> str:
    hex_value = value.lstrip("#")
    if len(hex_value) != HEX_LENGTH or any(
        c not in "0123456789ABCDEFabcdef" for c in hex_value
    ):
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a valid hex color (expected format: RRGGBB or #RRGGBB)"
        )
    return hex_value.upper()


def build_workbook(title_text: str, subtitle_text: str, main_color: str) -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    headers = ["Item", "Description", "Value"]
    sample_rows = [
        ("Item 1", "Description of item 1", "-"),
        ("Item 2", "Description of item 2", "-"),
        ("Item 3", "Description of item 3", "-"),
    ]
    last_col = len(headers)
    last_col_letter = get_column_letter(last_col)

    ws.merge_cells(f"A1:{last_col_letter}1")
    title_cell = ws["A1"]
    title_cell.value = title_text
    title_cell.font = Font(name=FONT_NAME, size=TITLE_SIZE, bold=True, color=main_color)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    ws.merge_cells(f"A2:{last_col_letter}2")
    subtitle_cell = ws["A2"]
    subtitle_cell.value = subtitle_text
    subtitle_cell.font = Font(name=FONT_NAME, size=SUBTITLE_SIZE, italic=True, color="595959")
    subtitle_cell.alignment = Alignment(horizontal="center", vertical="center")

    header_row = 4
    header_fill = PatternFill(start_color=main_color, end_color=main_color, fill_type="solid")
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_index, value=header)
        cell.font = Font(name=FONT_NAME, size=HEADER_SIZE, bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_offset, row_data in enumerate(sample_rows, start=1):
        row_index = header_row + row_offset
        for col_index, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_index, column=col_index, value=value)
            cell.font = Font(name=FONT_NAME, size=BODY_SIZE)
            cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

    for col_index in range(1, last_col + 1):
        column_letter = get_column_letter(col_index)
        max_length = max(
            len(str(ws.cell(row=r, column=col_index).value or ""))
            for r in range(header_row, header_row + len(sample_rows) + 1)
        )
        ws.column_dimensions[column_letter].width = max(12, max_length + 4)

    return wb


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a general-purpose .xlsx spreadsheet.")
    parser.add_argument("--output", type=Path, default=Path("output.xlsx"), help="Output file path")
    parser.add_argument("--title", default="Spreadsheet Title", help="Spreadsheet title text")
    parser.add_argument(
        "--subtitle",
        default="Subtitle or short description goes here.",
        help="Spreadsheet subtitle text",
    )
    parser.add_argument(
        "--color",
        type=parse_color,
        default=parse_color(DEFAULT_COLOR),
        help="Main color as hex code, e.g. #2E86AB (default: #1F4E79)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    workbook = build_workbook(args.title, args.subtitle, args.color)
    workbook.save(args.output)
    print(f"Spreadsheet saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
