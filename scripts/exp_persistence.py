"""Persistence control for the offset-decay curve. EXPLORATORY, not pre-registered; does not
change the H3 decision (docs/DECISIONS_H3.md).

docs/PI_DEFENSE_PREP.md (section 8) asks for an A_{t-1}-only predictor, "the single cheapest,
highest-value addition": the previous decision bin's action alone, no physiology. This script adds
it, plus the on-at-tau indicator of scripts/exp8_validation.on_at_tau_all_drugs, and compares them
with the full state (A) and physiology only (E) across bin-index offsets {0,1,2,4,8}, with the
label construction of scripts/h3_paired_bootstrap.offset_frames(offset_mode="bins").

Per stay and decision bin t (window [4t, 4t+4), decision time tau = 4(t+1)), using the notebook's
own vasopressor extraction (cell 9: six label drugs, amount > 0, endtime not null, dose-scored
drugs kept only in mcg/kg/min):
  prev_action  any of the six drugs active in bin t's window (start < 4t+4 and end > 4t): the
               action of the bin that ends at tau, i.e. A_{t-1} relative to the label a_{t+1}
               (the notebook's action_next at bin t is exactly this quantity at bin t+1, which is
               checked row by row below)
  prev_tier    dose-only SOFA cardio tier (0/2/3/4, notebook cell 31 thresholds) of the max rate
               per dose-scored drug active in bin t's window (notebook cell 12 dose matrix)
  on_at_tau    any of the six drugs running at tau (start <= tau < end), as on_at_tau_all_drugs

Feature sets: P = prev_action; P_dose = prev_action + one-hot prev_tier; I = on_at_tau; P+I;
A = the notebook's full state (feature_names); E = E_physiology_only; A+I; E+I; E+P.
Probe: logreg (the notebook's PROBES["logreg"] and cv_predict, copied verbatim: StandardScaler on
all rows, class_weight balanced, max_iter 2000, GroupKFold 5 by stay_id), one fit per feature set
and offset on that offset's own rows; gb as a check at offsets 0 and 8.

Bootstrap: patients resampled with replacement, 2,000 replicates, seed 42, drawn exactly as
h3_paired_bootstrap.paired_cluster_bootstrap draws them (RandomState(42).choice over the sorted
patient set, one draw per replicate, single-class replicates skipped). Every AUROC within a row
universe is evaluated on the SAME replicate draws, so every difference is paired. Two universes:
  common  rows present at offsets 0 and 8 (primary, as H3 Decision 2); for offsets 1, 2, 4 the
          common rows that also exist at that offset
  own     each offset's own rows; patients = all patients at offset 0 (secondary)
The common/own Delta of A reproduces H3's restricted/unrestricted results exactly (checked).

Writes one aggregate JSON per cohort; per-patient predictions are never written.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h3_paired_bootstrap as h3  # noqa: E402

EXPLORATORY_NOTE = ("exploratory, not pre-registered; does not change the H3 decision "
                    "(docs/DECISIONS_H3.md)")
OFFSETS = (0, 1, 2, 4, 8)
FAR = 8
N_BINS = 18
INTERVAL = 4.0
RANDOM_STATE = 42

VASO_ITEMS = {221906: "norepi", 221289: "epi", 221662: "dopamine", 221653: "dobutamine",
              221749: "phenylephrine", 222315: "vasopressin"}
DOSE_SCORED = ("dopamine", "dobutamine", "epi", "norepi")

# notebook cell 9, verbatim apart from the scratch dataset name
VASO_DOSE_QUERY = f'''
SELECT
  ie.stay_id, ie.itemid, ie.starttime, ie.endtime, ie.rate, ie.rateuom, ie.amount,
  TIMESTAMP_DIFF(ie.starttime, c.intime, MINUTE) / 60.0 AS start_hours_from_admit,
  TIMESTAMP_DIFF(ie.endtime, c.intime, MINUTE) / 60.0 AS end_hours_from_admit
FROM `physionet-data.mimiciv_3_1_icu.inputevents` ie
JOIN `scratch.sepsis_cohort` c USING(stay_id)
WHERE ie.itemid IN ({','.join(str(k) for k in VASO_ITEMS)})
  AND ie.amount > 0
  AND ie.endtime IS NOT NULL
'''

# notebook cell 21, verbatim
PROBES = {
    "logreg": lambda: LogisticRegression(max_iter=2000, class_weight="balanced"),
    "gb": lambda: GradientBoostingClassifier(random_state=RANDOM_STATE),
}


def cv_predict(X, y, groups, probe_fn, n_splits=5):
    """Notebook cell 21's cv_predict, verbatim."""
    cv = GroupKFold(n_splits=n_splits)
    Xs = StandardScaler().fit_transform(X)
    preds = np.zeros(len(y), dtype=float)
    for tr, va in cv.split(Xs, y, groups):
        clf = probe_fn()
        clf.fit(Xs[tr], y[tr])
        preds[va] = clf.predict_proba(Xs[va])[:, 1]
    return preds


# ---------------------------------------------------------------- features from dose intervals

def load_vaso_dose_clean(db_path: str, stay_ids) -> pd.DataFrame:
    """Notebook cell 9's vaso_dose_clean for the given stays, from a DuckDB build opened read-only.
    The cohort's intime is icustays.intime (notebook cell 5's c.intime)."""
    import duckdb
    from duckdb_backend import bq_to_duckdb
    con = duckdb.connect(os.path.expanduser(db_path), read_only=True)
    con.execute(f"SET threads = {int(os.environ.get('SAIL_THREADS', '8'))}")
    con.register("_persist_stays", pd.DataFrame({"stay_id": np.asarray(stay_ids, dtype=np.int64)}))
    con.execute("CREATE TEMP VIEW _persist_cohort AS SELECT s.stay_id, i.intime FROM _persist_stays s "
                "JOIN mimiciv_icu.icustays i USING(stay_id)")
    sql = bq_to_duckdb(VASO_DOSE_QUERY).replace("sail.sepsis_cohort", "_persist_cohort")
    raw = con.execute(sql).fetchdf()
    con.close()
    raw["drug"] = raw["itemid"].map(VASO_ITEMS)
    bad = raw["drug"].isin(DOSE_SCORED) & (raw["rateuom"] != "mcg/kg/min")
    return raw[~bad].copy()


def score_dose_tier_vec(dopamine, dobutamine, epi, norepi) -> np.ndarray:
    """Vectorised notebook cell 31 score_dose_tier (0/2/3/4)."""
    dop, dob, ep, ne = (np.nan_to_num(np.asarray(a, dtype=float)) for a in (dopamine, dobutamine, epi, norepi))
    tier = np.zeros(len(dop), dtype=int)
    tier[(dop > 0) & (dop <= 5) | (dob > 0)] = 2
    tier[(dop > 5) | ((ep > 0) & (ep <= 0.1)) | ((ne > 0) & (ne <= 0.1))] = 3
    tier[(dop > 15) | (ep > 0.1) | (ne > 0.1)] = 4
    return tier


def bin_features(vaso_dose_clean: pd.DataFrame, n_bins: int = N_BINS, interval: float = INTERVAL) -> pd.DataFrame:
    """Per (stay_id, bin) with any infusion row: prev_action, prev_tier, on_at_tau (see module doc).
    (stay, bin) pairs absent from the output have all three equal to 0."""
    v = vaso_dose_clean
    st = v["start_hours_from_admit"].values.astype(float)[:, None]
    en = v["end_hours_from_admit"].values.astype(float)[:, None]
    w0 = np.arange(n_bins, dtype=float)[None, :] * interval
    w1 = w0 + interval                                   # = decision time tau of bin t
    active = (st < w1) & (en > w0)                       # notebook cells 12 and 18 overlap rule
    on_tau = (st <= w1) & (w1 < en)                      # exp8_validation.on_at_tau_all_drugs
    keep = (active | on_tau).ravel()                     # rows with neither flag contribute nothing
    sid = np.repeat(v["stay_id"].values, n_bins)[keep]
    b = np.tile(np.arange(n_bins), len(v))[keep]
    ds = v["drug"].isin(DOSE_SCORED).values
    rate = np.where(active & ds[:, None], v["rate"].fillna(0).values.astype(float)[:, None], 0.0).ravel()[keep]
    long = pd.DataFrame({"stay_id": sid, "bin": b, "active": active.ravel()[keep], "on": on_tau.ravel()[keep],
                         "drug": np.repeat(v["drug"].values, n_bins)[keep], "rate": rate})
    out = long.groupby(["stay_id", "bin"], sort=True)[["active", "on"]].max()
    rl = long[long["drug"].isin(DOSE_SCORED) & long["active"]]
    dm = rl.groupby(["stay_id", "bin", "drug"])["rate"].max().unstack("drug").reindex(columns=list(DOSE_SCORED))
    out = out.join(dm, how="left")
    out["prev_tier"] = score_dose_tier_vec(out["dopamine"], out["dobutamine"], out["epi"], out["norepi"])
    out = out.reset_index()
    return pd.DataFrame({"stay_id": out["stay_id"].values, "bin": out["bin"].values.astype(int),
                         "prev_action": out["active"].values.astype(int), "on_at_tau": out["on"].values.astype(int),
                         "prev_tier": out["prev_tier"].values.astype(int)})


def augment_state(state_4h: pd.DataFrame, feats: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Merge the per-bin features onto state_4h rows and check prev_action against action_next:
    action_next at bin t must equal prev_action at bin t+1 for every row (the label's own rule)."""
    s = state_4h.merge(feats, on=["stay_id", "bin"], how="left")
    for c in ("prev_action", "on_at_tau", "prev_tier"):
        s[c] = s[c].fillna(0).astype(int)
    for k in (2, 3, 4):
        s[f"prev_tier{k}"] = (s["prev_tier"] == k).astype(int)
    nxt = state_4h[["stay_id", "bin", "action_next"]].assign(bin=state_4h["bin"] + 1)
    chk = nxt.merge(feats[["stay_id", "bin", "prev_action"]], on=["stay_id", "bin"], how="left")
    chk["prev_action"] = chk["prev_action"].fillna(0).astype(int)
    y = state_4h["action_next"].values.astype(int)
    on = s["on_at_tau"].values
    checks = {
        "rows": int(len(s)),
        "label_vs_prev_action_next_bin_mismatches": int((chk["action_next"].astype(int).values != chk["prev_action"].values).sum()),
        "rows_prev_action_1": int(s["prev_action"].sum()),
        "rows_on_at_tau_1": int(on.sum()),
        "label_rate_given_on_at_tau": float(y[on == 1].mean()) if on.any() else None,
        "label_rate_given_prev_action_1": float(y[s["prev_action"].values == 1].mean()),
        "label_rate_given_prev_action_0": float(y[s["prev_action"].values == 0].mean()),
        "rows_prev_tier": {str(k): int((s["prev_tier"] == k).sum()) for k in (0, 2, 3, 4)},
        "indicator_alone_auroc_offset0_all_rows": float(roc_auc_score(y, on)),
        "prev_action_alone_auroc_offset0_all_rows": float(roc_auc_score(y, s["prev_action"].values)),
    }
    return s, checks


def feature_sets(feature_names: list[str]) -> dict[str, list[str]]:
    e_cols = [c for c in feature_names if c not in ("sofa_total", "sofa_cardio")]
    p_dose = ["prev_action", "prev_tier2", "prev_tier3", "prev_tier4"]
    return {"P": ["prev_action"], "P_dose": p_dose, "I": ["on_at_tau"], "P+I": ["prev_action", "on_at_tau"],
            "E": e_cols, "E+P": e_cols + ["prev_action"], "E+I": e_cols + ["on_at_tau"],
            "A": list(feature_names), "A+I": list(feature_names) + ["on_at_tau"]}


# ---------------------------------------------------------------- fast paired cluster bootstrap

def draw_counts(n_patients: int, n_boot: int = 2000, seed: int = 42) -> np.ndarray:
    """Per-replicate patient multiplicities, the same draws as h3.paired_cluster_bootstrap
    (RandomState(seed).choice(patients, size=n, replace=True) == patients[randint(0, n, n)])."""
    rng = np.random.RandomState(seed)
    out = np.empty((n_boot, n_patients), dtype=np.uint16)
    for b in range(n_boot):
        out[b] = np.bincount(rng.choice(n_patients, size=n_patients, replace=True), minlength=n_patients)
    return out


def boot_auroc(y: np.ndarray, pred: np.ndarray, pidx: np.ndarray, counts: np.ndarray, chunk: int = 50) -> np.ndarray:
    """AUROC per replicate with row weights = multiplicity of the row's patient (identical to
    concatenating the resampled patients' rows). NaN where a replicate has a single class."""
    order = np.argsort(pred, kind="mergesort")
    ps, ys, pi = pred[order], y[order].astype(float), pidx[order]
    starts = np.r_[0, np.flatnonzero(np.diff(ps)) + 1]
    out = np.empty(counts.shape[0])
    for s in range(0, counts.shape[0], chunk):
        W = counts[s:s + chunk][:, pi].astype(float)
        gp = np.add.reduceat(W * ys, starts, axis=1)
        gn = np.add.reduceat(W * (1.0 - ys), starts, axis=1)
        below = np.cumsum(gn, axis=1) - gn
        tp, tn = gp.sum(1), gn.sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[s:s + chunk] = np.where((tp > 0) & (tn > 0), (gp * (below + 0.5 * gn)).sum(1) / (tp * tn), np.nan)
    return out


def ci(x: np.ndarray) -> list[float]:
    x = x[~np.isnan(x)]
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


class Universe:
    """A row universe (common or own) for one cohort: fixed patient set and replicate draws, with
    per-(feature set, probe, offset) point AUROCs and replicate AUROC vectors cached."""

    def __init__(self, name: str, patients: np.ndarray, rows: dict[int, pd.DataFrame], n_boot: int, seed: int):
        self.name, self.patients = name, np.unique(patients)
        self.rows = rows                     # offset -> DataFrame[stay_id, bin] defining the rows
        self.counts = draw_counts(len(self.patients), n_boot, seed)
        self.n_boot, self.seed, self.cache = n_boot, seed, {}

    def add(self, key, off: int, pred_df: pd.DataFrame):
        d = self.rows[off].merge(pred_df, on=["stay_id", "bin"], how="inner")
        pidx = np.searchsorted(self.patients, d["stay_id"].values)
        y, p = d["y"].values.astype(int), d["pred"].values
        self.cache[(key, off)] = {"n": int(len(d)), "n_patients": int(d["stay_id"].nunique()),
                                  "auroc": float(roc_auc_score(y, p)), "reps": boot_auroc(y, p, pidx, self.counts)}

    def point(self, key, off):
        c = self.cache[(key, off)]
        return {"n": c["n"], "n_patients": c["n_patients"], "auroc": c["auroc"], "ci": ci(c["reps"])}

    def diff(self, k1, o1, k2, o2) -> dict:
        a, b = self.cache[(k1, o1)], self.cache[(k2, o2)]
        d = a["reps"] - b["reps"]
        used = int((~np.isnan(d)).sum())
        return {"a": [k1, o1], "b": [k2, o2], "auroc_a": a["auroc"], "auroc_b": b["auroc"],
                "n_a": a["n"], "n_b": b["n"], "diff": a["auroc"] - b["auroc"], "ci": ci(d),
                "p_diff_le_zero": float(np.nanmean(d <= 0) if used else np.nan),
                "n_boot_used": used, "n_boot": self.n_boot, "seed": self.seed, "n_patients_resampled": int(len(self.patients))}


# ---------------------------------------------------------------- driver

def _fit(fs_name, cols, off, probe, frame):
    X = frame[cols].values.astype(np.float64)
    y = frame["y"].values.astype(int)
    g = frame["stay_id"].values
    p = cv_predict(X, y, g, PROBES[probe])
    return fs_name, probe, off, pd.DataFrame({"stay_id": g, "bin": frame["bin"].values, "y": y, "pred": p})


def run(checkpoint: str, db_path: str, cohort_label: str, out_json: str, n_boot: int = 2000, seed: int = 42,
        n_jobs: int = 8, gb_offsets=(0, FAR), skip_gb: bool = False) -> dict:
    from joblib import Parallel, delayed
    t0 = time.time()
    with open(checkpoint, "rb") as f:
        ck = pickle.load(f)
    state_4h, feature_names = ck["state_4h"], list(ck["feature_names"])
    # E as the notebook builds it (variants["E_physiology_only"], same row order as state_4h)
    e_cols = [c for c in feature_names if c not in ("sofa_total", "sofa_cardio")]
    e_matches = bool(np.allclose(state_4h[e_cols].values.astype(float), ck["variants"]["E_physiology_only"]))
    a_matches = bool(np.allclose(state_4h[feature_names].values.astype(float), ck["variants"]["A_full"]))
    stays = np.unique(state_4h["stay_id"].values)
    vaso = load_vaso_dose_clean(db_path, stays)
    feats = bin_features(vaso)
    state, checks = augment_state(state_4h, feats)
    checks.update({"E_matches_notebook_variant": e_matches, "A_matches_notebook_variant": a_matches,
                   "vaso_dose_clean_rows": int(len(vaso)), "stays": int(len(stays))})
    print(f"[{cohort_label}] features built in {time.time() - t0:.0f}s: {json.dumps(checks)}", flush=True)
    if checks["label_vs_prev_action_next_bin_mismatches"] != 0:
        print("WARNING: prev_action does not reproduce the notebook's action_next rule", flush=True)

    fsets = feature_sets(feature_names)
    all_cols = sorted({c for cols in fsets.values() for c in cols}, key=lambda c: (c not in feature_names, c))
    frames = h3.offset_frames(state, all_cols, OFFSETS, offset_mode="bins")
    tasks = [] if skip_gb else [(n, cols, off, "gb") for n, cols in fsets.items() for off in gb_offsets]
    tasks += [(n, cols, off, "logreg") for n, cols in fsets.items() for off in OFFSETS]  # slow gb fits first
    res = Parallel(n_jobs=n_jobs, verbose=5)(delayed(_fit)(n, c, o, p, frames[o]) for n, c, o, p in tasks)
    preds = {(n, p, o): df for n, p, o, df in res}
    print(f"[{cohort_label}] {len(tasks)} fits done at {time.time() - t0:.0f}s", flush=True)

    keys = lambda df: df[["stay_id", "bin"]]
    common0 = keys(frames[0]).merge(keys(frames[FAR]), on=["stay_id", "bin"])
    common = {off: common0.merge(keys(frames[off]), on=["stay_id", "bin"]) for off in OFFSETS}
    own = {off: keys(frames[off]) for off in OFFSETS}
    U = {"common": Universe("common", common0["stay_id"].values, common, n_boot, seed),
         "own": Universe("own", frames[0]["stay_id"].values, own, n_boot, seed)}
    for u in U.values():
        for (n, p, o), df in preds.items():
            u.add((n, p), o, df)
    print(f"[{cohort_label}] bootstrap done at {time.time() - t0:.0f}s", flush=True)

    out = {"_note": "Aggregates only (counts, AUROCs, CIs); no patient-level rows. " + EXPLORATORY_NOTE,
           "cohort": cohort_label, "checkpoint": checkpoint, "db": db_path, "offset_mode": "bins",
           "offsets": list(OFFSETS), "far_offset": FAR, "n_boot": n_boot, "seed": seed,
           "feature_sets": {k: (v if len(v) < 6 else f"{len(v)} columns: " + ", ".join(v)) for k, v in fsets.items()},
           "checks": checks, "universes": {}}
    for uname, u in U.items():
        probes = ["logreg"] + ([] if skip_gb else ["gb"])
        r = {"auroc": {}, "delta_0_minus_k": {}, "contrasts": {}}
        for p in probes:
            offs = OFFSETS if p == "logreg" else gb_offsets
            r["auroc"][p] = {n: {str(o): u.point((n, p), o) for o in offs} for n in fsets}
            r["delta_0_minus_k"][p] = {n: {str(k): u.diff((n, p), 0, (n, p), k) for k in offs if k != 0} for n in fsets}
            c = {}
            for o in offs:
                c[f"A_minus_E@{o}"] = u.diff(("A", p), o, ("E", p), o)
                c[f"AI_minus_EI@{o}"] = u.diff(("A+I", p), o, ("E+I", p), o)
                c[f"EI_minus_I@{o}"] = u.diff(("E+I", p), o, ("I", p), o)
                c[f"AI_minus_A@{o}"] = u.diff(("A+I", p), o, ("A", p), o)
            for o in (0, FAR):
                for other in ("P", "P_dose", "I", "P+I", "E+P"):
                    c[f"A_minus_{other}@{o}"] = u.diff(("A", p), o, (other, p), o)
            # does A decay faster than the persistence-only predictors?  (Delta_A - Delta_X)
            for other in ("P", "I", "E", "A+I", "E+I"):
                d_a = u.cache[(("A", p), 0)]["reps"] - u.cache[(("A", p), FAR)]["reps"]
                d_o = u.cache[((other, p), 0)]["reps"] - u.cache[((other, p), FAR)]["reps"]
                pt = (u.cache[(("A", p), 0)]["auroc"] - u.cache[(("A", p), FAR)]["auroc"]) - \
                     (u.cache[((other, p), 0)]["auroc"] - u.cache[((other, p), FAR)]["auroc"])
                c[f"DeltaA_minus_Delta{other}"] = {"diff": float(pt), "ci": ci(d_a - d_o)}
            r["contrasts"][p] = c
        out["universes"][uname] = r
    # reproduction of the frozen H3 result for A (logreg): must equal experiment5_h3_paired_bootstrap_bins.json
    dA_c, dA_o = out["universes"]["common"]["delta_0_minus_k"]["logreg"]["A"]["8"], out["universes"]["own"]["delta_0_minus_k"]["logreg"]["A"]["8"]
    out["h3_reproduction_A_logreg"] = {"common_rows": {k: dA_c[k] for k in ("auroc_a", "auroc_b", "diff", "ci", "n_a")},
                                       "own_rows": {k: dA_o[k] for k in ("auroc_a", "auroc_b", "diff", "ci", "n_a", "n_b")}}
    out["runtime_s"] = round(time.time() - t0, 1)
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[{cohort_label}] wrote {out_json} in {out['runtime_s']}s", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", required=True, help="notebook results/exp5_checkpoint_inputs.pkl")
    ap.add_argument("--db", required=True, help="DuckDB MIMIC-IV build (opened read-only)")
    ap.add_argument("--cohort", required=True, help="label, e.g. 13192")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-jobs", type=int, default=8)
    ap.add_argument("--skip-gb", action="store_true")
    a = ap.parse_args()
    run(a.checkpoint, a.db, a.cohort, a.out, a.n_boot, a.seed, a.n_jobs, skip_gb=a.skip_gb)


if __name__ == "__main__":
    main()
