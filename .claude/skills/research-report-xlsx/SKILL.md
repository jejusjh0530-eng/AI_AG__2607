---
name: research-report-xlsx
description: Researches a given topic via web search, OR analyzes a file the user references, and produces a styled multi-sheet Excel (.xlsx) report — auto-numbered ID column, bold title, italic quote columns, and growth-rate/comparison charts (Line or Bar, auto-selected) generated automatically from any numeric columns, all formatted in Malgun Gothic with a configurable main color. Use this skill whenever the user gives a topic and wants the findings delivered as an Excel/spreadsheet file rather than a Word doc or chat text (e.g. "이 주제로 조사해서 엑셀로 정리해줘", "~에 대해 리서치해서 xlsx로 만들어줘", "put this market research into a spreadsheet with charts"). ALSO use it whenever the user references an existing file — a data file (xlsx/csv) or a document (pdf/docx/txt/pptx) — and wants it reorganized, summarized, or turned into a new styled Excel file (e.g. "이 파일 분석해서 엑셀로 정리해줘", "clean up this CSV and add growth charts", "summarize this PDF into a spreadsheet with a comparison table"). Trigger even if the user doesn't say "skill" or name the .xlsx format explicitly, as long as they want research or file content delivered as an editable, chart-ready spreadsheet rather than a docx report or plain markdown summary.
---

# Research Report to XLSX

## What this skill does

Given a topic, or a file the user points at, this skill gathers the
relevant content, organizes it into one or more spreadsheet-shaped tables,
and renders the result as a styled `.xlsx` workbook using the bundled
`scripts/build_spreadsheet.py` generator (built on `openpyxl`).

The generator is data-driven, like `research-report-docx`'s `build_report.py`:
you hand it a JSON description of the workbook's sheets, and it takes care
of consistent styling and the "smart" spreadsheet behaviors automatically:

- **ID column** — every sheet gets a sequential `ID` column in column A
  (skipped if the sheet's data already starts with an identifier column
  such as ID/No/번호).
- **Title/header styling** — bold title (first sheet only) and bold white
  header row on the main color.
- **Quote columns** — any column whose header is `quote`/`quotation`/
  `인용구`/`인용문` is rendered in italic.
- **Body text** — 10pt for all normal data cells.
- **Auto charts** — any column with real numeric data (growth rate,
  YoY change, price/量 comparisons, etc. — percentage strings like
  `"12.5%"` are parsed automatically) gets its own chart: `LineChart` if
  the row categories look like a time series (years/months/quarters),
  `BarChart` otherwise. No chart is created for columns without enough
  real numbers, so placeholder/text-only tables stay chart-free.

Because charting is automatic, you don't need to decide chart types
yourself — just make sure any numeric comparison you want visualized
lives in its own column with a clear header, and the generator handles
the rest.

## Which mode applies

Figure out which of the two triggers applies before starting:

1. **Topic research mode** — the user gave a topic/subject and wants it
   researched and delivered as a spreadsheet.
2. **File analysis mode** — the user referenced a specific existing file
   and wants its content turned into a (new) styled spreadsheet.

These aren't mutually exclusive — a user can reference a file *and* ask
for supplementary web research. Use judgment; the JSON-building step is
the same either way, only where the content comes from differs.

## Workflow

### 1. Clarify scope if needed

If the topic is vague, or it's unclear which file the user means, or the
desired sheet breakdown isn't obvious, ask a brief clarifying question
before doing the heavier work. Don't over-ask for a simple, well-scoped
request.

### 2. Gather the content

**Topic research mode:** Use `WebSearch` (and `WebFetch` for promising
sources) to gather current, credible information. Prefer primary sources
and recent material. Actively look for numbers that belong in their own
column (growth rates, YoY/QoQ changes, price or market-share comparisons
across years/regions/brands/products) — these are what unlock the
auto-chart feature, so don't bury them inside prose. Keep the source URLs
you actually used for a "Sources" sheet.

**File analysis mode:** Read the referenced file first.
- **Structured data files** (`.xlsx`, `.csv`): read the existing
  headers/rows directly (e.g. with `openpyxl` or Python's `csv` module)
  so the data is carried over faithfully — this mode is about
  re-presenting the data with the ID column, styling, and auto-charts
  applied, not re-deriving it. Preserve the original column names and
  values; don't invent numbers.
- **Unstructured documents** (`.pdf`, `.docx`, `.txt`, `.pptx`, etc.):
  read/extract the text content, then pull out the concrete figures,
  comparisons, and notable quotes the same way you would for web
  research. Cite the source filename (and page/section if relevant) in
  a "Sources" sheet instead of URLs.

If the user gave both a file and a topic, combine: use the file's data as
the primary source and web research to fill gaps or add context.

### 3. Structure the findings into JSON

Write a JSON file (e.g. to a scratch/temp location) matching this schema:

```json
{
  "title": "Report title",
  "subtitle": "One-line description or date range",
  "color": "#1F4E79",
  "sheets": [
    {
      "name": "Overview",
      "headers": ["Item", "Note"],
      "rows": [["Market size", "..."], ["Key player", "..."]]
    },
    {
      "name": "Growth Data",
      "headers": ["Year", "Revenue", "Growth Rate"],
      "rows": [["2023", 120000, "-"], ["2024", 138000, "15.0%"], ["2025", 151800, "10.0%"]]
    },
    {
      "name": "Sources",
      "headers": ["Source", "URL"],
      "rows": [["Site name", "https://..."]]
    }
  ]
}
```

Guidelines:

- Each sheet is `{"name", "headers", "rows"}` — `rows` is a list of lists
  matching `headers` in order. Numbers can be plain numbers or percentage
  strings (`"12.5%"`); text stays text.
- Adapt the number and names of sheets to the content. The
  Overview/Data/Sources shape above is a starting point, not a fixed
  template — a simple request might only need one sheet; a rich topic
  might need several data sheets.
- Put any comparison/growth numbers you want charted in their own numeric
  column, with a category column (year, region, brand, product, ...) to
  its left — that's what the generator uses for the chart's axis labels.
  If a column is descriptive/non-numeric (like a "Growth Rate" column
  that's currently just a placeholder `-` in every row), the generator
  correctly skips charting it rather than erroring.
- If a sheet has a natural quote/testimonial column, name its header
  `Quote`, `Quotation`, `인용구`, or `인용문` so it renders in italic.
- If the user requested a specific main color, put its hex code in
  `"color"`; otherwise the generator falls back to a sensible default
  navy.

### 4. Generate the workbook

Run:

```bash
python "<skill-dir>/scripts/build_spreadsheet.py" --input findings.json --output "<topic>.xlsx"
```

Pass `--color "#RRGGBB"` instead of (or to override) the JSON's `"color"`
field if the user specifies a color at generation time. See
`scripts/build_spreadsheet.py` for the full option list.

### 5. Deliver the file

Save the output where the user's other generated files live (or ask if
unclear), and point them to it. Briefly summarize what each sheet covers,
which columns got auto-charted (and why others didn't, if that's not
obvious), and which sources were used — so the user can sanity-check the
content before relying on it.

## Why this shape

Excel's real value over Word here is that a table is functional data, not
just formatted text — so the generator is schema-driven (JSON in, xlsx
out) the same way `build_report.py` is for docx, but the schema is
table-shaped instead of prose-shaped, and the styling work goes into
things spreadsheets specifically need: a stable ID column, readable body
size, italics for quoted material, and charts that appear only when the
data actually supports them.

## Notes

- If `openpyxl` is not installed in the environment, install it first
  (`pip install openpyxl`).
- Sheet names are automatically sanitized and de-duplicated (Excel
  forbids `: \ / ? * [ ]` and caps names at 31 characters), so don't
  worry about picking perfectly Excel-safe sheet names in the JSON.
- If the user asks for a single-sheet spreadsheet instead of several, just
  put one entry in `"sheets"` — nothing else about the schema changes.
- If web search isn't available in the current environment (topic mode)
  or the referenced file can't be read (file mode), say so explicitly and
  offer the best available alternative (existing knowledge, or asking the
  user to paste the content) rather than fabricating data.
