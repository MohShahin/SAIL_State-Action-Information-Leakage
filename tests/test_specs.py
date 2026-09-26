"""Expected values here come from the published Vincent et al. (1996) SOFA criteria, not from
whatever the code currently returns, and every threshold is tested on both sides.

Cardiovascular (score = the higher of the MAP score and the dose score):
    MAP < 70 mmHg                                     -> 1
    dopamine <= 5, or any dobutamine                  -> 2
    dopamine > 5, or epinephrine/norepinephrine <= 0.1 -> 3
    dopamine > 15, or epinephrine/norepinephrine > 0.1 -> 4
Respiratory (PaO2/FiO2 in mmHg):
    >= 400 -> 0 | 300-399 -> 1 | 200-299 -> 2
    100-199 -> 3 if ventilated else 2 | < 100 -> 4 if ventilated else 2
"""
import math

import pytest

from sail.specs.sofa_cardio import sofa_cardio_decomposed, sofa_cardio_row
from sail.specs.sofa_resp import sofa_resp_official, sofa_resp_official_row


def _cardio(map_val=80, dopamine=0, dobutamine=0, epi=0, norepi=0):
    return sofa_cardio_decomposed(map_val, dopamine, dobutamine, epi, norepi)


# --- cardiovascular -----------------------------------------------------------------------

@pytest.mark.parametrize("map_val, expected", [(69.9, 1), (40, 1), (70, 0), (90, 0)])
def test_cardio_map_score_boundary_is_strictly_below_70(map_val, expected):
    score_map, score_dose, total = _cardio(map_val=map_val)
    assert (score_map, score_dose, total) == (expected, 0, expected)


@pytest.mark.parametrize("kwargs, tier", [
    ({}, 0),                          # no support at all
    ({"dopamine": 0.5}, 2),           # dopamine in (0, 5]
    ({"dopamine": 5}, 2),             # boundary: 5 is still tier 2
    ({"dobutamine": 3}, 2),           # any dobutamine
    ({"dopamine": 5.01}, 3),          # just above 5
    ({"dopamine": 6}, 3),             # Theorem 1's own worked example
    ({"dopamine": 15}, 3),            # boundary: 15 is still tier 3
    ({"epi": 0.05}, 3),               # epinephrine in (0, 0.1]
    ({"epi": 0.1}, 3),                # boundary
    ({"norepi": 0.05}, 3),
    ({"norepi": 0.1}, 3),
    ({"dopamine": 15.01}, 4),         # just above 15
    ({"epi": 0.11}, 4),               # just above 0.1
    ({"epi": 0.2}, 4),
    ({"norepi": 0.11}, 4),
])
def test_cardio_dose_tiers(kwargs, tier):
    _, score_dose, total = _cardio(**kwargs)   # MAP normal, so total is the dose tier alone
    assert score_dose == tier
    assert total == tier


def test_cardio_total_is_the_higher_of_map_and_dose_score():
    assert _cardio(map_val=50, dopamine=3)[2] == 2           # dose 2 beats MAP 1
    assert _cardio(map_val=50)[2] == 1                       # MAP alone
    assert _cardio(map_val=95, epi=0.3)[2] == 4              # dose 4, MAP normal
    assert _cardio(map_val=50, dopamine=6) == (1, 3, 3)      # both contribute; max wins


def test_cardio_missing_values_are_treated_as_no_contribution():
    """NaN/None doses count as zero (no support recorded); a missing MAP is not 'low'."""
    nan = float("nan")
    assert _cardio(map_val=nan, dopamine=nan, dobutamine=nan, epi=nan, norepi=nan) == (0, 0, 0)
    assert _cardio(map_val=None, dopamine=None) == (0, 0, 0)
    assert _cardio(map_val=50, dopamine=nan)[2] == 1         # a NaN dose does not hide a low MAP


def test_cardio_row_wrapper_returns_the_total_and_tolerates_missing_keys():
    assert sofa_cardio_row({"map": 65, "dopamine": 6, "dobutamine": 0, "epi": 0, "norepi": 0}) == 3
    assert sofa_cardio_row({"map": 60}) == 1                 # no drug keys at all
    assert sofa_cardio_row({}) == 0


# --- respiratory --------------------------------------------------------------------------

@pytest.mark.parametrize("pf, expected", [
    (450, 0), (400, 0),               # >= 400
    (399.9, 1), (350, 1), (300, 1),   # 300-399
    (299.9, 2), (250, 2), (200, 2),   # 200-299
])
def test_resp_upper_tiers_do_not_depend_on_ventilation(pf, expected):
    assert sofa_resp_official(pf, False) == expected
    assert sofa_resp_official(pf, True) == expected


@pytest.mark.parametrize("pf, ventilated, expected", [
    (199.9, True, 3), (199.9, False, 2),
    (150, True, 3), (150, False, 2),      # Proposition 3's own worked case
    (100, True, 3), (100, False, 2),      # boundary: 100 is still the 100-199 band
    (99.9, True, 4), (99.9, False, 2),
    (60, True, 4), (60, False, 2),
])
def test_resp_lower_tiers_depend_on_ventilation(pf, ventilated, expected):
    assert sofa_resp_official(pf, ventilated) == expected


def test_resp_missing_pf_is_nan_whatever_the_ventilation_status():
    nan = float("nan")
    for vent in (True, False, nan, None):
        assert math.isnan(sofa_resp_official(nan, vent))
    assert math.isnan(sofa_resp_official(None, True))


def test_resp_missing_ventilation_status_counts_as_not_ventilated():
    assert sofa_resp_official(150, float("nan")) == 2
    assert sofa_resp_official(150, None) == 2
    assert sofa_resp_official(50, float("nan")) == 2


def test_resp_row_wrapper():
    assert sofa_resp_official_row({"pf_ratio": 60, "ventilated": True}) == 4
    assert sofa_resp_official_row({"pf_ratio": 60}) == 2     # no ventilation key
    assert math.isnan(sofa_resp_official_row({}))            # no pf_ratio key
