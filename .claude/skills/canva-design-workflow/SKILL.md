---
name: canva-design-workflow
description: Turns a single topic into a finished Canva design through a concept-approval-first workflow — propose at least three design concepts, wait for the user to approve one, confirm what deliverable (poster, social post, presentation, card, etc.) they want, generate and save it as a draft in Canva, share a review link, and only on final approval export it as PNG and file it into a "canva/<topic>" folder in the user's Canva account. Use this whenever the user wants a Canva design made from an idea or topic (디자인 만들어줘, 포스터/카드뉴스/발표자료 제작, Canva 시안 만들어줘), especially when they want to see concept directions before anything is actually generated, rather than getting a design immediately.
---

# Canva Design Workflow

Turn a topic into an approved, finished Canva design without ever generating something the user didn't ask for. The workflow has two hard gates — concept approval, then final-save approval — and nothing is created in the user's Canva account until the user has passed both.

## Why this workflow matters

Canva's `generate-design` tool immediately produces real design candidates — every call has latency and account-visible side effects once converted. Jumping straight from a topic to a generated design risks producing something off-target that the user then has to explain and redo. This workflow front-loads the cheap, reversible part (textual concept ideas) before the expensive, stateful part (actual generation), so the user is only ever approving decisions, not correcting mistakes.

## Step 1: Capture the topic and scope

Before proposing anything, make sure you have:
- **The topic** — what the design is about/for.
- Anything else already implied by the request (audience, tone, brand, must-include text/images). Don't ask for details the user already gave.

If the topic itself is too vague to differentiate concepts (e.g. just "마케팅"), ask one clarifying question. Otherwise proceed — concepts don't require the deliverable type yet, so don't ask for that here.

## Step 2: Propose at least three design concepts — text only, no tool calls

Write at least three distinct design concept pitches based on the topic. Each concept should describe a direction in a few lines: visual mood/style, color direction, layout idea, and the angle or message it leans into. Make the three genuinely different from each other (e.g. minimal/corporate vs. bold/playful vs. photo-led/editorial) so the user is picking a real direction, not a cosmetic variant.

**Do not call `generate-design` or any other Canva creation tool at this step.** Concepts are a plain-text pitch for the user to react to — calling a Canva tool here would create real designs before the user has approved a direction, which is exactly what this workflow exists to prevent.

Present the concepts clearly labeled (Concept A/B/C…) and ask the user to pick one, or to request adjustments/new directions.

## Step 3: Gate on concept approval

Do not proceed past this point until the user has explicitly picked one concept. If they ask for changes, revise and re-present; if they reject all three, propose a fresh set rather than reusing the rejected ones. Treat silence or an ambiguous reply as "not yet approved" — ask again rather than assuming.

## Step 4: Confirm the deliverable type

Once a concept is approved, confirm what the user actually wants produced — this maps to `generate-design`'s `design_type` (e.g. `poster`, `instagram_post`, `presentation`, `card`, `flyer`, `logo`, `doc`, etc.). If the approved concept already implies an obvious format, propose it and let the user confirm rather than making them choose from the full enum unprompted. If it's genuinely open, ask directly.

Also confirm scope details `generate-design` needs and the concept doesn't already answer — e.g. presentation length (short/balanced/comprehensive), or whether to use a brand kit (`list-brand-kits`, only if the user wants an on-brand result).

## Step 5: Generate the design and save it as a draft

1. Call `generate-design` with `design_type` from Step 4 and a `query` that carries the full approved concept description from Step 2 plus the topic — the tool has no memory of the conversation, so include everything relevant every time.
2. If candidates aren't returned synchronously, poll with `get-design-candidates` using the returned `job_id`.
3. Show the resulting candidate thumbnail(s) to the user. If there are multiple, let them pick one — don't silently default to the first.
4. Convert the chosen candidate into a real, saved design with `create-design-from-candidate` (`job_id` + `candidate_id`). This is the "draft save" — the design now exists in the user's Canva account.

## Step 6: Share the draft for review

Call `get-design` on the new `design_id` to get its edit/view URL, and send that link to the user so they can review it directly in Canva. If they want edits before finalizing, use `start-editing-transaction` → `perform-editing-operations` → `commit-editing-transaction` (always get explicit user approval before the commit call, per that tool's own requirement), then re-share the updated thumbnail/link and ask again.

Do not treat this step as final save — it's a draft the user is reviewing. Nothing gets exported or filed away until they say so.

## Step 7: On final approval — export as PNG and file it away

Only after the user explicitly approves saving/finalizing:

1. Call `get-export-formats` on the `design_id` to confirm PNG is supported (and for which pages). If PNG genuinely isn't supported for this deliverable type, tell the user plainly rather than silently substituting another format — don't guess.
2. Call `export-design` with `format.type: "png"` and share the resulting download URL(s) with the user.
3. File the design into `canva/<topic>` inside the user's Canva account:
   - Find or create the top-level `canva` folder: `search-folders` (query `"canva"`, ownership `owned`); if none matches, `create-folder` with `parent_folder_id: "root"`.
   - Find or create the `<topic>` subfolder inside it: `list-folder-items` on the `canva` folder filtered to `item_types: ["folder"]` to check for an existing match by name (sanitize the topic string into a plain folder-safe name first); if none matches, `create-folder` with that `canva` folder as `parent_folder_id`.
   - `move-item-to-folder` the design into that subfolder.
4. Confirm to the user with: the Canva folder location, the design's edit/view link, and the PNG download link(s).

## Handling edge cases

- **User rejects all proposed concepts**: propose a new set of at least three — never reuse ones already rejected, and ask what specifically missed the mark so the next set actually differs.
- **User wants changes after the draft is saved (Step 6)**: use the editing-transaction tools, get their approval before committing, and re-share before asking for final approval again — don't re-run generation from scratch unless they ask for a different concept entirely.
- **PNG unsupported for the chosen deliverable**: surface this to the user and ask how they'd like to proceed (different export format, or a different deliverable type) — don't silently export something other than PNG.
- **Topic reused across sessions**: if a `canva/<topic>` folder already exists, reuse it — don't create duplicate folders with slightly different names for the same topic.
- **Multi-page design**: exporting produces one PNG per page — tell the user how many files they're getting, not just one link.
