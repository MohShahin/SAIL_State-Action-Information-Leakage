---
description: Phase 1 — rebuild the homepage as a product landing page around the real, unmocked extension demo GIF
---

# Website rebuild, Phase 1 — homepage

**Do not fabricate any content.** The demo GIF, screenshots, and install command are real and
already exist (`extension/docs/demo.gif`, `extension/docs/screenshots/`). Use them directly. Do not
write marketing copy claiming capabilities beyond what Tier 1 (the Jupyter-kernel check flow) and
the wizard actually do — no mention of live-as-you-type scanning (Tier 2, explicitly not built) or
AI-assisted suggestions (Phase 5, speced but not built) as if they exist today.

## Step 1 — Read before writing

Read `extension/docs/screenshots/` and `extension/docs/demo.gif` to confirm exactly what visual
assets exist. Read `extension/README.md` for the accurate, current feature list — the homepage's
claims must match this exactly, not a more ambitious version of it.

## Step 2 — Visual direction

Match the extension's own look, not the earlier academic Swiss-design system: dark background,
calm, teal accent for "clean," amber for "flagged" (reusing the extension's own established
palette), theme-native/system sans typography. This is a product page now, not a paper's front
matter.

## Step 3 — Build the homepage

Structure:
1. **Hero:** one-sentence hook (reuse the already-reviewed line from `docs/PI_DEFENSE_PREP.md`
   §12.1, adapted for a product context, not redrafted from scratch), the real demo GIF prominently
   placed, install command (`pip install sail-leakage`, and the VS Code extension's real install
   path — check `extension/README.md` for its exact current install instructions, likely via a
   `.vsix` or Marketplace link once published).
2. **How it works, 3 steps:** pick your dataset, confirm the auto-detected columns, read the
   report — matching the wizard's actual real flow, not an idealized version of it.
3. **What it checks:** a brief teaser of the five categories, linking to the (Phase 3) Detectors
   page for depth — don't duplicate the full explanations here.
4. Footer: links to About, Detectors, Papers, Datasets & Models, Privacy, Understanding Leakage —
   this is the new site-wide nav, replacing the old flat 10-item + two-track structure entirely.

## Step 4 — Verify

Full clean build, confirm zero broken links (the new nav will break every existing internal link
pointing at old paths — a full link-crawl and fix pass is required, not optional, given this is
exactly the class of bug this project has been bitten by twice before). Render at desktop and
mobile widths, confirm the GIF and screenshots display correctly at both.

## Reporting

Report the final homepage structure, the link-crawl result, and explicitly confirm every claim on
the page matches something that's actually built and verified — not the roadmap's future state.
