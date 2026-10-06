"""Exploratory, not pre-registered: label construction for scripts/exp_dose_decisions.py."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exp_dose_decisions as dd  # noqa: E402


def _dose(rows):
    return pd.DataFrame(rows, columns=["stay_id", "drug", "rate", "rateuom", "start_hours_from_admit", "end_hours_from_admit"])


DOSE = _dose([
    (1, "norepi", 0.05, "mcg/kg/min", 1.0, 10.0),
    (1, "norepi", 0.20, "mcg/kg/min", 10.0, 15.0),
    (2, "vasopressin", 2.4, "units/hour", 0.0, 20.0),   # 0.04 U/min = 0.1 NE-equivalent
    (2, "norepi", 0.30, "mcg/kg/min", 0.0, 6.0),
])


def test_tier_vec_matches_notebook_scoring():
    rng = np.random.RandomState(0)
    a = rng.choice([0, 0.03, 0.1, 0.11, 3, 5, 6, 15, 16], size=(500, 4))
    vec = dd.tier_vec(a[:, 0], a[:, 1], a[:, 2] / 50, a[:, 3] / 50)
    ref = [dd.score_dose_tier(r[0], r[1], r[2] / 50, r[3] / 50) for r in a]
    assert list(vec) == ref


def test_window_overlap_boundaries():
    d = _dose([(1, "norepi", 0.05, "mcg/kg/min", 4.0, 8.0)])
    w = dd.window_bins(d, "rate")
    assert sorted(w.index.get_level_values("bin")) == [1]            # [4, 8) only: start < w_end, end > w_start
    p = dd.instant_points(d, "rate")
    assert sorted(p.index.get_level_values("k")) == [1]              # running at 4h, not at 8h


def test_nee_conversion():
    r = dd.nee_rate(DOSE)
    assert np.allclose(r, [0.05, 0.20, 0.1, 0.30])


def test_labels():
    rows = pd.DataFrame({"stay_id": [1, 1, 1, 1, 2, 2], "bin": [0, 1, 2, 3, 0, 1]})
    lab, diag = dd.build_labels(DOSE, rows, nee_cuts=np.array([0.05, 0.2, 0.35]))
    lab = lab.set_index(["stay_id", "bin"])
    assert lab["on_tau"].tolist() == [True, True, True, False, True, True]
    # stay 1, bin 0: same tier, still on
    assert lab.loc[(1, 0), ["STOP", "UP_tierW", "DOWN_tierW", "UP_tierP"]].tolist() == [0, 0, 0, 0]
    # stay 1, bin 1: 0.05 -> 0.2 in the next bin (window) and at tau+4 (instant)
    assert lab.loc[(1, 1), ["UP_tierW", "UP_tierP", "STOP"]].tolist() == [1, 1, 0]
    # stay 1, bin 2: nothing running at 16h
    assert lab.loc[(1, 2), ["STOP", "UP_tierW", "DOWN_tierW"]].tolist() == [1, 0, 0]
    assert np.isnan(lab.loc[(1, 3), "STOP"])
    # stay 2, bin 0: norepi stops at 6h; window max of next bin still includes it, the instant does not
    assert lab.loc[(2, 0), ["DOWN_tierW", "DOWN_tierP", "STOP"]].tolist() == [0, 1, 0]
    # stay 2, bin 1: window tier 4 -> 0 (vasopressin only), NEE 0.4 -> 0.1
    assert lab.loc[(2, 1), ["DOWN_tierW", "DOWN_NEE", "STOP"]].tolist() == [1, 1, 0]


def test_at_risk_drops_impossible_moves():
    rows = pd.DataFrame({"stay_id": [1, 1, 2, 2], "bin": [0, 1, 0, 1]})
    lab, _ = dd.build_labels(DOSE, rows, nee_cuts=np.array([0.05, 0.2, 0.35]))
    r = dd.apply_at_risk(lab, ["UP_tierW", "DOWN_tierW"]).set_index(["stay_id", "bin"])
    assert np.isnan(r.loc[(2, 0), "UP_tierW"])          # already at tier 4: cannot go up
    assert r.loc[(2, 1), "DOWN_tierW"] == 1
    lab["row"] = np.arange(len(lab))
    fr = dd.offset_frame(dd.apply_at_risk(lab, ["UP_tierW"]), "UP_tierW", 0)
    assert len(fr) == 2                                  # stay 2's two tier-4 rows dropped
