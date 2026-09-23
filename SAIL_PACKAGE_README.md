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

SAIL doesn't guess what your columns mean — each of the five checks is explicit about exactly
what it needs, and a check only runs when you give it enough to run correctly. This example uses
a small toy table shaped like the real state tables from the underlying research project, with two
numbers (`persistence_auroc`, `full_state_auroc`) taken directly from that project's own verified
Experiment 8 result — so what you see printed below is a real finding, not a fabricated demo.

```python
import pandas as pd
import sail
from sail.specs.sofa_cardio import sofa_cardio_row

# Four decision points, all with a fixed dopamine dose while MAP varies --
# Theorem 1's own worked example (proof.html #thm1).
df = pd.DataFrame({
    "map":         [40, 55, 70, 90],
    "dopamine":    [6, 6, 6, 6],
    "dobutamine":  [0, 0, 0, 0],
    "epi":         [0, 0, 0, 0],
    "norepi":      [0, 0, 0, 0],
    "sofa_resp":   [2, 0, 1, 3],
    "sofa_coag":   [1, 0, 2, 0],
    "sofa_liver":  [0, 0, 1, 2],
    "sofa_renal":  [1, 0, 0, 1],
    "sofa_cns":    [0, 0, 1, 0],
    "t":               [10.0, 34.0, 58.0, 82.0],   # each decision point's timestamp
    "action_start":    [10.0, 34.0, 58.0, 82.0],   # the next action's window start
    "action_next":     [1, 0, 1, 0],
    "window_hours":    [4.0, 4.0, 4.0, 4.0],       # lookback window length
})
df["sofa_cardio"] = df.apply(sofa_cardio_row, axis=1)
df["sofa_total"] = (
    df["sofa_cardio"] + df["sofa_resp"] + df["sofa_coag"]
    + df["sofa_liver"] + df["sofa_renal"] + df["sofa_cns"]
)

report = sail.check(
    df,
    state_cols=["map", "sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns", "sofa_total"],
    action_col="action_next",
    timestamp_col="t",                 # feeds categories 3 and 4
    treatment_col="dopamine",          # default treatment column for construction_spec
    window_col="window_hours",         # category 3
    action_start_col="action_start",   # category 4
    treatment_intervals=[(8.0, 10.0)], # category 3: a shared (start, end) treatment timeline
    persistence_auroc=0.914,           # category 5: this project's own real Variant F result
    full_state_auroc=0.900,            # category 5: this project's own real Variant A result
    construction_spec={"scoring_fn": sofa_cardio_row, "signal_col": "map"},
    reconstruction_spec={
        "total_col": "sofa_total",
        "component_cols": ["sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns"],
        "target_col": "sofa_cardio",
    },
)

print(report.summary())
```

Every input above is optional except `df`, `state_cols`, and `action_col` — give a check only
what you have. Drop `treatment_intervals` (or `window_col`, or `timestamp_col`) and only the
temporal-overlap category is reported as **not run**; everything else still runs. You'll always
know exactly what was and wasn't evaluated, never a silent guess.

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
