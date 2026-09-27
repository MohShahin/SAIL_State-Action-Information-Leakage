---
description: Phase 4 — the Detectors page, five real categories with plain-language summaries linking into existing proof content, ending in the live "suggest a detector" issue
---

# Website rebuild, Phase 4 — Detectors

**Do not write new explanations of the five categories from scratch.** The correct plain-language
text already exists — in `SAIL_PACKAGE_README.md`'s category table and in the actual
`explanation`/docstring text inside `sail/detectors/*.py`. Reuse it. The correct deep math already
exists in `FORMAL_ANALYSIS.md` and `proof.html`. Link to it. This page's job is presentation and
navigation, not new content.

## Step 1 — Read before writing

1. `SAIL_PACKAGE_README.md`'s five-category table (name, what it catches, proven by).
2. `sail/detectors/construction.py`, `reconstruction.py`, `temporal_overlap.py`,
   `timing_violation.py`, `persistence.py` — the real `LeakageFinding` explanation text each
   produces, and each module's docstring.
3. `FORMAL_ANALYSIS.md`'s section headers and `proof.html`'s anchor IDs — identify the exact
   section/anchor for each of the five categories (Theorem 1 → construction 1a, Proposition 3 →
   construction 1b, Theorem 2 → reconstruction, Proposition 1 → temporal overlap, the H3/timing
   material → timing violation, the Experiment 8/Variant F material in `evidence.html` →
   persistence dominance). Report these five exact mappings before building anything — if any
   category doesn't have a clean, obvious deep-link target, say so rather than guessing one.

## Step 2 — Build `/detectors/`, in the dark theme from the start

Five cards, one per category, each:
1. Real category name (from the detector code, e.g. `construction_leakage_1a`).
2. A one-line plain-language summary, reused from `SAIL_PACKAGE_README.md`'s table — not
   paraphrased into new wording.
3. An expandable section with the fuller plain-language explanation (the actual `explanation`
   template text the detector produces, generalized from its worked example).
4. A "See the math" link to the exact section/anchor identified in Step 1 — not a generic link to
   the top of `proof.html`.

End of page: a "Suggest a new detector" button linking directly to
`https://github.com/MohShahin/SAIL_State-Action-Information-Leakage/issues/new?template=suggest-a-detector.yml`
(the real, live template from Phase 0 — verify this exact URL pattern is correct for issue forms,
don't assume the query-string format).

## Step 3 — Wire it into the rest of the site

1. Add "Detectors" to the shared nav in `base.njk` now that the page exists — per Phase 3's own
   note that this should happen once the page is real, not before.
2. Update the homepage's "What it checks" section (Phase 1) to link its five teaser cards to
   `/detectors/` instead of `/package/` — `/package/` was an honest interim link before this page
   existed; now that it does, point there instead.

## Step 4 — Verify

1. Full clean build, full link-crawl.
2. Confirm each of the five "See the math" links actually lands at its intended section/anchor —
   check the resulting URL and the content it scrolls to, not just that the link doesn't 404.
3. Confirm the "Suggest a new detector" link opens the real, correct issue template (verify against
   the live GitHub URL, same as Phase 0's verification standard).
4. Screenshots at desktop and mobile widths, using genuine viewport-width verification (per Phase
   3's own corrected method — measure `window.innerWidth` directly, don't trust a headless
   browser's `--window-size` flag at face value).

## Step 5 — Update the status doc

Update `docs/WEBSITE_REBUILD_STATUS.md`: mark Detectors done, remove "Detectors nav entry pending"
from the tracked items list (only "Understanding Leakage nav entry pending" and "old-page content
reskinning" remain open after this).

## Reporting

Report the five category-to-anchor mappings from Step 1, confirm each deep link was verified to
land correctly (not assumed), and confirm the suggest-a-detector link was checked against the live
GitHub page.
