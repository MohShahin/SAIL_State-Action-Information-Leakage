"""Calibration targets for the synthetic ground-truth experiment (scripts/simulate_sail.py).

EXPLORATORY, not pre-registered; does not change the H3 decision.

Runs on the cluster only. Reads the notebook's in-memory Experiment 5 inputs
(exp5_checkpoint_inputs.pkl: state_4h with stay_id, bin, the 25 state features and action_next)
and the six label drugs' infusion intervals from the DuckDB build (opened READ-ONLY), and writes
ONE JSON of cohort-level aggregates: counts, rates, histograms, autocorrelations and AUROCs. No
stay_id, no per-patient row and no prediction leaves this process.

What it measures (all on the modeling rows unless stated):
  rows per stay histogram, first-bin and bin-presence counts
  fraction of rows with any of the six label drugs running at tau (start <= tau < end)
  next-action prevalence, and the label rate given on / off at tau
  bin-level infusion occupancy on the 18-bin grid (any of the six drugs active in the bin window,
    the action label's own definition before the one-bin shift): run lengths in bins (with left /
    right censoring flags), runs per stay, fraction of stays ever on, occupancy at bin 0
  the cardiovascular subscore distribution given on / off at tau
  MAP, heart rate and lactate moments (clipped to a physiologic range), and their pooled
    within-stay lag-k correlation (bins mode)
  real references, by the frozen H3 functions (bins mode, common rows, logreg, 5-fold grouped CV,
    2,000 resamples, seed 42): variant E (no sofa_cardio, no sofa_total) and the on-at-tau
    indicator alone; variant A is read from the run's own H3 JSON, not recomputed.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h3_paired_bootstrap as h3  # noqa: E402
from simulate_sail import PROBE_LOGREG, cv_predict, run_lengths  # noqa: E402

VASO_ITEMS = {221906: "norepi", 221289: "epi", 221662: "dopamine", 221653: "dobutamine",
              221749: "phenylephrine", 222315: "vasopressin"}
DOSE_SCORED = ("norepi", "epi", "dopamine", "dobutamine")
N_BINS, INTERVAL = 18, 4


def infusion_intervals(db_path: str, stay_ids: np.ndarray) -> pd.DataFrame:
    """The notebook's vaso_bins_df (cell 9): six drugs, amount > 0, endtime present, dose-scored
    drugs kept only in mcg/kg/min; hours from ICU intime by unit-boundary counting (the port)."""
    con = duckdb.connect(db_path, read_only=True)
    con.register("cohort_ids", pd.DataFrame({"stay_id": stay_ids.astype("int64")}))
    items = ",".join(str(k) for k in VASO_ITEMS)
    df = con.execute(f"""
        SELECT ie.stay_id, ie.itemid, ie.rateuom,
               date_diff('minute', i.intime, ie.starttime) / 60.0 AS s,
               date_diff('minute', i.intime, ie.endtime) / 60.0 AS e
        FROM mimiciv_icu.inputevents ie
        JOIN mimiciv_icu.icustays i ON i.stay_id = ie.stay_id
        JOIN cohort_ids c ON c.stay_id = ie.stay_id
        WHERE ie.itemid IN ({items}) AND ie.amount > 0 AND ie.endtime IS NOT NULL
    """).df()
    con.close()
    df["drug"] = df["itemid"].map(VASO_ITEMS)
    bad = df["drug"].isin(DOSE_SCORED) & (df["rateuom"] != "mcg/kg/min")
    return df[~bad][["stay_id", "drug", "s", "e"]].reset_index(drop=True)


def occupancy_and_on(iv: pd.DataFrame, stay_ids: np.ndarray):
    """occ[i, t] = any infusion overlapping bin t's window [4t, 4t+4); on[i, t] = any infusion
    running at tau = 4(t+1) (start <= tau < end)."""
    pos = {s: k for k, s in enumerate(stay_ids)}
    occ = np.zeros((len(stay_ids), N_BINS), dtype=bool)
    on = np.zeros((len(stay_ids), N_BINS), dtype=bool)
    lo = np.arange(N_BINS) * INTERVAL
    hi = lo + INTERVAL
    for sid, s, e in zip(iv["stay_id"].values, iv["s"].values, iv["e"].values):
        k = pos.get(sid)
        if k is None:
            continue
        occ[k] |= (s < hi) & (e > lo)
        on[k] |= (s <= hi) & (hi < e)
    return occ, on


def lag_corr(df: pd.DataFrame, col: str, k: int) -> float:
    a = df[["stay_id", "bin", col]]
    b = a.assign(bin=a["bin"] - k)
    m = a.merge(b, on=["stay_id", "bin"], suffixes=("", "_k"))
    return float(np.corrcoef(m[col].values, m[col + "_k"].values)[0, 1])


def hist(values, lo, hi) -> dict:
    v = np.asarray(values)
    return {str(i): int((v == i).sum()) for i in range(lo, hi + 1)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkl", required=True)
    ap.add_argument("--h3-json", required=True, help="the run's own experiment5_h3_paired_bootstrap_bins.json")
    ap.add_argument("--db", default=os.path.expanduser("~/orcd/scratch/sail/mimic4.db"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args(argv)

    d = pickle.load(open(a.pkl, "rb"))
    st = d["state_4h"].sort_values(["stay_id", "bin"]).reset_index(drop=True)
    feats = list(d["feature_names"])
    stay_ids = np.unique(st["stay_id"].values)
    iv = infusion_intervals(a.db, stay_ids)
    occ, on = occupancy_and_on(iv, stay_ids)
    pos = np.searchsorted(stay_ids, st["stay_id"].values)
    b = st["bin"].values.astype(int)
    st["on_tau"] = on[pos, b].astype(int)
    y = st["action_next"].values.astype(int)

    out = {"exploratory": "exploratory, not pre-registered; does not change the H3 decision",
           "source": "13,192-stay primary cohort, notebook inputs of the full run from commit 1d3f170",
           "n_stays": int(len(stay_ids)), "n_rows": int(len(st))}
    rps = st.groupby("stay_id").size().values
    out["rows_per_stay_hist"] = hist(rps, 1, N_BINS)
    out["rows_per_stay_mean"] = float(rps.mean())
    first = st.groupby("stay_id")["bin"].min().values
    last = st.groupby("stay_id")["bin"].max().values
    out["first_bin_hist"] = hist(first, 0, N_BINS - 1)
    out["last_bin_hist"] = hist(last, 0, N_BINS - 1)
    out["rows_with_gap_before"] = int((st.groupby("stay_id")["bin"].diff().fillna(1) > 1).sum())
    out["rows_by_bin"] = hist(b, 0, N_BINS - 1)

    on_t = st["on_tau"].values.astype(bool)
    out["frac_on_at_tau"] = float(on_t.mean())
    out["n_on_at_tau"] = int(on_t.sum())
    out["next_action_prevalence"] = float(y.mean())
    out["label_rate_given_on"] = float(y[on_t].mean())
    out["label_rate_given_off"] = float(y[~on_t].mean())
    out["indicator_auroc_offset0_all_rows"] = float(roc_auc_score(y, on_t.astype(float)))

    # bin-level occupancy on the full 18-bin grid of every stay
    lens, lcens, rcens = [], [], []
    runs_per_stay = []
    for row in occ:
        r = run_lengths(row)
        runs_per_stay.append(len(r))
        for start, length in r:
            lens.append(length); lcens.append(start == 0); rcens.append(start + length == N_BINS)
    lens, lcens, rcens = map(np.asarray, (lens, lcens, rcens))
    unc = ~lcens & ~rcens
    out["occupancy"] = {
        "frac_bins_occupied": float(occ.mean()),
        "frac_stays_ever_on": float(occ.any(axis=1).mean()),
        "frac_occupied_at_bin0": float(occ[:, 0].mean()),
        "runs_per_stay_hist": hist(runs_per_stay, 0, 9),
        "n_runs": int(len(lens)), "n_runs_uncensored": int(unc.sum()),
        "run_length_hist_all": hist(lens, 1, N_BINS),
        "run_length_hist_uncensored": hist(lens[unc], 1, N_BINS),
        "run_length_hist_left_censored": hist(lens[lcens & ~rcens], 1, N_BINS),
        "run_length_mean_all": float(lens.mean()),
        "run_length_mean_uncensored": float(lens[unc].mean()),
        "run_length_median_all": float(np.median(lens)),
    }
    on_lens = [L for row in on for _, L in run_lengths(row)]
    out["on_at_tau_run_length_hist"] = hist(on_lens, 1, N_BINS)

    cardio = st["sofa_cardio"].round().astype(int).values
    out["sofa_cardio_hist_on"] = hist(cardio[on_t], 0, 4)
    out["sofa_cardio_hist_off"] = hist(cardio[~on_t], 0, 4)
    out["frac_on_with_dose_scored_cardio"] = float((cardio[on_t] >= 2).mean())

    # moments on values clipped to a physiologic range (the state table carries a few charting
    # outliers, e.g. MAP in the thousands, that dominate raw means, SDs and correlations)
    mom = {}
    clip = {"mbp": (20, 200), "heart_rate": (20, 250), "lactate": (0, 30), "sofa_total": (0, 24)}
    for col, (lo, hi) in clip.items():
        cl = st[["stay_id", "bin"]].assign(**{col: st[col].clip(lo, hi).values})
        v = cl[col].values
        q1, q2, q3 = np.percentile(v, [25, 50, 75])
        mom[col] = {"clip_range": [lo, hi], "n_clipped": int(((st[col] < lo) | (st[col] > hi)).sum()),
                    "mean": float(v.mean()), "sd": float(v.std()), "median": float(q2), "iqr": float(q3 - q1),
                    "mean_on": float(v[on_t].mean()), "mean_off": float(v[~on_t].mean()),
                    "lag_corr": {str(k): lag_corr(cl, col, k) for k in (1, 2, 4, 8)}}
    out["moments"] = mom
    out["frac_mbp_below_70"] = float((st["mbp"].values < 70).mean())

    # label persistence on the bin grid: P(y_{t+k} | y_t) and P(y_{t+k} | on_t)
    lab = st[["stay_id", "bin", "action_next", "on_tau"]]
    pers = {}
    for k in (1, 2, 4, 8):
        m = lab.merge(lab.assign(bin=lab["bin"] - k)[["stay_id", "bin", "action_next"]],
                      on=["stay_id", "bin"], suffixes=("", "_k"))
        pers[str(k)] = {"p_yk_given_y1": float(m.loc[m.action_next == 1, "action_next_k"].mean()),
                        "p_yk_given_y0": float(m.loc[m.action_next == 0, "action_next_k"].mean()),
                        "p_yk_given_on": float(m.loc[m.on_tau == 1, "action_next_k"].mean()),
                        "p_yk_given_off": float(m.loc[m.on_tau == 0, "action_next_k"].mean())}
    out["label_persistence"] = pers

    # real references with the frozen H3 functions (bins mode, common rows primary)
    a_json = json.load(open(a.h3_json))
    out["real_A_h3_bins"] = {k: a_json["restricted"][k] for k in
                             ("auroc_a", "auroc_b", "delta", "delta_ci_lo", "delta_ci_hi", "prediction_A_supported")}
    e_feats = [f for f in feats if f not in ("sofa_cardio", "sofa_total")]
    fr = h3.offset_frames(st, e_feats, offsets=(0, 8), offset_mode="bins")
    pr = h3.predict_offsets(fr, e_feats, PROBE_LOGREG, cv_predict)
    r = h3.paired_cluster_bootstrap(pr[0], pr[8], n_boot=a.n_boot, seed=42, restrict=True)
    out["real_E_h3_bins"] = {k: r[k] for k in ("auroc_a", "auroc_b", "delta", "delta_ci_lo", "delta_ci_hi",
                                               "prediction_A_supported", "n_rows_a", "n_patients")}
    fr = h3.offset_frames(st, ["on_tau"], offsets=(0, 8), offset_mode="bins")
    pi = {o: f[["stay_id", "bin", "y"]].assign(pred=f["on_tau"].values.astype(float)) for o, f in fr.items()}
    r = h3.paired_cluster_bootstrap(pi[0], pi[8], n_boot=a.n_boot, seed=42, restrict=True)
    out["real_indicator_h3_bins"] = {k: r[k] for k in ("auroc_a", "auroc_b", "delta", "delta_ci_lo", "delta_ci_hi",
                                                       "prediction_A_supported", "n_rows_a", "n_patients")}

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, dict)}, indent=1))
    print("occupancy", json.dumps(out["occupancy"]))
    print("real E", out["real_E_h3_bins"]); print("real indicator", out["real_indicator_h3_bins"])


if __name__ == "__main__":
    main()
