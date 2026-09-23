---
description: Phase B — temporal-overlap and timing-violation detectors (fully spec'd), plus persistence-dominance (design decisions flagged for review before building)
---

# SAIL package, Phase B

Same standing rule as Phase A: every detector traces to a proven result, every test asserts
against a number already verified in this repo. Category 5 below has open design decisions —
**stop and report back on those specifically before writing category 5's code**, even though
categories 3 and 4 can proceed directly.

## Category 3 — Temporal-overlap detector (`sail/detectors/temporal_overlap.py`)

Port the logic from `FORMAL_ANALYSIS.md` §5: given a window length and a treatment-interval table,
compute `O_t(w)` (overlap hours) and `c_t(w) = min(1, O_t(w)/w)`.

**Critical correctness requirement, not optional:** this detector must NOT assume "wider window ⇒
more contamination." §5.3's proven result is that absolute overlap `O_t(w)` is monotonic in `w`
(nested windows), but the *fraction* `c_t(w)` is not — it rises exactly when marginal treatment
density exceeds the average density accumulated so far. A detector that flags based on a naive
"bigger window = worse" heuristic would itself be wrong, in a way this project has already proven
wrong. Implement the actual derivative relationship, not a monotonicity assumption.

**Tests, against already-verified numbers:**
- The 4h-vs-24h reversal itself: construct the same treatment-timing pattern that produced this
  project's real result (4h window showing *higher* contamination than 24h — check
  `FORMAL_ANALYSIS.md` §5.3 for the exact framing) and confirm the detector reports the fraction
  correctly for both window lengths, without asserting or assuming the naive direction.
- A limiting case: `t` strictly inside an ongoing treatment interval, `w → 0` — confirm
  `c_t(w) → 1`.
- A clean case: no treatment interval anywhere near the window — confirm `flagged: False`.

## Category 4 — Timing-violation detector (`sail/detectors/timing_violation.py`)

Generalize the Phase 0 alignment check already performed manually on this project's own notebook
(`build_action_labels`, the `shift(-1)` logic, verified to produce zero overlap between the state
window `[t·I, (t+1)·I)` and the action's window `[(t+1)·I, (t+2)·I)`). Given a state window's
`(start, end)` per row and an action's associated timestamp or window, flag when the action's
window starts before the state's window ends — i.e., genuine boundary overlap, the one category
this project reserves the word "leakage" for in the strict sense.

**Tests:**
- Reconstruct this project's own actual case (state `[0,4)`, action window `[4,8)`) — confirm
  `flagged: False`, zero overlap, matching the real verified finding.
- Construct a deliberately violating case (action window starting at 2, inside the state's `[0,4)`)
  — confirm `flagged: True`.
- Boundary edge case: action window starting exactly at the state's end (touching, not
  overlapping) — confirm this is treated as `False`, matching the "adjacent, zero overlap" finding
  from this project's own verified case, not a stricter `<=` that would incorrectly flag the
  project's own pipeline.

## Category 5 — Persistence-dominance flag: design decisions needing sign-off before building

This is a diagnostic, not a proof — there's no single correct threshold, so these need an explicit
answer before any code gets written. Report back with the decisions rather than picking silently:

1. **What's the baseline?** The natural candidate is "predict `A_t` from `A_{t-1}` alone" (a
   single-feature persistence model) — matching the causal graph's own persistence pathway. Confirm
   this is the right baseline, or propose an alternative.
2. **What counts as "dominance"?** A candidate threshold, grounded in this project's own numbers:
   Variant F's action-recoverability (0.914) *exceeded* the full state's (0.900) — so one
   reasonable flag condition is "the user's treatment-history features alone achieve AUROC within
   some margin of, or exceeding, the full-state AUROC." Propose a specific margin (e.g., within
   0.02) rather than leaving it vague, and say why that number, not just what it is.
3. **What does the report say when flagged?** This should not claim "your model has leakage" —
   persistence-dominance is explicitly *not* leakage in this project's taxonomy. Draft the exact
   wording of the finding's `explanation` field and include it in what gets reported back, since
   getting this phrasing wrong is exactly the kind of thing that undermines the whole package's
   credibility with a partner like Verily.

**Do not write `sail/detectors/persistence.py` until these three are confirmed.**

## Verify before committing

1. Full test suite passes, including every negative case explicitly (not just the flagged ones).
2. Confirm the wheel builds and installs cleanly in a fresh virtual environment
   (`python -m venv`, `pip install dist/*.whl`, `python -c "import sail"`) — this was flagged as
   worth checking after Phase A and should be confirmed now before Phase B adds more surface area.
3. Still do not build `sail.check()` — the orchestrator remains Phase C's, once all five detectors
   actually exist.

## Reporting

Report categories 3 and 4's test results in full. Report category 5's three open decisions with
your recommended answers, clearly separated from the confirmed-working parts of this phase, and
stop there — do not proceed to writing category 5 in the same pass as reporting.
