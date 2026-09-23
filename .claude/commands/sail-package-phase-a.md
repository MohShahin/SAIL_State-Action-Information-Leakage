---
description: Phase A — scaffold the sail package and build construction-leakage + reconstruction-leakage detectors, tested against this project's own verified numbers
---

# SAIL package, Phase A

**The standing rule for this whole package effort:** every detector must be traceable to a proven
result already in this repo, and every test must assert against a number this project has already
verified — not a newly-invented expected value. If a detector can't be grounded this way, it
doesn't belong in Phase A; flag it for a later phase instead of shipping something untested against
reality.

## Step 1 — Scaffold

Create the package structure exactly as specified in `docs/SAIL_PACKAGE_ROADMAP.md`:
```
sail/__init__.py
sail/detectors/base.py
sail/detectors/construction.py
sail/detectors/reconstruction.py
sail/report.py
sail/specs/
tests/
pyproject.toml
```

`pyproject.toml`: minimal, modern (`[build-system]` with `hatchling` or `setuptools`), package name
`sail-leakage` (check PyPI availability for this name before finalizing — report back if it's
taken and propose an alternative rather than assuming it's free), Python 3.9+ compatible, no heavy
dependencies beyond `pandas` and `numpy`.

## Step 2 — `sail/detectors/base.py`

Define the shared interface:
```python
class LeakageFinding:
    category: str            # e.g. "construction_leakage_1a"
    flagged: bool
    explanation: str         # plain language, references the specific evidence
    evidence: dict           # the actual numbers/rows that triggered (or didn't trigger) the flag

class LeakageCheck(ABC):
    def run(self, df, spec) -> LeakageFinding: ...
```

Keep this minimal — do not over-engineer the base class before there are more than two detectors
to generalize from.

## Step 3 — Construction leakage detector (`sail/detectors/construction.py`)

Port the logic directly from `notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb`'s
`sofa_cardio_decomposed` function — this is Theorem 1's actual, already-proven implementation, not
a new algorithm. Generalize it to: given a scoring function (or a set of branch conditions) and a
treatment-status column, detect whether the output becomes constant with respect to a named
"true-signal" column once treatment is active (sub-type 1a), or whether identical true-signal
values map to different outputs depending on treatment status (sub-type 1b, Proposition 3's shape
— port from the respiratory-SOFA analysis in `FORMAL_ANALYSIS.md` §4.5).

**Test, asserting against already-verified numbers, not new ones:**
- Construct the exact dopamine=6 case from Theorem 1's proof. Confirm the detector flags 1a and its
  explanation references the correct branch logic.
- Construct the PF∈[100,200) collision case from Proposition 3 (ventilated vs. non-ventilated,
  identical PF). Confirm the detector flags 1b, not 1a — these are different shapes and the
  detector must distinguish them, not lump every construction-leakage case together.
- Construct a clean case (no treatment-status dependency at all) and confirm the detector correctly
  reports `flagged: False` — a detector that only ever says yes is useless; test the negative case
  explicitly.

## Step 4 — Reconstruction leakage detector (`sail/detectors/reconstruction.py`)

Port Theorem 2's logic: given a "total" column and a set of "component" columns, check whether a
named target component is exactly (or near-exactly, within a small numerical tolerance) recoverable
by subtracting the other components from the total.

**Test, against the real SOFA-total case:**
- Using this project's own SOFA subscore structure, confirm the detector flags `sofa_cardio` as
  reconstructible from `sofa_total` minus the other five subscores — this should be an exact
  match (it's an algebraic identity, not an approximation).
- Construct a case where the "total" doesn't actually include the target component (a case that
  should NOT be flagged) and confirm the detector correctly reports `flagged: False`.

## Step 5 — Report assembly

`sail/report.py`: a `LeakageReport` that collects findings from however many detectors were run,
with a `.summary()` producing plain-language output (not just a dict dump) and a `.to_json()` for
programmatic use. If a check couldn't run because a required column wasn't provided, the report
should say so explicitly per-category, not silently skip it.

## Step 6 — Verify before committing

1. Run the full test suite — every test must pass, and specifically confirm the negative-case tests
   (Step 3's clean case, Step 4's non-inclusion case) pass, not just the positive/flagged cases.
2. As a sanity check beyond unit tests, run the construction detector against a small extract of
   this project's own real state table (`state_4h` from the notebook, or a saved CSV if easier) and
   confirm it flags `sofa_cardio` — this is the package correctly re-deriving a finding this
   project already knows to be true, which is worth having as a concrete demonstration even this
   early.
3. Do not add Phase B's detectors (temporal overlap, timing violation, persistence) in this pass —
   scope discipline matters here exactly as it has everywhere else in this project.

## Reporting

Report the final package structure, confirm all tests pass, and report the PyPI name-availability
check result from Step 1 before this gets committed.
