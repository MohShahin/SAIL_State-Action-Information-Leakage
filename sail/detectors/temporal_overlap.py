"""
Category 3 -- temporal / window-overlap leakage (Proposition 1's shape,
``FORMAL_ANALYSIS.md`` Section 5): a feature's lookback window overlaps a
period when treatment was already active, contaminating what's meant to be a
clean pre-decision snapshot.

Ported directly from Section 5.1's definitions:
    O_t(w) = total treatment-hours overlapping [t-w, t)
    c_t(w) = min(1, O_t(w) / w)

**Critical correctness note, proven in Section 5.3, not assumed:** O_t(w) is
monotone non-decreasing in w (Proposition 1 -- nested windows), but the
FRACTION c_t(w) is NOT monotonic in w: it rises exactly when the marginal
treatment density in the newly-included slice exceeds the average density
accumulated so far, and can just as well fall as w grows. This detector
computes c_t(w) directly from the definition for whatever w it's given; it
does not assume, or need to assume, any particular direction as w changes.
"""

from typing import Any

from .base import LeakageCheck, LeakageFinding


def _overlap_hours(window_start: float, window_end: float, intervals) -> float:
    total = 0.0
    for start, end in intervals:
        lo = max(window_start, start)
        hi = min(window_end, end)
        if hi > lo:
            total += hi - lo
    return total


class TemporalOverlapDetector(LeakageCheck):
    """Detects Category 3 temporal/window-overlap leakage.

    Required ``spec`` keys:
        treatment_intervals: list of (start, end) tuples, in the same time
            units as ``time_col`` -- a single shared timeline across every
            row in ``df``. (Phase B simplification: a real multi-patient
            cohort needs a per-patient interval table joined on a patient
            key; deferred to whenever this detector is wired into a
            cohort-level ``sail.check()``.)
        time_col: column in ``df`` giving each decision point's time t.

    Exactly one of:
        window_hours: a single window length w applied to every row, or
        window_col: a column in ``df`` giving a per-row window length.

    Optional:
        threshold: c_t(w) above this flags a row (default 0.5, matching this
            project's own established ">50% overlap" convention used
            throughout ``FORMAL_ANALYSIS.md`` and ``mechanisms.html``).
    """

    def run(self, df, spec: dict[str, Any]) -> LeakageFinding:
        intervals = spec["treatment_intervals"]
        time_col = spec["time_col"]
        threshold = spec.get("threshold", 0.5)

        if "window_hours" in spec:
            windows = [spec["window_hours"]] * len(df)
        elif "window_col" in spec:
            windows = df[spec["window_col"]].tolist()
        else:
            raise KeyError("spec must provide either 'window_hours' or 'window_col'")

        records = []
        for t, w in zip(df[time_col].tolist(), windows):
            o = _overlap_hours(t - w, t, intervals)
            c = min(1.0, o / w) if w > 0 else (1.0 if o > 0 else 0.0)
            records.append({
                "t": t, "window_hours": w, "overlap_hours": o, "overlap_fraction": c,
            })

        flagged_rows = [r for r in records if r["overlap_fraction"] > threshold]
        flagged = len(flagged_rows) > 0

        if flagged:
            explanation = (
                f"{len(flagged_rows)} of {len(records)} decision point(s) have a "
                f"treatment-overlap fraction above {threshold:.0%} of the lookback "
                f"window. This is Proposition 1's shape -- the window is "
                f"contaminated by prior treatment; it is not a claim that the "
                f"fraction rises with a wider window (it may fall -- see Section 5.3)."
            )
        else:
            explanation = (
                f"No decision point exceeded {threshold:.0%} treatment-overlap "
                f"fraction across {len(records)} row(s) checked."
            )

        return LeakageFinding(
            category="temporal_overlap_leakage",
            flagged=flagged,
            explanation=explanation,
            evidence={"threshold": threshold, "records": records},
        )
