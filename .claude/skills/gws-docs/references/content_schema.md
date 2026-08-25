# Content JSON Schema

Input format for `scripts/build_batch_requests.py`.

```json
{
  "heading": "Document Title",
  "sections": [
    {
      "heading": "Section Title",
      "body": "First paragraph.\nSecond paragraph (each line becomes its own paragraph)."
    },
    {
      "heading": "Section With Bullets",
      "bullets": ["Point one", "Point two", "Point three"]
    }
  ]
}
```

- `heading` (top level, optional): rendered as the document's `TITLE` style. If the topic already has a clear title, set it here.
- `sections`: ordered list, rendered top to bottom.
  - `heading` (optional): rendered as `HEADING_1`.
  - `body` (optional): plain text; each `\n`-separated line becomes its own `NORMAL_TEXT` paragraph.
  - `bullets` (optional): list of strings, each rendered as a bulleted `NORMAL_TEXT` paragraph.

A section can mix `body` and `bullets` — body paragraphs are inserted first, then bullets.

## Google Docs API notes (why the script exists)

- `documents.batchUpdate` requests must reference exact character indices into the document body. Every `insertText` shifts all indices after it, so indices must be computed as a running offset, not looked up after the fact.
- The document body always starts at index `1` (index `0` is reserved).
- Applying styles (`updateParagraphStyle`, `createParagraphBullets`) requires the *same* range the text was just inserted into — get this wrong and either the wrong text gets styled or the API rejects the request.
- Because this is exactly the kind of fragile, easy-to-miscalculate operation the Docs API is known for, always generate the request list with the script rather than hand-writing indices.
- Indices are UTF-16 code units. The script uses Python's `len()`, which matches for all BMP text (Korean, English, CJK, etc.) but undercounts by 1 per character outside the BMP (most emoji). Avoid emoji in generated content, or the script's index math will drift.
