"""Decay curves for the exploratory persistence control (scripts/exp_persistence.py): logreg AUROC
by bin-index offset for P, I, E, A, A+I, E+I with patient-bootstrap 95% CIs, both cohorts, common
rows (top) and each offset's own rows (bottom). Exploratory, not pre-registered; does not change the
H3 decision.

    python scripts/exp_persistence_figure.py results/exploratory/persistence
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# reference categorical palette, fixed slot order; marker and line style as secondary encoding
SERIES = [("A", "#2a78d6", "o", "-"), ("E", "#eb6834", "s", "-"), ("A+I", "#1baf7a", "^", "-"),
          ("E+I", "#eda100", "v", "-"), ("P", "#e87ba4", "D", "--"), ("I", "#008300", "X", "--")]
LABELS = {"A": "A full state", "E": "E physiology only", "A+I": "A + on-at-tau", "E+I": "E + on-at-tau",
          "P": "P previous action only", "I": "I on-at-tau only"}
COHORTS = [("13192", "13,192 stays (primary)"), ("11354", "11,354 stays (sensitivity)")]
UNIVERSES = [("common", "rows present at offsets 0 and 8"), ("own", "each offset's own rows")]


def main(d: str):
    d = Path(d)
    data = {c: json.load(open(d / f"persistence_{c}.json")) for c, _ in COHORTS}
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e",
                         "ytick.color": "#52514e", "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.8), sharey=True, sharex=True)
    for j, (c, ctitle) in enumerate(COHORTS):
        for i, (u, utitle) in enumerate(UNIVERSES):
            ax = axes[i, j]
            auc = data[c]["universes"][u]["auroc"]["logreg"]
            for name, col, mk, ls in SERIES:
                offs = sorted(int(o) for o in auc[name])
                y = [auc[name][str(o)]["auroc"] for o in offs]
                lo = [auc[name][str(o)]["auroc"] - auc[name][str(o)]["ci"][0] for o in offs]
                hi = [auc[name][str(o)]["ci"][1] - auc[name][str(o)]["auroc"] for o in offs]
                ax.errorbar(offs, y, yerr=[lo, hi], color=col, marker=mk, ms=5, lw=2, ls=ls, capsize=2,
                            elinewidth=1, label=LABELS[name])
            n0, n8 = auc["A"]["0"]["n"], auc["A"]["8"]["n"]
            ax.set_title(f"{ctitle}\n{utitle} (n={n0:,} at 0, {n8:,} at 8)", fontsize=9, color="#0b0b0b")
            ax.set_xticks([0, 1, 2, 4, 8])
            ax.grid(axis="y", color="#e4e3df", lw=0.6)
            if i == 1:
                ax.set_xlabel("label offset (decision bins of 4 h)")
            if j == 0:
                ax.set_ylabel("AUROC, logreg (95% patient-bootstrap CI)")
    h, lab = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=6, frameon=False, fontsize=8)
    fig.suptitle("Persistence control: next-vasopressor AUROC by offset (exploratory, not pre-registered)",
                 fontsize=10, color="#0b0b0b")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = d / "persistence_decay_curves.png"
    fig.savefig(out, dpi=150)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/exploratory/persistence")
