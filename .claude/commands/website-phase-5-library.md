---
description: Phase 5 — Papers and Datasets/Models libraries as a real card-grid UI (Papers-With-Code/Hugging-Face-Hub style), with Giscus comments and the live submission issue links
---

# Website rebuild, Phase 5 — Libraries

**Do not fabricate any paper, dataset, or model entry.** The Papers library reuses the site's
existing five real citations — do not add invented ones to make the grid look fuller. The
Datasets & Models library currently has zero real entries; ship it with an honest, well-designed
empty state, not fabricated placeholder items pretending to be real.

## Step 1 — Read before writing

1. `src/papers.html`'s existing content (the five real citations) and its existing tag-filter JS —
   reuse both, don't rewrite the filtering logic from scratch if it already works.
2. `src/datasets-and-models.html` (Phase 1's placeholder) for its current honest framing.
3. `docs/giscus_snippet.html` for the comment embed.

## Step 2 — Card design (the actual visual spec)

One card per entry, in a responsive grid (reuse Phase 1/2's dark theme). Each card:
1. Title.
2. One-line description (reused from the existing citation's `relevance` text where it exists —
   don't write new summaries for the five real papers).
3. Small tag/metadata badges (e.g. venue and year for papers; "Dataset" / "Model" for the other
   library) — badges, not paragraphs, matching how Papers With Code or the Hugging Face Hub present
   this.
4. Click-through to the full citation/link.

This is a well-established, low-risk pattern — no need to invent a new layout concept.

## Step 3 — Build the Papers library

Re-skin `papers.html` into the card grid using the five existing real citations exactly as
currently written — this is a presentation change, not a content change. Keep the existing
tag-filter behavior, restyled to match.

## Step 4 — Build the Datasets & Models library

Same card-grid system, currently empty. Design a genuine, polished empty state — not a broken-
looking blank page and not fabricated example entries — something like a centered message ("This
library is just getting started — help us grow it") with the real "Submit a dataset or model" issue
link prominent, not buried.

## Step 5 — Embed Giscus on both pages

Embed the exact snippet from `docs/giscus_snippet.html` on both library pages (`data-mapping:
pathname` means each page automatically gets its own separate comment thread — confirm this works
as expected rather than assuming, since a wrong mapping mode could accidentally merge both pages'
comments into one thread).

## Step 6 — Wire in the real submission links

Confirm both "Suggest a paper" and "Submit a dataset or model" buttons point to the exact live
issue-template URLs from Phase 0, matching the same URL pattern already used for
"suggest-a-detector" in Phase 4.

## Step 7 — Verify

1. Full clean build, link-crawl.
2. Confirm the Giscus widget actually loads and renders on both pages (a real browser check, not
   just confirming the script tag is present in the HTML — Giscus loads via an iframe at runtime).
3. Screenshots at desktop and mobile, using the corrected viewport-verification method from Phase 3
   (measure `innerWidth`/`scrollWidth` directly, not headless Chrome's `--window-size` flag).
4. Confirm the tag filter (reused from the old `papers.html`) still works correctly after the
   re-skin.

## Reporting

Report both pages' final structure, confirm Giscus actually renders (with evidence, not an
assumption), and confirm the empty-state Datasets & Models page reads as intentional and inviting
rather than broken or unfinished.
