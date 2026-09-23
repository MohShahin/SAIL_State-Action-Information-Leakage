# SAIL

**Detect state–action information leakage in offline reinforcement learning and clinical prediction
pipelines — grounded in mathematically proven mechanisms, not heuristics.**

SAIL grew out of a research project proving that a widely-used ICU severity score (SOFA) can
become mathematically non-identifiable from patient physiology once treatment is active — meaning
a model using it can be partly reading back its own training data's treatment decisions rather than
learning from the patient. This package generalizes what that project proved into five reusable,
independently testable checks.

> **Status: early, actively developed.** Five detector categories exist and are tested against
> already-verified results from the underlying research project. This is not a claim of exhaustive
> coverage — see [What this does and doesn't check](#what-this-does-and-doesnt-check) below.

## Install

```bash
pip install sail-leakage
```

If the package name above isn't live on PyPI yet, install directly from source:

```bash
pip install git+https://github.com/MohShahin/SAIL_State-Action-Information-Leakage.git
```

## Quickstart

```python
import sail

report = sail.check(
    df,
    state_cols=["severity_score", "vital_1", "vital_2"],
    action_col="action_next",
    treatment_col="current_dose",       # enables construction + reconstruction + persistence checks
    window_col="window_start",          # enables the temporal-overlap check
    timestamp_col="decision_time",      # enables the timing-violation check
)

print(report.summary())
```

A report only checks what it has the inputs to check — if you don't provide `window_col`, the
temporal-overlap category is reported as **not run**, not silently skipped. You'll always know
exactly what was and wasn't evaluated.

## The five checks

| # | Category | What it catches | Proven by |
|---|---|---|---|
| 1 | Construction leakage | A state feature is partly *defined* by treatment, making it non-identifiable (or shift-colliding) with the signal it claims to measure | Theorem 1 / Proposition 3 |
| 2 | Reconstruction leakage | A "removed" feature is still exactly recoverable from other retained features | Theorem 2 |
| 3 | Temporal-overlap leakage | A feature's aggregation window overlaps a period when treatment was already active | Proposition 1 |
| 4 | Timing-violation leakage | The state's window extends into or past the action being predicted — the strict sense of "leakage" | Direct timestamp verification |
| 5 | Persistence-dominance flag | A trivial "last action repeats" baseline matches or exceeds the full state's predictive power — not leakage, but a related and equally important diagnostic | Motivated directly by this project's own Variant F result |

Full mathematical detail for each: see [`FORMAL_ANALYSIS.md`](FORMAL_ANALYSIS.md) in the parent
research repository.

## Why this taxonomy, and why trust it

Every category above is a generalization of something this project *proved*, not a heuristic
assembled under deadline pressure. Every detector's test suite asserts against numbers already
independently verified — including negative cases (confirming the detector correctly says "no"),
not just the cases it's designed to catch. The construction-leakage detector, for example, is
tested against the exact worked example (dopamine at 6 mcg/kg/min) that Theorem 1 proves in closed
form — if you want to check the math yourself rather than trust the package, the proof is public
and the test is the same case.

## What this does and doesn't check

**It doesn't read or understand your paper or your code.** SAIL checks the data you give it against
five specific, well-defined patterns — it has no opinion about anything outside those patterns, and
a clean report is not a certificate that your pipeline has no leakage of any kind.

**It doesn't train a model.** The persistence-dominance check (category 5) takes AUROC numbers you
already computed as input — it never fits anything itself, so it has no hidden assumptions about
your modeling choices.

**It's five categories, not a standard.** This is what one research project proved exists. If you
find a leakage pattern this package doesn't catch, that's expected, not a bug — [open an
issue](https://github.com/MohShahin/SAIL_State-Action-Information-Leakage/issues) and it's exactly
the kind of thing this project wants to hear about.

## The research behind this package

The full formal proofs, the empirical audit on 11,354 real ICU stays, and the project's honest
account of what's still open (including a pre-registered, not-yet-run statistical test) live at
**[the project site](https://mohshahin.github.io/SAIL_State-Action-Information-Leakage/)**.

## Citing this work

See [`CITATION.cff`](CITATION.cff).

## License

MIT — see [`LICENSE`](LICENSE).
