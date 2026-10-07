#!/usr/bin/env python3
"""Exploratory, not pre-registered; does not change the H3 decision.

Paired patient-level bootstrap for every gap the project reports as a difference of two AUROCs on
the same patients (FORMAL_ANALYSIS.md section 7: two marginal CIs cannot be compared for
same-patient AUROCs), plus CIs for the Experiment 2 mutual-information values, the
mortality-gap / action-gap ratio, and the optimism of the notebook's best-probe selection.

Input: the out-of-fold predictions written by scripts/paired_cis_predict.py (cluster only).

Resampling: stay_ids are drawn with replacement (RandomState(seed), n_boot replicates), every row
of a drawn stay enters with the stay's multiplicity, and ONE draw per replicate is shared by every
AUROC in that replicate (both members of each pair, both axes, every probe). The universe of
stays is the union of the action and mortality stays, so the ratio (mortality A-E)/(action A-E)
is computed on the same resampled patients. AUROC under integer multiplicities is computed
exactly as on the concatenated rows (weighted Mann-Whitney with ties counted 1/2), see
weighted_auc and its test.

p-values are two-sided bootstrap p-values, p = min(1, 2 min((1 + #{d<=0}), (1 + #{d>=0})) / (B+1)),
Holm-adjusted across the 15 action comparisons {A-E, A-C, C-D, D-E, A-B} x {logreg, rf, gb}.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARIANTS = ["A_full", "B_no_total_sofa", "C_no_cardio_sofa", "D_treatment_decomposed",
            "E_physiology_only", "F_disentangled"]
SHORT = {v[0]: v for v in VARIANTS}
PROBES = ["logreg", "rf", "gb"]
ACTION_PAIRS = [("A", "E"), ("A", "C"), ("C", "D"), ("D", "E"), ("A", "B"), ("F", "A"), ("F", "D")]
HOLM_PAIRS = ACTION_PAIRS[:5]
MORT_PAIRS = [("A", "E"), ("A", "D"), ("F", "A")]
HEADER = "exploratory, not pre-registered; does not change the H3 decision"


# ----------------------------------------------------------------------------- core statistics
def auc_prep(y: np.ndarray, p: np.ndarray):
    """Sort once; tie groups of equal predictions are kept together."""
    order = np.argsort(p, kind="mergesort")
    ps = p[order]
    starts = np.flatnonzero(np.r_[True, ps[1:] != ps[:-1]])
    return order, starts, np.asarray(y, dtype=float)[order]


def weighted_auc(prep, w: np.ndarray) -> float:
    """AUROC with integer row multiplicities w; equals roc_auc_score on the repeated rows."""
    order, starts, ys = prep
    ws = np.asarray(w, dtype=float)[order]
    gp = np.add.reduceat(ws * ys, starts)
    gn = np.add.reduceat(ws, starts) - gp
    P, N = gp.sum(), gn.sum()
    if P == 0 or N == 0:
        return float("nan")
    below = np.cumsum(gn) - gn
    return float((gp * (below + 0.5 * gn)).sum() / (P * N))


def draw_counts(n_patients: int, n_boot: int, seed: int) -> np.ndarray:
    """Per-replicate multiplicity of each patient; same draws as rng.choice(patients, n, True)."""
    rng = np.random.RandomState(seed)
    out = np.empty((n_boot, n_patients), dtype=np.int32)
    for b in range(n_boot):
        out[b] = np.bincount(rng.randint(0, n_patients, size=n_patients), minlength=n_patients)
    return out


def boot_p(d: np.ndarray) -> float:
    d = d[np.isfinite(d)]
    B = len(d)
    return float(min(1.0, 2 * min(1 + (d <= 0).sum(), 1 + (d >= 0).sum()) / (B + 1)))


def holm(p: list[float]) -> list[float]:
    p = np.asarray(p, dtype=float)
    m = len(p)
    order = np.argsort(p, kind="mergesort")
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def ci(x: np.ndarray) -> list[float]:
    x = x[np.isfinite(x)]
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def mi_column(col: np.ndarray, y: np.ndarray, n_bins: int = 10) -> float:
    """One column of the notebook's mutual_information_estimate (cell 21). Quantile edges are per
    feature, so the notebook's matrix-wide fit equals this per-column fit; subsample=None keeps
    resampled sets above 200,000 rows deterministic (below that it is a no-op)."""
    from sklearn.metrics import mutual_info_score
    from sklearn.preprocessing import KBinsDiscretizer
    disc = KBinsDiscretizer(n_bins=n_bins, encode="ordinal", strategy="quantile", subsample=None)
    xd = disc.fit_transform(col.reshape(-1, 1))[:, 0]
    return float(mutual_info_score(xd, y))


def mi_variants(cols: dict[str, np.ndarray], y: np.ndarray, feature_names: list[str]) -> dict[str, float]:
    """Mean per-column MI for variants A to E from the 25 A columns plus D's two replaced ones."""
    m = {c: mi_column(cols[c], y) for c in cols}
    a = list(feature_names)
    sets = {
        "A_full": a,
        "B_no_total_sofa": [c for c in a if c != "sofa_total"],
        "C_no_cardio_sofa": [c for c in a if c != "sofa_cardio"],
        "D_treatment_decomposed": [("D__" + c) if c in ("sofa_cardio", "sofa_total") else c for c in a],
        "E_physiology_only": [c for c in a if c not in ("sofa_total", "sofa_cardio")],
    }
    return {v: float(np.mean([m[c] for c in s])) for v, s in sets.items()}


def _mi_replicates(cols, y, feature_names, W):
    out = []
    for w in W:
        idx = np.repeat(np.arange(len(y)), w)
        out.append(mi_variants({c: v[idx] for c, v in cols.items()}, y[idx], feature_names))
    return out


# ----------------------------------------------------------------------------- analysis
def best_probes(points: dict[str, float]) -> dict[str, str]:
    """The notebook's choice: max point AUROC per variant over the same out-of-fold predictions."""
    return {v: max(PROBES, key=lambda p: points[f"{v}|{p}"]) for v in VARIANTS}


def analyse(pa: pd.DataFrame, pm: pd.DataFrame, n_boot: int = 2000, seed: int = 42,
            mi: pd.DataFrame | None = None, feature_names: list[str] | None = None, n_jobs: int = 1) -> dict:
    universe = np.union1d(pa["stay_id"].unique(), pm["stay_id"].unique())
    ia = np.searchsorted(universe, pa["stay_id"].values)
    im = np.searchsorted(universe, pm["stay_id"].values)
    counts = draw_counts(len(universe), n_boot, seed)
    one_a, one_m = np.ones(len(pa)), np.ones(len(pm))

    res = {"note": HEADER, "n_boot": n_boot, "seed": seed, "n_universe_stays": int(len(universe)),
           "n_action_rows": int(len(pa)), "n_action_stays": int(pa["stay_id"].nunique()),
           "n_mortality_rows": int(len(pm)), "n_mortality_stays": int(pm["stay_id"].nunique())}
    boots, points, preps = {}, {}, {}
    for axis, df, one in (("action", pa, one_a), ("mortality", pm, one_m)):
        y = df["y"].values
        for v in VARIANTS:
            for p in PROBES:
                key = (axis, f"{v}|{p}")
                preps[key] = auc_prep(y, df[f"pred_{v}_{p}"].values)
                points[key] = weighted_auc(preps[key], one)
                boots[key] = np.empty(n_boot)
    for b in range(n_boot):
        w = {"action": counts[b][ia], "mortality": counts[b][im]}
        for key, prep in preps.items():
            boots[key][b] = weighted_auc(prep, w[key[0]])
    for axis in ("action", "mortality"):
        res[f"{axis}_auroc"] = {k: {"auroc": points[(a, k)], "ci": ci(boots[(a, k)])}
                                for (a, k) in points if a == axis}
        bp = best_probes({k: points[(a, k)] for (a, k) in points if a == axis})
        res[f"{axis}_best_probe"] = bp

    def auc(axis, v, probe, boot=False):
        if probe == "best":
            probe = res[f"{axis}_best_probe"][v]
        k = (axis, f"{v}|{probe}")
        return boots[k] if boot else points[k]

    def pair_block(axis, pairs):
        out = []
        for x, z in pairs:
            for probe in PROBES + ["best"]:
                d = auc(axis, SHORT[x], probe) - auc(axis, SHORT[z], probe)
                db = auc(axis, SHORT[x], probe, True) - auc(axis, SHORT[z], probe, True)
                row = {"pair": f"{x}-{z}", "probe": probe, "delta": float(d), "ci": ci(db), "p": boot_p(db)}
                if probe == "best":
                    row["probes_used"] = [res[f"{axis}_best_probe"][SHORT[x]], res[f"{axis}_best_probe"][SHORT[z]]]
                out.append(row)
        return out

    res["action_pairs"] = pair_block("action", ACTION_PAIRS)
    res["mortality_pairs"] = pair_block("mortality", MORT_PAIRS)
    fam = [r for r in res["action_pairs"] if (tuple(r["pair"].split("-")) in HOLM_PAIRS and r["probe"] in PROBES)]
    assert len(fam) == 15
    for r, adj in zip(fam, holm([r["p"] for r in fam])):
        r["p_holm15"] = adj

    res["ratio_mortality_AE_over_action_AE"] = []
    for probe in PROBES + ["best"]:
        num = auc("mortality", "A_full", probe) - auc("mortality", "E_physiology_only", probe)
        den = auc("action", "A_full", probe) - auc("action", "E_physiology_only", probe)
        nb = auc("mortality", "A_full", probe, True) - auc("mortality", "E_physiology_only", probe, True)
        dbb = auc("action", "A_full", probe, True) - auc("action", "E_physiology_only", probe, True)
        res["ratio_mortality_AE_over_action_AE"].append(
            {"probe": probe, "ratio": float(num / den), "ci": ci(nb / dbb)})

    # Optimism of picking the best probe on the same folds that are reported.
    opt = {}
    for axis in ("action", "mortality"):
        rows = []
        for v in VARIANTS:
            bp = res[f"{axis}_best_probe"][v]
            stack = np.vstack([auc(axis, v, p, True) for p in PROBES])
            still_best = float(np.mean(np.argmax(stack, axis=0) == PROBES.index(bp)))
            for p in PROBES:
                if p == bp:
                    continue
                db = auc(axis, v, bp, True) - auc(axis, v, p, True)
                rows.append({"variant": v, "best": bp, "vs": p,
                             "best_minus_fixed": float(auc(axis, v, bp) - auc(axis, v, p)), "ci": ci(db)})
            rows.append({"variant": v, "best": bp, "share_replicates_same_best": still_best})
        opt[axis] = rows
    res["best_probe_optimism"] = opt

    if mi is not None:
        y = mi["y"].values
        cols = {c: mi[c].values for c in mi.columns if c not in ("stay_id", "y")}
        im_mi = np.searchsorted(universe, mi["stay_id"].values)
        point = mi_variants(cols, y, feature_names)
        from joblib import Parallel, delayed
        chunks = np.array_split(np.arange(n_boot), max(1, n_jobs))
        parts = Parallel(n_jobs=n_jobs)(delayed(_mi_replicates)(cols, y, feature_names, counts[c][:, im_mi])
                                        for c in chunks if len(c))
        reps = [r for part in parts for r in part]
        mib = {v: np.array([r[v] for r in reps]) for v in point}
        res["mutual_info"] = {v: {"mi": point[v], "ci": ci(mib[v])} for v in point}
        res["mutual_info_diff"] = [
            {"pair": f"{x}-{z}", "delta": point[SHORT[x]] - point[SHORT[z]],
             "ci": ci(mib[SHORT[x]] - mib[SHORT[z]])} for x, z in HOLM_PAIRS]
    return res


# ----------------------------------------------------------------------------- reference check
def point_check(res: dict, exp2_csv: Path, exp6_csv: Path, exp8_json: Path | None, notebook_mi: dict | None,
                tol: float = 1e-4) -> dict:
    out = {"tol": tol, "diffs": {}}
    for axis, path in (("action", exp2_csv), ("mortality", exp6_csv)):
        ref = pd.read_csv(path)
        for r in ref.itertuples():
            k = f"{r.variant}|{r.probe}"
            out["diffs"][f"{axis}:{k}"] = abs(res[f"{axis}_auroc"][k]["auroc"] - r.auroc)
        if axis == "action" and "mutual_info" in ref.columns and "mutual_info" in res:
            for v, g in ref.groupby("variant"):
                out["diffs"][f"mi:{v}"] = abs(res["mutual_info"][v]["mi"] - g["mutual_info"].iloc[0])
    if notebook_mi and "mutual_info" in res:
        for v, val in notebook_mi.items():
            out["diffs"][f"mi_notebook_fn:{v}"] = abs(res["mutual_info"][v]["mi"] - val)
    if exp8_json:
        e8 = json.loads(Path(exp8_json).read_text())
        for axis, key in (("action", "f_action_best_probe"), ("mortality", "f_mortality_best_probe")):
            b = e8[key]
            out["diffs"][f"{axis}:F_disentangled|{b['probe']}"] = abs(
                res[f"{axis}_auroc"][f"F_disentangled|{b['probe']}"]["auroc"] - float(b["auroc"]))
    out["max_abs_diff"] = max(out["diffs"].values())
    out["all_within_tol"] = bool(out["max_abs_diff"] <= tol)
    return out


# ----------------------------------------------------------------------------- report
def _f(x, nd=3):
    return f"{x:+.{nd}f}"


def markdown(res: dict) -> str:
    L = []
    bpa, bpm = res["action_best_probe"], res["mortality_best_probe"]
    L.append("| Axis | Gap | logreg | rf | gb | best probe (notebook) |")
    L.append("|---|---|---|---|---|---|")
    for axis, key in (("action", "action_pairs"), ("mortality", "mortality_pairs")):
        by = {}
        for r in res[key]:
            by.setdefault(r["pair"], {})[r["probe"]] = r
        for pair, d in by.items():
            cells = []
            for p in PROBES + ["best"]:
                r = d[p]
                s = f"{_f(r['delta'])} [{_f(r['ci'][0])}, {_f(r['ci'][1])}]"
                if "p_holm15" in r:
                    s += f" p_Holm {r['p_holm15']:.3g}"
                if p == "best":
                    s += f" ({'/'.join(r['probes_used'])})"
                cells.append(s)
            L.append(f"| {axis} | {pair} | " + " | ".join(cells) + " |")
    rr = {r["probe"]: r for r in res["ratio_mortality_AE_over_action_AE"]}
    L.append("| ratio | mortality A-E / action A-E | " + " | ".join(
        f"{rr[p]['ratio']:.3f} [{rr[p]['ci'][0]:.3f}, {rr[p]['ci'][1]:.3f}]" for p in PROBES + ["best"]) + " |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds-dir", required=True, type=Path)
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--ref-exp2", type=Path)
    ap.add_argument("--ref-exp6", type=Path)
    ap.add_argument("--ref-exp8", type=Path)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-jobs", type=int, default=1)
    ap.add_argument("--no-mi", action="store_true")
    a = ap.parse_args()
    pa = pd.read_parquet(a.preds_dir / "preds_action.parquet")
    pm = pd.read_parquet(a.preds_dir / "preds_mortality.parquet")
    pts = json.loads((a.preds_dir / "points.json").read_text())
    mi = None if a.no_mi else pd.read_parquet(a.preds_dir / "mi_action.parquet")
    res = analyse(pa, pm, a.n_boot, a.seed, mi, pts["feature_names"], a.n_jobs)
    res["cohort"] = a.cohort
    if a.ref_exp2 and a.ref_exp6:
        res["point_check"] = point_check(res, a.ref_exp2, a.ref_exp6, a.ref_exp8, pts.get("mutual_info"))
        print("point check max abs diff", res["point_check"]["max_abs_diff"],
              "within tol:", res["point_check"]["all_within_tol"], flush=True)
    a.out.write_text(json.dumps(res, indent=2))
    print(markdown(res))


if __name__ == "__main__":
    main()
