"""Decision 6(a): the H3 offset-decay test on rows with no infusion running at the decision time
(exploratory, outside the decision rule; docs/DECISIONS_H3.md, Decision 6 and the 2026-10-07
amendment).

Definition (approved, as run in the label alignment analysis as L2): "no infusion running at tau"
over all six label drugs, start <= tau < end, tau = 4 * (bin + 1) h after ICU admission, the end
of the state window [tau - 4, tau). Rows are filtered at SCORING ONLY: the per-row predictions of
the frozen H3 primary analysis (bin-index offsets, logreg, grouped 5-fold CV) are kept exactly as
fitted, nothing is refit.

Row identity. In bins mode a row at every offset is the STATE row (stay_id, bin); offset k only
changes its label to the action_next of bin + k. Common rows (Decision 2) are the (stay_id, bin)
pairs present at offsets 0 and 8. The on-at-tau indicator is evaluated once per (stay_id, bin) at
that state's tau, which is the offset-0 decision time, and the same rows are dropped at both
offsets. Own rows (sensitivity): each offset's own rows, filtered by the same per-state indicator.

Test: scripts/h3_paired_bootstrap.paired_cluster_bootstrap unchanged (patient-level paired
bootstrap, 2,000 resamples, seed 42, percentile CI, Prediction A iff CI lower bound > 0 and
Delta >= 0.10). Writes aggregates only.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h3_paired_bootstrap import paired_cluster_bootstrap  # noqa: E402

INTERVAL = 4.0
# Label drugs and unit filter: notebook cell 9, as in scripts/exp_label_alignment.py (PR #5).
VASO_ITEMS = {221906: "norepi", 221289: "epi", 221662: "dopamine", 221653: "dobutamine",
              221749: "phenylephrine", 222315: "vasopressin"}
DOSE_SCORED = {"norepi", "epi", "dopamine", "dobutamine"}
HEADER = ("exploratory, outside the H3 decision rule; Decision 6 outputs were seen before the "
          "definitions were approved, so this analysis is not blind")
KEEP = ["n_rows_a", "n_rows_b", "n_patients", "auroc_a", "auroc_b", "delta", "delta_ci_lo",
        "delta_ci_hi", "auroc_a_ci", "auroc_b_ci", "p_delta_ge_threshold", "p_delta_le_zero",
        "threshold", "n_boot", "n_boot_used", "n_boot_skipped_single_class", "seed",
        "prediction_A_supported", "restricted_rows"]


def extract_vaso(db_path: str, stay_ids) -> pd.DataFrame:
    """Same query as exp_label_alignment.extract_vaso (PR #5), read-only."""
    import duckdb
    con = duckdb.connect(os.path.expanduser(db_path), read_only=True)
    con.register("ids", pd.DataFrame({"stay_id": np.asarray(stay_ids, dtype=np.int64)}))
    items = ",".join(str(k) for k in VASO_ITEMS)
    sql = f"""
    SELECT ie.stay_id, ie.itemid, ie.rate, ie.rateuom,
           date_diff('minute', i.intime, ie.starttime) / 60.0 AS start_hours_from_admit,
           date_diff('minute', i.intime, ie.endtime) / 60.0 AS end_hours_from_admit
    FROM mimiciv_icu.inputevents ie
    JOIN mimiciv_icu.icustays i ON ie.stay_id = i.stay_id
    JOIN ids ON ie.stay_id = ids.stay_id
    WHERE ie.itemid IN ({items}) AND ie.amount > 0 AND ie.endtime IS NOT NULL
    """
    raw = con.execute(sql).df()
    con.close()
    raw["drug"] = raw["itemid"].map(VASO_ITEMS)
    bad = raw["drug"].isin(DOSE_SCORED) & (raw["rateuom"] != "mcg/kg/min")
    clean = raw[~bad].copy()
    return clean.rename(columns={"start_hours_from_admit": "time_bin_start",
                                 "end_hours_from_admit": "time_bin_end"})[
        ["stay_id", "drug", "time_bin_start", "time_bin_end"]]


def infusion_flags(vaso: pd.DataFrame, rows: pd.DataFrame, interval: float = INTERVAL) -> pd.DataFrame:
    """Per (stay_id, bin) row: on_at_tau (start <= tau < end, the PR #4 / #5 indicator) and L1
    (an infusion active in [tau, tau + interval), used only to check against action_next)."""
    sids = rows["stay_id"].values
    taus = (rows["bin"].values.astype(float) + 1.0) * interval
    on = np.zeros(len(rows), dtype=bool)
    l1 = np.zeros(len(rows), dtype=bool)
    by_stay = {sid: g for sid, g in vaso.groupby("stay_id")}
    pos = pd.Series(np.arange(len(rows))).groupby(sids).apply(lambda s: s.values).to_dict()
    for sid, idx in pos.items():
        g = by_stay.get(sid)
        if g is None:
            continue
        tau = taus[idx][:, None]
        st = g["time_bin_start"].values.astype(float)[None, :]
        en = g["time_bin_end"].values.astype(float)[None, :]
        on[idx] = ((st <= tau) & (tau < en)).any(1)
        l1[idx] = ((st < tau + interval) & (en > tau)).any(1)
    return pd.DataFrame({"stay_id": sids, "bin": rows["bin"].values, "on_at_tau": on, "L1": l1})


def restrict_off_at_tau(p0: pd.DataFrame, p8: pd.DataFrame, flags: pd.DataFrame, common: bool = True):
    """Scoring-only row restriction. p0, p8: prediction frames (stay_id, bin, y, pred), untouched
    apart from row selection. flags: one row per state (stay_id, bin) with on_at_tau.

    common=True: rows present at both offsets, then those off at tau (tau of the state row, the
    offset-0 decision time); both returned frames hold the same (stay_id, bin) rows.
    common=False: each offset's own rows, each filtered by the same per-state indicator.
    Every prediction row must have an indicator; a missing one raises."""
    f = flags[["stay_id", "bin", "on_at_tau"]]
    if f.duplicated(["stay_id", "bin"]).any():
        raise ValueError("indicator has duplicate (stay_id, bin) rows")

    def tag(p):
        m = p.merge(f, on=["stay_id", "bin"], how="left", validate="one_to_one")
        if m["on_at_tau"].isna().any():
            raise ValueError("prediction rows without an on-at-tau indicator")
        return m

    a, b = tag(p0), tag(p8)
    if common:
        keys = a[["stay_id", "bin"]].merge(b[["stay_id", "bin"]], on=["stay_id", "bin"])
        a = a.merge(keys, on=["stay_id", "bin"])
        b = b.merge(keys, on=["stay_id", "bin"])
    a = a[~a["on_at_tau"].astype(bool)].drop(columns="on_at_tau").reset_index(drop=True)
    b = b[~b["on_at_tau"].astype(bool)].drop(columns="on_at_tau").reset_index(drop=True)
    return a, b


def _slim(r: dict) -> dict:
    return {k: r[k] for k in KEEP}


def run(run_dir: Path, db_path: str, out_path: Path, cohort: str, n_boot: int, seed: int) -> dict:
    t0 = time.time()
    res_dir = run_dir / "notebook" / "results"
    p0 = pd.read_parquet(res_dir / "experiment5_predictions_offset0_bins.parquet")
    p8 = pd.read_parquet(res_dir / "experiment5_predictions_offset8_bins.parquet")
    saved = json.load(open(res_dir / "experiment5_h3_paired_bootstrap_bins.json"))
    ck = pickle.load(open(res_dir / "exp5_checkpoint_inputs.pkl", "rb"))
    st = ck["state_4h"][["stay_id", "bin", "action_next"]].reset_index(drop=True)
    del ck

    vaso = extract_vaso(db_path, np.unique(st["stay_id"].values))
    flags = infusion_flags(vaso, st[["stay_id", "bin"]])
    l1_match = int((flags["L1"].values == st["action_next"].values.astype(bool)).sum())
    chk = p0.merge(st, on=["stay_id", "bin"], how="left", validate="one_to_one")
    y0_match = int((chk["y"].values == chk["action_next"].values.astype(int)).sum())
    checks = {
        "L1_rebuilt_equals_action_next": {"rows_matching": l1_match, "rows": int(len(st))},
        "offset0_y_equals_action_next": {"rows_matching": y0_match, "rows": int(len(p0))},
        "offset0_rows_equal_state_rows": bool(len(p0) == len(st) and chk["action_next"].notna().all()),
        "offset8_rows_subset_of_offset0": bool(len(p8.merge(p0[["stay_id", "bin"]], on=["stay_id", "bin"])) == len(p8)),
        "state_rows_off_at_tau": int((~flags["on_at_tau"]).sum()),
    }
    print(f"[{time.time()-t0:.0f}s] {cohort}: checks {checks}", flush=True)

    sanity = paired_cluster_bootstrap(p0, p8, n_boot, seed, restrict=True)
    ref = saved["restricted"]
    sanity_match = {k: (round(sanity[k], 4) == round(ref[k], 4)) for k in ("delta", "delta_ci_lo", "delta_ci_hi", "auroc_a", "auroc_b")}
    sanity_match["n_rows"] = sanity["n_rows_a"] == ref["n_rows_a"]
    print(f"[{time.time()-t0:.0f}s] sanity Delta={sanity['delta']:.4f} ({sanity['delta_ci_lo']:.4f},{sanity['delta_ci_hi']:.4f}) "
          f"vs saved {ref['delta']:.4f} ({ref['delta_ci_lo']:.4f},{ref['delta_ci_hi']:.4f}) match={sanity_match}", flush=True)

    out = {"note": HEADER, "cohort": cohort,
           "inputs": "saved per-row predictions of the H3 run (bins mode, offsets 0 and 8, logreg), "
                     "the run's checkpoint state rows, infusions re-extracted read-only from the DuckDB build",
           "definitions": {
               "tau": "4 * (bin + 1) hours after ICU admission, end of the state window [tau-4, tau)",
               "off_at_tau": "no label drug (six drugs) with start <= tau < end; Decision 6(a), L2 row set of PR #5",
               "row_identity": "bins mode: a row is the state (stay_id, bin) at every offset; offset 8 relabels it "
                               "with action_next of bin + 8. The indicator is taken at the state's tau "
                               "(offset-0 decision time) and applied to that same row at both offsets",
               "common_rows": "rows present at offsets 0 and 8, then restricted to off at tau (primary for 6a)",
               "own_rows": "each offset's own rows, restricted to off at tau (sensitivity)",
               "scoring_only": "predictions as fitted in the H3 run, no refit",
               "decision_rule": "Prediction A iff delta CI lower bound > 0 and delta >= 0.10 (Decision 5)",
               "guard": "Decision 6: if Prediction A holds on all rows but the decay disappears on these rows, "
                        "report as decay attributable to continuation structure"},
           "checks": checks,
           "sanity_unrestricted_H3_common_rows": {"recomputed": _slim(sanity), "saved_delta": ref["delta"],
                                                   "saved_ci": [ref["delta_ci_lo"], ref["delta_ci_hi"]],
                                                   "matches_to_4_decimals": sanity_match}}
    for name, common in (("common_rows_off_at_tau", True), ("own_rows_off_at_tau", False)):
        a, b = restrict_off_at_tau(p0, p8, flags, common=common)
        r = paired_cluster_bootstrap(a, b, n_boot, seed, restrict=common)
        r = _slim(r)
        r["prevalence_offset0"] = float(a["y"].mean())
        r["prevalence_offset8"] = float(b["y"].mean())
        r["n_patients_offset0"] = int(a["stay_id"].nunique())
        r["n_patients_offset8"] = int(b["stay_id"].nunique())
        out[name] = r
        print(f"[{time.time()-t0:.0f}s] {name}: n0={r['n_rows_a']:,} n8={r['n_rows_b']:,} pts={r['n_patients']:,} "
              f"AUROC0={r['auroc_a']:.4f} AUROC8={r['auroc_b']:.4f} Delta={r['delta']:.4f} "
              f"({r['delta_ci_lo']:.4f},{r['delta_ci_hi']:.4f}) A={r['prediction_A_supported']}", flush=True)
    out["runtime_s"] = round(time.time() - t0, 1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--db", default="~/orcd/scratch/sail/mimic4.db")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    run(a.run_dir, a.db, a.out, a.cohort, a.n_boot, a.seed)


if __name__ == "__main__":
    main()
