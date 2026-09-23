import pandas as pd

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
