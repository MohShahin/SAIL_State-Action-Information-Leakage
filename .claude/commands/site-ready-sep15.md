---
description: Complete pre-showcase readiness pass — content precision, redundancy removal, UX/mobile polish, and final full-site verification, gated in phases
---

# Site readiness for September 15

Five phases. **Phases 2 and 3 require an audit reported in full before any file is touched** —
same discipline as `/site-audit-and-showcase`. Do not combine phases into single commits; match
this project's established one-focused-commit-per-change pattern throughout.

**Standing guardrail for this whole command:** three days before a live event is not the time to
take on new risk. Every change here should make the site *more* correct or *more* robust, never
more clever. If a fix requires a genuinely large refactor to do properly, stop and report rather
than attempting it under time pressure — a known, well-understood rough edge is safer than a
rushed fix with an unknown failure mode.

---

## Phase 1 — Content precision (small, do first, no audit gate needed)

1. Update the H3/Experiment 5 wording on `status.html`, `evidence.html`, and `showcase.html`'s Act
   3 to state precisely why H3 is still open — not "not yet run," but: the negative-control data
   exists (`notebook/results/experiment5_negative_controls.json`, five offsets each independently
   bootstrapped), but the pre-registered test needs per-patient predictions saved across offsets so
   they can be resampled *jointly* — the current run only saved the aggregate AUROC and CI per
   offset, discarding the individual predictions needed for a paired bootstrap. State this as a
   small, well-understood next step (new code to save predictions + one new analysis pass), not an
   open-ended gap.
2. Grep the entire `src/` tree for leftover placeholder language: `TODO`, `FIXME`, `lorem ipsum`,
   `coming soon`, `draft`, `placeholder`, `XXX`. Report every hit with file and line. Fix any that
   are genuine leftovers; leave any that are legitimate prose (e.g., "the manuscript draft" is not
   a placeholder) — use judgment, don't strip words that happen to match a pattern.

Commit this phase alone once both items are done.

---

## Phase 2 — Redundancy audit (read-only, report before touching anything)

**Important distinction to hold throughout this phase:** the homepage's condensed sections
summarizing and linking to dedicated pages (`mechanisms.html`, `evidence.html`, etc.) are the
*intended* hub-and-spoke pattern, not redundancy — do not flag or touch that pattern. What counts
as genuine redundancy here is content that duplicates *without adding anything or linking back* —
copy-pasted explanations that have since drifted inconsistently (the `mechanisms.html`/`proof.html`
Theorem 1 threshold mismatch found in the last audit is exactly this failure mode — check whether
anything similar still exists elsewhere), dead CSS, orphaned files, and missing cross-links.

Check and report each of the following, with specifics, before fixing anything:

1. **Duplicated explanations that could drift again.** Grep for near-identical multi-sentence blocks
   explaining the same theorem, mechanism, or experiment across two or more pages *without* one
   linking to the other as the authoritative source. Report each instance found.
2. **Dead CSS.** For every class defined in `src/assets/style.css` and in each page's local
   `<style>` block, check whether it's actually referenced in any HTML. Report unused classes —
   do not remove any yet.
3. **Orphaned files.** Check `src/assets/img/` (is `logo.png` used anywhere, or only
   `logo-cropped.png`/`favicon.png`/`apple-touch-icon.png`?) and any other asset that isn't
   referenced by any page.
4. **Navigation completeness.** Confirm every page's nav includes a link to `/showcase/` — it was
   added after the shared `base.njk` nav was last touched, so check whether it was actually wired
   into the shared nav include or only linked from the homepage. This is a real risk: if it's not
   in the shared nav, most of the site can't discover it.
5. **Unused JS.** Any function or variable defined but never called, in any page's inline
   `<script>` — a lower priority than the above, but report what's found.

**Report the complete list, organized by category, before proceeding to fixes.**

---

## Phase 3 — Close Phase 2's findings, plus mobile/UX polish (only after Phase 2 is reported)

1. Fix each reported redundancy/dead-code/navigation finding as separate, small commits grouped by
   type (one commit for nav fix, one for dead CSS removal, etc.) — not one giant cleanup commit.
2. **The shared mobile horizontal-overflow issue** (present on both `evidence.html` and
   `showcase.html`, per the last audit) — this is explicitly in scope now, since the user asked for
   the site to be smooth and mobile-friendly, not deferred as before. Diagnose the actual cause
   (likely a fixed-width element — a table or the new chart — not wrapped in a scrollable
   container) before fixing. Confirm the fix doesn't affect desktop layout. Since this is the one
   genuinely riskier change in this command (CSS/layout, close to the deadline), verify it visually
   at multiple widths (375px, 390px, 768px, desktop) before committing, not just at the one width
   that showed the problem.
3. **Basic accessibility spot-check:** confirm all `<img>` tags across the site have meaningful
   `alt` text (not empty or filename-derived), and confirm the new six-variant chart's color triple
   (`#DC2626`/`#CA8A04`/`#059669`, validated for contrast in the last round) is the only place a
   status-color pattern is used — if the same red/amber/green concept appears anywhere else on the
   site with different, unvalidated colors, flag it.
4. **External resource loading check:** confirm Google Fonts, MathJax, and Prism.js loads on
   `proof.html`, `mechanisms.html`, and `reproducibility.html` don't cause a jarring flash of
   unstyled content — if `font-display` isn't set on the Google Fonts link, consider adding
   `&display=swap` if not already present (check first; it may already be there from the original
   build).

---

## Phase 4 — Extend real-browser verification to the showcase page

The existing `/verify-site` command predates `/showcase/` and doesn't cover it. Extend it (or run
an equivalent one-off Playwright pass, reusing the same real-browser discipline — not jsdom, for
the same reasons `/verify-site` originally specified):

1. Load `/showcase/` at desktop width: confirm Act 1's visualizer link works, Act 2's six-variant
   chart renders with no label collisions, Act 3's content matches Phase 1's updated wording exactly.
2. Load `/showcase/` at 375px and 390px mobile widths: confirm the Phase 3 overflow fix actually
   resolved the issue, with a screenshot as evidence, not just an assertion.
3. Click through from `/showcase/` to the live visualizer and confirm the toggle/gauge interaction
   still works end to end (this was verified once before the showcase page existed — confirm the
   showcase's embed/link doesn't break it).

Report PASS/FAIL per check, screenshots included, same reporting discipline as `/verify-site`.

---

## Phase 5 — Final pre-Sep-15 checklist

1. Full clean build (`rm -rf node_modules _site && npm ci && npm run build`) — confirm zero errors.
2. Crawl every internal link across all pages (reuse the link-crawl approach from the Eleventy
   migration's original verification) — confirm zero broken links, including the new `/showcase/`
   page's links.
3. Spot-check external links (GitHub repo, DOI links in `papers.html`, PhysioNet) resolve with a
   200 — these can rot independently of anything in this project.
4. Confirm the GitHub Actions deploy workflow is green on the current `HEAD` commit, not just that
   the push succeeded — a green push and a green deploy are different facts, checked separately
   earlier in this project for good reason.
5. Produce one final explicit statement: either "the site is ready for September 15," or a
   specific, numbered list of what remains — not a vague "mostly done."

---

## Reporting

Report after every phase, not just at the end. Phase 2's report is the most important gate in this
command — do not proceed past it without it being shown in full, exactly as the last audit did.
