"""
Category 1 -- construction leakage: a scoring function whose output is partly
determined by treatment status rather than the physiological signal it claims
to measure.

Generalized from two proven, distinctly-shaped results in this project:

- **1a -- full non-identifiability** (Theorem 1's shape, ``sofa_cardio``):
  once treatment is active, the score becomes CONSTANT with respect to the
  signal it's supposed to measure, across every signal value observed while
  treatment is active.
- **1b -- score-shift collision** (Proposition 3's shape, respiratory SOFA's
  ventilatory-support conditional): the score still varies with the signal,
  but at least one signal value maps to a DIFFERENT score depending on
  treatment status alone.

A case is checked for 1a first; only if 1a does not hold (the score still
varies with the signal even while treatment is active -- exactly the
"what does *not* hold" finding in ``FORMAL_ANALYSIS.md`` Section 4.5, checked
rather than assumed by analogy) is it checked for 1b. This mirrors the actual
distinction proven there: the two shapes are mutually exclusive by
definition, not a matter of picking whichever fires first.
"""

from typing import Any

from .base import LeakageCheck, LeakageFinding


class ConstructionLeakageDetector(LeakageCheck):
    """Detects both shapes of Category 1 construction leakage.

    Required ``spec`` keys:
        scoring_fn: callable(row) -> score, applied per-row via ``df.apply``.
        signal_col: name of the physiological column the score is supposed
            to reflect.
        treatment_cols: list of column names; treatment is considered
            "active" for a row when any of these columns is truthy/> 0.

    Optional:
        signal_round: decimal places to round ``signal_col`` to before
            testing for identical-signal-value collisions (default 6) --
            real continuous measurements need this for exact-match grouping
            to find anything; it is not a substitute for a proper tolerance-
            based binning strategy on noisy real-world data (a known Phase A
            simplification, not attempted here).
    """

    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        scoring_fn = spec["scoring_fn"]
        signal_col = spec["signal_col"]
        treatment_cols = list(spec["treatment_cols"])
        signal_round = spec.get("signal_round", 6)

        work = df.copy()
        work["_score"] = work.apply(scoring_fn, axis=1)
        work["_active"] = work[treatment_cols].fillna(0).gt(0).any(axis=1)
        work["_signal_r"] = work[signal_col].round(signal_round)

        active = work[work["_active"]]
        inactive = work[~work["_active"]]

        is_1a, groups_checked = self._check_1a(active, treatment_cols)
        if is_1a:
            return LeakageFinding(
                category="construction_leakage_1a",
                flagged=True,
                explanation=(
                    f"'{signal_col}' has no effect on the score once treatment "
                    f"({', '.join(treatment_cols)}) is active: across "
                    f"{groups_checked} distinct active treatment level(s) tested, "
                    f"each spanning multiple '{signal_col}' values, the score stayed "
                    f"constant. This is Theorem 1's shape -- full non-identifiability."
                ),
                evidence={
                    "active_rows": int(active.shape[0]),
                    "treatment_levels_checked": groups_checked,
                    "example_scores": sorted(active["_score"].unique().tolist())[:5],
                },
            )

        collisions = self._check_1b(active, inactive)
        if collisions:
            return LeakageFinding(
                category="construction_leakage_1b",
                flagged=True,
                explanation=(
                    f"Found {len(collisions)} value(s) of '{signal_col}' where "
                    f"treatment-active and treatment-inactive rows receive different "
                    f"scores for the identical '{signal_col}' value. This is "
                    f"Proposition 3's shape -- a score-shift collision, not full "
                    f"non-identifiability."
                ),
                evidence={"collisions": collisions[:10]},
            )

        return LeakageFinding(
            category="construction_leakage",
            flagged=False,
            explanation=(
                f"No construction leakage detected: '{signal_col}' still determines "
                f"the score independent of treatment status, and no '{signal_col}' "
                f"value collides across treatment status."
            ),
            evidence={
                "active_rows": int(active.shape[0]),
                "inactive_rows": int(inactive.shape[0]),
            },
        )

    @staticmethod
    def _check_1a(active, treatment_cols) -> tuple[bool, int]:
        if active.empty:
            return False, 0
        groups_checked = 0
        for _, group in active.groupby(treatment_cols, dropna=False):
            if group["_signal_r"].nunique() <= 1:
                continue  # can't test constancy against a signal that never varied
            groups_checked += 1
            if group["_score"].nunique() > 1:
                return False, groups_checked  # signal still moved the score somewhere
        return groups_checked > 0, groups_checked

    @staticmethod
    def _check_1b(active, inactive) -> list[dict]:
        if active.empty or inactive.empty:
            return []
        merged = active[["_signal_r", "_score"]].merge(
            inactive[["_signal_r", "_score"]],
            on="_signal_r",
            suffixes=("_active", "_inactive"),
        )
        mismatched = merged[merged["_score_active"] != merged["_score_inactive"]]
        return mismatched.drop_duplicates("_signal_r").to_dict("records")
