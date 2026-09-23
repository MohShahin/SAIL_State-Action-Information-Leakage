import pandas as pd

from sail.detectors.construction import ConstructionLeakageDetector
from sail.specs.sofa_cardio import sofa_cardio_row
from sail.specs.sofa_resp import sofa_resp_official_row


def test_theorem1_dopamine6_flags_1a():
    """Theorem 1's own corrected example (proof.html #thm1): dopamine fixed at
    6 mcg/kg/min, MAP swept across {40, 55, 70, 90} -- the score should be 3
    identically regardless of MAP."""
    df = pd.DataFrame({
        "map": [40, 55, 70, 90],
        "dopamine": [6, 6, 6, 6],
        "dobutamine": [0, 0, 0, 0],
        "epi": [0, 0, 0, 0],
        "norepi": [0, 0, 0, 0],
    })
    scored = df.apply(sofa_cardio_row, axis=1)
    assert (scored == 3).all()  # ground truth per Theorem 1's own worked example

    finding = ConstructionLeakageDetector().run(df, {
        "scoring_fn": sofa_cardio_row,
        "signal_col": "map",
        "treatment_cols": ["dopamine", "dobutamine", "epi", "norepi"],
    })
    assert finding.flagged is True
    assert finding.category == "construction_leakage_1a"


def test_proposition3_pf150_flags_1b():
    """Proposition 3's own worked case (FORMAL_ANALYSIS.md Section 4.5):
    PF=150 (inside [100,200)) scores 3 when ventilated, 2 when not --
    identical PF, different score, purely a function of treatment status."""
    assert sofa_resp_official_row({"pf_ratio": 150, "ventilated": True}) == 3
    assert sofa_resp_official_row({"pf_ratio": 150, "ventilated": False}) == 2

    df = pd.DataFrame({
        "pf_ratio": [150, 150, 250, 350, 450],
        "ventilated": [True, False, True, False, True],
    })
    finding = ConstructionLeakageDetector().run(df, {
        "scoring_fn": sofa_resp_official_row,
        "signal_col": "pf_ratio",
        "treatment_cols": ["ventilated"],
    })
    assert finding.flagged is True
    assert finding.category == "construction_leakage_1b"


def test_clean_case_not_flagged():
    """A scoring function with no treatment dependence at all: score is a
    pure, strictly-monotonic function of the signal, and treatment status
    changes nothing. The negative case -- a detector that only ever says yes
    is useless."""

    def pure_signal_score(row):
        return 1 if row["signal"] >= 50 else 0

    df = pd.DataFrame({
        "signal": [10, 30, 50, 70, 90, 10, 30, 50, 70, 90],
        "treatment": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
    })
    finding = ConstructionLeakageDetector().run(df, {
        "scoring_fn": pure_signal_score,
        "signal_col": "signal",
        "treatment_cols": ["treatment"],
    })
    assert finding.flagged is False
    assert finding.category == "construction_leakage"
