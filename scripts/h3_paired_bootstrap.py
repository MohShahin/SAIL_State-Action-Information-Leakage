"""H3: the pre-registered paired cluster bootstrap on the offset-decay curve (FORMAL_ANALYSIS.md
section 7), with the per-patient predictions Experiment 5 did not keep.

Delta = AUROC(offset 0) - AUROC(offset 8). Patients (stay_id) are resampled with replacement and
both AUROCs are computed on the same resampled patient set, so Delta's sampling distribution is
obtained directly. Two row sets are reported:

  restricted    rows present at BOTH offsets (same (stay_id, bin) pairs), the paired design
                proposed by the project lead; a documented deviation from the notebook's
                per-offset row sets, where offset 8 has far fewer rows than offset 0
  unrestricted  each offset keeps its own rows for the resampled patients (sensitivity check,
                matches the published per-offset AUROCs at offset 0)

Offsets are built exactly as notebook cell 35 does (shift by ROWS of state_4h within a stay,
offset_mode="rows"); offset_mode="bins" shifts by bin index on the 18-bin grid instead, for the
alignment question raised during the port. Per-patient predictions are written as parquet files
under results/ (gitignored by default: they are patient-level and must stay on the cluster);
only the aggregate JSON is meant to be committed, after being added to the .gitignore allowlist.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

DELTA_THRESHOLD = 0.10          # FORMAL_ANALYSIS.md section 7, Prediction A
DEFAULT_OFFSETS = (0, 1, 2, 4, 8)


def offset_frames(state_4h: pd.DataFrame, feature_names: list[str], offsets=DEFAULT_OFFSETS,
                  offset_mode: str = "rows") -> dict[int, pd.DataFrame]:
    """One frame per offset with columns stay_id, bin, y and the features, labelled with the
    action `offset` steps ahead of action_next. offset 0 is the notebook's own y_action."""
    base = state_4h.sort_values(["stay_id", "bin"]).reset_index(drop=True)
    out = {}
    for off in offsets:
        if off == 0:
            df = base.copy()
            df["y"] = df["action_next"].astype(int)
        elif offset_mode == "rows":
            df = base.copy()
            df["y"] = df.groupby("stay_id")["action_next"].shift(-off)
            df = df.dropna(subset=["y"])
            df["y"] = df["y"].astype(int)
        elif offset_mode == "bins":
            lab = base[["stay_id", "bin", "action_next"]].copy()
            lab["bin"] = lab["bin"] - off
            lab = lab.rename(columns={"action_next": "y"})
            df = base.drop(columns=["action_next"]).merge(lab, on=["stay_id", "bin"], how="inner")
            df["y"] = df["y"].astype(int)
        else:
            raise ValueError(f"offset_mode must be 'rows' or 'bins', got {offset_mode!r}")
        out[off] = df[["stay_id", "bin", "y"] + list(feature_names)].reset_index(drop=True)
    return out


def predict_offsets(frames: dict[int, pd.DataFrame], feature_names: list[str], probe_fn, cv_predict,
                    n_splits: int = 5) -> dict[int, pd.DataFrame]:
    """Grouped cross-validated predictions per offset, using the notebook's own cv_predict."""
    preds = {}
    for off, df in frames.items():
        X = df[feature_names].values.astype(np.float64)
        y = df["y"].values.astype(int)
        g = df["stay_id"].values
        p = cv_predict(X, y, g, probe_fn, n_splits=n_splits)
        preds[off] = pd.DataFrame({"stay_id": g, "bin": df["bin"].values, "y": y, "pred": p})
    return preds


def _group_index(groups: np.ndarray) -> dict:
    order = np.argsort(groups, kind="stable")
    sg = groups[order]
    uniq, starts = np.unique(sg, return_index=True)
    ends = np.append(starts[1:], len(sg))
    return {g: order[s:e] for g, s, e in zip(uniq, starts, ends)}


def paired_cluster_bootstrap(p_a: pd.DataFrame, p_b: pd.DataFrame, n_boot: int = 2000, seed: int = 42,
                             restrict: bool = True, threshold: float = DELTA_THRESHOLD) -> dict:
    """Bootstrap distribution of Delta = AUROC(p_a) - AUROC(p_b), resampling patients.

    restrict=True keeps only (stay_id, bin) rows present in both frames so the two AUROCs are
    computed on identical rows; restrict=False keeps each frame's own rows for the resampled
    patients. Both resample the same patient set on every replicate."""
    if restrict:
        m = p_a.merge(p_b, on=["stay_id", "bin"], suffixes=("_a", "_b"))
        a = m[["stay_id", "bin"]].assign(y=m["y_a"].values, pred=m["pred_a"].values)
        b = m[["stay_id", "bin"]].assign(y=m["y_b"].values, pred=m["pred_b"].values)
    else:
        a, b = p_a, p_b
    ya, pa, ga = a["y"].values, a["pred"].values, a["stay_id"].values
    yb, pb, gb = b["y"].values, b["pred"].values, b["stay_id"].values
    patients = np.union1d(np.unique(ga), np.unique(gb))
    ia, ib = _group_index(ga), _group_index(gb)
    empty = np.array([], dtype=int)
    rng = np.random.RandomState(seed)
    deltas, auc_a, auc_b, skipped = [], [], [], 0
    for _ in range(n_boot):
        s = rng.choice(patients, size=len(patients), replace=True)
        xa = np.concatenate([ia.get(g, empty) for g in s])
        xb = np.concatenate([ib.get(g, empty) for g in s])
        if len(np.unique(ya[xa])) < 2 or len(np.unique(yb[xb])) < 2:
            skipped += 1
            continue
        ra, rb = roc_auc_score(ya[xa], pa[xa]), roc_auc_score(yb[xb], pb[xb])
        auc_a.append(ra); auc_b.append(rb); deltas.append(ra - rb)
    deltas = np.asarray(deltas)
    point_a, point_b = roc_auc_score(ya, pa), roc_auc_score(yb, pb)
    return {
        "restricted_rows": bool(restrict),
        "n_rows_a": int(len(ya)), "n_rows_b": int(len(yb)), "n_patients": int(len(patients)),
        "auroc_a": float(point_a), "auroc_b": float(point_b), "delta": float(point_a - point_b),
        "delta_ci_lo": float(np.percentile(deltas, 2.5)), "delta_ci_hi": float(np.percentile(deltas, 97.5)),
        "auroc_a_ci": [float(np.percentile(auc_a, 2.5)), float(np.percentile(auc_a, 97.5))],
        "auroc_b_ci": [float(np.percentile(auc_b, 2.5)), float(np.percentile(auc_b, 97.5))],
        "p_delta_ge_threshold": float(np.mean(deltas >= threshold)),
        "p_delta_le_zero": float(np.mean(deltas <= 0)),
        "threshold": float(threshold), "n_boot": int(n_boot), "n_boot_used": int(len(deltas)),
        "n_boot_skipped_single_class": int(skipped), "seed": int(seed),
        "prediction_A_supported": bool(np.percentile(deltas, 2.5) > 0 and (point_a - point_b) >= threshold),
    }


def save_predictions(preds: dict[int, pd.DataFrame], out_dir: Path, tag: str = "rows") -> list[str]:
    """Patient-level files: cluster only, never committed."""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for off, df in preds.items():
        p = out_dir / f"experiment5_predictions_offset{off}_{tag}.parquet"
        df.to_parquet(p, index=False); paths.append(str(p))
    return paths


def run_h3(state_4h: pd.DataFrame, feature_names: list[str], probe_fn, cv_predict, out_dir,
           n_boot: int = 2000, seed: int = 42, offsets=DEFAULT_OFFSETS, offset_mode: str = "rows",
           far_offset: int = 8, save_patient_level: bool = True) -> dict:
    """Experiment 5b with per-patient predictions kept, then the section 7 paired test."""
    frames = offset_frames(state_4h, feature_names, offsets, offset_mode)
    preds = predict_offsets(frames, feature_names, probe_fn, cv_predict)
    out_dir = Path(out_dir)
    saved = save_predictions(preds, out_dir, tag=offset_mode) if save_patient_level else []
    curve = []
    for off in offsets:
        df = preds[off]
        curve.append({"offset_bins": int(off), "offset_mode": offset_mode, "n": int(len(df)),
                      "n_patients": int(df["stay_id"].nunique()),
                      "auroc": float(roc_auc_score(df["y"], df["pred"]))})
    summary = {
        "test": "FORMAL_ANALYSIS.md section 7, paired cluster bootstrap on Delta = AUROC(0) - AUROC(far_offset)",
        "offset_mode": offset_mode, "far_offset": int(far_offset), "probe": "logreg",
        "decay_curve": curve,
        "restricted": paired_cluster_bootstrap(preds[0], preds[far_offset], n_boot, seed, restrict=True),
        "unrestricted_sensitivity": paired_cluster_bootstrap(preds[0], preds[far_offset], n_boot, seed, restrict=False),
        "patient_level_files_cluster_only": saved,
    }
    with open(out_dir / f"experiment5_h3_paired_bootstrap_{offset_mode}.json", "w") as f:
        json.dump(summary, f, indent=2)
    r, u = summary["restricted"], summary["unrestricted_sensitivity"]
    print(f"H3 ({offset_mode} offsets): restricted rows n={r['n_rows_a']:,} patients={r['n_patients']:,}  "
          f"AUROC(0)={r['auroc_a']:.3f} AUROC({far_offset})={r['auroc_b']:.3f}  Delta={r['delta']:.3f} "
          f"CI=({r['delta_ci_lo']:.3f},{r['delta_ci_hi']:.3f})  P(Delta>=0.10)={r['p_delta_ge_threshold']:.3f}  "
          f"Prediction A supported: {r['prediction_A_supported']}")
    print(f"    unrestricted: AUROC(0)={u['auroc_a']:.3f} (n={u['n_rows_a']:,}) AUROC({far_offset})={u['auroc_b']:.3f} "
          f"(n={u['n_rows_b']:,})  Delta={u['delta']:.3f} CI=({u['delta_ci_lo']:.3f},{u['delta_ci_hi']:.3f})")
    return summary
