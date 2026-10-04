import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")  # optional dependency: scripts/ are not part of the sail package

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exp8_validation as v  # noqa: E402

DRUGS = ["norepi", "epi", "dopamine", "dobutamine"]


def test_known_at_tau_intervals_ignore_future_starts():
    vd = pd.DataFrame({"stay_id": [1, 1, 1], "drug": ["norepi", "norepi", "epi"],
                       "start_hours_from_admit": [2.0, 10.0, 3.0], "end_hours_from_admit": [6.0, 14.0, 20.0]})
    assert v.known_at_tau_intervals(vd, DRUGS, tau=8.0, stay_id=1) == [(2.0, 20.0)]   # 10h start not yet known
    assert v.f1_at_tau(vd, DRUGS, 1, 8.0) == 6.0                                        # merged 2..20 running at 8
    assert v.f1_at_tau(vd, DRUGS, 1, 1.0) == 0.0
    vd2 = pd.DataFrame({"stay_id": [1], "drug": ["norepi"], "start_hours_from_admit": [2.0], "end_hours_from_admit": [8.0]})
    assert v.f1_at_tau(vd2, DRUGS, 1, 8.0) == 0.0                                       # ended exactly at tau: not running


def test_strictly_before_matches_notebook_definition():
    vd = pd.DataFrame({"stay_id": [1, 2], "drug": ["norepi", "epi"],
                       "start_hours_from_admit": [2.0, 5.0], "end_hours_from_admit": [9.0, 7.0]})
    edges = pd.DataFrame({"stay_id": [1, 1, 2, 2], "bin": [0, 1, 0, 1], "decision_time": [4.0, 8.0, 4.0, 8.0]})
    f1_nb = np.array([2.0, 6.0, 0.0, 0.0]); f2_nb = np.array([2.0, 6.0, 4.0, 1.0])
    changes = {1: [(2.0, 3)], 2: [(5.0, 3), (7.0, 0)]}
    r = v.check_strictly_before(vd, DRUGS, edges, f1_nb, f2_nb, changes, sample=None)
    assert r["strictly_before_decision_time"] and r["rows_checked"] == 4


def test_indicator_ablation_runs():
    rng = np.random.RandomState(0); n = 400
    groups = np.repeat(np.arange(40), 10); y = rng.binomial(1, 0.4, n)
    f1 = np.where(y == 1, rng.rand(n) * 10, 0.0) * (rng.rand(n) < 0.8); f2 = rng.rand(n) * 5
    X_D = rng.randn(n, 3)
    def cv_predict(X, yy, g, probe_fn, n_splits=5):
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GroupKFold
        p = np.zeros(len(yy))
        for tr, va in GroupKFold(n_splits).split(X, yy, g):
            p[va] = LogisticRegression(max_iter=500).fit(X[tr], yy[tr]).predict_proba(X[va])[:, 1]
        return p
    def boot(yy, p, g, metric, n_boot=50):
        return 0.0, 1.0
    from sklearn.linear_model import LogisticRegression
    r = v.indicator_ablation(X_D, f1, f2, y, groups, lambda: LogisticRegression(max_iter=500), cv_predict, boot, n_boot=10)
    assert r["D_plus_on_vasopressor_indicator"]["auroc"] > r["D"]["auroc"]
    assert 0 <= r["prevalence_on_vasopressor_at_tau"] <= 1


def test_indicator_and_off_rows_shapes():
    rng = np.random.RandomState(3); n = 300
    groups = np.repeat(np.arange(30), 10); y = rng.binomial(1, 0.4, n)
    f1 = np.where(rng.rand(n) < 0.3, 5.0, 0.0); y[f1 > 0] = 1          # on-at-tau rows are label 1 by construction
    X = rng.randn(n, 2)
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    def cv_predict(Xm, yy, g, probe_fn, n_splits=5):
        p = np.zeros(len(yy))
        for tr, va in GroupKFold(n_splits).split(Xm, yy, g):
            p[va] = LogisticRegression(max_iter=500).fit(Xm[tr], yy[tr]).predict_proba(Xm[va])[:, 1]
        return p
    r = v.indicator_and_off_rows(f1, y, groups, {"A": X}, {"logreg": lambda: LogisticRegression(max_iter=500)}, cv_predict, lambda *a, **k: (0.0, 1.0), n_boot=5)
    assert r["n_rows_on"] + r["n_rows_off"] == n and r["label_rate_on"] == 1.0
    assert 0.5 < r["indicator_alone_auroc"] <= 1.0 and "A" in r["off_rows"]


def test_on_at_tau_all_drugs_counts_every_label_drug():
    vb = pd.DataFrame({"stay_id": [1, 2], "drug": ["phenylephrine", "norepi"],
                       "time_bin_start": [2.0, 10.0], "time_bin_end": [9.0, 12.0]})
    edges = pd.DataFrame({"stay_id": [1, 1, 2], "bin": [0, 1, 0], "decision_time": [4.0, 12.0, 4.0]})
    assert v.on_at_tau_all_drugs(vb, edges).tolist() == [True, False, False]
