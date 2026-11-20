"""Label alignment decomposition (exploratory, not pre-registered; does not change the H3 decision).

Question: is the action-recoverability AUROC just the "Off by a Beat" misalignment (Tang, Yao,
Wiens, Parbhoo, npj Digital Medicine 9, 360, 2026: 49 of 57 sepsis RL papers pair each action with
a state that already reflects it)? And does FORMAL_ANALYSIS.md section 1.1's "zero overlap" sentence
hold for the infusions that make the label positive?

Same states as the notebook (state_4h rows, variants A_full and E_physiology_only, logreg probe
with the notebook's cv_predict; gb as a check), offset 0, decision time tau = 4 * (bin + 1). The
state window is [tau - 4, tau). Labels, all on the same (stay_id, bin) rows unless stated:

  L0 contemporaneous  any label-drug infusion active in [tau - 4, tau), the state's own bin (the
                      misaligned convention Tang et al. describe)
  L1 published        any infusion active in [tau, tau + 4): the notebook's action_next
  L2 initiation       L1 on the rows with no label drug running at tau (start <= tau < end);
                      provisional Decision 6a, pending the project lead's definitions
  L3 continuation     an infusion running at tau + 4 (start <= tau + 4 < end), all rows;
                      provisional Decision 6b, pending the project lead's definitions
  L4 new start        L1 counting only infusion episodes that START in [tau, tau + 4); episodes
                      are a drug's MIMIC rows merged when they touch or overlap (a rate change
                      splits one infusion into several rows), so a row that only continues an
                      infusion begun before tau does not count. L4_any_drug merges across all six
                      drugs (a second drug added to a running one is not a new start).

The "I" score is the on-at-tau indicator over the six label drugs (Exp 8's six-drug definition).
Paired patient bootstrap: one patient resample per replicate shared by every label and score, so
any difference between two cells (A minus E, or a label against another label) has a paired CI.
Resampling with replacement is implemented as integer row weights (a patient drawn k times
contributes its rows k times), identical to concatenating the drawn patients' rows.

Writes aggregates only (counts, prevalences, AUROCs, CIs). Patient-level predictions are not
written anywhere.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

INTERVAL = 4.0
VASO_ITEMS = {221906: "norepi", 221289: "epi", 221662: "dopamine", 221653: "dobutamine",
              221749: "phenylephrine", 222315: "vasopressin"}
DOSE_SCORED = {"norepi", "epi", "dopamine", "dobutamine"}
HEADER = "exploratory, not pre-registered; does not change the H3 decision"
PROVISIONAL = "provisional, pending the project lead's definitions"


# ----------------------------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------------------------
def extract_vaso(db_path: str, stay_ids) -> pd.DataFrame:
    """Notebook cell 9 (vaso_dose_query + unit filter) for the given stays, read-only.
    intime is icustays.intime, which is what the notebook's cohort table carries."""
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
    return clean.rename(columns={"start_hours_from_admit": "time_bin_start", "end_hours_from_admit": "time_bin_end"})[
        ["stay_id", "drug", "time_bin_start", "time_bin_end"]]


# ----------------------------------------------------------------------------------------------
# labels
# ----------------------------------------------------------------------------------------------
def merge_episodes(starts: np.ndarray, ends: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Merge intervals that overlap or touch (next start <= current end)."""
    if len(starts) == 0:
        return np.array([]), np.array([])
    o = np.argsort(starts, kind="stable")
    s, e = starts[o], ends[o]
    ms, me = [s[0]], [e[0]]
    for a, b in zip(s[1:], e[1:]):
        if a <= me[-1]:
            me[-1] = max(me[-1], b)
        else:
            ms.append(a); me.append(b)
    return np.asarray(ms, float), np.asarray(me, float)


def build_labels(vaso_bins_df: pd.DataFrame, rows: pd.DataFrame, interval: float = INTERVAL) -> pd.DataFrame:
    """One output row per input (stay_id, bin) row, in the same order. Columns: tau, the labels,
    the on-at-tau indicator and the overlap flags used to test the "zero overlap" sentence."""
    taus_all = (rows["bin"].values.astype(float) + 1.0) * interval
    sids_all = rows["stay_id"].values
    n = len(rows)
    cols = {k: np.zeros(n, dtype=bool) for k in
            ["L0", "L1", "L3", "L4", "L4_any_drug", "on_at_tau", "on_at_tau_strict",
             "L1_raw_row_started_before_tau", "L1_episode_started_before_tau",
             "L1_dose_scored_straddles_tau", "L1_raw_row_starts_in_window"]}
    by_stay = {sid: g for sid, g in vaso_bins_df.groupby("stay_id")}
    pos_of = pd.Series(np.arange(n)).groupby(sids_all).apply(lambda s: s.values).to_dict()
    for sid, idx in pos_of.items():
        g = by_stay.get(sid)
        if g is None:
            continue
        tau = taus_all[idx][:, None]
        st = g["time_bin_start"].values.astype(float)[None, :]
        en = g["time_bin_end"].values.astype(float)[None, :]
        dose = g["drug"].isin(DOSE_SCORED).values[None, :]
        in_label = (st < tau + interval) & (en > tau)
        cols["L0"][idx] = ((st < tau) & (en > tau - interval)).any(1)
        cols["L1"][idx] = in_label.any(1)
        cols["on_at_tau"][idx] = ((st <= tau) & (tau < en)).any(1)
        cols["on_at_tau_strict"][idx] = ((st < tau) & (tau < en)).any(1)
        cols["L3"][idx] = ((st <= tau + interval) & (tau + interval < en)).any(1)
        cols["L1_raw_row_started_before_tau"][idx] = (in_label & (st < tau)).any(1)
        cols["L1_raw_row_starts_in_window"][idx] = (in_label & (st >= tau)).any(1)
        cols["L1_dose_scored_straddles_tau"][idx] = (in_label & (st < tau) & dose).any(1)
        # per-drug episodes
        new_start = np.zeros(len(idx), dtype=bool)
        ep_before = np.zeros(len(idx), dtype=bool)
        for _d, gd in g.groupby("drug"):
            es, ee = merge_episodes(gd["time_bin_start"].values.astype(float), gd["time_bin_end"].values.astype(float))
            es, ee = es[None, :], ee[None, :]
            lab = (es < tau + interval) & (ee > tau)
            new_start |= (lab & (es >= tau)).any(1)
            ep_before |= (lab & (es < tau)).any(1)
        cols["L4"][idx] = new_start
        cols["L1_episode_started_before_tau"][idx] = ep_before
        # episodes merged across all six drugs
        es, ee = merge_episodes(g["time_bin_start"].values.astype(float), g["time_bin_end"].values.astype(float))
        es, ee = es[None, :], ee[None, :]
        cols["L4_any_drug"][idx] = ((es < tau + interval) & (ee > tau) & (es >= tau)).any(1)
    out = pd.DataFrame({"stay_id": sids_all, "bin": rows["bin"].values, "tau": taus_all})
    for k, v in cols.items():
        out[k] = v
    return out


def overlap_summary(lab: pd.DataFrame) -> dict:
    """Aggregate counts for the "zero overlap" test. The state window [tau-4, tau) and the label
    window [tau, tau+4) never overlap; the question is whether the infusion that makes the label
    positive started inside or before the state window (it then also overlaps the state window,
    since it is still running after tau)."""
    p = lab["L1"].values
    npos = int(p.sum())

    def frac(col):
        c = lab[col].values & p
        return {"rows": int(c.sum()), "fraction_of_L1_positive": float(c.sum() / max(npos, 1))}

    only_straddle = p & ~lab["L4"].values
    return {
        "n_rows": int(len(lab)), "n_L1_positive": npos,
        "positive_with_a_label_row_started_before_tau": frac("L1_raw_row_started_before_tau"),
        "positive_with_a_label_episode_started_before_tau": frac("L1_episode_started_before_tau"),
        "positive_with_a_dose_scored_label_infusion_straddling_tau (in the state's own dose features)": frac("L1_dose_scored_straddles_tau"),
        "positive_with_on_at_tau": frac("on_at_tau"),
        "positive_only_because_of_an_episode_started_before_tau (L1=1, L4=0)": {
            "rows": int(only_straddle.sum()), "fraction_of_L1_positive": float(only_straddle.sum() / max(npos, 1))},
        "positive_with_a_raw_row_starting_in_label_window (incl. rate-change rows)": frac("L1_raw_row_starts_in_window"),
        "L0_L1_crosstab": {f"L0={a}_L1={b}": int(((lab["L0"].values == a) & (p == b)).sum()) for a in (0, 1) for b in (0, 1)},
        "P_L1_given_L0": float(p[lab["L0"].values].mean()) if lab["L0"].any() else None,
        "P_L1_given_on_at_tau": float(p[lab["on_at_tau"].values].mean()) if lab["on_at_tau"].any() else None,
        "P_L1_given_not_on_at_tau": float(p[~lab["on_at_tau"].values].mean()) if (~lab["on_at_tau"]).any() else None,
    }


# ----------------------------------------------------------------------------------------------
# fast weighted AUROC for the paired bootstrap
# ----------------------------------------------------------------------------------------------
class WeightedAUC:
    """Precomputes the score order and tie groups once; each call takes row weights (patient
    multiplicities) and returns the AUROC of the weighted sample, ties counted as 1/2."""

    def __init__(self, y: np.ndarray, score: np.ndarray):
        y = np.asarray(y).astype(bool)
        u, inv = np.unique(np.asarray(score, float), return_inverse=True)
        self.inv, self.ng, self.y = inv, len(u), y

    def __call__(self, w: np.ndarray) -> float:
        wp = np.bincount(self.inv, weights=w * self.y, minlength=self.ng)
        wn = np.bincount(self.inv, weights=w * ~self.y, minlength=self.ng)
        P, N = wp.sum(), wn.sum()
        if P == 0 or N == 0:
            return np.nan
        below = np.cumsum(wn) - wn
        return float((wp * (below + 0.5 * wn)).sum() / (P * N))


def paired_bootstrap(cells: dict, row_patient_idx: dict, n_patients: int, n_boot: int = 2000, seed: int = 42) -> dict:
    """cells: {key: (row_set_name, y, score)}; row_patient_idx: {row_set_name: patient index per
    row}. Returns {key: array of replicate AUROCs}, the same patient draws for every key."""
    aucs = {k: WeightedAUC(y, s) for k, (_rs, y, s) in cells.items()}
    rng = np.random.RandomState(seed)
    patients = np.arange(n_patients)
    out = {k: np.empty(n_boot) for k in cells}
    for b in range(n_boot):
        draw = rng.choice(patients, size=n_patients, replace=True)
        cnt = np.bincount(draw, minlength=n_patients).astype(float)
        wts = {rs: cnt[pi] for rs, pi in row_patient_idx.items()}
        for k, (rs, _y, _s) in cells.items():
            out[k][b] = aucs[k](wts[rs])
    return out


def ci(a: np.ndarray) -> list[float]:
    a = a[~np.isnan(a)]
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]


# ----------------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------------
def notebook_probes(random_state: int = 42):
    """PROBES and cv_predict copied verbatim from notebook cell 21."""
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.preprocessing import StandardScaler
    probes = {"logreg": lambda: LogisticRegression(max_iter=2000, class_weight="balanced"),
              "gb": lambda: GradientBoostingClassifier(random_state=random_state)}

    def cv_predict(X, y, groups, probe_fn, n_splits=5):
        cv = GroupKFold(n_splits=n_splits)
        Xs = StandardScaler().fit_transform(X)
        preds = np.zeros(len(y), dtype=float)
        for tr, va in cv.split(Xs, y, groups):
            clf = probe_fn()
            clf.fit(Xs[tr], y[tr])
            preds[va] = clf.predict_proba(Xs[va])[:, 1]
        return preds
    return probes, cv_predict


def _fit(task, X, y, g, probe_name):
    probes, cv_predict = notebook_probes()
    return task, cv_predict(X, y, g, probes[probe_name])


def run(run_dir: Path, db_path: str, out_dir: Path, cohort: str, n_boot: int, seed: int, n_jobs: int,
        probes_to_run=("logreg", "gb")) -> dict:
    from joblib import Parallel, delayed
    t0 = time.time()
    ck = pickle.load(open(run_dir / "notebook" / "results" / "exp5_checkpoint_inputs.pkl", "rb"))
    st = ck["state_4h"].reset_index(drop=True)
    variants = ck["variants"]
    assert np.array_equal(st["stay_id"].values, ck["groups"]), "checkpoint row order mismatch"
    XA, XE = variants["A_full"], variants["E_physiology_only"]
    vaso = extract_vaso(db_path, np.unique(st["stay_id"].values))
    lab = build_labels(vaso, st[["stay_id", "bin"]])
    l1_match = int((lab["L1"].values.astype(int) == st["action_next"].values.astype(int)).sum())
    res = {"note": HEADER, "cohort": cohort, "run_dir": str(run_dir), "db": db_path,
           "n_rows": int(len(st)), "n_patients": int(st["stay_id"].nunique()),
           "reproduces_action_next": {"rows_matching": l1_match, "rows": int(len(st)),
                                      "exact": bool(l1_match == len(st))},
           "definitions": {
               "tau": "decision time = 4 * (bin + 1) hours from ICU admission; state window [tau-4, tau)",
               "L0_contemporaneous": "any label-drug infusion active in [tau-4, tau) (same bin as the state)",
               "L1_published": "any label-drug infusion active in [tau, tau+4) (notebook action_next)",
               "L2_initiation": f"L1 on rows with no label drug running at tau (start <= tau < end); {PROVISIONAL}",
               "L3_continuation": f"an infusion running at tau+4 (start <= tau+4 < end), all rows; {PROVISIONAL}",
               "L4_new_start": "L1 counting only per-drug infusion episodes (touching rows merged) that start in [tau, tau+4)",
               "L4_any_drug": "as L4 with episodes merged across all six drugs",
               "I": "on-at-tau indicator over the six label drugs (start <= tau < end), used as a score",
               "A": "A_full (25 features incl. SOFA subscores and sofa_total)",
               "E": "E_physiology_only (A minus sofa_cardio and sofa_total)",
               "A_minus_E": "AUROC(A) - AUROC(E) on the same rows, paired bootstrap CI"},
           "settings": {"probe_primary": "logreg", "probe_check": "gb", "cv": "GroupKFold 5 by stay_id",
                        "n_boot": n_boot, "seed": seed, "offset": 0}}
    res["overlap"] = overlap_summary(lab)
    off = ~lab["on_at_tau"].values
    row_sets = {"all": np.ones(len(st), bool), "off_at_tau": off}
    labels = {"L0": ("all", lab["L0"].values), "L1": ("all", lab["L1"].values),
              "L2": ("off_at_tau", lab["L1"].values), "L3": ("all", lab["L3"].values),
              "L4": ("all", lab["L4"].values), "L4_any_drug": ("all", lab["L4_any_drug"].values)}
    g_all = st["stay_id"].values
    tasks = []
    for ln, (rs, y) in labels.items():
        m = row_sets[rs]
        for vn, X in (("A", XA), ("E", XE)):
            for pn in probes_to_run:
                tasks.append(((ln, vn, pn), X[m], y[m].astype(int), g_all[m], pn))
    print(f"[{time.time()-t0:.0f}s] labels built; L1 reproduces action_next on {l1_match:,}/{len(st):,} rows; "
          f"fitting {len(tasks)} probe runs with {n_jobs} workers", flush=True)
    fitted = Parallel(n_jobs=n_jobs, verbose=5)(delayed(_fit)(t, X, y, g, pn) for t, X, y, g, pn in tasks)
    preds = dict(fitted)
    print(f"[{time.time()-t0:.0f}s] fits done", flush=True)
    # bootstrap cells
    pats, pidx = np.unique(g_all, return_inverse=True)
    row_patient_idx = {rs: pidx[m] for rs, m in row_sets.items()}
    on = lab["on_at_tau"].values.astype(float)
    cells = {}
    for ln, (rs, y) in labels.items():
        m = row_sets[rs]
        for (l2, vn, pn), p in preds.items():
            if l2 == ln:
                cells[(ln, vn, pn)] = (rs, y[m], p)
        if rs == "all":
            cells[(ln, "I", "raw")] = (rs, y[m], on[m])
    boot = paired_bootstrap(cells, row_patient_idx, len(pats), n_boot=n_boot, seed=seed)
    print(f"[{time.time()-t0:.0f}s] bootstrap done", flush=True)
    point = {k: float(roc_auc_score(y, s)) for k, (_rs, y, s) in cells.items()}

    def cell(k):
        return {"auroc": point[k], "ci": ci(boot[k])}

    def diff(k1, k2):
        d = boot[k1] - boot[k2]
        return {"delta": point[k1] - point[k2], "ci": ci(d), "p_le_zero": float(np.nanmean(d <= 0))}

    table = {}
    for ln, (rs, y) in labels.items():
        m = row_sets[rs]
        row = {"row_set": rs, "n_rows": int(m.sum()), "n_patients": int(len(np.unique(g_all[m]))),
               "prevalence": float(y[m].mean())}
        for pn in probes_to_run:
            row[pn] = {"A": cell((ln, "A", pn)), "E": cell((ln, "E", pn)),
                       "A_minus_E": diff((ln, "A", pn), (ln, "E", pn))}
        row["I"] = cell((ln, "I", "raw")) if rs == "all" else {"auroc": None, "ci": None,
                                                               "note": "constant 0 on these rows by construction"}
        table[ln] = row
    res["labels"] = table
    # decomposition
    dec = {"alignment_leakage_L0_minus_L1": {}, "continuation_L1_minus_L4": {}, "continuation_L1_minus_L4_any_drug": {},
           "continuation_L1_all_rows_minus_L2_off_rows": {}, "sofa_construction_A_minus_E": {}}
    for pn in probes_to_run:
        for nm, (a, b) in {"alignment_leakage_L0_minus_L1": ("L0", "L1"), "continuation_L1_minus_L4": ("L1", "L4"),
                           "continuation_L1_minus_L4_any_drug": ("L1", "L4_any_drug"),
                           "continuation_L1_all_rows_minus_L2_off_rows": ("L1", "L2")}.items():
            dec[nm][pn] = {"A": diff((a, "A", pn), (b, "A", pn)), "E": diff((a, "E", pn), (b, "E", pn))}
            ae_a = boot[(a, "A", pn)] - boot[(a, "E", pn)]
            ae_b = boot[(b, "A", pn)] - boot[(b, "E", pn)]
            dd = ae_a - ae_b
            dec[nm][pn]["A_minus_E_change"] = {"delta": (point[(a, "A", pn)] - point[(a, "E", pn)]) - (point[(b, "A", pn)] - point[(b, "E", pn)]),
                                               "ci": ci(dd)}
        dec["sofa_construction_A_minus_E"][pn] = {ln: table[ln][pn]["A_minus_E"] for ln in labels}
    for nm, (a, b) in {"alignment_leakage_L0_minus_L1": ("L0", "L1"), "continuation_L1_minus_L4": ("L1", "L4"),
                       "continuation_L1_minus_L4_any_drug": ("L1", "L4_any_drug")}.items():
        dec[nm]["I"] = diff((a, "I", "raw"), (b, "I", "raw"))
    res["decomposition"] = dec
    res["runtime_s"] = round(time.time() - t0, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"label_alignment_{cohort}.json", "w") as f:
        json.dump(res, f, indent=2)
    for ln, r in table.items():
        lr = r["logreg"]
        print(f"{cohort} {ln:12s} n={r['n_rows']:,} prev={r['prevalence']:.3f}  A={lr['A']['auroc']:.3f} E={lr['E']['auroc']:.3f} "
              f"I={r['I']['auroc'] if r['I']['auroc'] is not None else float('nan'):.3f}  A-E={lr['A_minus_E']['delta']:.3f} "
              f"({lr['A_minus_E']['ci'][0]:.3f},{lr['A_minus_E']['ci'][1]:.3f})", flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--db", default="~/orcd/scratch/sail/mimic4.db")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-jobs", type=int, default=24)
    ap.add_argument("--probes", default="logreg,gb")
    a = ap.parse_args()
    run(a.run_dir, a.db, a.out_dir, a.cohort, a.n_boot, a.seed, a.n_jobs, tuple(a.probes.split(",")))


if __name__ == "__main__":
    main()
