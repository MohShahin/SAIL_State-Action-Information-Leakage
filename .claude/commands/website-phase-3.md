---
description: Phase 3 — unify the shared header/nav across every page (dark theme, logo, new IA), explicitly deferring old-page content reskinning to later phases
---

# Website rebuild, Phase 3 — header/nav unification

**Scope for this phase, precisely:** the shared header/nav in `base.njk`, applied consistently
across all 15 existing pages. This phase does NOT reskin the content area of any existing page
(`proof.html`, `mechanisms.html`, `evidence.html`, `visualizer.html`, `reproducibility.html`,
`status.html`, `demo.html`, `showcase.html`) — those keep their current light-theme content for now.
The visible seam between a new dark header and old light content below it is a known, accepted
interim state, not a bug to chase inside this phase — same category of tradeoff as Phase 1's
untouched-nav seam, now resolved at the header level and explicitly tracked for the content level.

## Step 1 — Update `base.njk`

1. Add the logo (`logo-cropped.png`) to the header, matching how Phase 1's homepage placed it.
2. Re-theme the shared header to Phase 1/2's dark `.landing-dark` system.
3. Replace the old flat nav with the new IA, **linking only to pages that actually exist today**:
   Home, About, Papers, Datasets & Models, Privacy. Do not add a "Detectors" or "Understanding
   Leakage" link yet — those pages don't exist until Phases 4 and 6. Adding a nav link to a page
   that doesn't exist would be exactly the kind of broken-link risk this project has been careful
   about everywhere else.

## Step 2 — Verify the header renders correctly on every page

This is the part that actually matters for "flows smoothly" — a full crawl, not a spot check:
1. Full clean build.
2. Screenshot all 15 pages (reuse the existing screenshot approach from Phases 1–2) — confirm the
   new dark header renders correctly and the logo displays at the correct size on every single one,
   including the pages whose content area stays in the old light theme. The header/content seam on
   those pages should look like a deliberate two-tone transition, not a rendering error — if
   anything looks broken rather than just stylistically transitional, that's a real bug to fix here.
3. Full link-crawl — confirm the new nav's links all resolve, and confirm no page anywhere still
   links to a URL that assumed the old nav structure.
4. Check both desktop and mobile widths for the new header specifically — logos are a common
   mobile-overflow culprit.

## Step 3 — Update the status doc

Update `docs/WEBSITE_REBUILD_STATUS.md`: mark header/nav unification done, and add an explicit new
tracked item for "old-page content reskinning" (the eight pages listed above) as future work — not
implied, written down the same way the nav migration itself was tracked after Phase 1.

## Reporting

Report per-page confirmation that the header renders correctly (not just "the build succeeded"),
the link-crawl result, and explicitly show a screenshot of at least one old-theme page (e.g.
`proof.html`) so the header/content seam can be reviewed and accepted or flagged before Phase 4
builds another new page on top of this.
