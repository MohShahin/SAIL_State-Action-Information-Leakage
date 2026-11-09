"""Aggregate-only figures for results/figures/.

Three subcommands:

  h3-replicates  CLUSTER ONLY. Recomputes the bootstrap replicates of the pinned H3 test (common
                 rows, bin-index offsets) from the run's per-patient prediction parquets, by calling
                 scripts/h3_paired_bootstrap.paired_cluster_bootstrap itself with the frozen settings
                 (2,000 patient resamples, seed 42). The function does not return its replicates, so
                 its roc_auc_score is wrapped to record each AUROC as it is computed; nothing in the
                 resampling is reimplemented. The recomputed summary is checked field by field
                 against the committed JSON before the replicates are written. The output holds
                 2,000 cohort-level Delta values (no patient rows); it stays on the cluster.
  h3             Decay curve (panel 1) from the committed bins JSON and, given --replicates, the
                 bootstrap distribution of Delta (panel 2). Without --replicates, panel 1 only.
  cohort         Cohort flow diagram from results/experiment0_cohort_duckdb_diagnostics.json.

Examples:
  python scripts/make_figures.py h3-replicates \\
      --pred-dir <pinned run dir>/notebook/results \\
      --committed results/experiment5_h3_paired_bootstrap_bins.json --out h3_replicates.json
  python scripts/make_figures.py h3 --bins-json results/experiment5_h3_paired_bootstrap_bins.json \\
      --replicates h3_replicates.json --out results/figures/h3_pinned_29fb4ec_bins.png
  python scripts/make_figures.py cohort \\
      --diag results/experiment0_cohort_duckdb_diagnostics.json --out results/figures/cohort_flow.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(INK_2)
    ax.spines["bottom"].set_color(INK_2)
    ax.tick_params(colors=INK_2)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------------------------
# H3 replicates (cluster)
# ---------------------------------------------------------------------------------------------
def h3_replicates(pred_dir: Path, committed: Path, out: Path, near: int = 0, far: int = 8,
                  n_boot: int = 2000, seed: int = 42, tag: str = "bins") -> dict:
    import pandas as pd

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import h3_paired_bootstrap as h3

    p_a = pd.read_parquet(Path(pred_dir) / f"experiment5_predictions_offset{near}_{tag}.parquet")
    p_b = pd.read_parquet(Path(pred_dir) / f"experiment5_predictions_offset{far}_{tag}.parquet")

    recorded: list[float] = []
    original = h3.roc_auc_score

    def recording(y, p):
        v = original(y, p)
        recorded.append(float(v))
        return v

    h3.roc_auc_score = recording
    try:
        res = h3.paired_cluster_bootstrap(p_a, p_b, n_boot=n_boot, seed=seed, restrict=True)
    finally:
        h3.roc_auc_score = original

    # per used replicate: AUROC(a) then AUROC(b); the last two calls are the point estimates
    reps = np.asarray(recorded[:-2]).reshape(-1, 2)
    if len(reps) != res["n_boot_used"]:
        raise RuntimeError(f"recorded {len(reps)} replicates, function used {res['n_boot_used']}")
    deltas = reps[:, 0] - reps[:, 1]
    lo, hi = np.percentile(deltas, 2.5), np.percentile(deltas, 97.5)
    if (lo, hi) != (res["delta_ci_lo"], res["delta_ci_hi"]):
        raise RuntimeError("recorded replicates do not reproduce the function's own CI")

    ref = json.loads(Path(committed).read_text())["restricted"]
    diffs = {k: (res[k], ref.get(k)) for k in res if res[k] != ref.get(k)}
    if diffs:
        raise RuntimeError(f"recomputed summary differs from {committed}: {diffs}")

    payload = {
        "note": "Bootstrap replicates of Delta = AUROC(0) - AUROC(8), common rows, recomputed with "
                "scripts/h3_paired_bootstrap.paired_cluster_bootstrap; cohort-level values only.",
        "source_pred_dir": str(pred_dir), "committed_json": str(committed),
        "matches_committed_restricted_block": True,
        "summary": res,
        "delta_replicates": deltas.tolist(),
        "auroc_a_replicates": reps[:, 0].tolist(),
        "auroc_b_replicates": reps[:, 1].tolist(),
    }
    Path(out).write_text(json.dumps(payload))
    print(f"recomputed Delta={res['delta']:.4f} CI=({lo:.4f}, {hi:.4f}) n_boot_used={len(deltas)}; "
          f"identical to {committed}: True")
    return payload


# ---------------------------------------------------------------------------------------------
# H3 figure
# ---------------------------------------------------------------------------------------------
def h3_figure(bins_json: Path, out: Path, replicates: Path | None = None, title_run: str = "") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = json.loads(Path(bins_json).read_text())
    r = d["restricted"]
    curve = d["decay_curve"]
    reps = None
    if replicates is not None:
        reps = json.loads(Path(replicates).read_text())
        s = reps["summary"]
        for k in ("delta", "delta_ci_lo", "delta_ci_hi", "auroc_a", "auroc_b"):
            if s[k] != r[k]:
                raise RuntimeError(f"replicates file does not belong to {bins_json} ({k})")

    ncol = 2 if reps is not None else 1
    fig, axes = plt.subplots(1, ncol, figsize=(6.2 * ncol, 4.6), squeeze=False)
    ax = axes[0, 0]
    x = [c["offset_bins"] for c in curve]
    y = [c["auroc"] for c in curve]
    ax.plot(x, y, color=BLUE, linewidth=2, marker="o", markersize=7, label="AUROC, each offset's own rows")
    for c in curve:
        ax.annotate(f"n={c['n']:,}", (c["offset_bins"], c["auroc"]), textcoords="offset points",
                    xytext=(6, 6), fontsize=8, color=INK_2)
    xa, xb = -0.25, d["far_offset"] - 0.25
    for xx, v, ci in ((xa, r["auroc_a"], r["auroc_a_ci"]), (xb, r["auroc_b"], r["auroc_b_ci"])):
        ax.errorbar([xx], [v], yerr=[[v - ci[0]], [ci[1] - v]], fmt="s", color=ORANGE, markersize=7,
                    capsize=4, linewidth=1.5)
    ax.plot([], [], "s", color=ORANGE, label=f"common rows (n={r['n_rows_a']:,}), 95% CI")
    ax.annotate(f"{r['auroc_a']:.3f}", (xa, r["auroc_a"]), textcoords="offset points", xytext=(-30, -4),
                fontsize=8, color=INK_2)
    ax.annotate(f"{r['auroc_b']:.3f}", (xb, r["auroc_b"]), textcoords="offset points", xytext=(-30, -4),
                fontsize=8, color=INK_2)
    ax.set_xticks(x)
    ax.set_xlim(-1.0, d["far_offset"] + 1.0)
    ax.set_xlabel("Offset of predicted action (4h bins)", color=INK)
    ax.set_ylabel("AUROC (logreg, grouped CV)", color=INK)
    ax.set_title("H3 decay curve, bin-index offsets", color=INK, fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    _style(ax)

    if reps is not None:
        ax = axes[0, 1]
        deltas = np.asarray(reps["delta_replicates"])
        ax.hist(deltas, bins=40, color=BLUE, edgecolor="white", linewidth=0.6)
        ax.axvline(r["threshold"], color=ORANGE, linestyle="--", linewidth=1.5,
                   label=f"threshold {r['threshold']:.2f}")
        ax.axvline(0, color=INK_2, linestyle=":", linewidth=1.5, label="0")
        ax.axvspan(r["delta_ci_lo"], r["delta_ci_hi"], color=BLUE, alpha=0.12,
                   label=f"95% CI {r['delta_ci_lo']:.4f} to {r['delta_ci_hi']:.4f}")
        ax.axvline(r["delta"], color=INK, linewidth=1.5, label=f"Delta = {r['delta']:.4f}")
        ax.set_xlim(-0.01, max(deltas.max(), r["delta_ci_hi"]) + 0.01)
        ax.set_xlabel("Delta = AUROC(0) - AUROC(8), common rows", color=INK)
        ax.set_ylabel("Bootstrap replicates", color=INK)
        ax.set_title(f"Paired cluster bootstrap ({len(deltas):,} patient resamples, seed {r['seed']})",
                     color=INK, fontsize=11)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
        _style(ax)

    if title_run:
        fig.suptitle(title_run, color=INK, fontsize=11)
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------------------------
# Cohort flow
# ---------------------------------------------------------------------------------------------
def cohort_figure(diag_json: Path, out: Path, sensitivity_n: int | None = None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    d = json.loads(Path(diag_json).read_text())
    st = d["stages_notebook_ranking"]
    sens = sensitivity_n if sensitivity_n is not None else d["published_cohort_for_comparison"]
    stages = [
        ("ICU stays, MIMIC-IV v3.1", d["icustays_total"]),
        ("Adult, first ICU stay, LOS >= 1 day", st["adult_first_icu_stay_los_ge_1d"]),
        ("+ vasopressor", st["plus_vasopressor"]),
        ("+ Sepsis-3 (v3.1 derived table)\nPRIMARY COHORT", st["plus_sepsis3_cohort"]),
    ]

    fig, ax = plt.subplots(figsize=(9.5, 6.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(1.1, 10)
    ax.axis("off")
    w, h, x0 = 4.2, 1.2, 0.3
    ys = [8.6, 6.3, 4.0, 1.4]

    def box(x, y, text, n, edge, fill):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    linewidth=1.5, edgecolor=edge, facecolor=fill))
        ax.text(x + w / 2, y + h * 0.66, text, ha="center", va="center", fontsize=9, color=INK)
        ax.text(x + w / 2, y + h * 0.2, f"n = {n:,}", ha="center", va="center", fontsize=11,
                color=INK, fontweight="bold")

    for i, ((label, n), y) in enumerate(zip(stages, ys)):
        primary = i == len(stages) - 1
        box(x0, y, label, n, BLUE if primary else INK_2, "#e8f1fb" if primary else "#fcfcfb")
        if i:
            prev_n, prev_y = stages[i - 1][1], ys[i - 1]
            ax.annotate("", xy=(x0 + w / 2, y + h), xytext=(x0 + w / 2, prev_y),
                        arrowprops=dict(arrowstyle="-|>", color=INK_2, linewidth=1.2))
            ax.text(x0 + w / 2 + 0.15, (y + h + prev_y) / 2, f"excluded {prev_n - n:,}",
                    va="center", fontsize=8.5, color=INK_2)

    sx = 5.5
    sy = ys[3]
    box(sx, sy, "Sepsis-3 condition replaced by the\nstays of a MIMIC-IV v2.2 build\nSENSITIVITY COHORT", sens,
        ORANGE, "#fdf0ea")
    ax.annotate("", xy=(sx + w / 2, sy + h), xytext=(x0 + w, ys[2] + h / 2),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, linewidth=1.2,
                                connectionstyle="angle,angleA=0,angleB=90"))
    ax.text(sx + 0.1, ys[2] + h / 2 + 0.25, "SAIL_COHORT_STAYS override", fontsize=8.5, color=INK_2)
    ax.set_title("Cohort flow, DuckDB reproduction (counts of ICU stays)", color=INK, fontsize=12)
    fig.tight_layout()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("h3-replicates")
    a.add_argument("--pred-dir", type=Path, required=True)
    a.add_argument("--committed", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    b = sub.add_parser("h3")
    b.add_argument("--bins-json", type=Path, required=True)
    b.add_argument("--replicates", type=Path)
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--title", default="")
    c = sub.add_parser("cohort")
    c.add_argument("--diag", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--sensitivity-n", type=int)
    args = ap.parse_args(argv)
    if args.cmd == "h3-replicates":
        h3_replicates(args.pred_dir.expanduser(), args.committed, args.out)
    elif args.cmd == "h3":
        h3_figure(args.bins_json, args.out, args.replicates, args.title)
    else:
        cohort_figure(args.diag, args.out, args.sensitivity_n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
