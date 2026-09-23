"""
Category 2 -- reconstruction leakage (Theorem 2's shape): a feature removed
from a state definition is still exactly (or near-exactly) recoverable by
subtracting the other retained component features from a retained total.
"""

from typing import Any

from .base import LeakageCheck, LeakageFinding


class ReconstructionLeakageDetector(LeakageCheck):
    """Detects Category 2 reconstruction leakage.

    Required ``spec`` keys:
        total_col: name of the retained "total" column.
        component_cols: names of the other retained component columns (must
            NOT include ``target_col``).
        target_col: the "removed" feature being checked for recoverability.

    Optional:
        tolerance: max allowed |reconstructed - actual| per row to still
            count as recoverable (default 1e-9, i.e. exact -- Theorem 2 is an
            algebraic identity, not an approximation).
    """

    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        total_col = spec["total_col"]
        component_cols = list(spec["component_cols"])
        target_col = spec["target_col"]
        tolerance = spec.get("tolerance", 1e-9)

        if target_col in component_cols:
            raise ValueError("target_col must not be included in component_cols")

        n_rows = int(len(df))
        if n_rows == 0:
            return LeakageFinding(
                category="reconstruction_leakage",
                flagged=False,
                explanation="No rows to check.",
                evidence={"n_rows": 0},
            )

        reconstructed = df[total_col] - df[component_cols].sum(axis=1)
        actual = df[target_col]
        diff = (reconstructed - actual).abs()
        max_diff = float(diff.max())
        flagged = bool((diff <= tolerance).all())

        if flagged:
            explanation = (
                f"'{target_col}' is exactly recoverable from '{total_col}' minus "
                f"{component_cols}: max reconstruction error across {n_rows} rows was "
                f"{max_diff:.2e}, within tolerance ({tolerance:.0e}). This is Theorem "
                f"2's shape -- removing '{target_col}' from the state does not remove "
                f"the information it carries."
            )
        else:
            explanation = (
                f"'{target_col}' is NOT reliably recoverable from '{total_col}' minus "
                f"{component_cols}: max reconstruction error across {n_rows} rows was "
                f"{max_diff:.2e}, exceeding tolerance ({tolerance:.0e})."
            )

        return LeakageFinding(
            category="reconstruction_leakage",
            flagged=flagged,
            explanation=explanation,
            evidence={"max_abs_error": max_diff, "n_rows": n_rows, "tolerance": tolerance},
        )
