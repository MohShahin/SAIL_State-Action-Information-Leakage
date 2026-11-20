"""Synthetic checks for scripts/exp_scaler_within_fold.py: the scaler sees training rows only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")  # optional dependency: scripts/ are not part of the sail package

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exp_scaler_within_fold as esw  # noqa: E402


class _SpyProbe:
    """Records the matrices it is fit on and scored on; predicts a constant-free score."""

    seen = []

    def fit(self, X, y):
        _SpyProbe.seen.append(("fit", X.copy()))
        return self

    def predict_proba(self, X):
        _SpyProbe.seen.append(("predict", X.copy()))
        s = 1.0 / (1.0 + np.exp(-X[:, 0]))
        return np.column_stack([1 - s, s])


def _data(seed=0, n_groups=50, per=8):
    rng = np.random.RandomState(seed)
    g = np.repeat(np.arange(n_groups), per)
    # group-specific location so held-out folds have a different mean than the training rows
    X = rng.randn(len(g), 3) + (g[:, None] % 7) * 3.0
    y = (rng.rand(len(g)) < 0.4).astype(int)
    return X, y, g


def test_scaler_fit_on_train_rows_only():
    X, y, g = _data()
    log = []
    esw.cv_predict_within_fold(X, y, g, esw.logreg, n_splits=5, _scaler_log=log)
    assert len(log) == 5
    for tr, va, sc in log:
        assert set(tr).isdisjoint(va)
        assert set(g[tr]).isdisjoint(g[va])                      # grouped folds
        assert np.allclose(sc.mean_, X[tr].mean(axis=0))
        assert np.allclose(sc.scale_, X[tr].std(axis=0))
        assert not np.allclose(sc.mean_, X.mean(axis=0))         # not the full matrix
        assert not np.allclose(sc.mean_, X[va].mean(axis=0))     # and not the test fold


def test_probe_sees_train_standardised_and_test_with_train_stats():
    X, y, g = _data(seed=1)
    _SpyProbe.seen = []
    esw.cv_predict_within_fold(X, y, g, _SpyProbe, n_splits=5)
    fits = [m for kind, m in _SpyProbe.seen if kind == "fit"]
    preds = [m for kind, m in _SpyProbe.seen if kind == "predict"]
    assert len(fits) == len(preds) == 5
    for Xtr, Xva in zip(fits, preds):
        assert np.allclose(Xtr.mean(axis=0), 0, atol=1e-10)      # exactly centred on train rows
        assert not np.allclose(Xva.mean(axis=0), 0, atol=1e-3)   # test rows are not re-centred


def test_full_matrix_copy_is_the_notebook_behaviour_and_differs():
    X, y, g = _data(seed=2)
    _SpyProbe.seen = []
    esw.cv_predict_full_matrix(X, y, g, _SpyProbe, n_splits=5)
    fits = [m for kind, m in _SpyProbe.seen if kind == "fit"]
    preds = [m for kind, m in _SpyProbe.seen if kind == "predict"]
    pooled = np.vstack(fits[:1] + preds[:1])                     # fold 1 train + test = every row
    assert np.allclose(pooled.mean(axis=0), 0, atol=1e-10)       # scaler fit on all rows
    a = esw.cv_predict_full_matrix(X, y, g, esw.logreg)
    b = esw.cv_predict_within_fold(X, y, g, esw.logreg)
    assert a.shape == b.shape and not np.allclose(a, b)


def test_same_folds_as_notebook_and_runs_through_frozen_h3():
    rng = np.random.RandomState(3)
    rows = [{"stay_id": s, "bin": b, "f1": rng.randn() + s % 3, "f2": rng.randn(),
             "action_next": int(rng.rand() < 0.4)} for s in range(40) for b in range(12)]
    st = pd.DataFrame(rows)
    st["f1"] = st["f1"] + st["action_next"]
    import h3_paired_bootstrap as h3
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        s = h3.run_h3(st, ["f1", "f2"], esw.logreg, esw.cv_predict_within_fold, Path(d), n_boot=20,
                      seed=42, offset_mode="bins", far_offset=8, save_patient_level=False)
    r = s["restricted"]
    assert r["n_boot"] == 20 and r["seed"] == 42 and r["n_rows_a"] == r["n_rows_b"]
