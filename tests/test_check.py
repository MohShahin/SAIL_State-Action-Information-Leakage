import pandas as pd
import pytest

import sail
from sail.detectors.construction import ConstructionLeakageDetector
from sail.detectors.persistence import PersistenceDominanceDetector
from sail.detectors.reconstruction import ReconstructionLeakageDetector
from sail.detectors.temporal_overlap import TemporalOverlapDetector
from sail.detectors.timing_violation import TimingViolationDetector
from sail.specs.sofa_cardio import sofa_cardio_row

STATE_COLS = ["map", "sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns", "sofa_total"]
ACTION_COL = "action_next"


def _build_df():
    """One combined table wide enough to feed every category at once --
    Theorem 1's dopamine=6/MAP-swept rows (construction), the same rows'
    derived subscores summing to sofa_total (reconstruction), decision times
    t (temporal overlap), and state/action window columns (timing
    violation). The rows don't represent one coherent clinical narrative --
    each column set is only meant to satisfy its own category's own test.
    """
    df = pd.DataFrame({
        "map": [40, 55, 70, 90],
        "dopamine": [6, 6, 6, 6],
        "dobutamine": [0, 0, 0, 0],
        "epi": [0, 0, 0, 0],
        "norepi": [0, 0, 0, 0],
        "sofa_resp": [2, 0, 1, 3],
        "sofa_coag": [1, 0, 2, 0],
        "sofa_liver": [0, 0, 1, 2],
        "sofa_renal": [1, 0, 0, 1],
        "sofa_cns": [0, 0, 1, 0],
        "t": [10.0, 34.0, 58.0, 82.0],
        "action_start": [10.0, 34.0, 58.0, 82.0],  # adjacent, zero overlap -- not a violation
        "action_next": [1, 0, 1, 0],
    })
    df["sofa_cardio"] = df.apply(sofa_cardio_row, axis=1)
    df["sofa_total"] = (
        df["sofa_cardio"] + df["sofa_resp"] + df["sofa_coag"]
        + df["sofa_liver"] + df["sofa_renal"] + df["sofa_cns"]
    )
    return df


CONSTRUCTION_SPEC = {"scoring_fn": sofa_cardio_row, "signal_col": "map"}
RECONSTRUCTION_SPEC = {
    "total_col": "sofa_total",
    "component_cols": ["sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns"],
    "target_col": "sofa_cardio",
}
TREATMENT_INTERVALS = [(8.0, 10.0)]


def test_full_spec_runs_all_five_and_matches_direct_calls():
    df = _build_df()
    df["window_hours"] = 4.0

    report = sail.check(
        df, STATE_COLS, ACTION_COL,
        timestamp_col="t",
        treatment_col="dopamine",
        window_col="window_hours",
        persistence_auroc=0.914,
        full_state_auroc=0.900,
        treatment_intervals=TREATMENT_INTERVALS,
        action_start_col="action_start",
        construction_spec=CONSTRUCTION_SPEC,
        reconstruction_spec=RECONSTRUCTION_SPEC,
    )

    assert len(report.findings) == 5
    assert report.skipped == {}
    categories = {f.category for f in report.findings}
    assert categories == {
        "construction_leakage_1a",
        "reconstruction_leakage",
        "temporal_overlap_leakage",
        "timing_violation_leakage",
        "persistence_dominance",
    }

    by_category = {f.category: f for f in report.findings}

    direct_construction = ConstructionLeakageDetector().run(df, {
        **CONSTRUCTION_SPEC, "treatment_cols": ["dopamine"],
    })
    assert by_category["construction_leakage_1a"].flagged == direct_construction.flagged
    assert by_category["construction_leakage_1a"].explanation == direct_construction.explanation

    direct_reconstruction = ReconstructionLeakageDetector().run(df, RECONSTRUCTION_SPEC)
    assert by_category["reconstruction_leakage"].flagged == direct_reconstruction.flagged
    assert by_category["reconstruction_leakage"].explanation == direct_reconstruction.explanation

    direct_temporal = TemporalOverlapDetector().run(df, {
        "treatment_intervals": TREATMENT_INTERVALS, "time_col": "t", "window_col": "window_hours",
    })
    assert by_category["temporal_overlap_leakage"].flagged == direct_temporal.flagged
    assert by_category["temporal_overlap_leakage"].explanation == direct_temporal.explanation

    direct_timing = TimingViolationDetector().run(df, {
        "state_end_col": "t", "action_start_col": "action_start",
    })
    assert by_category["timing_violation_leakage"].flagged == direct_timing.flagged
    assert direct_timing.flagged is False  # adjacent windows, this project's own real case

    direct_persistence = PersistenceDominanceDetector().run(df, {
        "persistence_auroc": 0.914, "full_state_auroc": 0.900,
    })
    assert by_category["persistence_dominance"].flagged == direct_persistence.flagged
    assert direct_persistence.flagged is True  # the real Variant F result


def test_partial_spec_skips_only_the_underspecified_category():
    """No window_col/treatment_intervals -- category 3 should be the only
    one reported as not run; 1/2/4/5 still run correctly."""
    df = _build_df()
    report = sail.check(
        df, STATE_COLS, ACTION_COL,
        timestamp_col="t",
        treatment_col="dopamine",
        persistence_auroc=0.914,
        full_state_auroc=0.900,
        action_start_col="action_start",
        construction_spec=CONSTRUCTION_SPEC,
        reconstruction_spec=RECONSTRUCTION_SPEC,
    )

    ran = {f.category for f in report.findings}
    assert ran == {
        "construction_leakage_1a",
        "reconstruction_leakage",
        "timing_violation_leakage",
        "persistence_dominance",
    }
    assert set(report.skipped.keys()) == {"temporal_overlap_leakage"}
    assert "not provided" in report.skipped["temporal_overlap_leakage"]

    summary = report.summary()
    assert "NOT RUN" in summary
    assert "temporal_overlap_leakage" in summary


def test_minimal_spec_reports_everything_as_not_run_but_stays_useful():
    """Only the required base columns -- every category should be reported
    as not run, explicitly, not silently absent."""
    df = _build_df()
    report = sail.check(df, STATE_COLS, ACTION_COL)

    assert report.findings == []
    assert len(report.skipped) == 5
    assert set(report.skipped.keys()) == {
        "construction_leakage",
        "reconstruction_leakage",
        "temporal_overlap_leakage",
        "timing_violation_leakage",
        "persistence_dominance",
    }

    summary = report.summary()
    assert "NOT RUN (5)" in summary
    for category in report.skipped:
        assert category in summary


def test_missing_state_column_raises_keyerror_naming_it():
    """A typo in state_cols is an input error, not a silent skip."""
    df = _build_df()
    with pytest.raises(KeyError, match="no_such_column"):
        sail.check(df, [*STATE_COLS, "no_such_column"], ACTION_COL)


def test_missing_action_column_raises_keyerror_naming_it():
    df = _build_df()
    with pytest.raises(KeyError, match="no_such_action"):
        sail.check(df, STATE_COLS, "no_such_action")


def test_every_missing_column_is_reported_at_once():
    df = _build_df()
    with pytest.raises(KeyError) as excinfo:
        sail.check(df, ["missing_a", "map", "missing_b"], "missing_c")
    for name in ("missing_a", "missing_b", "missing_c"):
        assert name in str(excinfo.value)
    assert "'map'" not in str(excinfo.value)   # only the absent ones are named


def test_action_col_none_means_not_provided_not_a_missing_column():
    """A caller that couldn't determine an action column (e.g. a UI whose auto-detection found no
    match) passes None, not a column name -- None must mean "not provided," the same as every other
    optional parameter here, not raise a KeyError claiming a column literally named None is absent.

    Reproduces the exact crash the SAIL VS Code extension's wizard hit for real: a file whose action-
    like column ("next_insulin_units") didn't match the wizard's auto-detect pattern, so the wizard
    sent action_col=None, and every real check crashed with `KeyError: columns not found in df:
    [None]` instead of the five honest "not run" cards the docstring's own rule promises.
    """
    df = _build_df()
    report = sail.check(df, STATE_COLS, None)
    assert report.findings == []
    assert len(report.skipped) == 5
    assert set(report.skipped.keys()) == {
        "construction_leakage",
        "reconstruction_leakage",
        "temporal_overlap_leakage",
        "timing_violation_leakage",
        "persistence_dominance",
    }


def test_state_cols_with_a_none_entry_is_ignored_not_treated_as_missing():
    """Same principle as action_col=None, for the other half of the validated pair: a None sitting
    inside state_cols (e.g. built from a field map with an unmapped slot) is not a column name to
    look up -- it's the absence of one, and must not raise."""
    df = _build_df()
    report = sail.check(df, [*STATE_COLS, None], ACTION_COL)
    assert report.findings == []
    assert len(report.skipped) == 5


def test_action_col_can_be_omitted_entirely_not_just_passed_as_none():
    """action_col now defaults to None, so a caller (e.g. the bridge) can leave it out of the call
    entirely -- not just pass None explicitly -- with the same "not provided" result."""
    df = _build_df()
    report = sail.check(df, STATE_COLS)
    assert report.findings == []
    assert len(report.skipped) == 5


def test_a_real_wrong_column_name_still_raises_even_alongside_none():
    """The fix for None must not swallow a genuine typo sitting next to it."""
    df = _build_df()
    with pytest.raises(KeyError, match="no_such_column"):
        sail.check(df, [*STATE_COLS, None, "no_such_column"], ACTION_COL)
