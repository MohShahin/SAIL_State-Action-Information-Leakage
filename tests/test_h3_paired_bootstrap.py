"""Synthetic checks for the section 7 paired cluster bootstrap and the offset construction."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")  # optional dependency: scripts/ are not part of the sail package

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import h3_paired_bootstrap as h3  # noqa: E402


def _state(n_stays=40, n_bins=18, seed=0):
    rng = np.random.RandomState(seed)
    rows = []
    for s in range(n_stays):
        bins = sorted(rng.choice(n_bins, size=rng.randint(6, n_bins + 1), replace=False))
        for b in bins:
            rows.append({"stay_id": s, "bin": b, "f1": rng.randn(), "f2": rng.randn(),
                         "action_next": int(rng.rand() < 0.4)})
    return pd.DataFrame(rows)


def test_offset_rows_matches_notebook_shift():
    st = _state()
    fr = h3.offset_frames(st, ["f1", "f2"], offsets=(0, 2), offset_mode="rows")
    base = st.sort_values(["stay_id", "bin"]).reset_index(drop=True)
    expect = base.groupby("stay_id")["action_next"].shift(-2).dropna().astype(int).values
    assert np.array_equal(fr[2]["y"].values, expect)
    assert len(fr[0]) == len(st)


def test_offset_bins_uses_bin_index_not_row_position():
    st = pd.DataFrame({"stay_id": [1, 1, 1], "bin": [0, 1, 5], "f1": [0.0, 0.0, 0.0],
                       "action_next": [0, 1, 1]})
    rows = h3.offset_frames(st, ["f1"], offsets=(1,), offset_mode="rows")[1]
    bins = h3.offset_frames(st, ["f1"], offsets=(1,), offset_mode="bins")[1]
    assert len(rows) == 2          # row shift pairs bin 1 with bin 5
    assert len(bins) == 1          # bin shift finds only bin 0 -> bin 1


def test_paired_bootstrap_recovers_known_delta():
    rng = np.random.RandomState(1)
    n_pat, n_per = 300, 10
    stay = np.repeat(np.arange(n_pat), n_per); b = np.tile(np.arange(n_per), n_pat)
    y = rng.binomial(1, 0.4, size=len(stay))
    strong = np.clip(y * 2.0 + rng.randn(len(stay)) * 0.8, -5, 5)   # high AUROC
    weak = np.clip(y * 0.3 + rng.randn(len(stay)), -5, 5)           # low AUROC
    pa = pd.DataFrame({"stay_id": stay, "bin": b, "y": y, "pred": strong})
    pb = pd.DataFrame({"stay_id": stay, "bin": b, "y": y, "pred": weak})
    r = h3.paired_cluster_bootstrap(pa, pb, n_boot=200, seed=0, restrict=True)
    assert r["n_rows_a"] == r["n_rows_b"] == len(stay)
    assert r["delta_ci_lo"] <= r["delta"] <= r["delta_ci_hi"]
    assert r["delta"] > 0.2 and r["prediction_A_supported"]
    same = h3.paired_cluster_bootstrap(pa, pa, n_boot=100, seed=0, restrict=True)
    assert abs(same["delta"]) < 1e-12 and same["delta_ci_lo"] <= 0 <= same["delta_ci_hi"]
    assert not same["prediction_A_supported"]


def test_unrestricted_keeps_each_offsets_rows():
    rng = np.random.RandomState(2)
    pa = pd.DataFrame({"stay_id": np.repeat(np.arange(50), 8), "bin": np.tile(np.arange(8), 50)})
    pa["y"] = rng.binomial(1, 0.5, len(pa)); pa["pred"] = pa["y"] + rng.randn(len(pa))
    pb = pa[pa["bin"] < 4].copy(); pb["pred"] = rng.randn(len(pb))
    r = h3.paired_cluster_bootstrap(pa, pb, n_boot=50, seed=0, restrict=False)
    assert r["n_rows_a"] == 400 and r["n_rows_b"] == 200 and r["n_patients"] == 50
    rr = h3.paired_cluster_bootstrap(pa, pb, n_boot=50, seed=0, restrict=True)
    assert rr["n_rows_a"] == rr["n_rows_b"] == 200
