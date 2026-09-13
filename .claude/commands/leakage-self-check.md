---
description: Build a static, honest leakage self-check questionnaire on papers.html, ending in a pre-filled GitHub issue to contact the SAIL team — no backend, no file upload, no fabricated analysis
---

# Leakage self-check tool

**The single most important rule in this command:** this tool never claims to analyze anything.
It is a structured self-assessment based on SAIL's own published taxonomy, answered entirely by
the visitor about their own work. At every point where it would be tempting to make the output
sound more authoritative than it is — do not. If a design decision here ever starts to resemble
"quietly read and summarize their paper," stop and report rather than building it; that is
explicitly out of scope, decided already, not a re-open point.

## Phase 0 — Check existing patterns first (read-only)

1. Read `about.html`'s existing "Contact & collaboration" section to confirm the exact current
   contact mechanism (GitHub issues) and the exact repo URL to build issue links against.
2. Read `papers.html`'s existing JS (the tag-filter system) to match its coding style and the
   site's established vanilla-JS-no-framework pattern — this addition should look and feel like
   part of the same page, not a bolted-on widget.
3. Check `CITATION.cff` for any additional contact detail that should be surfaced (author name,
   etc.) — use only what's actually there, don't invent anything.

Report what's found before building.

## Phase 1 — Build the questionnaire (static, client-side, no file upload)

Add a new section to `papers.html`, after the existing paper cards, titled something like "Think
your paper's state representation might have this problem? Self-check."

**Framing copy, required, not optional:** state plainly, before any question, that this is a
self-assessment tool based on this project's own findings — not an automated review of any
uploaded document, and that no file or paper text is read, stored, or analyzed by this tool.

**Inputs:**
1. An optional single-line text field: "Link to your paper (arXiv, journal, preprint server —
   optional)." Explicitly labeled as carried through only as a reference for a human reviewer if
   the visitor chooses to contact the team — never fetched or parsed by any code on this page.
2. A short sequence of yes/no questions, grounded directly in the mechanisms this project actually
   proved (do not invent new categories) — draft along these lines, adjusting wording for clarity:
   - Does your state representation include any variable whose value is partly determined by the
     treatment action active at or immediately before the current decision point (e.g., a
     composite severity score that takes current drug/dose as an input, the way SOFA's
     cardiovascular and respiratory subscores do)?
   - Is that state used to predict, evaluate, or train a policy for the *next* treatment decision?
   - Does your state's aggregation window (if any) span a period during which treatment may
     already have been active?
   - Have you tested whether a version of your state with treatment-derived features removed
     changes model performance — and if so, on which task (next-action prediction, or an actual
     outcome like mortality)?
   - Does your state ever include information about the *same or later* decision point's action —
     i.e., information that would not have been available yet at the time the decision was made?

## Phase 2 — Map answers to a self-check read (not a verdict)

Based on the answer pattern, show one of a small number of pre-written, carefully-hedged responses
— examples of the *shape* these should take (adjust wording, keep the hedging intact):

- If treatment-derived state info exists and is used to predict the next action, but the
  visitor hasn't tested removing it: "This resembles the treatment-confounded severity
  construction pattern this project documents (see Theorem 1 / mechanisms.html) — worth checking
  directly against your own state definition, not assumed from these answers alone."
- If the aggregation-window question is "yes": "This resembles the treatment-overlap pattern (see
  Proposition 1 / mechanisms.html)."
- If the last question ("same or later decision point") is "yes": this is the one case worth
  flagging more directly, since it's closest to the genuinely reserved sense of "leakage" this
  project uses — but still phrase it as "worth a closer look," not a diagnosis.
- If none apply: say so plainly — do not manufacture a finding to make the tool seem more useful
  than the answers actually support.

**Every output branch, without exception, ends with the same line:** "This is a self-check based
on published patterns, not a review of your actual paper. If you'd like the SAIL team to look at
this directly, "

## Phase 3 — The contact path (GitHub issue, pre-filled, no new service)

A button/link, always visible regardless of the self-check's outcome, that opens:

```
https://github.com/MohShahin/SAIL_State-Action-Information-Leakage/issues/new?title=<url-encoded-title>&body=<url-encoded-body>
```

The pre-filled body should include: the optional paper link if provided, which self-check
questions were answered yes/no, and a short prompt line like "I'd like the SAIL team's input on
whether this reflects any of the patterns described in this project." Construct this with plain
JS `encodeURIComponent` — no backend, no form-submission service, no new external dependency.

## Phase 4 — Verify before committing

1. Build and confirm the new section renders correctly at desktop and mobile widths.
2. Manually click through 2–3 different answer combinations and confirm each produces the correct
   mapped response from Phase 2, and that the GitHub issue link opens with the correct title/body
   pre-filled for each case — check the actual resulting URL, don't assume the encoding is correct.
3. Confirm no code path anywhere reads, uploads, or transmits any file — there should be no
   `<input type="file">` anywhere in this addition. If one exists, remove it; a file input that
   accepts a file but does nothing with it is worse than not having one, since it implies false
   functionality.
4. Re-read the framing copy from Phase 1 one final time and confirm it still reads as honest about
   what this tool is and isn't — this is the line most worth re-checking right before committing.

## Reporting

Report what was built, with the exact rendered framing copy quoted in full (not paraphrased) so it
can be checked for honesty before this goes live three days before a public event.
