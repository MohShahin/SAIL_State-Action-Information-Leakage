"""Synthetic ground-truth experiment for H3 ("Experiment G" in docs/PI_DEFENSE_PREP.md).

EXPLORATORY, not pre-registered; does not change the H3 decision.

Question: can the pre-registered H3 decision rule (Prediction A if Delta = AUROC(0) - AUROC(8)
has a 95% CI lower bound above 0 and Delta >= 0.10) tell the SOFA-construction mechanism apart from
plain treatment persistence? Here the truth is known, because we write the data-generating process.

The simulator (one ICU stay = 18 decision bins of 4h, as in the notebook):
  severity   hidden AR(1) per stay with a patient level, a patient drift and Gaussian shocks
  dose tier  1..3 from the current severity while an infusion runs
  MAP        baseline minus severity plus the drug's effect (by tier) plus noise
  policy     at each decision time tau (end of bin t), if no infusion continues past tau, start
             one in bin t+1 with probability sigmoid(intercept + slope * (70 - MAP_t) / 10); a
             started infusion runs for R bins, R = 1 + NegBin(shape, mean run_extra), drawn at the
             start and NOT revised (persistence is a pure, controllable knob). A stay can also be
             admitted already on a vasopressor. A fraction of runs are non-dose-scored drugs
             (phenylephrine / vasopressin in MIMIC): they count for the action label, not for SOFA.
  labels     occupancy a_t = any infusion during bin t; action_next_t = a_{t+1} (the notebook's
             one-bin shift of the bin-window label); on_tau_t = the run active in bin t continues
             past tau (so on_tau_t = 1 implies action_next_t = 1, as in the real cohort)
  SOFA-like  sofa_cardio with a switchable treatment branch:
               "on"        max(MAP < 70, 1 + tier if a dose-scored infusion runs in bin t)  (real SOFA)
               "off"       MAP < 70 only; the drug still raises MAP
               "off_pure"  MAP < 70 only and the drug has NO effect on any observed feature, so the
                           state is a function of physiology alone (property (1) of section 4)
             plus renal, coagulation and respiratory subscores from severity-linked labs and
             sofa_total = the sum.
State variants as in the notebook: A = all features, E = A without sofa_cardio and sofa_total.
The on-at-tau indicator alone is scored as a fixed predictor (no fitting).

Every setting is passed through the UNCHANGED scripts/h3_paired_bootstrap.py functions
(offset_frames in bins mode, predict_offsets with the notebook's logreg probe and grouped 5-fold
cv_predict, paired_cluster_bootstrap with 2,000 resamples, seed 42, common rows primary).

Usage
  python scripts/simulate_sail.py calib --targets results/exploratory/simulation/calibration_aggregates.json
  python scripts/simulate_sail.py grid --out DIR [--workers 18] [--n-stays 12000] [--n-boot 2000]
  python scripts/simulate_sail.py summarize --out DIR --dest results/exploratory/simulation
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h3_paired_bootstrap as h3  # noqa: E402

N_BINS = 18
OFFSETS = (0, 1, 2, 4, 8)
BRANCHES = ("on", "off", "off_pure")
PERSISTENCE = {"short": 0.5, "realistic": 1.0, "long": 2.0}   # multiplier on the calibrated run_extra
SEEDS = (0, 1, 2)
FEATURES_A = ["mbp", "heart_rate", "lactate", "creatinine", "platelets", "pf_ratio",
              "sofa_resp", "sofa_coag", "sofa_renal", "sofa_cardio", "sofa_total"]
FEATURES_E = [f for f in FEATURES_A if f not in ("sofa_cardio", "sofa_total")]
EXPLORATORY = "exploratory, not pre-registered; does not change the H3 decision"


# ---- the notebook's probe and CV, copied verbatim from notebook cell 24 ---------------------------
def PROBE_LOGREG():
    return LogisticRegression(max_iter=2000, class_weight="balanced")


def cv_predict(X, y, groups, probe_fn, n_splits=5):
    cv = GroupKFold(n_splits=n_splits)
    Xs = StandardScaler().fit_transform(X)
    preds = np.zeros(len(y), dtype=float)
    for tr, va in cv.split(Xs, y, groups):
        clf = probe_fn()
        clf.fit(Xs[tr], y[tr])
        preds[va] = clf.predict_proba(Xs[va])[:, 1]
    return preds


# ---- helpers -----------------------------------------------------------------------------------
def run_lengths(row) -> list[tuple[int, int]]:
    """(start, length) of every run of consecutive True values in a 1-D boolean sequence."""
    r = np.concatenate([[0], np.asarray(row, dtype=np.int8), [0]])
    d = np.diff(r)
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    return [(int(s), int(e - s)) for s, e in zip(starts, ends)]


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# real rows-per-stay shape (13,192 cohort, see calibration_aggregates.json); overwritten by `calib`
_DEFAULT_ROWS_PER_STAY = {str(k): (1.0 if k == 17 else 0.0) for k in range(1, 18)}


@dataclass
class SimParams:
    n_stays: int = 12000
    branch: str = "on"
    # severity
    sev_mean: float = 0.0
    sev_patient_sd: float = 0.8
    sev_init_sd: float = 0.6
    phi: float = 0.80                 # AR(1) persistence of the deviation from the patient level
    sev_noise: float = 0.40
    drift_mean: float = -0.04         # per-bin drift (recovery on average)
    drift_sd: float = 0.04
    # MAP and other observed physiology
    map0: float = 78.0
    map_slope: float = 7.0
    map_noise: float = 6.0
    drug_map: tuple = (8.0, 10.0, 12.0)   # MAP raise by dose tier 1..3
    drug_gain: float = 1.0                 # multiplier on drug_map (calibrated)
    drug_hr: float = 0.0                   # heart-rate raise while any infusion runs (real: none on vs off)
    tier_cut: tuple = (0.6, 1.4)           # severity cut points for tiers 2 and 3
    # policy
    start_intercept: float = -2.6
    start_slope: float = 1.6
    admit_intercept: float = -1.0
    run_extra: float = 4.0            # mean of R - 1, R = run length in bins
    run_shape: float = 1.0            # NegBin shape (1 = geometric)
    persistence: float = 1.0          # multiplier on run_extra
    scored_fraction: float = 0.80     # share of runs that are dose-scored drugs
    rows_per_stay: dict = field(default_factory=lambda: dict(_DEFAULT_ROWS_PER_STAY))


def simulate(p: SimParams, seed: int):
    """Returns (state_4h, occ, on_tau, sev): the notebook-shaped frame (stay_id, bin, FEATURES_A,
    action_next, on_tau, severity) on each stay's modeling rows, plus the full 18-bin occupancy
    and on-at-tau arrays (n_stays x 18) for the marginals."""
    if p.branch not in BRANCHES:
        raise ValueError(f"branch must be one of {BRANCHES}, got {p.branch!r}")
    rng = np.random.default_rng(seed)
    n, T = p.n_stays, N_BINS
    level = rng.normal(p.sev_mean, p.sev_patient_sd, n)
    drift = rng.normal(p.drift_mean, p.drift_sd, n)
    sev = np.empty((n, T))
    dev = rng.normal(0.0, p.sev_init_sd, n)
    for t in range(T):
        if t:
            dev = p.phi * dev + p.sev_noise * rng.normal(size=n)
        sev[:, t] = level + drift * t + dev
    # patient-level lab offsets and per-bin noise, drawn up front so the policy does not change them
    u_cr, u_pl, u_pf, u_hr = (rng.normal(0, s, n) for s in (0.30, 0.30, 0.25, 12.0))
    e_map, e_hr = rng.normal(0, p.map_noise, (n, T)), rng.normal(0, 8.0, (n, T))
    e_lac, e_cr, e_pl, e_pf = (rng.normal(0, s, (n, T)) for s in (0.30, 0.12, 0.12, 0.20))
    u_start, u_scored = rng.random((n, T + 1)), rng.random((n, T + 1))
    mean_extra = p.run_extra * p.persistence
    if p.run_shape > 0 and mean_extra > 0:
        pr = p.run_shape / (p.run_shape + mean_extra)
        extra = rng.negative_binomial(p.run_shape, pr, (n, T + 1))
    else:
        extra = np.zeros((n, T + 1), dtype=int)

    occ = np.zeros((n, T), dtype=bool)
    on_tau = np.zeros((n, T), dtype=bool)
    scored_now = np.zeros((n, T), dtype=bool)
    tier = np.zeros((n, T), dtype=int)
    mbp = np.zeros((n, T))
    drug_on_obs = p.branch != "off_pure"
    drug_map = p.drug_gain * np.asarray((0.0,) + tuple(p.drug_map))

    # admission: some stays arrive on a vasopressor (decided on an untreated MAP draw)
    map_pre = p.map0 - p.map_slope * sev[:, 0] + e_map[:, 0]
    start = u_start[:, 0] < _sigmoid(p.admit_intercept + p.start_slope * (70.0 - map_pre) / 10.0)
    remaining = np.where(start, extra[:, 0], -1)          # -1 = no run; >= 0 bins left after this one
    scored = u_scored[:, 0] < p.scored_fraction
    for t in range(T):
        a = remaining >= 0
        occ[:, t] = a
        tr = 1 + (sev[:, t] > p.tier_cut[0]).astype(int) + (sev[:, t] > p.tier_cut[1]).astype(int)
        tier[:, t] = np.where(a, tr, 0)
        scored_now[:, t] = a & scored
        mbp[:, t] = p.map0 - p.map_slope * sev[:, t] + e_map[:, t] + (drug_map[tier[:, t]] if drug_on_obs else 0.0)
        cont = a & (remaining > 0)
        on_tau[:, t] = cont
        go = (~cont) & (u_start[:, t + 1] < _sigmoid(p.start_intercept + p.start_slope * (70.0 - mbp[:, t]) / 10.0))
        new_scored = u_scored[:, t + 1] < p.scored_fraction
        remaining = np.where(cont, remaining - 1, np.where(go, extra[:, t + 1], -1))
        scored = np.where(cont, scored, new_scored)
    # action_next_t = a_{t+1}; bin 17 has no label (beyond the 72h grid), exactly as the notebook
    nxt = np.zeros((n, T), dtype=float)
    nxt[:, :-1] = occ[:, 1:]
    nxt[:, -1] = np.nan

    hr = 87 + 3 * sev + u_hr[:, None] + e_hr + (p.drug_hr * occ if drug_on_obs else 0.0)
    lactate = np.exp(0.4 + 0.35 * sev + e_lac)
    creat = np.exp(0.05 + 0.25 * sev + u_cr[:, None] + e_cr)
    plt_ = 200 * np.exp(-0.30 * sev + u_pl[:, None] + e_pl)
    pf = 300 * np.exp(-0.25 * sev + u_pf[:, None] + e_pf)
    s_resp = np.select([pf < 100, pf < 200, pf < 300, pf < 400], [4, 3, 2, 1], 0)
    s_coag = np.select([plt_ < 20, plt_ < 50, plt_ < 100, plt_ < 150], [4, 3, 2, 1], 0)
    s_renal = np.select([creat >= 5.0, creat >= 3.5, creat >= 2.0, creat >= 1.2], [4, 3, 2, 1], 0)
    s_map = (mbp < 70).astype(int)
    if p.branch == "on":
        cardio = np.maximum(s_map, np.where(scored_now, 1 + tier, 0))
    else:
        cardio = s_map
    total = s_resp + s_coag + s_renal + cardio

    # modeling rows: bins 0 .. L-1, L drawn from the real rows-per-stay distribution
    ks = np.array([int(k) for k in p.rows_per_stay])
    w = np.array([float(v) for v in p.rows_per_stay.values()])
    L = rng.choice(ks, size=n, p=w / w.sum())
    keep = np.arange(T)[None, :] < L[:, None]
    sid, b = np.nonzero(keep)
    cols = {"mbp": mbp, "heart_rate": hr, "lactate": lactate, "creatinine": creat, "platelets": plt_,
            "pf_ratio": pf, "sofa_resp": s_resp, "sofa_coag": s_coag, "sofa_renal": s_renal,
            "sofa_cardio": cardio, "sofa_total": total}
    df = pd.DataFrame({"stay_id": sid, "bin": b})
    for c in FEATURES_A:
        df[c] = cols[c][sid, b].astype(float)
    df["action_next"] = nxt[sid, b].astype(int)
    df["on_tau"] = on_tau[sid, b].astype(int)
    df["severity"] = sev[sid, b]
    return df, occ, on_tau, sev


def marginals(df: pd.DataFrame, occ: np.ndarray) -> dict:
    """The same aggregates the calibration script computes on the real cohort."""
    on = df["on_tau"].values.astype(bool)
    y = df["action_next"].values
    lens = np.array([L for row in occ for _, L in run_lengths(row)] or [0])
    hist = {str(k): int((lens == k).sum()) for k in range(1, N_BINS + 1)}
    lag = {}
    a = df[["stay_id", "bin", "mbp"]]
    for k in (1, 8):
        m = a.merge(a.assign(bin=a["bin"] - k), on=["stay_id", "bin"], suffixes=("", "_k"))
        lag[str(k)] = float(np.corrcoef(m["mbp"], m["mbp_k"])[0, 1])
    lab = df[["stay_id", "bin", "action_next"]]
    pers = {}
    for k in (1, 2, 4, 8):
        m = lab.merge(lab.assign(bin=lab["bin"] - k), on=["stay_id", "bin"], suffixes=("", "_k"))
        pers[str(k)] = {"p_yk_given_y1": float(m.loc[m.action_next == 1, "action_next_k"].mean()),
                        "p_yk_given_y0": float(m.loc[m.action_next == 0, "action_next_k"].mean())}
    return {"n_stays": int(df["stay_id"].nunique()), "n_rows": int(len(df)), "label_persistence": pers,
            "frac_on_at_tau": float(on.mean()), "next_action_prevalence": float(y.mean()),
            "label_rate_given_on": float(y[on].mean()) if on.any() else float("nan"),
            "label_rate_given_off": float(y[~on].mean()),
            "frac_bins_occupied": float(occ.mean()), "frac_occupied_at_bin0": float(occ[:, 0].mean()),
            "frac_stays_ever_on": float(occ.any(axis=1).mean()),
            "run_length_mean_all": float(lens.mean()), "run_length_hist_all": hist,
            "mbp_mean_on": float(df.loc[on, "mbp"].mean()), "mbp_mean_off": float(df.loc[~on, "mbp"].mean()),
            "mbp_sd": float(df["mbp"].std()), "mbp_lag_corr": lag,
            "frac_mbp_below_70": float((df["mbp"] < 70).mean()),
            "frac_on_with_dose_scored_cardio": float((df.loc[on, "sofa_cardio"] >= 2).mean()) if on.any() else float("nan")}


# ---- calibration to the real aggregates ----------------------------------------------------------
def calibration_loss(m: dict, tg: dict) -> float:
    """Squared standardized distance between simulated and real aggregates (lower is better)."""
    occ = tg["occupancy"]
    th = np.array([occ["run_length_hist_all"][str(k)] for k in range(1, N_BINS + 1)], float)
    sh = np.array([m["run_length_hist_all"][str(k)] for k in range(1, N_BINS + 1)], float)
    th, sh = th / th.sum(), sh / max(sh.sum(), 1)
    # run-length shape on 1..7, 8..17 and full-grid (18) mass
    shape = np.sum((np.r_[th[:7], th[7:17].sum(), th[17]] - np.r_[sh[:7], sh[7:17].sum(), sh[17]]) ** 2)
    mo = tg["moments"]["mbp"]
    terms = [
        (m["frac_on_at_tau"], tg["frac_on_at_tau"], 0.01),
        (m["label_rate_given_off"], tg["label_rate_given_off"], 0.01),
        (m["frac_occupied_at_bin0"], occ["frac_occupied_at_bin0"], 0.02),
        (m["frac_stays_ever_on"], occ["frac_stays_ever_on"], 0.02),
        (m["run_length_mean_all"], occ["run_length_mean_all"], 0.25),
        (m["mbp_mean_off"], mo["mean_off"], 1.0),
        (m["mbp_mean_on"], mo["mean_on"], 1.0),
        (m["mbp_sd"], mo["sd"], 1.0),
        (m["mbp_lag_corr"]["1"], mo["lag_corr"]["1"], 0.03),
        (m["mbp_lag_corr"]["8"], mo["lag_corr"]["8"], 0.03),
        (m["frac_mbp_below_70"], tg["frac_mbp_below_70"], 0.02),
        (m["frac_on_with_dose_scored_cardio"], tg["frac_on_with_dose_scored_cardio"], 0.02),
    ]
    for k in ("1", "4", "8"):
        terms.append((m["label_persistence"][k]["p_yk_given_y1"], tg["label_persistence"][k]["p_yk_given_y1"], 0.02))
        terms.append((m["label_persistence"][k]["p_yk_given_y0"], tg["label_persistence"][k]["p_yk_given_y0"], 0.02))
    return float(sum(((a - b) / sc) ** 2 for a, b, sc in terms) + shape / 0.0005)


CALIB_BOUNDS = {"start_intercept": (-6.0, 0.0), "start_slope": (0.0, 4.0), "admit_intercept": (-3.0, 4.0),
                "run_extra": (0.5, 15.0), "run_shape": (0.1, 5.0), "map0": (55.0, 100.0), "map_slope": (1.0, 15.0),
                "map_noise": (1.0, 12.0), "phi": (0.3, 0.99), "sev_noise": (0.05, 1.0), "sev_mean": (-1.5, 1.5),
                "sev_patient_sd": (0.1, 1.5), "drift_mean": (-0.2, 0.1), "drug_gain": (0.0, 2.0),
                "scored_fraction": (0.5, 1.0)}
CALIB_KEYS = tuple(CALIB_BOUNDS)


class _CalibObjective:
    """Picklable objective for differential evolution (common random numbers: one fixed seed)."""

    def __init__(self, base: SimParams, targets: dict, seed: int):
        self.base, self.targets, self.seed = base, targets, seed

    def params(self, x) -> SimParams:
        return replace(self.base, **dict(zip(CALIB_KEYS, map(float, x))))

    def __call__(self, x) -> float:
        df, occ, _, _ = simulate(self.params(x), self.seed)
        return calibration_loss(marginals(df, occ), self.targets)


def calibrate(targets: dict, n_stays: int = 6000, seed: int = 123, maxiter: int = 80, workers: int = 1):
    """Differential evolution over CALIB_BOUNDS on the aggregate loss, branch "on". The fitted
    parameters are then used unchanged for every branch; only `persistence` varies in the grid."""
    from scipy.optimize import differential_evolution
    rps = {k: v for k, v in targets["rows_per_stay_hist"].items() if int(k) <= N_BINS - 1}
    base = SimParams(n_stays=n_stays, branch="on", rows_per_stay=rps)
    obj = _CalibObjective(base, targets, seed)
    res = differential_evolution(obj, [CALIB_BOUNDS[k] for k in CALIB_KEYS], maxiter=maxiter, popsize=10,
                                 seed=seed, polish=False, workers=workers, updating="deferred" if workers != 1 else "immediate",
                                 tol=1e-6)
    return replace(obj.params(res.x), n_stays=12000), float(res.fun)


# ---- one setting through the frozen H3 functions -------------------------------------------------
def _h3_summary(r: dict) -> dict:
    keys = ("n_rows_a", "n_rows_b", "n_patients", "auroc_a", "auroc_b", "delta", "delta_ci_lo",
            "delta_ci_hi", "p_delta_ge_threshold", "n_boot_used", "prediction_A_supported")
    return {k: r[k] for k in keys}


def evaluate(df: pd.DataFrame, n_boot: int = 2000, seed: int = 42, offsets=OFFSETS, far: int = 8) -> dict:
    out = {}
    for name, feats in (("A", FEATURES_A), ("E", FEATURES_E)):
        frames = h3.offset_frames(df, feats, offsets, offset_mode="bins")
        preds = h3.predict_offsets(frames, feats, PROBE_LOGREG, cv_predict)
        curve = {str(o): float(roc_auc_score(preds[o]["y"], preds[o]["pred"])) for o in offsets}
        res = {"decay_curve_own_rows": curve,
               "restricted": _h3_summary(h3.paired_cluster_bootstrap(preds[0], preds[far], n_boot, seed, restrict=True))}
        if name == "A":
            res["unrestricted"] = _h3_summary(h3.paired_cluster_bootstrap(preds[0], preds[far], n_boot, seed, restrict=False))
        out[name] = res
    frames = h3.offset_frames(df, ["on_tau"], offsets, offset_mode="bins")
    pi = {o: f[["stay_id", "bin", "y"]].assign(pred=f["on_tau"].values.astype(float)) for o, f in frames.items()}
    out["indicator"] = {
        "decay_curve_own_rows": {str(o): float(roc_auc_score(pi[o]["y"], pi[o]["pred"])) for o in offsets},
        "restricted": _h3_summary(h3.paired_cluster_bootstrap(pi[0], pi[far], n_boot, seed, restrict=True))}
    out["A_minus_E_offset0"] = out["A"]["decay_curve_own_rows"]["0"] - out["E"]["decay_curve_own_rows"]["0"]
    return out


def run_setting(params: SimParams, branch: str, persistence: str, seed: int, n_boot: int = 2000) -> dict:
    p = replace(params, branch=branch, persistence=PERSISTENCE[persistence])
    df, occ, _, _ = simulate(p, seed)
    return {"branch": branch, "persistence": persistence, "persistence_multiplier": PERSISTENCE[persistence],
            "sim_seed": seed, "marginals": marginals(df, occ), "h3": evaluate(df, n_boot=n_boot),
            "exploratory": EXPLORATORY}


def _worker(args):
    params, branch, pers, seed, n_boot, out_dir = args
    path = Path(out_dir) / f"setting_{branch}_{pers}_seed{seed}.json"
    if path.exists():
        return str(path)
    r = run_setting(params, branch, pers, seed, n_boot)
    path.write_text(json.dumps(r, indent=1))
    a = r["h3"]["A"]["restricted"]
    print(f"{branch:8s} {pers:9s} seed={seed}  A: Delta={a['delta']:.3f} CI=({a['delta_ci_lo']:.3f},"
          f"{a['delta_ci_hi']:.3f}) A={a['prediction_A_supported']}  A-E={r['h3']['A_minus_E_offset0']:.3f}", flush=True)
    return str(path)


def load_params(path) -> SimParams:
    d = json.load(open(path))["params"]
    d["drug_map"], d["tier_cut"] = tuple(d["drug_map"]), tuple(d["tier_cut"])
    return SimParams(**d)


# ---- summary table and figure --------------------------------------------------------------------
def summarize(out_dir, dest) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(out_dir).glob("setting_*.json")):
        r = json.load(open(f))
        m, h = r["marginals"], r["h3"]
        row = {"branch": r["branch"], "persistence": r["persistence"], "seed": r["sim_seed"],
               "mean_run_bins": m["run_length_mean_all"], "frac_on_at_tau": m["frac_on_at_tau"],
               "prevalence": m["next_action_prevalence"]}
        for v in ("A", "E", "indicator"):
            rr = h[v]["restricted"]
            row.update({f"{v}_auroc0": rr["auroc_a"], f"{v}_auroc8": rr["auroc_b"], f"{v}_delta": rr["delta"],
                        f"{v}_ci_lo": rr["delta_ci_lo"], f"{v}_ci_hi": rr["delta_ci_hi"],
                        f"{v}_predA": rr["prediction_A_supported"]})
        row["A_minus_E_offset0"] = h["A_minus_E_offset0"]
        rows.append(row)
    t = pd.DataFrame(rows)
    order = {k: i for i, k in enumerate(PERSISTENCE)}
    border = {k: i for i, k in enumerate(BRANCHES)}
    t = t.sort_values(["branch", "persistence", "seed"], key=lambda s: s.map(order) if s.name == "persistence"
                      else (s.map(border) if s.name == "branch" else s)).reset_index(drop=True)
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    t.round(4).to_csv(dest / "grid_results.csv", index=False)
    figure(t, dest / "delta_vs_persistence.png")
    return t


def figure(t: pd.DataFrame, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"on": "#2a78d6", "off": "#eb6834", "off_pure": "#1baf7a"}
    labels = {"on": "treatment branch ON (real SOFA)", "off": "branch OFF (MAP only; drug raises MAP)",
              "off_pure": "branch OFF, drug invisible in the state"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=False)
    for ax, (v, title) in zip(axes, (("A", "Variant A (full state), logreg probe"),
                                     ("indicator", "On-at-tau indicator alone"))):
        for k, br in enumerate(BRANCHES):
            s = t[t.branch == br]
            if s.empty:
                continue
            x = s.groupby("persistence", sort=False)["mean_run_bins"].mean()
            g = s.groupby("persistence", sort=False)
            mean, lo, hi = g[f"{v}_delta"].mean(), g[f"{v}_ci_lo"].min(), g[f"{v}_ci_hi"].max()
            xs = x.values + (k - 1) * 0.04
            ax.errorbar(xs, mean.values, yerr=[mean.values - lo.values, hi.values - mean.values], color=colors[br],
                        marker="o", ms=8, lw=2, capsize=3, label=labels[br])
        ax.axhline(h3.DELTA_THRESHOLD, color="#52514e", ls="--", lw=1)
        ax.text(ax.get_xlim()[0], h3.DELTA_THRESHOLD, " Prediction A threshold 0.10", va="bottom", fontsize=8, color="#52514e")
        ax.axhline(0, color="#c3c2b7", lw=0.8)
        ax.set_xlabel("simulated mean infusion run length (4h bins)")
        ax.set_ylabel("Delta = AUROC(0) - AUROC(8), common rows")
        ax.set_title(title, fontsize=10)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
    axes[0].legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle("Synthetic ground truth: H3 Delta vs treatment persistence (exploratory, not pre-registered)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calib"); c.add_argument("--targets", required=True); c.add_argument("--dest", required=True)
    c.add_argument("--maxiter", type=int, default=80); c.add_argument("--workers", type=int, default=1)
    g = sub.add_parser("grid"); g.add_argument("--params", required=True); g.add_argument("--out", required=True)
    g.add_argument("--workers", type=int, default=1); g.add_argument("--n-stays", type=int, default=12000)
    g.add_argument("--n-boot", type=int, default=2000)
    s = sub.add_parser("summarize"); s.add_argument("--out", required=True); s.add_argument("--dest", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "calib":
        tg = json.load(open(a.targets))
        p, loss = calibrate(tg, maxiter=a.maxiter, workers=a.workers)
        check = SimParams(**{**asdict(p), "n_stays": 12000})
        df, occ, _, _ = simulate(check, 7)
        m = marginals(df, occ)
        Path(a.dest).mkdir(parents=True, exist_ok=True)
        d = {"exploratory": EXPLORATORY, "loss": loss, "params": asdict(p), "simulated_marginals_branch_on_seed7": m}
        (Path(a.dest) / "sim_params.json").write_text(json.dumps(d, indent=1))
        print(json.dumps(d, indent=1))
    elif a.cmd == "grid":
        params = replace(load_params(a.params), n_stays=a.n_stays)
        Path(a.out).mkdir(parents=True, exist_ok=True)
        jobs = [(params, br, pe, sd, a.n_boot, a.out) for br in BRANCHES for pe in PERSISTENCE for sd in SEEDS]
        if a.workers > 1:
            from multiprocessing import Pool
            with Pool(a.workers) as pool:
                list(pool.imap_unordered(_worker, jobs))
        else:
            for j in jobs:
                _worker(j)
    else:
        t = summarize(a.out, a.dest)
        print(t.round(3).to_string())


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    main()
