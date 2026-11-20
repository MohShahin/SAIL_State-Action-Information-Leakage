"""Synthetic checks for the exploratory persistence control (scripts/exp_persistence.py):
the fast paired bootstrap must reproduce h3_paired_bootstrap.paired_cluster_bootstrap exactly,
and the per-bin features must follow the notebook's action label rule."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exp_persistence as ep  # noqa: E402
import h3_paired_bootstrap as h3  # noqa: E402


def _preds(n_stays=60, seed=0, ties=False):
    rng = np.random.RandomState(seed)
    rows = []
    for s in range(n_stays):
        for b in sorted(rng.choice(18, size=rng.randint(3, 12), replace=False)):
            y = int(rng.rand() < 0.4)
            p = rng.rand() + 0.6 * y
            rows.append({"stay_id": 1000 + s, "bin": b, "y": y, "pred": round(p, 1) if ties else p})
    return pd.DataFrame(rows)


@pytest.mark.parametrize("restrict", [True, False])
@pytest.mark.parametrize("ties", [False, True])
def test_fast_bootstrap_matches_h3(restrict, ties):
    a = _preds(seed=1, ties=ties)
    b = _preds(seed=2, ties=ties)
    b = b[b["bin"] < 14]                                  # offset-like: fewer rows at the far offset
    ref = h3.paired_cluster_bootstrap(a, b, n_boot=200, seed=42, restrict=restrict)
    keys_a, keys_b = a[["stay_id", "bin"]], b[["stay_id", "bin"]]
    if restrict:
        rows = keys_a.merge(keys_b, on=["stay_id", "bin"])
        u = ep.Universe("common", rows["stay_id"].values, {0: rows, 8: rows}, n_boot=200, seed=42)
    else:
        pats = np.union1d(a["stay_id"].unique(), b["stay_id"].unique())
        u = ep.Universe("own", pats, {0: keys_a, 8: keys_b}, n_boot=200, seed=42)
    u.add("x", 0, a)
    u.add("x", 8, b)
    d = u.diff("x", 0, "x", 8)
    assert d["auroc_a"] == pytest.approx(ref["auroc_a"], abs=1e-12)
    assert d["auroc_b"] == pytest.approx(ref["auroc_b"], abs=1e-12)
    assert d["ci"][0] == pytest.approx(ref["delta_ci_lo"], abs=1e-10)
    assert d["ci"][1] == pytest.approx(ref["delta_ci_hi"], abs=1e-10)
    assert d["n_boot_used"] == ref["n_boot_used"]
    assert u.point("x", 0)["ci"] == pytest.approx(ref["auroc_a_ci"], abs=1e-10)


def test_bin_features_follow_label_rule():
    # stay 1: norepi 0.05 from 3h to 9.5h, vasopressin from 12h to 12.5h
    # stay 2: dopamine 20 from 8h to 16h (ends exactly at a decision time)
    v = pd.DataFrame({"stay_id": [1, 1, 2], "drug": ["norepi", "vasopressin", "dopamine"],
                      "rate": [0.05, 0.03, 20.0],
                      "start_hours_from_admit": [3.0, 12.0, 8.0], "end_hours_from_admit": [9.5, 12.5, 16.0]})
    f = ep.bin_features(v).set_index(["stay_id", "bin"])
    # stay 1: active in bins 0 [0,4), 1 [4,8), 2 [8,12), 3 [12,16) (vasopressin)
    assert [int(f.loc[(1, t), "prev_action"]) for t in range(4)] == [1, 1, 1, 1]
    # running at tau = 4, 8 (norepi) and at 12 (vasopressin starts exactly at tau: start <= tau < end);
    # not at 16 (vasopressin ended 12.5)
    assert [int(f.loc[(1, t), "on_at_tau"]) for t in range(4)] == [1, 1, 1, 0]
    assert [int(f.loc[(1, t), "prev_tier"]) for t in range(4)] == [3, 3, 3, 0]   # vasopressin is not dose-scored
    # stay 2: active in bins 2, 3; on at tau = 12 only (ends at 16, so not running at 16)
    assert [int(f.loc[(2, t), "prev_action"]) for t in (2, 3)] == [1, 1]
    assert [int(f.loc[(2, t), "on_at_tau"]) for t in (2, 3)] == [1, 0]
    assert [int(f.loc[(2, t), "prev_tier"]) for t in (2, 3)] == [4, 4]
    # starting exactly at tau = 8 (bin 1's decision time): on at tau, but not active in bin 1 itself
    assert (int(f.loc[(2, 1), "prev_action"]), int(f.loc[(2, 1), "on_at_tau"])) == (0, 1)
    assert (2, 4) not in f.index and (2, 0) not in f.index


def test_augment_state_checks_label_rule():
    v = pd.DataFrame({"stay_id": [1], "drug": ["epi"], "rate": [0.2],
                      "start_hours_from_admit": [5.0], "end_hours_from_admit": [11.0]})
    feats = ep.bin_features(v)
    # notebook: action_next at bin t = any infusion active in bin t+1
    st = pd.DataFrame({"stay_id": [1] * 4, "bin": [0, 1, 2, 3], "action_next": [1, 1, 0, 0], "x": [0.0] * 4})
    s, chk = ep.augment_state(st, feats)
    assert chk["label_vs_prev_action_next_bin_mismatches"] == 0
    assert s["prev_action"].tolist() == [0, 1, 1, 0]
    assert s["on_at_tau"].tolist() == [0, 1, 0, 0]
    assert s["prev_tier4"].tolist() == [0, 1, 1, 0]
    bad = st.assign(action_next=[0, 1, 0, 0])
    assert ep.augment_state(bad, feats)[1]["label_vs_prev_action_next_bin_mismatches"] == 1
