---
name: news-scrap-briefing
description: Uses Playwright MCP to scrape a small set of news articles the user points at (by URL, site, or keyword/topic) — capturing a screenshot of each as evidence — then analyzes the scraped content and produces two matched deliverables from it: a styled Word (.docx) report (overview, per-article summary with embedded screenshot, sources list) via python-docx, and a styled PowerPoint (.pptx) deck (title slide, one slide per article with screenshot and key points, closing synthesis slide) via python-pptx. Use this skill whenever the user wants news/articles scraped and turned into both a written report and presentation slides (e.g. "이 기사들 스크랩해서 보고서랑 발표자료 만들어줘", "네이버 뉴스에서 이 주제 관련 기사 스크랩해서 워드랑 PPT로 정리해줘", "scrape these articles and build a report and a deck from them"). Trigger even if the user only asks for one of the two output formats, or doesn't name python-docx/python-pptx/Playwright explicitly, as long as the core ask is "scrape article(s), then turn the findings into a document and/or slides" rather than just reading or summarizing in chat.
---

# News Scrap Briefing

## What this skill does

Given articles the user points at — direct URLs, a site + topic/keyword, or
"the ones we just looked at" from earlier in the conversation — this skill:

1. Scrapes each article with **Playwright MCP** (`mcp__playwright__*` tools),
   capturing a full-page screenshot of each as visual evidence.
2. Analyzes the scraped content (headline, source, body text) to produce a
   short summary and a few key points per article, plus an overall synthesis
   across all of them.
3. Renders that analysis twice, from **one shared JSON file**, into:
   - a Word report via `scripts/build_docx_report.py` (`python-docx`)
   - a PowerPoint deck via `scripts/build_pptx_deck.py` (`python-pptx`)

Both generators are data-driven, like the sibling `research-report-docx`
skill's `build_report.py`: you hand them a JSON description of the content
and they take care of consistent styling (Malgun Gothic, sized headings, a
configurable main color) so the work goes into the scraping and the
analysis, not into Word/PowerPoint formatting.

## Workflow

### 1. Clarify scope if needed

Figure out the article set before scraping:

- **Source restriction**: only scrape articles from **Naver News**
  (`news.naver.com`). If the user points at a URL or site outside Naver
  News, or asks to search/browse a different outlet, tell them this skill
  only sources articles from Naver News and ask for a Naver News URL,
  section, or keyword instead — don't silently scrape the other site.
- **Direct URL(s)** — scrape exactly those.
- **Site + topic/keyword** (e.g. "네이버 뉴스 IT/과학 탭에서 AI 관련 기사") —
  navigate to the listing, find articles matching the topic, and pick a
  reasonable number.
- **Referring to articles already open/found earlier in this conversation**
  — reuse those instead of re-searching.

If the user gave no count, default to **3–5 articles** — enough for a real
comparison/synthesis without turning a quick briefing into a research
project. If the request is genuinely ambiguous (no URLs, no site, no topic
at all), ask a brief clarifying question before scraping. Don't over-ask
when a URL or a clear topic+site is already in hand.

### 2. Scrape each article with Playwright MCP

For every article:

1. `mcp__playwright__browser_navigate` to the article URL.
2. `mcp__playwright__browser_snapshot` (or `browser_find`) to read the
   headline, byline/source, and body text for analysis, and to get a
   `ref` for the article's main content container (the element that wraps
   the headline + body — not the whole `<body>`).
3. `mcp__playwright__browser_take_screenshot` **scoped to that content
   element** (pass its ref as `target`/`element`) rather than
   `fullPage: true`. A real article page includes related-article rails,
   comment sections, and footers below the fold — a literal full-page
   capture of all of that produces an extremely tall, thin image (some
   news sites run 5,000–10,000+ px tall) that looks bad embedded and
   provides no extra evidence value over the article itself. If you can't
   confidently identify a single content element, fall back to
   `fullPage: true`, but expect a much taller image — the generators cap
   how large it renders in the document, but can't make a 1:10 aspect
   ratio look good.

Save every screenshot under `output/playwright/` (per this project's
Playwright-output convention), inside a subfolder named for this briefing,
e.g. `output/playwright/news-scrap-briefing/<topic-or-date>/article-1.png`,
`article-2.png`, etc. — one screenshot per article, numbered in the order
you'll present them.

If a listing page is involved (site + topic mode), you'll also end up on
the listing/search page first — only the individual article pages need
full-page screenshots; the listing page itself doesn't.

### 3. Structure the findings into one shared JSON file

Write a JSON file (e.g. to a scratch/temp location) matching this schema —
it drives **both** generators:

```json
{
  "title": "Briefing topic or headline theme",
  "subtitle": "One-line scope note, e.g. a date or site name",
  "color": "#1F4E79",
  "sections": [
    {
      "heading": "Overview",
      "paragraphs": ["1-3 sentence synthesis across all scraped articles — the shared theme, notable disagreement, or trend."]
    },
    {
      "heading": "Article headline, verbatim",
      "source": "Outlet name · https://article-url",
      "paragraphs": ["1-2 sentence summary of this article."],
      "bullets": ["Key point 1", "Key point 2"],
      "image": "output/playwright/news-scrap-briefing/<topic>/article-1.png"
    },
    {
      "heading": "Key Takeaways",
      "bullets": ["Synthesis point 1", "Synthesis point 2"],
      "include_in": ["pptx"]
    },
    {
      "heading": "Sources",
      "bullets": ["Article headline — https://article-url", "..."],
      "include_in": ["docx"]
    }
  ]
}
```

Guidelines:

- One section per article (heading = the article's real headline, `source`
  = outlet + URL, `image` = that article's screenshot path from step 2).
  Put the Overview section first, one section per article in presentation
  order, then any closing sections last.
- `include_in: ["pptx"]` / `["docx"]` restricts a section to just one
  output — use this for a "Key Takeaways" synthesis slide that would be
  redundant in the written report's Overview, or a "Sources" list of raw
  URLs that's more useful as a document appendix than as a slide. Omit
  `include_in` entirely for sections (like the Overview and each article)
  that belong in both.
- If the user requested a specific main color, put its hex code in
  `"color"`; otherwise the generator falls back to a sensible default navy.
- Keep bullets genuinely short (they render as slide bullets, not just
  document bullets) — a phrase or a single sentence, not a paragraph.

### 4. Generate both documents

```bash
python "<skill-dir>/scripts/build_docx_report.py" --input briefing.json --output "<topic> briefing.docx"
python "<skill-dir>/scripts/build_pptx_deck.py" --input briefing.json --output "<topic> briefing.pptx"
```

Pass `--color "#RRGGBB"` to either command to override the JSON's `"color"`
field if the user specifies a color at generation time. See each script's
module docstring for the full schema reference.

### 5. Deliver both files

Save both outputs where the user's other generated documents live (or ask
if unclear), and send them to the user. Briefly summarize what was
scraped, what each article's key point was, and which sections went into
only the report or only the deck (if any) — so the user can sanity-check
before relying on either.

## Why this shape

One JSON, two renderers: the report and the deck are two views of the same
analysis, not two separate write-ups, so keeping them schema-compatible
(with `include_in` as the only per-output escape hatch) means the content
stays in sync automatically — edit the JSON once to fix a summary, and
both outputs pick it up on the next generation run.

## Notes

- If `python-docx` or `python-pptx` is not installed, install them first
  (`pip install python-docx python-pptx`).
- If Playwright MCP tools aren't available in the current environment, say
  so explicitly rather than substituting a different scraping method
  silently — the user asked for Playwright specifically.
- If an article's page blocks full-page screenshots (paywall, heavy lazy
  loading, etc.), take the best screenshot you can get and note the
  limitation in that article's summary rather than fabricating content.
- A single-URL request still goes through the same schema — just one
  article section between Overview and any closing section.
- Both generators automatically downscale, re-compress, and fit
  screenshots within a bounded box before embedding them (via
  `scripts/image_utils.py`) — you don't need to resize screenshots
  yourself before referencing them in the JSON's `"image"` field. This is
  a safety net for file size and layout, not a substitute for scoping the
  screenshot sensibly in step 2 — an element-scoped capture will always
  look better embedded than a full-page one that got shrunk to fit.
