import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")  # optional dependency: scripts/ are not part of the sail package

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exp_label_alignment as la  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402


def _rows(stay, bins):
    return pd.DataFrame({"stay_id": [stay] * len(bins), "bin": list(bins)})


def test_labels_on_hand_built_infusions():
    # stay 1: norepi 2h..6h split by a rate change at 5h (two MIMIC rows), then a new
    # vasopressin episode 13h..14h. Bins 0..3 have tau = 4, 8, 12, 16.
    v = pd.DataFrame({"stay_id": [1, 1, 1], "drug": ["norepi", "norepi", "vasopressin"],
                      "time_bin_start": [2.0, 5.0, 13.0], "time_bin_end": [5.0, 6.0, 14.0]})
    lab = la.build_labels(v, _rows(1, [0, 1, 2, 3]))
    # L0: active in [tau-4, tau)
    assert lab["L0"].tolist() == [True, True, False, True]
    # L1: active in [tau, tau+4)
    assert lab["L1"].tolist() == [True, False, True, False]
    # on at tau: start <= tau < end
    assert lab["on_at_tau"].tolist() == [True, False, False, False]
    # L4: bin 0 is positive only through the 5h rate-change row, which continues the 2h episode
    assert lab["L4"].tolist() == [False, False, True, False]
    assert lab["L1_raw_row_started_before_tau"].tolist() == [True, False, False, False]
    assert lab["L1_raw_row_starts_in_window"].tolist() == [True, False, True, False]   # the rate-change row
    assert lab["L1_episode_started_before_tau"].tolist() == [True, False, False, False]
    assert lab["L1_dose_scored_straddles_tau"].tolist() == [True, False, False, False]
    # L3: running at tau + 4 (8, 12, 16, 20)
    assert lab["L3"].tolist() == [False, False, False, False]


def test_continuation_and_added_drug():
    # norepi running 1h..30h; vasopressin added at 9h. tau = 4, 8, 12.
    v = pd.DataFrame({"stay_id": [7, 7], "drug": ["norepi", "vasopressin"],
                      "time_bin_start": [1.0, 9.0], "time_bin_end": [30.0, 20.0]})
    lab = la.build_labels(v, _rows(7, [0, 1, 2]))
    assert lab["L1"].all() and lab["L3"].all() and lab["on_at_tau"].all()
    assert lab["L4"].tolist() == [False, True, False]            # a new drug starts in [8, 12)
    assert lab["L4_any_drug"].tolist() == [False, False, False]  # but therapy was already running
    s = la.overlap_summary(lab)
    assert s["positive_only_because_of_an_episode_started_before_tau (L1=1, L4=0)"]["rows"] == 2


def test_stays_without_infusions_are_all_negative():
    v = pd.DataFrame({"stay_id": [1], "drug": ["epi"], "time_bin_start": [0.0], "time_bin_end": [1.0]})
    lab = la.build_labels(v, pd.concat([_rows(2, [0, 1]), _rows(1, [0])], ignore_index=True))
    assert lab["stay_id"].tolist() == [2, 2, 1]
    assert lab["L1"].tolist() == [False, False, False] and lab["L0"].tolist() == [False, False, True]


def test_weighted_auc_equals_concatenated_resample():
    rng = np.random.RandomState(0)
    groups = np.repeat(np.arange(30), 7)
    y = rng.binomial(1, 0.4, len(groups))
    s = np.round(rng.rand(len(groups)) + 0.5 * y, 1)    # rounded to force ties
    draw = rng.choice(30, size=30, replace=True)
    idx = np.concatenate([np.where(groups == g)[0] for g in draw])
    w = np.bincount(draw, minlength=30).astype(float)[groups]
    assert la.WeightedAUC(y, s)(w) == pytest.approx(roc_auc_score(y[idx], s[idx]), abs=1e-12)


def test_paired_bootstrap_shares_draws():
    rng = np.random.RandomState(1)
    groups = np.repeat(np.arange(20), 5)
    y = rng.binomial(1, 0.5, 100); s = rng.rand(100)
    cells = {"a": ("all", y, s), "b": ("all", y, s)}
    out = la.paired_bootstrap(cells, {"all": groups}, 20, n_boot=50, seed=42)
    assert np.allclose(out["a"], out["b"])
