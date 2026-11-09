"""
``sail.check(df, ...)`` -- the single public entry point that dispatches
across all five leakage-detector categories, running only the ones it has
enough input to run and reporting explicitly, per category, when it can't.

**The one rule that matters most here:** if a category's required inputs
aren't provided, the report says so explicitly -- never silently omits a
category, never guesses a default.

For what each check needs, and why the signature has more parameters than the original
sketch, see the ``sail.check`` docstring (``help(sail.check)``) or call ``sail.requirements()``.
"""

import warnings
from typing import Any, Optional, Sequence

from .detectors.construction import ConstructionLeakageDetector
from .detectors.persistence import PersistenceDominanceDetector
from .detectors.reconstruction import ReconstructionLeakageDetector
from .detectors.temporal_overlap import TemporalOverlapDetector
from .detectors.timing_violation import TimingViolationDetector
from .report import LeakageReport


def check(
    df,
    state_cols: Sequence[Optional[str]],
    action_col: Optional[str] = None,
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

    **Plain tables.** A bare table of patient rows (state columns plus an action) is *not* enough
    to run the detectors: each one needs a specific extra input (see "What each check needs"
    below, or call ``sail.requirements()``). Checks that lack their input are listed as
    "NOT RUN" with the exact parameters that would enable them; ``report.summary()`` ends with a
    "TO RUN MORE CHECKS" block saying the same. Nothing is silently skipped or guessed.

    ``state_cols`` and ``action_col`` are validated against ``df`` but **no detector reads them**:
    they identify which columns are the model's state and action, so a typo fails loudly and
    ``None`` ("not identified") is accepted. The detectors take their own, more specific columns.

    What each check needs:
        1. construction: ``construction_spec`` (``scoring_fn``, ``signal_col``; optional
           ``treatment_cols``, defaulting to ``[treatment_col]``).
        2. reconstruction: ``reconstruction_spec`` (``total_col``, ``component_cols``,
           ``target_col``).
        3. temporal overlap: ``window_col``, ``timestamp_col`` and ``treatment_intervals``.
        4. timing violation: ``timestamp_col`` and ``action_start_col``. These must be
           *different* columns (state window end vs. action window start); with the same column
           the check cannot fail, and a ``UserWarning`` is raised.
        5. persistence dominance: ``persistence_auroc`` and ``full_state_auroc`` (optional
           ``margin``).

    A note on this signature versus ``docs/SAIL_PACKAGE_ROADMAP.md``'s original sketch: that sketch
    assumed ``state_cols``, ``action_col``, ``treatment_col`` and ``window_col`` alone would be
    enough to run every category. Once the detectors were built, several turned out to need more
    specific inputs: there is no generic way to test "is this state feature treatment-derived"
    without knowing what physiological signal it measures (construction), which column is the
    retained total a target was removed from (reconstruction), or where an action's window starts
    (timing). So every parameter from the sketch is kept and the more specific ones were added.

    Parameters
    ----------
    state_cols, action_col: validated against ``df`` (``KeyError`` naming any real-but-absent
        column; ``None`` entries are never treated as missing). Consumed by no detector.
    timestamp_col: decision-point time. Doubles as category 3's ``time_col`` and category 4's
        ``state_end_col``.
    treatment_col: default for ``construction_spec["treatment_cols"]``.
    window_col: per-row window length column, for category 3.
    treatment_intervals: shared ``(start, end)`` list for category 3 (a single shared timeline
        across every row is a Phase B simplification).
    action_start_col: the action window's start column, for category 4.
    construction_spec, reconstruction_spec: see above.
    persistence_auroc, full_state_auroc, margin: category 5, passed to
        ``PersistenceDominanceDetector``.
    """
    missing_cols = [c for c in (*state_cols, action_col) if c is not None and c not in df.columns]
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
            "measure). To enable: construction_spec={'scoring_fn': ..., 'signal_col': ...}",
        )

    # --- Category 2: reconstruction leakage ---
    if reconstruction_spec is not None:
        report.add(ReconstructionLeakageDetector().run(df, reconstruction_spec))
    else:
        report.skip(
            "reconstruction_leakage",
            "not run: reconstruction_spec not provided (needs total_col, "
            "component_cols, target_col). To enable: reconstruction_spec="
            "{'total_col': ..., 'component_cols': [...], 'target_col': ...}",
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
        if timestamp_col == action_start_col:
            warnings.warn(
                f"timestamp_col and action_start_col are both {timestamp_col!r}: the timing-"
                "violation check compares action start to state-window end, so with the same "
                "column it cannot fail. Pass the state window's end as timestamp_col and the "
                "action window's start as action_start_col.",
                UserWarning,
                stacklevel=2,
            )
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


_REQUIREMENTS = (
    ("construction_leakage", "construction_spec={'scoring_fn': ..., 'signal_col': ...}"),
    ("reconstruction_leakage",
     "reconstruction_spec={'total_col': ..., 'component_cols': [...], 'target_col': ...}"),
    ("temporal_overlap_leakage", "window_col=..., timestamp_col=..., treatment_intervals=[(s, e)]"),
    ("timing_violation_leakage",
     "timestamp_col=<state window end>, action_start_col=<action window start> (different columns)"),
    ("persistence_dominance", "persistence_auroc=..., full_state_auroc=..."),
)


def requirements() -> str:
    """Plain-language list of what each of the five checks needs, so a plain table can be mapped
    onto them. Printed text, e.g. ``print(sail.requirements())``."""
    lines = ["Extra inputs to sail.check(df, state_cols, action_col, ...) for each check:"]
    lines.extend(f"  {cat}: {need}" for cat, need in _REQUIREMENTS)
    lines.append("state_cols/action_col only name your columns; no detector reads them.")
    return "\n".join(lines)
