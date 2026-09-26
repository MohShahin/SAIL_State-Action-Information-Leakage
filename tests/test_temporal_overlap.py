import pandas as pd
import pytest

from sail.detectors.temporal_overlap import TemporalOverlapDetector


def test_4h_vs_24h_reversal():
    """Reconstructs the mechanism behind this project's own empirically
    observed 4h-vs-24h reversal (FORMAL_ANALYSIS.md Section 5.3): a burst of
    treatment entirely within the last 4 hours, but small relative to a 24h
    lookback that also includes a long treatment-free stretch beforehand.
    The detector must report the fraction correctly for both window lengths
    without assuming which direction is "worse" -- it isn't told in advance."""
    intervals = [(20.0, 24.0)]  # 4 continuous hours of treatment, ending exactly at t=24

    finding_4h = TemporalOverlapDetector().run(pd.DataFrame({"t": [24.0]}), {
        "treatment_intervals": intervals, "time_col": "t", "window_hours": 4.0,
    })
    finding_24h = TemporalOverlapDetector().run(pd.DataFrame({"t": [24.0]}), {
        "treatment_intervals": intervals, "time_col": "t", "window_hours": 24.0,
    })

    c_4h = finding_4h.evidence["records"][0]["overlap_fraction"]
    c_24h = finding_24h.evidence["records"][0]["overlap_fraction"]

    assert c_4h == 1.0  # the entire 4h window is treatment
    assert abs(c_24h - (4.0 / 24.0)) < 1e-9  # same 4 treatment-hours, diluted over 24h
    assert c_4h > c_24h  # the reversal itself: narrower window shows MORE contamination
    assert finding_4h.flagged is True
    assert finding_24h.flagged is False  # 4/24 = 16.7%, below the 50% threshold


def test_limit_w_to_zero_inside_ongoing_treatment():
    """Section 5.4: for t strictly inside an ongoing treatment interval,
    c_t(w) -> 1 as w -> 0+. Since O_t(w) <= w by construction whenever the
    entire window sits inside the interval, this holds exactly, not just in
    the limit, for any sufficiently small w -- so a tiny but nonzero w is a
    faithful, non-approximate test of the limiting behavior."""
    intervals = [(10.0, 30.0)]  # ongoing interval spanning t=20
    finding = TemporalOverlapDetector().run(pd.DataFrame({"t": [20.0]}), {
        "treatment_intervals": intervals, "time_col": "t", "window_hours": 1e-6,
    })
    assert finding.evidence["records"][0]["overlap_fraction"] == 1.0


def test_clean_case_not_flagged():
    """No treatment interval anywhere near the window -- the negative case."""
    intervals = [(0.0, 2.0)]  # treatment happened, but long before the decision point
    finding = TemporalOverlapDetector().run(pd.DataFrame({"t": [50.0]}), {
        "treatment_intervals": intervals, "time_col": "t", "window_hours": 4.0,
    })
    assert finding.flagged is False
    assert finding.evidence["records"][0]["overlap_fraction"] == 0.0


def _record(intervals, w=10.0, t=10.0):
    finding = TemporalOverlapDetector().run(pd.DataFrame({"t": [t]}), {
        "treatment_intervals": intervals, "time_col": "t", "window_hours": w,
    })
    return finding, finding.evidence["records"][0]


@pytest.mark.parametrize("intervals", [
    [(0.0, 5.0)],                  # one interval: the reference case
    [(0.0, 3.0), (2.0, 5.0)],      # overlapping: same 5h covered, 1h shared
    [(0.0, 5.0), (0.0, 5.0)],      # exact duplicate
])
def test_overlapping_and_duplicate_intervals_count_each_hour_once(intervals):
    """Treatment-hours are the UNION of the intervals, not their sum. All three
    inputs cover exactly hours [0, 5) of the 10h window [0, 10), so each must
    give 5 treatment-hours = 0.50 -- exactly at, not above, the 0.5 threshold,
    so none is flagged. (Summing per interval gave 6h / 0.60 for the overlapping
    case and 10h / 1.00 for the duplicate, both falsely flagged.)"""
    finding, rec = _record(intervals)
    assert rec["overlap_hours"] == 5.0
    assert rec["overlap_fraction"] == 0.5
    assert finding.flagged is False


def test_nested_interval_adds_nothing():
    """(2, 4) sits entirely inside (0, 10): the union is still 10h, fraction 1.0,
    not 12h."""
    _, rec = _record([(0.0, 10.0), (2.0, 4.0)])
    assert rec["overlap_hours"] == 10.0
    assert rec["overlap_fraction"] == 1.0


def test_union_is_order_independent_and_touching_intervals_merge():
    """Intervals need not be sorted, and end-to-end (touching) intervals cover
    their combined span exactly once."""
    _, rec = _record([(6.0, 8.0), (0.0, 3.0), (3.0, 4.0)])
    assert rec["overlap_hours"] == 6.0   # [0,4) + [6,8)
    assert rec["overlap_fraction"] == 0.6


def test_union_is_clipped_to_the_window():
    """Only the part of the union inside [t - w, t) counts."""
    _, rec = _record([(-5.0, 2.0), (1.0, 4.0), (9.0, 15.0)])   # union [-5,4) + [9,15)
    assert rec["overlap_hours"] == 5.0   # [0,4) + [9,10)


def test_genuinely_overlapping_case_is_still_flagged_when_union_exceeds_threshold():
    """The fix must not under-report: a union of 6h in a 10h window is 0.60 > 0.5."""
    finding, rec = _record([(0.0, 4.0), (3.0, 6.0)])   # union [0,6)
    assert rec["overlap_fraction"] == 0.6
    assert finding.flagged is True


def test_one_shot_iterable_of_intervals_is_used_for_every_row():
    """An iterator can only be read once; every row must still see all of it."""
    df = pd.DataFrame({"t": [10.0, 10.0, 10.0]})
    finding = TemporalOverlapDetector().run(df, {
        "treatment_intervals": iter([(0.0, 5.0)]), "time_col": "t", "window_hours": 10.0,
    })
    assert [r["overlap_fraction"] for r in finding.evidence["records"]] == [0.5, 0.5, 0.5]


def test_missing_window_spec_raises_keyerror():
    """Neither window_hours nor window_col is provided -- an input error, not a default."""
    with pytest.raises(KeyError, match="window_hours"):
        TemporalOverlapDetector().run(pd.DataFrame({"t": [10.0]}), {
            "treatment_intervals": [(0.0, 5.0)], "time_col": "t",
        })
