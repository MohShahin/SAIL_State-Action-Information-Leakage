"""Independent validation of Experiment 8 (Variant F = D + explicit treatment-history features).

Two checks, both aggregate-only in what they write:

1. strictly_before: F1 (hours on vasopressor) and F2 (hours since the last dose-tier change) must
   depend only on information available at the decision time tau. They are recomputed here from
   the raw dose intervals censored at tau (every interval end is replaced by min(end, tau), every
   tier-change event after tau is dropped) and compared element-wise with the notebook's values.
   Any difference would mean a feature looks past the decision boundary.

2. indicator_ablation: how much of Variant F's action-recoverability AUROC is carried by the single
   binary "on a vasopressor at tau" (F1 > 0)? Variant D plus that indicator is evaluated with the
   notebook's own cv_predict and clustered bootstrap, next to D plus F1 plus F2. If the two are
   close, the history features add little beyond the current treatment state, which is the
   persistence reading of Experiment 8.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def censored_intervals(vaso_dose_clean: pd.DataFrame, dose_scored_drugs, tau: float, stay_id) -> list[tuple[float, float]]:
    """Merged dose-scored intervals of one stay using only what is known at tau: starts at or
    before tau, ends censored at tau (an infusion still running at tau has no known end)."""
    g = vaso_dose_clean[(vaso_dose_clean["stay_id"] == stay_id) & vaso_dose_clean["drug"].isin(dose_scored_drugs)]
    pairs = sorted((float(s), min(float(e), tau)) for s, e in zip(g["start_hours_from_admit"], g["end_hours_from_admit"]) if float(s) <= tau)
    merged: list[list[float]] = []
    for a, b in pairs:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def f1_at_tau_censored(vaso_dose_clean, dose_scored_drugs, stay_id, tau: float) -> float:
    """Hours on vasopressor at tau from censored intervals: covered if the last merged interval
    reaches tau (its end was censored at tau, i.e. the infusion was still running)."""
    for a, b in censored_intervals(vaso_dose_clean, dose_scored_drugs, tau, stay_id):
        if a <= tau and b >= tau and (b == tau):          # still running at tau
            return tau - a
    return 0.0


def check_strictly_before(vaso_dose_clean, dose_scored_drugs, decision_edges: pd.DataFrame,
                          f1_notebook: np.ndarray, f2_notebook: np.ndarray, changes_by_stay: dict,
                          sample: int | None = 2000, seed: int = 42) -> dict:
    """Recompute F1 on a random sample of (stay, tau) rows from censored data; recompute F2 from
    the tier-change timeline keeping only changes at or before tau. Returns max abs differences."""
    rng = np.random.RandomState(seed)
    idx = np.arange(len(decision_edges))
    if sample is not None and sample < len(idx):
        idx = np.sort(rng.choice(idx, size=sample, replace=False))
    d1, d2 = [], []
    for i in idx:
        row = decision_edges.iloc[i]
        sid, tau = row["stay_id"], float(row["decision_time"])
        f1_c = f1_at_tau_censored(vaso_dose_clean, dose_scored_drugs, sid, tau)
        last = 0.0
        for ts, _tier in changes_by_stay.get(sid, []):
            if ts <= tau:
                last = ts
        f2_c = tau - last
        d1.append(abs(f1_c - float(f1_notebook[i]))); d2.append(abs(f2_c - float(f2_notebook[i])))
    d1, d2 = np.asarray(d1), np.asarray(d2)
    return {"rows_checked": int(len(idx)), "f1_max_abs_diff": float(d1.max()), "f1_rows_differing": int((d1 > 1e-9).sum()),
            "f2_max_abs_diff": float(d2.max()), "f2_rows_differing": int((d2 > 1e-9).sum()),
            "strictly_before_decision_time": bool((d1 <= 1e-9).all() and (d2 <= 1e-9).all())}


def indicator_ablation(X_D: np.ndarray, f1: np.ndarray, f2: np.ndarray, y: np.ndarray, groups: np.ndarray,
                       probe_fn, cv_predict, bootstrap_ci, n_boot: int = 300) -> dict:
    """AUROC of D, D + 1[F1 > 0], D + F1 + F2 under the same probe and CV."""
    on = (f1 > 0).astype(float).reshape(-1, 1)
    out = {}
    for name, X in [("D", X_D), ("D_plus_on_vasopressor_indicator", np.hstack([X_D, on])),
                    ("D_plus_F1_F2", np.column_stack([X_D, f1, f2]))]:
        p = cv_predict(X, y, groups, probe_fn)
        lo, hi = bootstrap_ci(y, p, groups, roc_auc_score, n_boot=n_boot)
        out[name] = {"auroc": float(roc_auc_score(y, p)), "ci_lo": float(lo), "ci_hi": float(hi)}
    out["indicator_share_of_F_gain"] = float(
        (out["D_plus_on_vasopressor_indicator"]["auroc"] - out["D"]["auroc"]) /
        max(out["D_plus_F1_F2"]["auroc"] - out["D"]["auroc"], 1e-9))
    out["prevalence_on_vasopressor_at_tau"] = float(on.mean())
    out["label_given_on"] = float(y[on[:, 0] == 1].mean()) if (on == 1).any() else None
    out["label_given_off"] = float(y[on[:, 0] == 0].mean()) if (on == 0).any() else None
    return out


def run_exp8_validation(vaso_dose_clean, dose_scored_drugs, decision_edges, f1, f2, changes_by_stay,
                        X_D, y, groups, probe_fn, cv_predict, bootstrap_ci, out_dir, n_boot: int = 300,
                        sample: int | None = 2000) -> dict:
    res = {"strictly_before": check_strictly_before(vaso_dose_clean, dose_scored_drugs, decision_edges, f1, f2, changes_by_stay, sample=sample),
           "indicator_ablation": indicator_ablation(X_D, f1, f2, y, groups, probe_fn, cv_predict, bootstrap_ci, n_boot=n_boot),
           "n_rows": int(len(y)), "probe": "logreg"}
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(out_dir) / "experiment8_validation.json", "w") as f:
        json.dump(res, f, indent=2)
    sb, ia = res["strictly_before"], res["indicator_ablation"]
    print(f"Exp 8 strictly-before check on {sb['rows_checked']:,} rows: F1 diff {sb['f1_max_abs_diff']:.2e}, "
          f"F2 diff {sb['f2_max_abs_diff']:.2e} -> {'PASS' if sb['strictly_before_decision_time'] else 'FAIL'}")
    print(f"Exp 8 ablation (logreg): D={ia['D']['auroc']:.3f}  D+on_indicator={ia['D_plus_on_vasopressor_indicator']['auroc']:.3f}  "
          f"D+F1+F2={ia['D_plus_F1_F2']['auroc']:.3f}  indicator share of F gain={ia['indicator_share_of_F_gain']:.2f}  "
          f"P(action|on)={ia['label_given_on']:.3f} P(action|off)={ia['label_given_off']:.3f}")
    return res
