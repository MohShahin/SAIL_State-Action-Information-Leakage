---
description: Phase C1 — build the sail.check() orchestrator, now that all five detectors exist and are individually verified
---

# SAIL package, Phase C1 — orchestrator

All five detectors exist and are tested individually. This phase assembles them behind the single
public API sketched in `docs/SAIL_PACKAGE_ROADMAP.md` — `sail.check(df, ...)`.

## Build `sail/check.py`

```python
def check(df, state_cols, action_col, timestamp_col=None,
          treatment_col=None, window_col=None,
          persistence_auroc=None, full_state_auroc=None) -> LeakageReport:
```

Run each category only when the inputs it needs are actually provided:
- Categories 1/2 (construction, reconstruction) need `treatment_col` and the relevant state columns.
- Category 3 (temporal overlap) needs `window_col`.
- Category 4 (timing violation) needs `timestamp_col` and an action-window definition.
- Category 5 (persistence) needs `persistence_auroc` and `full_state_auroc` explicitly — per the
  Phase B decision, this category never fits a model itself.

**The one rule that matters most here:** if a category's required inputs aren't provided, the
report must say so explicitly per category ("not run: window_col not provided"), never silently
omit it and never guess a default. A user glancing at a report with 3 findings should immediately
know two categories didn't run and why, not assume the package checked everything.

## Extend `LeakageReport`

`.summary()` should group by category, clearly separating "flagged," "not flagged," and "not run"
sections — in that order, flagged first, since that's what a user actually came for.

## Tests

1. Full spec (all inputs provided) against a synthetic table combining Phase A/B's individual test
   fixtures — confirm all 5 categories run and produce the same per-category results as calling
   each detector directly (the orchestrator must not change any detector's actual logic).
2. Partial spec (e.g. no `window_col`) — confirm categories 1/2/4/5 still run correctly and
   category 3 is reported as "not run," not silently absent from the summary.
3. Minimal spec (only the required base columns) — confirm the report is still useful and honest
   about what it couldn't check.

## Verify

Rebuild the wheel, fresh-venv install, run all three orchestrator tests from that install. Confirm
the full existing Phase A/B test suite still passes unchanged — this phase should not touch any
detector's internals, only wire them together.

## Report

Confirm all tests pass and paste one example `.summary()` output (from the full-spec test) so the
actual report formatting can be reviewed before this ships.
