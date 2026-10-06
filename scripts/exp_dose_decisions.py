"""Exploratory, not pre-registered; does not change the H3 decision.

Does the SOFA cardiovascular mechanism (Theorem 1: once any dose-scored infusion runs, SOFA cardio
equals the vasopressor dose tier) matter for decisions that carry information? Under the published
label every row with a label drug running at tau is positive, so those rows carry none. Here the
analysis is restricted to exactly those rows (any of the six label drugs running at tau,
start <= tau < end) and the next-bin decision is relabelled as a titration decision:

  STOP   no label drug running at tau + 4h (the next decision time). Under the notebook's overlap
         rule ("active in the next bin") STOP would be 0 on every one of these rows, because an
         infusion running at tau overlaps the next bin by construction; the end of the next bin is
         therefore the first point where stopping is observable.
  UP     not STOP, and the dose tier of the next bin is above the current bin's
  DOWN   not STOP, and the dose tier of the next bin is below the current bin's

Tier definitions (each gives its own UP and DOWN label, all one-vs-rest on the on-at-tau rows):
  tierW  the notebook's SOFA cardio dose tier for a bin (cell 12 window-max rate per drug over the
         4h window, cell 14/31 thresholds). Bin t is compared with bin t + 1. This is the tier the
         requested definition names; note that the next bin's window max includes the infusion
         already running at tau.
  tierP  the same thresholds applied to the rates running at an instant (start <= time < end):
         tau compared with tau + 4h. Sensitivity definition, free of the window-max carry-over.
  NEE    norepinephrine-equivalent dose (Goradia et al., J Crit Care 2021;61:233-240): NE + epi +
         phenylephrine / 10 + dopamine / 100 + vasopressin (U/min) x 2.5, i.e. 0.04 U/min of
         vasopressin = 0.1 mcg/kg/min NE. Vasopressin is charted in units/hour in MIMIC-IV
         (divided by 60) or units/min. Dobutamine is an inotrope and is excluded, as in Goradia.
         Per bin: sum over drugs of each drug's window max. Five levels Komorowski-style: 0 = none,
         1 to 4 = quartiles of the cohort's nonzero bin values.

State variants A, D, E come from the notebook's Experiment 5 checkpoint (row-aligned with
state_4h); F = D + F1 + F2 is recomputed here with the notebook's cell 31 definitions. Probes:
logreg (H3 settings) and gb, both through the notebook's cv_predict (GroupKFold 5 by stay_id,
StandardScaler). Paired patient bootstrap (h3_paired_bootstrap.paired_cluster_bootstrap, 2,000
resamples, seed 42, identical rows) for A minus E and A minus D. Offsets {0, 2, 4} in bins mode:
the features of an on-at-tau row at bin t, the label of the on-at-tau row at bin t + k.

Writes one aggregate JSON per cohort. Nothing patient-level leaves the process.
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
import h3_paired_bootstrap as h3  # noqa: E402  (frozen; imported, never modified)

INTERVAL = 4.0
N_BINS = 18
RANDOM_STATE = 42
VASO_ITEMS = {221906: "norepi", 221289: "epi", 221662: "dopamine", 221653: "dobutamine",
              221749: "phenylephrine", 222315: "vasopressin"}
DOSE_SCORED = ("dopamine", "dobutamine", "epi", "norepi")
LABELS = ("STOP", "UP_tierW", "DOWN_tierW", "UP_tierP", "DOWN_tierP", "UP_NEE", "DOWN_NEE")
VARIANTS = ("A_full", "D_treatment_decomposed", "E_physiology_only", "F_disentangled")
HEADER = ("exploratory, not pre-registered; does not change the H3 decision. Titration labels are this "
          "analysis's own definitions, not the project lead's.")

PROBES = {
    "logreg": lambda: LogisticRegression(max_iter=2000, class_weight="balanced"),
    "gb": lambda: GradientBoostingClassifier(random_state=RANDOM_STATE),
}


# ----------------------------------------------------------------------------------------------
# Notebook definitions (cells 21 and 31), copied so the analysis does not depend on notebook state
# ----------------------------------------------------------------------------------------------
def cv_predict(X, y, groups, probe_fn, n_splits=5):
    cv = GroupKFold(n_splits=n_splits)
    Xs = StandardScaler().fit_transform(X)
    preds = np.zeros(len(y), dtype=float)
    for tr, va in cv.split(Xs, y, groups):
        clf = probe_fn()
        clf.fit(Xs[tr], y[tr])
        preds[va] = clf.predict_proba(Xs[va])[:, 1]
    return preds


def score_dose_tier(dopamine, dobutamine, epi, norepi):
    dopamine = 0.0 if pd.isna(dopamine) else dopamine
    dobutamine = 0.0 if pd.isna(dobutamine) else dobutamine
    epi = 0.0 if pd.isna(epi) else epi
    norepi = 0.0 if pd.isna(norepi) else norepi
    if dopamine > 15 or epi > 0.1 or norepi > 0.1:
        return 4
    if dopamine > 5 or (0 < epi <= 0.1) or (0 < norepi <= 0.1):
        return 3
    if (0 < dopamine <= 5) or dobutamine > 0:
        return 2
    return 0


def tier_vec(dopamine, dobutamine, epi, norepi):
    """Vectorised score_dose_tier (NaN treated as 0, as in the notebook)."""
    dp, db, ep, ne = (np.nan_to_num(np.asarray(a, dtype=float)) for a in (dopamine, dobutamine, epi, norepi))
    t = np.zeros(len(dp), dtype=int)
    t[(dp > 0) & (dp <= 5) | (db > 0)] = 2
    t[(dp > 5) | ((ep > 0) & (ep <= 0.1)) | ((ne > 0) & (ne <= 0.1))] = 3
    t[(dp > 15) | (ep > 0.1) | (ne > 0.1)] = 4
    return t


def merge_intervals(pairs):
    pairs = sorted(pairs)
    merged = []
    for s, e in pairs:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def compute_dose_tier_timeline(stay_events):
    if stay_events.empty:
        return [(0.0, 0)]
    events = []
    for row in stay_events.itertuples(index=False):
        events.append((row.start_hours_from_admit, 1, row.drug, row.rate))
        events.append((row.end_hours_from_admit, -1, row.drug, row.rate))
    events.sort(key=lambda e: (e[0], -e[1]))
    active = {"dopamine": [], "dobutamine": [], "epi": [], "norepi": []}
    timeline = []
    for t, delta, drug, rate in events:
        if delta == 1:
            active[drug].append(rate)
        else:
            active[drug].remove(rate)
        tier = score_dose_tier(max(active["dopamine"], default=0.0), max(active["dobutamine"], default=0.0),
                               max(active["epi"], default=0.0), max(active["norepi"], default=0.0))
        timeline.append((t, tier))
    return timeline


def f1_f2(vaso_dose_clean, stay_ids, taus):
    """Notebook cell 31 F1 (hours on a dose-scored vasopressor at tau) and F2 (hours since the last
    dose-tier change at or before tau), for rows given as parallel arrays."""
    grp = vaso_dose_clean[vaso_dose_clean["drug"].isin(DOSE_SCORED)]
    merged, changes = {}, {}
    for sid, g in grp.groupby("stay_id"):
        merged[sid] = merge_intervals(list(zip(g["start_hours_from_admit"], g["end_hours_from_admit"])))
        ch, prev = [], None
        for ts, tier in compute_dose_tier_timeline(g):
            if tier != prev:
                ch.append((ts, tier)); prev = tier
        changes[sid] = ch
    f1 = np.zeros(len(taus)); f2 = np.zeros(len(taus))
    for i, (sid, tau) in enumerate(zip(stay_ids, taus)):
        for a, b in merged.get(sid, []):
            if a <= tau < b:
                f1[i] = tau - a
                break
        last = 0.0
        for ts, _t in changes.get(sid, []):
            if ts <= tau:
                last = ts
            else:
                break
        f2[i] = tau - last
    return f1, f2


# ----------------------------------------------------------------------------------------------
# Dose extraction (notebook cell 9, read-only DuckDB, cohort taken from the checkpoint)
# ----------------------------------------------------------------------------------------------
def extract_vaso_dose_clean(db_path: str, stay_ids) -> pd.DataFrame:
    import duckdb
    con = duckdb.connect(db_path, read_only=True)
    con.register("cohort_ids", pd.DataFrame({"stay_id": np.asarray(stay_ids, dtype=np.int64)}))
    items = ",".join(str(k) for k in VASO_ITEMS)
    sql = f"""
    SELECT ie.stay_id, ie.itemid, ie.starttime, ie.endtime, ie.rate, ie.rateuom, ie.amount,
           date_diff('minute', c.intime, ie.starttime) / 60.0 AS start_hours_from_admit,
           date_diff('minute', c.intime, ie.endtime) / 60.0 AS end_hours_from_admit
    FROM mimiciv_icu.inputevents ie
    JOIN mimiciv_icu.icustays c ON ie.stay_id = c.stay_id
    JOIN cohort_ids k ON ie.stay_id = k.stay_id
    WHERE ie.itemid IN ({items}) AND ie.amount > 0 AND ie.endtime IS NOT NULL
    """
    raw = con.execute(sql).df()
    con.close()
    raw["drug"] = raw["itemid"].map(VASO_ITEMS)
    bad = raw["drug"].isin(DOSE_SCORED) & (raw["rateuom"] != "mcg/kg/min")
    return raw[~bad].reset_index(drop=True)


# ----------------------------------------------------------------------------------------------
# Per-bin and per-instant dose summaries
# ----------------------------------------------------------------------------------------------
def nee_rate(df: pd.DataFrame) -> np.ndarray:
    """Norepinephrine-equivalent rate per infusion row (Goradia 2021). Rows with an unconvertible
    unit (phenylephrine in mcg/min: no weight available) contribute 0 and are counted separately."""
    r = df["rate"].astype(float).values
    d = df["drug"].values; u = df["rateuom"].values
    out = np.zeros(len(df))
    out[d == "norepi"] = r[d == "norepi"]
    out[d == "epi"] = r[d == "epi"]
    out[d == "dopamine"] = r[d == "dopamine"] / 100.0
    m = (d == "phenylephrine") & (u == "mcg/kg/min"); out[m] = r[m] / 10.0
    m = (d == "vasopressin") & (u == "units/hour"); out[m] = r[m] / 60.0 * 2.5
    m = (d == "vasopressin") & (u == "units/min"); out[m] = r[m] * 2.5
    return np.nan_to_num(out)


def _explode(df: pd.DataFrame, k0: np.ndarray, k1: np.ndarray) -> pd.DataFrame:
    keep = k1 >= k0
    df, k0, k1 = df[keep], k0[keep], k1[keep]
    n = (k1 - k0 + 1).astype(int)
    rep = df.loc[df.index.repeat(n)].copy()
    rep["k"] = np.repeat(k0, n) + (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n))
    return rep


def window_bins(dose: pd.DataFrame, value_col: str, n_bins: int = N_BINS) -> pd.DataFrame:
    """Max of value_col per (stay_id, bin, drug) over infusions overlapping [4b, 4b+4): the
    notebook's build_dose_matrix overlap rule (start < w_end and end > w_start)."""
    s = dose["start_hours_from_admit"].values.astype(float); e = dose["end_hours_from_admit"].values.astype(float)
    k0 = np.maximum(np.floor(s / INTERVAL), 0).astype(int)
    k1 = np.minimum(np.ceil(e / INTERVAL) - 1, n_bins - 1).astype(int)
    rep = _explode(dose[["stay_id", "drug", value_col]].reset_index(drop=True), k0, k1).rename(columns={"k": "bin"})
    return rep.groupby(["stay_id", "bin", "drug"])[value_col].max().unstack("drug")


def instant_points(dose: pd.DataFrame, value_col: str, n_points: int = N_BINS + 1) -> pd.DataFrame:
    """Max of value_col per (stay_id, k, drug) over infusions running at time 4k (start <= 4k < end)."""
    s = dose["start_hours_from_admit"].values.astype(float); e = dose["end_hours_from_admit"].values.astype(float)
    k0 = np.maximum(np.ceil(s / INTERVAL), 1).astype(int)
    k1 = np.minimum(np.ceil(e / INTERVAL) - 1, n_points).astype(int)
    rep = _explode(dose[["stay_id", "drug", value_col]].reset_index(drop=True), k0, k1)
    return rep.groupby(["stay_id", "k", "drug"])[value_col].max().unstack("drug")


def _tier_from_table(t: pd.DataFrame) -> pd.Series:
    cols = {d: (t[d].values if d in t.columns else np.zeros(len(t))) for d in DOSE_SCORED}
    return pd.Series(tier_vec(cols["dopamine"], cols["dobutamine"], cols["epi"], cols["norepi"]), index=t.index)


def build_labels(vaso_dose_clean: pd.DataFrame, rows: pd.DataFrame, nee_cuts=None) -> tuple[pd.DataFrame, dict]:
    """rows: frame with stay_id and bin. Returns a frame aligned to rows with on_tau, the seven
    labels (NaN where on_tau is False), tier/level at bin t, and a dict of diagnostics."""
    dose = vaso_dose_clean.copy()
    dose["nee"] = nee_rate(dose)
    ds = dose[dose["drug"].isin(DOSE_SCORED)]
    # window tiers per bin (dose-scored drugs) and NEE levels per bin (all convertible drugs)
    wt = window_bins(ds, "rate")
    tierW = _tier_from_table(wt.fillna(0.0))
    wn = window_bins(dose, "nee").fillna(0.0).sum(axis=1)
    nz = wn[wn > 0].values
    if nee_cuts is None:
        nee_cuts = np.quantile(nz, [0.25, 0.5, 0.75]) if len(nz) else np.array([np.inf] * 3)
    neeL = pd.Series(np.where(wn.values > 0, 1 + np.searchsorted(nee_cuts, wn.values, side="right"), 0), index=wn.index)
    # instants: any of the six drugs running, and the instant tier
    on_any = instant_points(dose.assign(one=1.0), "one").notna().any(axis=1)
    pt = instant_points(ds, "rate")
    tierP = _tier_from_table(pt.fillna(0.0))

    def look(series, keys_stay, keys_idx, fill):
        idx = pd.MultiIndex.from_arrays([keys_stay, keys_idx])
        return series.reindex(idx).fillna(fill).values

    sid = rows["stay_id"].values; b = rows["bin"].values.astype(int)
    out = pd.DataFrame({"stay_id": sid, "bin": b})
    out["on_tau"] = look(on_any, sid, b + 1, False).astype(bool)
    on_next = look(on_any, sid, b + 2, False).astype(bool)
    tw0, tw1 = look(tierW, sid, b, 0), look(tierW, sid, b + 1, 0)
    tp0, tp1 = look(tierP, sid, b + 1, 0), look(tierP, sid, b + 2, 0)
    nl0, nl1 = look(neeL, sid, b, 0), look(neeL, sid, b + 1, 0)
    stop = ~on_next
    lab = {"STOP": stop,
           "UP_tierW": ~stop & (tw1 > tw0), "DOWN_tierW": ~stop & (tw1 < tw0),
           "UP_tierP": ~stop & (tp1 > tp0), "DOWN_tierP": ~stop & (tp1 < tp0),
           "UP_NEE": ~stop & (nl1 > nl0), "DOWN_NEE": ~stop & (nl1 < nl0)}
    for k, v in lab.items():
        out[k] = np.where(out["on_tau"], v.astype(float), np.nan)
    out["tierW_t"] = tw0; out["tierP_tau"] = tp0; out["neeL_t"] = nl0
    diag = {"nee_quartile_cuts_ne_mcg_kg_min": [float(c) for c in nee_cuts],
            "nee_nonzero_bins": int(len(nz)),
            "phenylephrine_rows_unconvertible_mcg_min": int(((dose["drug"] == "phenylephrine") & (dose["rateuom"] != "mcg/kg/min")).sum()),
            "vasopressin_rows_by_unit": {str(k): int(v) for k, v in dose.loc[dose["drug"] == "vasopressin", "rateuom"].value_counts().items()}}
    return out, diag


# ----------------------------------------------------------------------------------------------
# Modelling
# ----------------------------------------------------------------------------------------------
def offset_frame(lab: pd.DataFrame, label: str, k: int) -> pd.DataFrame:
    """Rows on at tau at bin t, labelled with the on-at-tau row at bin t + k (bins mode)."""
    on = lab[lab["on_tau"]]
    src = on[["stay_id", "bin", "row"]]
    tgt = on[["stay_id", "bin", label]].copy()
    tgt["bin"] = tgt["bin"] - k
    m = src.merge(tgt, on=["stay_id", "bin"], how="inner").rename(columns={label: "y"})
    m["y"] = m["y"].astype(int)
    return m


def _fit_task(X, y, g, bins, probe):
    os.environ["OMP_NUM_THREADS"] = "1"
    p = cv_predict(X, y, g, PROBES[probe])
    return pd.DataFrame({"stay_id": g, "bin": bins, "y": y, "pred": p})


def _boot_task(pa, pb, n_boot, seed):
    r = h3.paired_cluster_bootstrap(pa, pb, n_boot=n_boot, seed=seed, restrict=True)
    keep = ("n_rows_a", "n_patients", "auroc_a", "auroc_b", "delta", "delta_ci_lo", "delta_ci_hi",
            "auroc_a_ci", "auroc_b_ci", "p_delta_le_zero", "n_boot", "n_boot_used", "seed")
    return {k: r[k] for k in keep}


def run(checkpoint, db, out_path, cohort_tag, offsets=(0, 2, 4), probes=("logreg", "gb"), n_boot=2000,
        n_jobs=32, expected_dose_rows=None, expected_on_rows=None, labels=LABELS):
    from joblib import Parallel, delayed
    t0 = time.time()
    with open(checkpoint, "rb") as f:
        ck = pickle.load(f)
    st = ck["state_4h"].reset_index(drop=True)
    variants = ck["variants"]
    vdc = extract_vaso_dose_clean(db, st["stay_id"].unique())
    print(f"[{time.time()-t0:.0f}s] dose rows {len(vdc):,} (expected {expected_dose_rows})", flush=True)
    lab, diag = build_labels(vdc, st[["stay_id", "bin"]])
    lab["row"] = np.arange(len(lab))
    n_on = int(lab["on_tau"].sum())
    print(f"[{time.time()-t0:.0f}s] on-at-tau rows {n_on:,} (expected {expected_on_rows})", flush=True)

    # consistency with the notebook: SOFA cardio in the state equals the window tier where tier >= 2
    sc = st["sofa_cardio"].values; tw = lab["tierW_t"].values
    checks = {"dose_rows": int(len(vdc)), "dose_rows_expected": expected_dose_rows,
              "on_rows": n_on, "on_rows_expected": expected_on_rows,
              "published_label_rate_on_rows": float(st.loc[lab["on_tau"].values, "action_next"].mean()),
              "rows_tierW_ge2_sofa_cardio_mismatch": int(((tw >= 2) & (sc != tw)).sum()),
              "rows_tierW_0_sofa_cardio_gt1": int(((tw == 0) & (sc > 1)).sum())}
    print(f"checks {checks}", flush=True)

    taus = (st["bin"].values + 1) * INTERVAL
    f1, f2 = f1_f2(vdc, st["stay_id"].values, taus)
    X = {"A_full": variants["A_full"], "D_treatment_decomposed": variants["D_treatment_decomposed"],
         "E_physiology_only": variants["E_physiology_only"],
         "F_disentangled": np.column_stack([variants["D_treatment_decomposed"], f1, f2])}
    print(f"[{time.time()-t0:.0f}s] F1/F2 done", flush=True)

    frames = {(lb, k): offset_frame(lab, lb, k) for lb in labels for k in offsets}
    tasks = [(lb, k, v, p) for lb in labels for k in offsets for p in probes for v in VARIANTS]
    preds = Parallel(n_jobs=n_jobs, verbose=5)(
        delayed(_fit_task)(X[v][frames[(lb, k)]["row"].values], frames[(lb, k)]["y"].values,
                           frames[(lb, k)]["stay_id"].values, frames[(lb, k)]["bin"].values, p)
        for lb, k, v, p in tasks)
    P = dict(zip(tasks, preds))
    print(f"[{time.time()-t0:.0f}s] {len(tasks)} CV fits done", flush=True)

    pairs = [("A_full", "E_physiology_only"), ("A_full", "D_treatment_decomposed")]
    btasks = [(lb, k, p, a, b) for lb in labels for k in offsets for p in probes for a, b in pairs]
    boots = Parallel(n_jobs=n_jobs, verbose=5)(
        delayed(_boot_task)(P[(lb, k, a, p)], P[(lb, k, b, p)], n_boot, RANDOM_STATE) for lb, k, p, a, b in btasks)
    B = dict(zip(btasks, boots))
    print(f"[{time.time()-t0:.0f}s] {len(btasks)} bootstraps done", flush=True)

    results = []
    for lb in labels:
        for k in offsets:
            fr = frames[(lb, k)]
            y = fr["y"].values
            ctx = {"tierW_t": lab["tierW_t"].values[fr["row"].values],
                   "tierP_tau": lab["tierP_tau"].values[fr["row"].values],
                   "F1_hours_on": f1[fr["row"].values]}
            entry = {"label": lb, "offset_bins": int(k), "n_rows": int(len(fr)), "n_patients": int(fr["stay_id"].nunique()),
                     "n_positive": int(y.sum()), "prevalence": float(y.mean()),
                     "single_feature_auroc_no_fit": {c: float(roc_auc_score(y, v)) for c, v in ctx.items()},
                     "probes": {}}
            for p in probes:
                entry["probes"][p] = {
                    "auroc": {v: float(roc_auc_score(P[(lb, k, v, p)]["y"], P[(lb, k, v, p)]["pred"])) for v in VARIANTS},
                    "A_minus_E": B[(lb, k, p, "A_full", "E_physiology_only")],
                    "A_minus_D": B[(lb, k, p, "A_full", "D_treatment_decomposed")]}
            results.append(entry)
            print(lb, k, entry["n_rows"], f"prev={entry['prevalence']:.3f}",
                  {p: {v[:1]: round(a, 3) for v, a in entry["probes"][p]["auroc"].items()} for p in probes}, flush=True)

    summary = {"status": HEADER, "cohort": cohort_tag, "n_stays_cohort": int(st["stay_id"].nunique()),
               "n_rows_state": int(len(st)), "checks": checks, "label_diagnostics": diag,
               "settings": {"probes": {"logreg": "LogisticRegression(max_iter=2000, class_weight='balanced')",
                                       "gb": "GradientBoostingClassifier(random_state=42)"},
                            "cv": "notebook cv_predict: StandardScaler on all rows, GroupKFold(5) by stay_id",
                            "bootstrap": f"paired patient bootstrap, {n_boot} resamples, seed {RANDOM_STATE}, identical rows (h3_paired_bootstrap.paired_cluster_bootstrap restrict=True)",
                            "offsets": list(offsets), "offset_mode": "bins (features at t, label of the on-at-tau row at t + k)",
                            "row_set": "rows with any of the six label drugs running at tau (start <= tau < end)",
                            "labels": "one-vs-rest on the on-at-tau rows; see the script docstring",
                            "nee": "Goradia 2021: NE + epi + phenylephrine/10 + dopamine/100 + vasopressin(U/min)*2.5; dobutamine excluded; 5 levels (0, quartiles of nonzero)"},
               "results": results, "runtime_s": round(time.time() - t0, 1)}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {out_path} in {time.time()-t0:.0f}s", flush=True)
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cohort-tag", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--n-jobs", type=int, default=32)
    ap.add_argument("--offsets", default="0,2,4")
    ap.add_argument("--probes", default="logreg,gb")
    ap.add_argument("--labels", default=",".join(LABELS))
    ap.add_argument("--expected-dose-rows", type=int, default=None)
    ap.add_argument("--expected-on-rows", type=int, default=None)
    a = ap.parse_args()
    run(a.checkpoint, a.db, a.out, a.cohort_tag, offsets=tuple(int(x) for x in a.offsets.split(",")),
        probes=tuple(a.probes.split(",")), n_boot=a.n_boot, n_jobs=a.n_jobs,
        expected_dose_rows=a.expected_dose_rows, expected_on_rows=a.expected_on_rows,
        labels=tuple(a.labels.split(",")))
