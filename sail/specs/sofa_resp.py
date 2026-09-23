"""
Respiratory SOFA scoring per the OFFICIAL Vincent et al. (1996) rule,
including the ventilatory-support (V) conditional on its two highest tiers --
this is the formula Proposition 3 is a proof about (``FORMAL_ANALYSIS.md``
Section 4.5), NOT this project's own simplified ``sofa_resp`` (which takes PF
alone and does not implement the V conditional -- deliberately left unchanged
elsewhere in the project; see the note in Section 4.5 before touching that
function for anything else).
"""

import pandas as pd


def sofa_resp_official(pf_ratio, ventilated):
    """Vincent et al. (1996) respiratory criterion, official V-conditional form."""
    if pd.isna(pf_ratio):
        return float("nan")
    v = bool(ventilated) if not pd.isna(ventilated) else False
    if pf_ratio >= 400:
        return 0
    if pf_ratio >= 300:
        return 1
    if pf_ratio >= 200:
        return 2
    if pf_ratio >= 100:
        return 3 if v else 2
    return 4 if v else 2


def sofa_resp_official_row(row):
    """Row-apply wrapper -- for use as a ``ConstructionLeakageDetector``
    ``scoring_fn``."""
    return sofa_resp_official(row.get("pf_ratio"), row.get("ventilated"))
