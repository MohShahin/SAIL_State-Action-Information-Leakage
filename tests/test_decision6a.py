"""Synthetic checks for the Decision 6(a) scoring-only row restriction."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")  # optional dependency: scripts/ are not part of the sail package

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exp_decision6a as d6  # noqa: E402


def _toy():
    # one stay, bins 0..9; offset 8 (bins mode) keeps state bins 0 and 1 only
    p0 = pd.DataFrame({"stay_id": 1, "bin": np.arange(10), "y": [0, 1] * 5, "pred": np.linspace(0, 1, 10)})
    p8 = pd.DataFrame({"stay_id": 1, "bin": [0, 1], "y": [1, 0], "pred": [0.3, 0.7]})
    return p0, p8


def test_on_at_tau_uses_start_le_tau_lt_end():
    rows = pd.DataFrame({"stay_id": [1, 1, 1, 1], "bin": [0, 1, 2, 3]})   # tau = 4, 8, 12, 16
    vaso = pd.DataFrame({"stay_id": [1, 1], "drug": ["norepi", "vasopressin"],
                         "time_bin_start": [8.0, 13.0], "time_bin_end": [12.0, 14.0]})
    f = d6.infusion_flags(vaso, rows)
    # tau=8: started exactly at tau -> on; tau=12: ended exactly at tau -> off; tau=16: nothing
    assert f["on_at_tau"].tolist() == [False, True, False, False]
    # L1 = active in [tau, tau+4): tau=4 sees the start at 8? no (8 is not < 8); tau=8 yes; tau=12 yes (13-14)
    assert f["L1"].tolist() == [False, True, True, False]


def test_common_rows_same_state_rows_at_both_offsets_and_preds_untouched():
    p0, p8 = _toy()
    flags = pd.DataFrame({"stay_id": 1, "bin": np.arange(10), "on_at_tau": [True, False] + [False] * 8})
    a, b = d6.restrict_off_at_tau(p0, p8, flags, common=True)
    assert a["bin"].tolist() == b["bin"].tolist() == [1]
    assert a["pred"].tolist() == [p0.loc[1, "pred"]] and b["pred"].tolist() == [0.7]
    assert a["y"].tolist() == [1] and b["y"].tolist() == [0]


def test_own_rows_filter_each_offset_separately():
    p0, p8 = _toy()
    flags = pd.DataFrame({"stay_id": 1, "bin": np.arange(10), "on_at_tau": [True] + [False] * 8 + [True]})
    a, b = d6.restrict_off_at_tau(p0, p8, flags, common=False)
    assert a["bin"].tolist() == list(range(1, 9))
    assert b["bin"].tolist() == [1]


def test_missing_indicator_raises():
    p0, p8 = _toy()
    flags = pd.DataFrame({"stay_id": 1, "bin": np.arange(9), "on_at_tau": False})
    with pytest.raises(ValueError):
        d6.restrict_off_at_tau(p0, p8, flags)


def test_restriction_feeds_paired_bootstrap():
    rng = np.random.RandomState(0)
    rows = []
    for s in range(60):
        for b in range(12):
            rows.append({"stay_id": s, "bin": b, "y": int(rng.rand() < 0.4), "pred": rng.rand()})
    p0 = pd.DataFrame(rows)
    p8 = p0[p0["bin"] < 4].copy()
    p8["y"] = rng.randint(0, 2, len(p8))
    flags = p0[["stay_id", "bin"]].assign(on_at_tau=rng.rand(len(p0)) < 0.5)
    a, b = d6.restrict_off_at_tau(p0, p8, flags, common=True)
    r = d6.paired_cluster_bootstrap(a, b, n_boot=50, seed=1, restrict=True)
    off = flags.loc[~flags["on_at_tau"] & (flags["bin"] < 4)]
    assert r["n_rows_a"] == r["n_rows_b"] == len(off)
