"""Synthetic checks for scripts/paired_cis.py (exploratory, not pre-registered)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")  # optional dependency: scripts/ are not part of the sail package
from sklearn.metrics import roc_auc_score  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import paired_cis as pc  # noqa: E402


def test_weighted_auc_equals_concatenated_resample():
    rng = np.random.RandomState(0)
    n_stay = 60
    groups = np.repeat(np.arange(n_stay), rng.randint(1, 8, n_stay))
    y = (rng.rand(len(groups)) < 0.4).astype(int)
    p = np.round(rng.rand(len(groups)) + 0.3 * y, 2)  # rounding forces ties
    prep = pc.auc_prep(y, p)
    assert pc.weighted_auc(prep, np.ones(len(y))) == pytest.approx(roc_auc_score(y, p), abs=1e-12)
    counts = pc.draw_counts(n_stay, 5, 42)
    rng2 = np.random.RandomState(42)
    for b in range(5):
        s = rng2.choice(np.arange(n_stay), size=n_stay, replace=True)   # notebook-style draw
        idx = np.concatenate([np.where(groups == g)[0] for g in s])
        assert np.array_equal(np.bincount(s, minlength=n_stay), counts[b])
        assert pc.weighted_auc(prep, counts[b][groups]) == pytest.approx(roc_auc_score(y[idx], p[idx]), abs=1e-12)


def test_holm_and_boot_p():
    adj = pc.holm([0.01, 0.04, 0.03, 0.5])
    assert adj == pytest.approx([0.04, 0.09, 0.09, 0.5])
    assert pc.boot_p(np.ones(1999)) == pytest.approx(2 / 2000)
    assert pc.boot_p(np.r_[np.ones(1000), -np.ones(1000)]) == 1.0


def test_mi_per_column_matches_matrix_fit():
    from sklearn.metrics import mutual_info_score
    from sklearn.preprocessing import KBinsDiscretizer
    rng = np.random.RandomState(1)
    X = np.c_[rng.randn(500), rng.randint(0, 3, 500), rng.rand(500)]
    y = (rng.rand(500) < 0.3).astype(int)
    Xd = KBinsDiscretizer(n_bins=10, encode="ordinal", strategy="quantile").fit_transform(X)
    for j in range(3):
        assert pc.mi_column(X[:, j], y) == pytest.approx(mutual_info_score(Xd[:, j], y), abs=1e-12)


def test_analyse_runs_and_pairs_share_draws():
    rng = np.random.RandomState(2)
    stays = np.repeat(np.arange(80), 4)
    pa = pd.DataFrame({"stay_id": stays, "bin": np.tile(np.arange(4), 80), "y": rng.randint(0, 2, len(stays))})
    pm = pd.DataFrame({"stay_id": np.arange(80), "y": rng.randint(0, 2, 80)})
    for df in (pa, pm):
        for v in pc.VARIANTS:
            for p in pc.PROBES:
                df[f"pred_{v}_{p}"] = rng.rand(len(df)) + 0.2 * df["y"]
    res = pc.analyse(pa, pm, n_boot=50, seed=42)
    same = [r for r in res["action_pairs"] if r["pair"] == "A-E" and r["probe"] == "gb"][0]
    assert same["delta"] == pytest.approx(res["action_auroc"]["A_full|gb"]["auroc"]
                                          - res["action_auroc"]["E_physiology_only|gb"]["auroc"])
    assert sum("p_holm15" in r for r in res["action_pairs"]) == 15
    assert "| ratio |" in pc.markdown(res)
