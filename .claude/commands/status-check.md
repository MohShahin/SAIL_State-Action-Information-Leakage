---
description: Full read-only status check — git state, prior command outcomes, live production URL, and the H3-wording drift — before deciding what (if anything) still needs fixing before Sep 15
---

# Pre-showcase status check

**This entire command is read-only.** Do not fix anything found here — report it, so the next step
can be a deliberate decision rather than another round of immediate changes three days out.

## Phase 1 — Git and deploy state

1. `git log --oneline -25` — list recent history so we have a shared picture of what's actually
   landed, including every `/site-audit-and-showcase`, `/phase4-followup`, `/site-ready-sep15`, and
   `/leakage-self-check` commit.
2. `git status --short` — confirm the working tree is clean (nothing built-but-uncommitted sitting
   around).
3. `git fetch && git log HEAD..origin/main --oneline` and `git log origin/main..HEAD --oneline` —
   confirm local and remote are exactly in sync, both directions.
4. Check the GitHub Actions run for the current `HEAD` commit specifically (via `gh run list` if
   available, otherwise report that this needs a manual check in the browser) — confirm it's green,
   not just that the push succeeded. A successful push and a successful deploy are different facts.

## Phase 2 — Confirm `/site-ready-sep15`'s actual outcome

That command's Phase 5 was supposed to end in an explicit readiness statement. Check whether one
exists in any commit message or `docs/` file from that run. If it's not clearly recorded:
1. Re-run its Phase 5 checks directly: full clean build (`rm -rf node_modules _site && npm ci &&
   npm run build`), confirm zero errors, then crawl all internal links across every page (reuse the
   approach already used for the original Eleventy migration verification) and report any broken
   links found.
2. Confirm the mobile-overflow fix from that command's Phase 3 actually landed — check
   `evidence.html` and `showcase.html` at a 375px viewport (real browser via Playwright, not just
   reading the CSS) and report pass/fail.

## Phase 3 — Confirm `/leakage-self-check`'s actual outcome

1. Check whether `papers.html` actually contains the self-check section — if the command never ran
   or didn't complete, say so plainly rather than assuming it exists.
2. If it exists: **quote the exact rendered framing copy verbatim** (the text stating this is a
   self-check, not an automated analysis) — this needs a human's eyes on the actual wording, not a
   summary of it.
3. Confirm no `<input type="file">` exists anywhere in the addition.
4. Test the GitHub issue pre-fill link with one real example answer combination — report the
   actual resulting URL and confirm it decodes to sensible title/body text.

## Phase 4 — Test the real production URL, not localhost

1. Fetch `https://mohshahin.github.io/SAIL_State-Action-Information-Leakage/` directly (not the
   local build) and confirm the homepage loads.
2. Fetch `/showcase/`, `/papers/`, `/proof/`, `/mechanisms/`, `/evidence/`, `/status/` on the live
   URL specifically — confirm each returns real content, not a 404, and that the content reflects
   the latest work (e.g., check `/papers/` for the self-check section, `/showcase/` for the
   six-variant chart including Variant F).
3. **This is the most important check in this whole command:** a push succeeding locally does not
   guarantee the live site reflects it. If anything fetched from the live URL looks stale compared
   to what's in the local repo, report this as the top-priority finding, above everything else.

## Phase 5 — The H3-wording drift, specifically

Re-check the exact wording of the H3/Experiment-5 explanation on `evidence.html`, `status.html`,
and `showcase.html`'s Act 3 — quote each verbatim, side by side, and report whether they still say
the same thing in different words (drift, previously flagged and deliberately deferred) or whether
one now links to `proof.html`'s canonical version instead of restating it.

## Phase 6 — Anything else visibly incomplete

Grep the entire `src/` tree one more time for `TODO`, `FIXME`, `placeholder`, `coming soon` — a
final sweep in case anything was left mid-edit across the many separate command runs this session.

## Reporting — one consolidated dashboard, not six separate reports

Produce a single summary at the end, organized as:
- **Confirmed working, live, verified on the real URL** — the things that need zero further action.
- **Uncertain / needs a decision** — anything found stale, drifted, or unconfirmed, with enough
  detail to decide whether it's worth fixing before Sep 15 or accepting as-is.
- **Broken** — anything actually failing, if found. Flag this most prominently if it exists.

Do not propose fixes in this report — that's the next command, once this one's findings are
reviewed.
