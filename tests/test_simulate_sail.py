"""Unit tests for the synthetic ground-truth simulator (scripts/simulate_sail.py). Small and
deterministic; exploratory work, not part of the pre-registered H3 test."""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import h3_paired_bootstrap as h3  # noqa: E402
import simulate_sail as S  # noqa: E402

RPS = {str(k): (1.0 if k in (12, 17) else 0.0) for k in range(1, 18)}


def _sim(branch="on", n=400, seed=3, **kw):
    p = S.SimParams(n_stays=n, branch=branch, rows_per_stay=RPS, **kw)
    return S.simulate(p, seed)


def test_run_lengths():
    assert S.run_lengths([0, 1, 1, 0, 1, 0, 0, 1, 1, 1]) == [(1, 2), (4, 1), (7, 3)]
    assert S.run_lengths([0, 0]) == []
    assert S.run_lengths([1, 1, 1]) == [(0, 3)]


def test_deterministic_given_seed():
    a, *_ = _sim(seed=11)
    b, *_ = _sim(seed=11)
    c, *_ = _sim(seed=12)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_frame_layout_and_rows():
    df, occ, on, sev = _sim()
    assert list(df.columns[:2]) == ["stay_id", "bin"]
    assert set(S.FEATURES_A) <= set(df.columns) and "action_next" in df.columns
    assert set(df.groupby("stay_id").size().unique()) <= {12, 17}
    assert df["bin"].max() <= S.N_BINS - 2          # bin 17 has no next action
    assert occ.shape == (400, S.N_BINS) and on.shape == occ.shape


def test_label_is_next_bin_occupancy_and_on_implies_label():
    df, occ, on, _ = _sim()
    s, b = df["stay_id"].values, df["bin"].values
    assert np.array_equal(df["action_next"].values, occ[s, b + 1].astype(int))
    assert (df.loc[df.on_tau == 1, "action_next"] == 1).all()
    # on at tau means the run active in bin t continues into bin t+1 (bins 0..16; 17 has no successor)
    assert np.all(~on[:, :-1] | (occ[:, :-1] & occ[:, 1:]))


def test_treatment_branch_switches_the_cardio_score():
    on_df, occ, _, _ = _sim("on")
    off_df, *_ = _sim("off")
    # same seed: the physiology, policy and labels are identical across "on" and "off"
    assert np.array_equal(on_df["action_next"].values, off_df["action_next"].values)
    np.testing.assert_allclose(on_df["mbp"].values, off_df["mbp"].values)
    assert np.array_equal(off_df["sofa_cardio"].values, (off_df["mbp"].values < 70).astype(float))
    running = occ[on_df["stay_id"].values, on_df["bin"].values]
    assert (on_df.loc[running, "sofa_cardio"] >= 1).mean() > 0.5          # dose-set scores while running
    assert (on_df.loc[~running, "sofa_cardio"] == (on_df.loc[~running, "mbp"] < 70)).all()
    tot = on_df[["sofa_resp", "sofa_coag", "sofa_renal", "sofa_cardio"]].sum(axis=1)
    assert np.allclose(tot, on_df["sofa_total"])


def test_off_pure_hides_the_drug():
    df, occ, _, sev = _sim("off_pure", scored_fraction=1.0)
    p = S.SimParams()
    s, b = df["stay_id"].values, df["bin"].values
    resid = df["mbp"].values - (p.map0 - p.map_slope * sev[s, b])
    running = occ[s, b]
    assert abs(resid[running].mean() - resid[~running].mean()) < 1.5   # no drug raise in MAP


def test_persistence_lengthens_runs():
    means = []
    for mult in (0.5, 1.0, 2.0):
        _, occ, _, _ = _sim(n=1500, persistence=mult)
        means.append(np.mean([L for row in occ for _, L in S.run_lengths(row)]))
    assert means[0] < means[1] < means[2]


def test_frozen_h3_functions_accept_the_frame():
    df, *_ = _sim(n=200)
    rows = h3.offset_frames(df, S.FEATURES_E, (0, 8), "rows")
    bins = h3.offset_frames(df, S.FEATURES_E, (0, 8), "bins")
    # contiguous bins, so the two offset constructions coincide
    for o in (0, 8):
        pd.testing.assert_frame_equal(rows[o].sort_values(["stay_id", "bin"]).reset_index(drop=True),
                                      bins[o].sort_values(["stay_id", "bin"]).reset_index(drop=True))
    r = S.evaluate(df, n_boot=20)
    for v in ("A", "E", "indicator"):
        assert isinstance(r[v]["restricted"]["prediction_A_supported"], bool)
        assert 0.0 <= r[v]["restricted"]["auroc_a"] <= 1.0


def test_marginals_keys():
    df, occ, _, _ = _sim(n=300)
    m = S.marginals(df, occ)
    assert m["label_rate_given_on"] == 1.0
    assert 0 < m["frac_on_at_tau"] < m["next_action_prevalence"] < 1
    assert sum(m["run_length_hist_all"].values()) > 0
