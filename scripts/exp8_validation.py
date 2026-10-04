"""Independent validation of Experiment 8 (Variant F = D + explicit treatment-history features).

Two checks, both aggregate-only in what they write:

1. strictly_before: F1 (hours on vasopressor) and F2 (hours since the last dose-tier change) must
   depend only on information available at the decision time tau. They are recomputed here from
   the raw dose intervals restricted to infusions that had started by tau (whether one is still
   running at tau is known at tau; nothing else about its end is used) and tier changes at or
   before tau, then compared element-wise with the notebook's values. Any difference would mean
   a feature looks past the decision boundary. Note what this check does NOT claim: an infusion
   running at tau is, by construction of action_next, active in the next bin, so F1 > 0 implies
   the label; the ablation below quantifies that.

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


def known_at_tau_intervals(vaso_dose_clean: pd.DataFrame, dose_scored_drugs, tau: float, stay_id) -> list[tuple[float, float]]:
    """Merged dose-scored intervals of one stay using only what is known at tau: infusions that
    started at or before tau. Whether an infusion is still running at tau (end > tau) is known at
    tau; its eventual end time is not used beyond that test."""
    g = vaso_dose_clean[(vaso_dose_clean["stay_id"] == stay_id) & vaso_dose_clean["drug"].isin(dose_scored_drugs)]
    pairs = sorted((float(s), float(e)) for s, e in zip(g["start_hours_from_admit"], g["end_hours_from_admit"]) if float(s) <= tau)
    merged: list[list[float]] = []
    for a, b in pairs:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def f1_at_tau(vaso_dose_clean, dose_scored_drugs, stay_id, tau: float) -> float:
    """Hours on vasopressor at tau: the merged interval that has started and is still running."""
    for a, b in known_at_tau_intervals(vaso_dose_clean, dose_scored_drugs, tau, stay_id):
        if a <= tau < b:
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
    d1, d2, examples = [], [], []
    for i in idx:
        row = decision_edges.iloc[i]
        sid, tau = row["stay_id"], float(row["decision_time"])
        f1_c = f1_at_tau(vaso_dose_clean, dose_scored_drugs, sid, tau)
        last = 0.0
        for ts, _tier in changes_by_stay.get(sid, []):
            if ts <= tau:
                last = ts
        f2_c = tau - last
        d1.append(abs(f1_c - float(f1_notebook[i]))); d2.append(abs(f2_c - float(f2_notebook[i])))
        if (d1[-1] > 1e-9 or d2[-1] > 1e-9) and len(examples) < 5:
            examples.append({"row": int(i), "tau": tau, "f1_notebook": float(f1_notebook[i]), "f1_recomputed": f1_c,
                             "f2_notebook": float(f2_notebook[i]), "f2_recomputed": f2_c})
    d1, d2 = np.asarray(d1), np.asarray(d2)
    return {"rows_checked": int(len(idx)), "f1_max_abs_diff": float(d1.max()), "f1_rows_differing": int((d1 > 1e-9).sum()),
            "f2_max_abs_diff": float(d2.max()), "f2_rows_differing": int((d2 > 1e-9).sum()),
            "strictly_before_decision_time": bool((d1 <= 1e-9).all() and (d2 <= 1e-9).all()),
            "differing_examples_no_patient_ids": examples}


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


def indicator_and_off_rows(f1: np.ndarray, y: np.ndarray, groups: np.ndarray, variants: dict, probes: dict,
                           cv_predict, bootstrap_ci, n_boot: int = 300) -> dict:
    """The on-at-tau indicator on its own, and variants A and E evaluated on the rows where the
    patient is NOT on a vasopressor at tau (on-at-tau rows are all label 1, so only off rows carry
    information). Each requested probe is refitted with grouped CV on the off rows alone."""
    on = (f1 > 0)
    out = {"indicator_alone_auroc": float(roc_auc_score(y, on.astype(float))),
           "n_rows_all": int(len(y)), "n_rows_off": int((~on).sum()), "n_rows_on": int(on.sum()),
           "label_rate_off": float(y[~on].mean()), "label_rate_on": float(y[on].mean()),
           "off_rows": {}}
    yo, go = y[~on], groups[~on]
    for vname, X in variants.items():
        Xo = X[~on]
        out["off_rows"][vname] = {}
        for pname, pfn in probes.items():
            p = cv_predict(Xo, yo, go, pfn)
            lo, hi = bootstrap_ci(yo, p, go, roc_auc_score, n_boot=n_boot)
            out["off_rows"][vname][pname] = {"auroc": float(roc_auc_score(yo, p)), "ci_lo": float(lo), "ci_hi": float(hi)}
    return out


def on_at_tau_all_drugs(vaso_bins_df: pd.DataFrame, decision_edges: pd.DataFrame) -> np.ndarray:
    """1 if ANY of the label's drugs (all six, as in vaso_bins_df: the action label's own drug set,
    including phenylephrine and vasopressin) has an infusion running at the decision time tau
    (start <= tau < end), aligned to decision_edges' rows."""
    iv = vaso_bins_df[["stay_id", "time_bin_start", "time_bin_end"]]
    by_stay = {sid: (g["time_bin_start"].values, g["time_bin_end"].values) for sid, g in iv.groupby("stay_id")}
    out = np.zeros(len(decision_edges), dtype=bool)
    for i, (sid, tau) in enumerate(zip(decision_edges["stay_id"].values, decision_edges["decision_time"].values)):
        if sid in by_stay:
            st, en = by_stay[sid]
            out[i] = bool(((st <= tau) & (tau < en)).any())
    return out


def run_exp8_validation(vaso_dose_clean, dose_scored_drugs, decision_edges, f1, f2, changes_by_stay,
                        X_D, y, groups, probe_fn, cv_predict, bootstrap_ci, out_dir, n_boot: int = 300,
                        sample: int | None = 2000, off_row_variants: dict | None = None, off_row_probes: dict | None = None,
                        vaso_bins_df: pd.DataFrame | None = None) -> dict:
    res = {"strictly_before": check_strictly_before(vaso_dose_clean, dose_scored_drugs, decision_edges, f1, f2, changes_by_stay, sample=sample),
           "indicator_ablation": indicator_ablation(X_D, f1, f2, y, groups, probe_fn, cv_predict, bootstrap_ci, n_boot=n_boot),
           "n_rows": int(len(y)), "probe": "logreg"}
    if off_row_variants:
        # dose_scored_drugs only (norepi, epi, dopamine, dobutamine): the F1 definition
        res["indicator_and_off_rows"] = indicator_and_off_rows(f1, y, groups, off_row_variants, off_row_probes or {"logreg": probe_fn},
                                                               cv_predict, bootstrap_ci, n_boot=n_boot)
        res["indicator_and_off_rows"]["drug_set"] = "dose_scored_4 (F1 > 0)"
        if vaso_bins_df is not None:
            # all six label drugs: the definition that matches the action label
            on6 = on_at_tau_all_drugs(vaso_bins_df, decision_edges).astype(float)
            r6 = indicator_and_off_rows(on6, y, groups, off_row_variants, off_row_probes or {"logreg": probe_fn},
                                        cv_predict, bootstrap_ci, n_boot=n_boot)
            r6["drug_set"] = "all_6_label_drugs"
            res["indicator_and_off_rows_all_drugs"] = r6
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(out_dir) / "experiment8_validation.json", "w") as f:
        json.dump(res, f, indent=2)
    sb, ia = res["strictly_before"], res["indicator_ablation"]
    print(f"Exp 8 strictly-before check on {sb['rows_checked']:,} rows: F1 diff {sb['f1_max_abs_diff']:.2e}, "
          f"F2 diff {sb['f2_max_abs_diff']:.2e} -> {'PASS' if sb['strictly_before_decision_time'] else 'FAIL'}")
    if "indicator_and_off_rows" in res:
        io = res["indicator_and_off_rows"]
        for _k in ("indicator_and_off_rows", "indicator_and_off_rows_all_drugs"):
            if _k not in res:
                continue
            io = res[_k]
            print(f"[{io['drug_set']}] indicator alone AUROC={io['indicator_alone_auroc']:.3f}; off rows n={io['n_rows_off']:,} (label rate {io['label_rate_off']:.3f}, on {io['label_rate_on']:.3f}): "
                  + "  ".join(f"{v} {pn}={r['auroc']:.3f}" for v, d in io["off_rows"].items() for pn, r in d.items()))
        io = res["indicator_and_off_rows"]
        if False: print(f"Exp 8 indicator alone AUROC={io['indicator_alone_auroc']:.3f}; off-at-tau rows n={io['n_rows_off']:,} (label rate {io['label_rate_off']:.3f}): "
              + "  ".join(f"{v} {pn}={r['auroc']:.3f}" for v, d in io["off_rows"].items() for pn, r in d.items()))
    print(f"Exp 8 ablation (logreg): D={ia['D']['auroc']:.3f}  D+on_indicator={ia['D_plus_on_vasopressor_indicator']['auroc']:.3f}  "
          f"D+F1+F2={ia['D_plus_F1_F2']['auroc']:.3f}  indicator share of F gain={ia['indicator_share_of_F_gain']:.2f}  "
          f"P(action|on)={ia['label_given_on']:.3f} P(action|off)={ia['label_given_off']:.3f}")
    return res
