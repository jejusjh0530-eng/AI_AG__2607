---
name: tistory-blog-writer
description: Given a topic, researches it (WebSearch or claude-in-chrome browsing) and writes a blog-style post directly into the user's Tistory blog via the claude-in-chrome browser extension — opens tistory.com, waits for the user to log in themselves if needed, fills in the title and body in the post editor, saves it as a temporary draft (임시저장), then asks the user to review and approve before ever publishing. Use this whenever the user asks to write, post, or upload a blog article to Tistory about a topic (e.g. "이 주제로 티스토리에 글 써줘", "블로그에 포스팅해줘", "~조사해서 티스토리에 올려줘", "write a Tistory post about X"), even if they don't explicitly mention claude-in-chrome or the skill name. Always confirm the topic and, once a draft is approved, whether to publish it as 공개(public) or 비공개(private) — never guess or skip this confirmation.
---

# Tistory Blog Writer

Turn a topic into a real draft sitting in the user's Tistory blog, using the claude-in-chrome browser extension to do the actual typing and clicking — not just a document handed back in chat.

## Why this shape

Writing a Tistory post has two halves that are easy to get wrong in opposite directions: the research/writing half (get it wrong and the post is inaccurate or generic) and the publishing half (get it wrong and something goes public that the user never approved, or credentials get typed into a login form by the agent). This skill treats those as separate phases with a hard checkpoint between them: nothing becomes visible to anyone but the user until they've explicitly reviewed the draft and explicitly chosen 공개/비공개.

## Workflow

### 1. Confirm the topic

If the user's topic is vague or could mean several different things (a broad theme, an ambiguous time range like "요즘"), ask a brief clarifying question. For a clear, well-scoped topic, proceed directly — don't over-ask.

### 2. Research the topic

Use `WebSearch`/`WebFetch`, or claude-in-chrome (`navigate` to a search engine, `get_page_text` to read results) if the user specifically wants browser-based research. Gather enough concrete, current material for several distinct points — this is a blog post, not an academic report, so prioritize a few well-explained findings over an exhaustive list. Keep track of the sources actually used; Tistory posts in this workflow end with a short source line, not a formal bibliography.

### 3. Write the post in blog style, not report style

Blog readers skim. Structure the draft as:
- A short, specific title (not a generic label like "AI 소식").
- A one- or two-sentence hook paragraph that states why this matters right now.
- 3-6 numbered or headed sections, each a short paragraph — not walls of text, not a table.
- A brief closing paragraph tying the points together (what to watch next, why it matters).
- A one-line source credit at the end.

Write in the user's language (match the language they asked in). Keep paragraphs conversational — this content is going to a public or semi-public blog, not a corporate deliverable.

### 4. Open Tistory and get to the editor

Load the claude-in-chrome tools if not already loaded (`ToolSearch` with `select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__find,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__browser_batch,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp`), then:

1. `tabs_context_mcp` with `createIfEmpty: true` to get a tab.
2. `navigate` to `https://www.tistory.com`.
3. Check whether the user is already logged in — look for their blog name / "글쓰기" button in the page text or a screenshot, versus a login prompt.
4. **If not logged in: stop and ask the user to log in themselves in the browser window.** Never type a username, password, or complete an OAuth/social login step on the user's behalf — entering credentials is off-limits regardless of whether the user offers them. Wait for the user to confirm they've logged in, then re-check.
5. Once logged in, `find` the "글쓰기" link and click it (this opens a new tab with the post editor, typically `https://<blogname>.tistory.com/manage/newpost`).

### 5. Fill in the title and body

The Tistory editor is a rich-text field: clicking the title placeholder and typing sets the title; clicking into the body area below it and typing fills the body. Use `Return` key presses (via `computer` with `action: "key"`) to create paragraph breaks between sections rather than trying to paste literal `\n` characters.

Batch the click/type/key sequence with `browser_batch` — this is many small actions and doing them one at a time is slow and burns turns. Take a `screenshot` afterward to confirm the title and opening paragraphs landed correctly before moving on; scroll up if the view is showing the tail end of the body.

Skip thumbnail image and category selection unless the user specifically asks for them — leaving them unset is the normal, low-friction default and Tistory doesn't require either to save or publish.

### 6. Save as a temporary draft — do not publish yet

Click "임시저장" (temp save). This is safe to do without asking first: it's a private, reversible draft save, not publishing. Confirm it worked (the button typically shows a saved count, e.g. "임시저장 | 1").

### 7. Get explicit approval before anything becomes visible

Publishing — even to a private/비공개 state — puts a real post into the user's account and is not something to do unprompted. After the temp save, tell the user what was written (title + a one-line summary of the sections) and ask what they want to do next: keep it as a draft only, publish now, or edit it themselves. Use `AskUserQuestion` for this rather than assuming.

### 8. If they want to publish: ask 공개 vs 비공개

This is the one confirmation that must never be skipped or defaulted, per the user's own stated requirement for this workflow. Click "완료" to open the publish dialog, then ask the user directly whether they want 공개(public), 공개(보호)(password-protected), or 비공개(private) — the dialog's radio buttons map directly to this choice, and the save button's label changes to match the selected option (e.g. "비공개 저장", "발행"). Select the option the user chose and click that button.

### 9. Report back

Tell the user the final state of the post (draft only / saved private / published public with URL) and clean up: close any claude-in-chrome tabs this skill opened that the user doesn't need kept open (`tabs_close_mcp`).

## Notes

- If claude-in-chrome tools are deferred, load them in one `ToolSearch` call, not one tool at a time (see step 4).
- If the login wait or an editor interaction seems stuck (element not found, page not responding after 2-3 attempts), stop and describe what happened rather than retrying indefinitely — this mirrors the general browser-automation guidance to avoid rabbit holes.
- If web search / browser research isn't available in the current environment, say so explicitly and offer to write from existing knowledge, noting it may not reflect the latest information.
