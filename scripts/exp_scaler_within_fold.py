#!/usr/bin/env python3
"""Exploratory, not pre-registered; a sensitivity analysis on where the StandardScaler is fit.

The notebook's cv_predict (cells 21 and 24) fits StandardScaler on the FULL feature matrix and only
then runs GroupKFold(5) by stay_id, so every held-out fold is scaled with means and SDs that saw its
own rows. This script reruns the logistic-regression results with the scaler fit on the training
folds only and applied to the held-out fold, and changes nothing else:

  cv_predict_full_matrix   verbatim copy of the notebook's cv_predict (reproduces the reported runs)
  cv_predict_within_fold   identical, except StandardScaler().fit(X[tr]) inside each fold

Covered (every logreg result produced through cv_predict):
  h3      scripts/h3_paired_bootstrap.run_h3, unchanged, both offset modes (bins primary, rows
          sensitivity), common-rows primary and own-rows sensitivity, seed 42, SAIL_H3_NBOOT (2000)
  exp2    Experiment 2 logreg, variants A to E, clustered CI (300 resamples, seed 42)
  exp5    Experiment 5 negative controls (a) shuffled labels and (d) placebo feature, logreg
  exp6    Experiment 6 mortality logreg, variants A to E
  exp8    Experiment 8 variant F logreg, action and mortality axes
rf and gb are tree ensembles, invariant to a per-feature affine rescaling, so they are not rerun.

Inputs: the notebook's own Experiment 5 checkpoint (exp5_checkpoint_inputs.pkl: state_4h, variants
A to E, y_action, groups) for h3, exp2 and exp5; for exp6 and exp8 the matrices are rebuilt by
executing the notebook's own code cells in-process against a READ-ONLY DuckDB (`matrices` step),
since the notebook never saved them. Patient-level files stay in --work (cluster scratch); only the
aggregate JSON written by `report` is meant for the repo.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import h3_paired_bootstrap as h3  # noqa: E402  (the frozen pre-registered code path)

RANDOM_STATE = 42
TOL = 5e-5  # "matches to 4 decimals"
VARIANTS_AE = ["A_full", "B_no_total_sofa", "C_no_cardio_sofa", "D_treatment_decomposed", "E_physiology_only"]
NB = REPO / "notebook" / "Sepsis_RL_SOFA_Leakage_Experiments.ipynb"
RUN_CELLS = [3, 5, 7, 9, 11, 12, 14, 18, 19, 21, 24, 28, 31, 33]
CUTS = {
    21: "exp2_results, exp2_best, exp2_gap = run_experiment2(",
    24: "exp6_results, exp6_best = run_experiment6(",
    33: "def _evaluate_variant(",
}


def logreg():
    """PROBES['logreg'] in notebook cells 21 and 24."""
    return LogisticRegression(max_iter=2000, class_weight="balanced")


def cv_predict_full_matrix(X, y, groups, probe_fn, n_splits=5):
    """Verbatim notebook cv_predict: the scaler sees every row before the split."""
    cv = GroupKFold(n_splits=n_splits)
    Xs = StandardScaler().fit_transform(X)
    preds = np.zeros(len(y), dtype=float)
    for tr, va in cv.split(Xs, y, groups):
        clf = probe_fn()
        clf.fit(Xs[tr], y[tr])
        preds[va] = clf.predict_proba(Xs[va])[:, 1]
    return preds


def cv_predict_within_fold(X, y, groups, probe_fn, n_splits=5, _scaler_log=None):
    """The same folds and probe; the scaler is fit on the training rows of each fold only."""
    cv = GroupKFold(n_splits=n_splits)
    preds = np.zeros(len(y), dtype=float)
    for tr, va in cv.split(X, y, groups):
        sc = StandardScaler().fit(X[tr])
        if _scaler_log is not None:
            _scaler_log.append((tr, va, sc))
        clf = probe_fn()
        clf.fit(sc.transform(X[tr]), y[tr])
        preds[va] = clf.predict_proba(sc.transform(X[va]))[:, 1]
    return preds


SCALERS = {"full_matrix": cv_predict_full_matrix, "within_fold": cv_predict_within_fold}


def bootstrap_ci_metric_clustered(y_true, y_pred, groups, metric_fn, n_boot=500, seed=RANDOM_STATE):
    """Verbatim notebook cell 21 (patient-clustered percentile CI)."""
    rng = np.random.RandomState(seed)
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    group_to_idx = {g: np.where(groups == g)[0] for g in unique_groups}
    scores = []
    for _ in range(n_boot):
        sampled_groups = rng.choice(unique_groups, size=n_groups, replace=True)
        idx = np.concatenate([group_to_idx[g] for g in sampled_groups])
        if len(np.unique(y_true[idx])) < 2:
            continue
        scores.append(metric_fn(y_true[idx], y_pred[idx]))
    return float(np.percentile(scores, 2.5)), float(np.percentile(scores, 97.5))


def auroc_with_ci(X, y, g, cv, n_boot=300):
    p = cv(X, y, g, logreg)
    lo, hi = bootstrap_ci_metric_clustered(y, p, g, roc_auc_score, n_boot=n_boot)
    return {"auroc": float(roc_auc_score(y, p)), "ci_lo": lo, "ci_hi": hi}


def _git_head():
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


# --------------------------------------------------------------------------- step: checkpoint-based
def step_checkpoint(checkpoint: Path, work: Path, n_boot: int):
    with open(checkpoint, "rb") as f:
        ck = pickle.load(f)
    state_4h, variants, feature_names = ck["state_4h"], ck["variants"], ck["feature_names"]
    y_action, groups = ck["y_action"], ck["groups"]
    out = {"n_action_rows": int(len(y_action)), "n_action_stays": int(len(np.unique(groups))), "h3": {},
           "exp2_logreg": {}, "exp5_controls_logreg": {}}
    t0 = time.time()
    for name, cv in SCALERS.items():
        out["h3"][name] = {}
        for mode in ("bins", "rows"):
            d = work / "h3" / name
            d.mkdir(parents=True, exist_ok=True)
            s = h3.run_h3(state_4h, feature_names, logreg, cv, d, n_boot=n_boot, seed=RANDOM_STATE,
                          offset_mode=mode, save_patient_level=True)
            s.pop("patient_level_files_cluster_only", None)
            out["h3"][name][mode] = s
            print(f"[{time.time() - t0:.0f}s] h3 {name} {mode} done", flush=True)
        out["exp2_logreg"][name] = {v: auroc_with_ci(variants[v], y_action, groups, cv) for v in VARIANTS_AE}
        print(f"[{time.time() - t0:.0f}s] exp2 {name} done", flush=True)
        # Experiment 5 controls (a) and (d), same RNG order as notebook cell 37
        rng = np.random.RandomState(RANDOM_STATE)
        y_shuf = y_action.copy()
        rng.shuffle(y_shuf)
        a = auroc_with_ci(variants["A_full"], y_shuf, groups, cv)
        placebo = rng.binomial(1, y_action.mean(), size=variants["A_full"].shape[0]).reshape(-1, 1).astype(float)
        d = auroc_with_ci(np.hstack([variants["E_physiology_only"], placebo]), y_action, groups, cv)
        out["exp5_controls_logreg"][name] = {"shuffled_labels": a, "placebo_feature_matched_prevalence": d}
        print(f"[{time.time() - t0:.0f}s] exp5 controls {name} done", flush=True)
    (work / "checkpoint_part.json").write_text(json.dumps(out, indent=2))


# --------------------------------------------------------------------------- step: rebuild matrices
def _cell_sources(nb_path: Path = NB) -> dict[int, str]:
    nb = json.loads(nb_path.read_text())
    out = {}
    for i in RUN_CELLS:
        cell = nb["cells"][i]
        assert cell["cell_type"] == "code", f"cell {i} is not code; notebook structure changed"
        src = "".join(cell["source"])
        if i in CUTS:
            assert src.count(CUTS[i]) == 1, f"cut marker for cell {i} not found exactly once"
            src = src.split(CUTS[i])[0]
        out[i] = src
    return out


def step_matrices(work: Path):
    """Executes the notebook's own cells up to the Exp 6 / Exp 8 matrices, DuckDB read-only."""
    import duckdb
    import duckdb_backend as sail_db
    os.environ["SAIL_BACKEND"] = "duckdb"
    os.environ.setdefault("SAIL_REPO", str(REPO))
    db_path = os.path.expanduser(os.environ.get("SAIL_DUCKDB", "~/orcd/scratch/sail/mimic4.db"))
    assert "'" not in db_path
    tmp = work / "duckdb_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(":memory:")
    con.execute(f"SET threads = {int(os.environ.get('SAIL_THREADS', '8'))}")
    con.execute(f"SET memory_limit = '{os.environ.get('SAIL_MEM', '24GB')}'")
    con.execute(f"SET temp_directory = '{tmp}'")
    con.execute(f"ATTACH '{db_path}' AS mimic (READ_ONLY)")
    con.execute("USE mimic")
    sail_db.SCRATCH_SCHEMA = "memory"  # cohort scratch table in memory; the database is untouched
    sail_db._con = con
    nbdir = work / "nb"
    (nbdir / "results").mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(nbdir)  # the notebook writes ./results; nothing goes into the repo
    ns: dict = {"__name__": "__sail_notebook__"}
    t0 = time.time()
    try:
        for i, src in _cell_sources().items():
            print(f"[cell {i}] start {time.time() - t0:.0f}s", flush=True)
            exec(compile(src, f"<cell {i}>", "exec"), ns)
    finally:
        os.chdir(cwd)
    keep = {k: ns[k] for k in ("variants", "y_action", "groups", "mortality_variants", "y_mortality",
                               "groups_mortality", "feature_names")}
    with open(work / "matrices.pkl", "wb") as f:
        pickle.dump(keep, f)
    print(f"matrices saved {time.time() - t0:.0f}s", flush=True)


def step_exp68(work: Path, checkpoint: Path):
    with open(work / "matrices.pkl", "rb") as f:
        m = pickle.load(f)
    with open(checkpoint, "rb") as f:
        ck = pickle.load(f)
    # the rebuilt action matrix must be the checkpoint's, so F sits on the same rows as Exp 2 / H3
    a_new, a_ck = m["variants"]["A_full"], ck["variants"]["A_full"]
    same_rows = bool(a_new.shape == a_ck.shape and np.array_equal(m["groups"], ck["groups"])
                     and np.array_equal(m["y_action"], ck["y_action"]))
    max_abs = float(np.nanmax(np.abs(a_new - a_ck))) if a_new.shape == a_ck.shape else None
    out = {"rebuilt_vs_checkpoint": {"same_rows_and_labels": same_rows, "variant_A_max_abs_diff": max_abs},
           "n_mortality_rows": int(len(m["y_mortality"])), "exp6_logreg": {}, "exp8_logreg": {}}
    for name, cv in SCALERS.items():
        mv = m["mortality_variants"]
        out["exp6_logreg"][name] = {v: auroc_with_ci(mv[v], m["y_mortality"], m["groups_mortality"], cv)
                                    for v in VARIANTS_AE}
        out["exp8_logreg"][name] = {
            "F_action": auroc_with_ci(m["variants"]["F_disentangled"], m["y_action"], m["groups"], cv),
            "F_mortality": auroc_with_ci(mv["F_disentangled"], m["y_mortality"], m["groups_mortality"], cv),
        }
        print(f"exp6/exp8 {name} done", flush=True)
    (work / "exp68_part.json").write_text(json.dumps(out, indent=2))


# --------------------------------------------------------------------------- step: aggregate report
def _cmp(pairs):
    """pairs: list of (label, ours, reference). Returns the max abs diff and the worst label."""
    diffs = [(abs(float(a) - float(b)), k) for k, a, b in pairs]
    worst = max(diffs)
    return {"n_compared": len(diffs), "max_abs_diff": worst[0], "worst": worst[1],
            "match_4dp": bool(worst[0] < TOL)}


H3_KEYS = ["auroc_a", "auroc_b", "delta", "delta_ci_lo", "delta_ci_hi"]


def step_report(work: Path, cohort: str, ref_dir: Path, ref_points: Path | None, out_json: Path):
    ck = json.loads((work / "checkpoint_part.json").read_text())
    e68 = json.loads((work / "exp68_part.json").read_text()) if (work / "exp68_part.json").exists() else None
    fm, wf = "full_matrix", "within_fold"
    sanity = {}

    pairs = []
    for mode in ("bins", "rows"):
        ref = json.loads((ref_dir / f"experiment5_h3_paired_bootstrap_{mode}.json").read_text())
        ours = ck["h3"][fm][mode]
        for blk in ("restricted", "unrestricted_sensitivity"):
            pairs += [(f"h3.{mode}.{blk}.{k}", ours[blk][k], ref[blk][k]) for k in H3_KEYS]
        pairs += [(f"h3.{mode}.curve.{c['offset_bins']}", c["auroc"], r["auroc"])
                  for c, r in zip(ours["decay_curve"], ref["decay_curve"])]
    sanity["h3_vs_reported_run"] = _cmp(pairs)

    ref2 = pd.read_csv(ref_dir / "experiment2_action_recoverability_full.csv")
    ref2 = ref2[ref2.probe == "logreg"].set_index("variant")
    sanity["exp2_vs_reported_run"] = _cmp(
        [(f"exp2.{v}.{k}", ck["exp2_logreg"][fm][v][k], ref2.loc[v, rk])
         for v in VARIANTS_AE for k, rk in (("auroc", "auroc"), ("ci_lo", "auroc_ci_lo"), ("ci_hi", "auroc_ci_hi"))])
    ref5 = json.loads((ref_dir / "experiment5_negative_controls.json").read_text())
    sanity["exp5_vs_reported_run"] = _cmp(
        [(f"exp5.{c}.{k}", ck["exp5_controls_logreg"][fm][c][k], ref5[c][k])
         for c in ("shuffled_labels", "placebo_feature_matched_prevalence") for k in ("auroc", "ci_lo", "ci_hi")])

    def diff(a, b, keys):
        return {k: float(b[k]) - float(a[k]) for k in keys}

    h3_out = {}
    for mode in ("bins", "rows"):
        h3_out[mode] = {}
        for blk in ("restricted", "unrestricted_sensitivity"):
            a, b = ck["h3"][fm][mode][blk], ck["h3"][wf][mode][blk]
            keep = H3_KEYS + ["n_rows_a", "n_rows_b", "n_patients", "p_delta_ge_threshold",
                              "prediction_A_supported", "n_boot", "n_boot_used", "seed"]
            h3_out[mode][blk] = {fm: {k: a[k] for k in keep}, wf: {k: b[k] for k in keep},
                                 "within_minus_full": diff(a, b, H3_KEYS)}
        h3_out[mode]["decay_curve"] = [
            {"offset_bins": c0["offset_bins"], "n": c0["n"], fm: c0["auroc"], wf: c1["auroc"],
             "within_minus_full": c1["auroc"] - c0["auroc"]}
            for c0, c1 in zip(ck["h3"][fm][mode]["decay_curve"], ck["h3"][wf][mode]["decay_curve"])]

    def table(d, keys):
        return {k: {fm: d[fm][k], wf: d[wf][k], "within_minus_full_auroc": d[wf][k]["auroc"] - d[fm][k]["auroc"]}
                for k in keys}

    result = {
        "what": "Within-fold StandardScaler sensitivity for every logreg result built through cv_predict",
        "status": "exploratory, not pre-registered; does not replace any pinned or reported result",
        "cohort_stays": int(cohort), "code_commit": _git_head(),
        "scalers": {fm: "notebook cv_predict: StandardScaler fit on all rows, then GroupKFold(5) by stay_id",
                    wf: "same folds and probe; StandardScaler fit on each fold's training rows only"},
        "probe": "LogisticRegression(max_iter=2000, class_weight='balanced')",
        "not_rerun": "rf and gb probes: tree ensembles are invariant to per-feature affine rescaling",
        "n_action_rows": ck["n_action_rows"], "n_action_stays": ck["n_action_stays"],
        "sanity_full_matrix_reproduces_reported": sanity,
        "h3": {"primary": "bins mode, restricted (common rows)", **h3_out},
        "exp2_logreg": table(ck["exp2_logreg"], VARIANTS_AE),
        "exp5_controls_logreg": table(ck["exp5_controls_logreg"], ["shuffled_labels", "placebo_feature_matched_prevalence"]),
    }
    if e68 is not None:
        ref6 = pd.read_csv(ref_dir / "experiment6_mortality_full.csv")
        ref6 = ref6[ref6.probe == "logreg"].set_index("variant")
        sanity["exp6_vs_reported_run"] = _cmp(
            [(f"exp6.{v}.{k}", e68["exp6_logreg"][fm][v][k], ref6.loc[v, rk])
             for v in VARIANTS_AE for k, rk in (("auroc", "auroc"), ("ci_lo", "auroc_ci_lo"), ("ci_hi", "auroc_ci_hi"))])
        if ref_points is not None and ref_points.exists():
            pts = json.loads(ref_points.read_text())
            sanity["exp8_vs_notebook_cv_predict_points"] = _cmp([
                ("exp8.F_action", e68["exp8_logreg"][fm]["F_action"]["auroc"], pts["action_auroc"]["F_disentangled|logreg"]),
                ("exp8.F_mortality", e68["exp8_logreg"][fm]["F_mortality"]["auroc"], pts["mortality_auroc"]["F_disentangled|logreg"])])
        result["n_mortality_rows"] = e68["n_mortality_rows"]
        result["rebuilt_matrices_vs_checkpoint"] = e68["rebuilt_vs_checkpoint"]
        result["exp6_logreg"] = table(e68["exp6_logreg"], VARIANTS_AE)
        result["exp8_logreg"] = table(e68["exp8_logreg"], ["F_action", "F_mortality"])
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2))
    r = h3_out["bins"]["restricted"]
    print(f"cohort {cohort}  H3 bins restricted  full: Delta={r[fm]['delta']:.4f} "
          f"CI=({r[fm]['delta_ci_lo']:.4f},{r[fm]['delta_ci_hi']:.4f})  within: Delta={r[wf]['delta']:.4f} "
          f"CI=({r[wf]['delta_ci_lo']:.4f},{r[wf]['delta_ci_hi']:.4f})")
    print(json.dumps(sanity, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["checkpoint", "matrices", "exp68", "report"])
    ap.add_argument("--work", required=True, type=Path, help="cluster scratch dir (patient-level files)")
    ap.add_argument("--checkpoint", type=Path, help="exp5_checkpoint_inputs.pkl from the reported run")
    ap.add_argument("--cohort", default="13192")
    ap.add_argument("--ref-dir", type=Path, help="the reported run's notebook/results directory")
    ap.add_argument("--ref-points", type=Path, help="points.json from the notebook cv_predict rerun (Exp 8 logreg)")
    ap.add_argument("--out", type=Path, help="aggregate JSON path")
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.step == "checkpoint":
        step_checkpoint(args.checkpoint, args.work, int(os.environ.get("SAIL_H3_NBOOT", "2000")))
    elif args.step == "matrices":
        step_matrices(args.work)
    elif args.step == "exp68":
        step_exp68(args.work, args.checkpoint)
    else:
        step_report(args.work, args.cohort, args.ref_dir, args.ref_points, args.out)


if __name__ == "__main__":
    main()
