"""
Category 5 -- persistence-dominance flag. **Not leakage** -- a related,
equally useful diagnostic this project's own Variant F result (Experiment 8)
motivates directly: two purely temporal treatment-history features, with no
raw treatment-dose term of any kind, out-predicted the full physiological
state (action-recoverability AUROC 0.914 vs. 0.900 -- see
``results/experiment8_variant_f_summary.json``). A package that only checked
construction/reconstruction/temporal-overlap/timing-violation leakage would
miss exactly the finding that made this project's own result sharper than
expected: sometimes a state's predictive power is mostly ordinary treatment
persistence, not any of the leakage mechanisms above.

Design decisions (sign-off recorded 2026-09-23, before this file was
written):

1. **Baseline:** "predict A_t from A_{t-1} alone" -- the simplest,
   domain-agnostic operationalization of ordinary persistence, matching the
   causal graph's own persistence pathway (Proposition 2). NOT Variant F's
   own F1/F2 duration features, which are vasopressor/SOFA-specific
   engineering that wouldn't generalize to another domain this package might
   be pointed at.
2. **Dominance margin:** 0.02 AUROC, applied as
   ``persistence_auroc >= full_state_auroc - margin`` -- comfortably and
   non-trivially captures the real Variant F case (0.914 vs. 0.900) without
   being loose enough to flag a merely weakly-correlated feature.
3. **Wording:** every explanation, flagged or not, states plainly that this
   is not a leakage finding.

Consistent with how every other detector in this package works, this
detector compares two ALREADY-COMPUTED AUROC numbers -- it does not fit a
model itself. Fitting the persistence baseline (A_t ~ A_{t-1}) and the
full-state model is the caller's responsibility, exactly as this project
computed Variant F's and Variant A's AUROCs externally and only the final
numbers are recorded in this project's own results files.
"""

from typing import Any

from .base import LeakageCheck, LeakageFinding


class PersistenceDominanceDetector(LeakageCheck):
    """Detects Category 5 persistence dominance. Not a leakage category.

    Required ``spec`` keys:
        persistence_auroc: AUROC of a single-feature "predict A_t from
            A_{t-1} alone" model.
        full_state_auroc: AUROC of the full state's action-recoverability
            model, on the same task.

    Optional:
        margin: how close (or in excess) the persistence baseline must be to
            count as "dominant" (default 0.02).
    """

    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        persistence_auroc = spec["persistence_auroc"]
        full_state_auroc = spec["full_state_auroc"]
        margin = spec.get("margin", 0.02)

        gap = full_state_auroc - persistence_auroc
        # A tiny epsilon keeps the documented "within margin OF, or exceeding" boundary
        # inclusive in practice: ordinary decimal AUROC inputs (e.g. 0.90 - 0.88) don't
        # represent exactly in binary float, so a bare `gap <= margin` can reject a case
        # that is exactly at the margin by design (same class of issue the reconstruction
        # detector's own `tolerance` parameter exists to handle).
        flagged = gap <= margin + 1e-9

        if flagged:
            explanation = (
                f"Not leakage: a treatment-persistence baseline (predicting the next "
                f"action from the prior action alone) achieves an AUROC within "
                f"{margin} of, or exceeding, the full state's action-recoverability "
                f"AUROC ({persistence_auroc:.3f} vs {full_state_auroc:.3f}). This "
                f"means much of the state's apparent predictive power may reflect "
                f"ordinary treatment persistence rather than the construction- or "
                f"reconstruction-leakage mechanisms this package's other detectors "
                f"check for. See this project's own Experiment 8 / Variant F result, "
                f"where two purely temporal history features alone out-predicted the "
                f"full physiological state for exactly this reason."
            )
        else:
            explanation = (
                f"The treatment-persistence baseline (AUROC {persistence_auroc:.3f}) "
                f"falls meaningfully below the full state's action-recoverability "
                f"AUROC ({full_state_auroc:.3f}, gap {gap:.3f} > margin {margin:.3f}) "
                f"-- the state's predictive power isn't readily explained by ordinary "
                f"treatment persistence alone."
            )

        return LeakageFinding(
            category="persistence_dominance",
            flagged=flagged,
            explanation=explanation,
            evidence={
                "persistence_auroc": persistence_auroc,
                "full_state_auroc": full_state_auroc,
                "margin": margin,
                "gap": gap,
            },
        )
