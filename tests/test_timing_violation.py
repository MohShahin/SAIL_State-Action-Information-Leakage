import pandas as pd

from sail.detectors.timing_violation import TimingViolationDetector


def test_projects_own_real_case_not_flagged():
    """State [0,4), action window [4,8) -- adjacent, zero overlap. This is
    this project's own actual, verified case (Phase 0's manual alignment
    check on build_action_labels' shift(-1) logic)."""
    df = pd.DataFrame({"state_end": [4], "action_start": [4]})
    finding = TimingViolationDetector().run(df, {
        "state_end_col": "state_end", "action_start_col": "action_start",
    })
    assert finding.flagged is False


def test_violating_case_flagged():
    """Action window starting at 2, inside the state's [0,4) -- a
    deliberately constructed genuine violation."""
    df = pd.DataFrame({"state_end": [4], "action_start": [2]})
    finding = TimingViolationDetector().run(df, {
        "state_end_col": "state_end", "action_start_col": "action_start",
    })
    assert finding.flagged is True


def test_boundary_touching_not_flagged():
    """Action window starting exactly at the state's end -- touching, not
    overlapping. A stricter <= here would incorrectly flag this project's
    own real pipeline (the case above), so this boundary is asserted
    explicitly rather than left to coincide with the "real case" test."""
    df = pd.DataFrame({"state_end": [4.0], "action_start": [4.0]})
    finding = TimingViolationDetector().run(df, {
        "state_end_col": "state_end", "action_start_col": "action_start",
    })
    assert finding.flagged is False


SPEC = {"state_end_col": "state_end", "action_start_col": "action_start"}


def test_rows_without_an_action_time_neither_flag_nor_count():
    """NaN < x is False, so an untested row used to count as 'no violation' and inflate n_rows."""
    df = pd.DataFrame({"state_end": [4.0, 4.0, 4.0, 4.0],
                       "action_start": [2.0, 6.0, float("nan"), float("nan")]})
    finding = TimingViolationDetector().run(df, SPEC)
    assert finding.evidence["n_violations"] == 1
    assert finding.evidence["n_rows"] == 2
    assert finding.evidence["n_missing"] == 2
    assert "1 of 2 row(s)" in finding.explanation
    assert "2 row(s) with a missing" in finding.explanation


def test_missing_state_end_is_also_excluded():
    df = pd.DataFrame({"state_end": [float("nan"), 4.0], "action_start": [2.0, 4.0]})
    finding = TimingViolationDetector().run(df, SPEC)
    assert finding.flagged is False
    assert finding.evidence["n_rows"] == 1 and finding.evidence["n_missing"] == 1


def test_all_rows_missing_is_not_reported_as_clean():
    df = pd.DataFrame({"state_end": [4.0, 4.0], "action_start": [float("nan"), float("nan")]})
    finding = TimingViolationDetector().run(df, SPEC)
    assert finding.flagged is False
    assert finding.evidence == {"n_violations": 0, "n_rows": 0, "n_missing": 2,
                                "same_column": False}
    assert "No row could be tested" in finding.explanation
    assert "No timing violation" not in finding.explanation


def test_no_missing_rows_reports_zero_and_no_exclusion_note():
    df = pd.DataFrame({"state_end": [4.0], "action_start": [4.0]})
    finding = TimingViolationDetector().run(df, SPEC)
    assert finding.evidence["n_missing"] == 0
    assert "excluded" not in finding.explanation
