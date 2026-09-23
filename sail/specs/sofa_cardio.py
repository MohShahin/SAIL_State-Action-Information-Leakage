"""
Cardiovascular SOFA scoring, ported directly from this project's own verified
notebook implementation (``notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb``,
the ``sofa_cardio_decomposed`` function) -- the exact function Theorem 1 is a
proof about. Unchanged from the notebook other than the row-wrapper below.
"""

import pandas as pd


def sofa_cardio_decomposed(map_val, dopamine, dobutamine, epi, norepi):
    """Vincent et al. (1996) cardiovascular criterion.

    Returns (score_from_map, score_from_dose, total).
    """
    dopamine = 0 if pd.isna(dopamine) else dopamine
    dobutamine = 0 if pd.isna(dobutamine) else dobutamine
    epi = 0 if pd.isna(epi) else epi
    norepi = 0 if pd.isna(norepi) else norepi
    score_map = 1 if (not pd.isna(map_val) and map_val < 70) else 0
    score_dose = 0
    if dopamine > 15 or epi > 0.1 or norepi > 0.1:
        score_dose = 4
    elif dopamine > 5 or (0 < epi <= 0.1) or (0 < norepi <= 0.1):
        score_dose = 3
    elif (0 < dopamine <= 5) or dobutamine > 0:
        score_dose = 2
    return score_map, score_dose, max(score_map, score_dose)


def sofa_cardio_row(row):
    """Row-apply wrapper returning just the final score -- for use as a
    ``ConstructionLeakageDetector`` ``scoring_fn``."""
    _, _, total = sofa_cardio_decomposed(
        row.get("map"), row.get("dopamine"), row.get("dobutamine"),
        row.get("epi"), row.get("norepi"),
    )
    return total
