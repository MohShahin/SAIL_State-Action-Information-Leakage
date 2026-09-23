"""
``sail.check(df, ...)`` -- the single public entry point that dispatches
across all five leakage-detector categories, running only the ones it has
enough input to run and reporting explicitly, per category, when it can't.

**The one rule that matters most here:** if a category's required inputs
aren't provided, the report says so explicitly -- never silently omits a
category, never guesses a default.

A note on this signature versus ``docs/SAIL_PACKAGE_ROADMAP.md``'s original
sketch: that sketch was written before any detector existed, and assumed
``state_cols``, ``action_col``, ``treatment_col``, and ``window_col`` alone
would be enough to run every category. Once the detectors were actually
built (Phases A/B), several categories turned out to need more specific
inputs than that -- there is no generic, dataset-agnostic way to test
"is this state feature treatment-derived" without knowing what physiological
signal it's supposed to measure (construction leakage), or which column is
the retained "total" a target was removed from (reconstruction leakage), or
where an action's own window starts (timing violation). This function keeps
every parameter from the original sketch -- ``state_cols`` and ``action_col``
are validated against ``df`` but do not gate or feed any detector directly,
since none of the five, as actually built, consume a generic state-column
list or action-label column -- and adds the more specific parameters each
detector actually needs. This gap between the original aspirational sketch
and what the built detectors require is a real finding from building this
orchestrator, not swept under the rug: see the Phase C1 report for the full
reasoning.
"""

from typing import Any, Optional

from .detectors.construction import ConstructionLeakageDetector
from .detectors.persistence import PersistenceDominanceDetector
from .detectors.reconstruction import ReconstructionLeakageDetector
from .detectors.temporal_overlap import TemporalOverlapDetector
from .detectors.timing_violation import TimingViolationDetector
from .report import LeakageReport


def check(
    df,
    state_cols,
    action_col,
    timestamp_col: Optional[str] = None,
    treatment_col: Optional[str] = None,
    window_col: Optional[str] = None,
    persistence_auroc: Optional[float] = None,
    full_state_auroc: Optional[float] = None,
    *,
    treatment_intervals: Optional[list] = None,
    action_start_col: Optional[str] = None,
    construction_spec: Optional[dict[str, Any]] = None,
    reconstruction_spec: Optional[dict[str, Any]] = None,
    margin: Optional[float] = None,
) -> LeakageReport:
    """Run every category the given inputs support enough of.

    state_cols, action_col: validated against ``df`` (raises ``KeyError`` if
        missing). Not currently consumed by any individual detector -- see
        the module docstring.
    timestamp_col: decision-point time. Doubles as category 3's ``time_col``
        and category 4's ``state_end_col``.
    treatment_col: default for ``construction_spec["treatment_cols"]`` if
        that dict doesn't specify its own.
    window_col: per-row window length column, for category 3.
    treatment_intervals: shared ``(start, end)`` treatment-interval list for
        category 3 -- see ``TemporalOverlapDetector`` (a single shared
        timeline across every row is a Phase B simplification).
    action_start_col: the action window's start column, for category 4.
    construction_spec: dict with ``scoring_fn``, ``signal_col``, and
        optionally ``treatment_cols`` (defaults to ``[treatment_col]``) --
        category 1.
    reconstruction_spec: dict with ``total_col``, ``component_cols``,
        ``target_col`` -- category 2.
    persistence_auroc, full_state_auroc, margin: category 5, passed straight
        through to ``PersistenceDominanceDetector``.
    """
    missing_cols = [c for c in (*state_cols, action_col) if c not in df.columns]
    if missing_cols:
        raise KeyError(f"columns not found in df: {missing_cols}")

    report = LeakageReport()

    # --- Category 1: construction leakage ---
    if construction_spec is not None:
        spec = dict(construction_spec)
        spec.setdefault("treatment_cols", [treatment_col] if treatment_col else [])
        report.add(ConstructionLeakageDetector().run(df, spec))
    else:
        report.skip(
            "construction_leakage",
            "not run: construction_spec not provided (needs scoring_fn and "
            "signal_col -- treatment_col and state_cols alone don't specify which "
            "state feature to test or what physiological signal it's supposed to "
            "measure)",
        )

    # --- Category 2: reconstruction leakage ---
    if reconstruction_spec is not None:
        report.add(ReconstructionLeakageDetector().run(df, reconstruction_spec))
    else:
        report.skip(
            "reconstruction_leakage",
            "not run: reconstruction_spec not provided (needs total_col, "
            "component_cols, target_col)",
        )

    # --- Category 3: temporal-overlap leakage ---
    missing_3 = [
        name for name, val in (
            ("window_col", window_col),
            ("timestamp_col", timestamp_col),
            ("treatment_intervals", treatment_intervals),
        ) if val is None
    ]
    if not missing_3:
        report.add(TemporalOverlapDetector().run(df, {
            "treatment_intervals": treatment_intervals,
            "time_col": timestamp_col,
            "window_col": window_col,
        }))
    else:
        report.skip("temporal_overlap_leakage", f"not run: {', '.join(missing_3)} not provided")

    # --- Category 4: timing-violation leakage ---
    missing_4 = [
        name for name, val in (
            ("timestamp_col", timestamp_col),
            ("action_start_col", action_start_col),
        ) if val is None
    ]
    if not missing_4:
        report.add(TimingViolationDetector().run(df, {
            "state_end_col": timestamp_col,
            "action_start_col": action_start_col,
        }))
    else:
        report.skip("timing_violation_leakage", f"not run: {', '.join(missing_4)} not provided")

    # --- Category 5: persistence-dominance flag ---
    missing_5 = [
        name for name, val in (
            ("persistence_auroc", persistence_auroc),
            ("full_state_auroc", full_state_auroc),
        ) if val is None
    ]
    if not missing_5:
        spec: dict[str, Any] = {
            "persistence_auroc": persistence_auroc,
            "full_state_auroc": full_state_auroc,
        }
        if margin is not None:
            spec["margin"] = margin
        report.add(PersistenceDominanceDetector().run(df, spec))
    else:
        report.skip("persistence_dominance", f"not run: {', '.join(missing_5)} not provided")

    return report
