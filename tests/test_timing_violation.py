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
