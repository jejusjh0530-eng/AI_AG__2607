---
name: research-report-docx
description: Researches a given topic using web search and produces a styled Word (.docx) report — title page, organized sections with body text, bullet points, a data table, and a sources list, all formatted in Malgun Gothic with a 40pt title, 20pt body text, and a configurable main color. Use this skill whenever the user gives a topic and asks for a report, briefing, summary, or write-up to be delivered as a Word/docx file (e.g. "이 주제로 조사해서 워드 파일로 정리해줘", "~에 대해 리서치해서 docx로 만들어줘", "market research report as a .docx", "write up a briefing document on X"). Trigger even if the user doesn't say "skill" or name the file format explicitly, as long as they want research findings delivered as an editable Word document rather than plain chat text or a markdown file.
---

# Research Report to DOCX

## What this skill does

Given a topic, this skill researches it on the web, organizes the findings
into a clear report structure, and renders the result as a styled `.docx`
file using the bundled `scripts/build_report.py` generator (built on
`python-docx`).

The generator is data-driven: you hand it a JSON summary of the report's
content, and it takes care of consistent styling — font, sizes, color,
page numbers — so you can focus on the research and the writing, not on
Word formatting.

## Workflow

1. **Clarify scope if needed.** If the topic is vague, ambiguous, or could
   mean several different things, ask the user a brief clarifying question
   before researching (e.g. which industry, which time range, which
   country/market). Don't over-ask for a simple, well-scoped topic.

2. **Research the topic.** Use `WebSearch` (and `WebFetch` for promising
   sources) to gather current, credible information. Prefer primary
   sources and recent material. Collect enough detail to support several
   distinct sections — an overview, a few concrete points or findings, and
   any figures worth putting in a table. Keep a list of the source URLs
   you actually used; they go in a "Sources" section at the end of the
   report so the reader can verify the content.

3. **Structure the findings into JSON.** Write a JSON file (e.g. to a
   scratch/temp location) matching this schema:

   ```json
   {
     "title": "Report title",
     "subtitle": "One-line description or date range",
     "color": "#1F4E79",
     "sections": [
       {"heading": "1. Overview", "paragraphs": ["..."]},
       {"heading": "2. Key Findings", "bullets": ["...", "..."]},
       {"heading": "3. Data", "table": {"headers": ["...", "..."], "rows": [["...", "..."]]}},
       {"heading": "4. Sources", "bullets": ["https://...", "https://..."]}
     ]
   }
   ```

   Each section may combine `paragraphs`, `bullets`, and `table` freely —
   include only what fits the content. Adapt the number and names of
   sections to the topic; the four-section shape above is a starting
   point, not a fixed template. If the user requested a specific main
   color, put its hex code in `"color"`; otherwise the generator falls
   back to a sensible default navy.

4. **Generate the document.** Run:

   ```bash
   python "<skill-dir>/scripts/build_report.py" --input findings.json --output "<topic>.docx"
   ```

   Pass `--color "#RRGGBB"` instead of (or to override) the JSON's
   `"color"` field if the user specifies a color at generation time. See
   `scripts/build_report.py` for the full option list — it applies Malgun
   Gothic throughout, a 40pt title, 26pt section headings, 20pt body/bullet
   text, 16pt table text, and shades the table header row with the main
   color.

5. **Deliver the file.** Save the output where the user's other generated
   documents live (or ask if unclear), and point them to it. Briefly
   summarize what the report covers and which sources were used, so the
   user can sanity-check it before relying on the content.

## Why this shape

Word documents don't support CSS-style pixel sizing — `python-docx` works
in points, so sizes here are specified in pt, matching normal Word
conventions. Keeping the generator schema-driven (JSON in, docx out) means
the same styling logic works for any topic without editing the script per
report — only the research changes.

## Notes

- If `python-docx` is not installed in the environment, install it first
  (`pip install python-docx`).
- If the user asks for a different structure (e.g. no table, or an
  executive-summary-only report), just shape the JSON's `sections` array
  accordingly — the script does not require any particular section count
  or names.
- If web search isn't available in the current environment, say so
  explicitly and offer to write the report from existing knowledge
  instead, noting that it may not reflect the latest information.
