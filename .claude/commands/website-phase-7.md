---
description: Phase 7 — Privacy & HIPAA page, sourced directly from extension/docs/PHASE_5_DATA_SHARING.md as the single canonical source
---

# Website rebuild, Phase 7 — Privacy & HIPAA

**Do not independently redraft the privacy commitments.** `extension/docs/PHASE_5_DATA_SHARING.md`
is the canonical source, already reconciled to the full three-tier design. Restating it in new
words on this page risks exactly the wording-drift problem this project has already caught and
fixed once (the H3 explanation duplicated with subtly different phrasing across three pages) —
avoid repeating that mistake in a new place.

## Step 1 — Read the canonical source

Read `extension/docs/PHASE_5_DATA_SHARING.md` in full. Also read `src/privacy.html` (Phase 1's
placeholder) for what it already states about the package's local-only execution.

## Step 2 — Build the page

Structure:
1. **The package is local-only.** State plainly: every detector in `sail-leakage` runs entirely on
   the user's own machine — pandas/numpy computation, zero network calls, verified across every
   phase of its build. No data or code is ever transmitted anywhere by the package itself.
2. **The VS Code extension's three-tier design.** Reproduce the Tier A/B/C table directly from
   `PHASE_5_DATA_SHARING.md` — aggregate metadata, code-snippet opt-in with pre-send preview, raw
   data values never transmissible — with its current status marker (spec complete, implementation
   not started) stated exactly as that document states it. Do not imply this is built if the source
   document says it isn't.
3. **HIPAA framing, stated carefully.** Explain the architectural reasoning (no PHI transmission by
   design likely avoids needing a BAA for the LLM-suggestion feature) with the same hedge already
   established in this project: this describes the architecture, not a legal compliance
   certification — institutions should have their own compliance review confirm this satisfies
   their specific obligations.
4. Link to the source document itself for anyone who wants the full technical detail, rather than
   trying to reproduce every nuance on the page.

## Step 3 — Verify

Full clean build, link-crawl, screenshots at desktop and mobile. Diff the page's Tier A/B/C
description against the source document's actual current text to confirm no drift was introduced
in translating it to page copy.

## Reporting

Report the page's final content and explicitly confirm it was checked against
`PHASE_5_DATA_SHARING.md`'s current text line by line, not paraphrased from memory of an earlier
conversation about it.
