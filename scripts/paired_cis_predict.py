#!/usr/bin/env python3
"""Exploratory, not pre-registered; does not change the H3 decision.

Recreates the out-of-fold predictions behind Experiments 2 (next action), 6 (mortality) and 8
(variant F) so that paired, patient-level uncertainty can be put on the AUROC differences the
project reports (scripts/paired_cis.py does the bootstrap). The notebook keeps none of these
predictions, so this script executes the notebook's own code cells in-process, in order, with
three cuts that only remove model training it would otherwise repeat:

  cell 21  stops before `run_experiment2(...)`        (keeps PROBES, cv_predict, MI estimator)
  cell 24  stops before `run_experiment6(...)`        (keeps mortality_snap, mortality_variants)
  cell 33  stops before `def _evaluate_variant(`      (keeps variant F on both axes)

Cells skipped: 2 (Colab auth), 16 (Experiment 1), 22 (Exp 5 checkpoint), 26 (Experiment 7),
29 (Experiment 3), 32 (Exp 8 hand-check); none of them feeds the matrices used here.

Predictions then come from the notebook's own `cv_predict` and `PROBES` (GroupKFold 5 by stay_id,
StandardScaler, random_state 42), for variants A to F and probes logreg, rf, gb on both axes.

The DuckDB file is opened READ-ONLY. The notebook's cohort scratch table goes to an attached
in-memory catalog instead (SCRATCH_SCHEMA patched), so nothing is written into the database.

Outputs (patient-level, cluster only, under --out):
  preds_action.parquet      stay_id, bin, y, pred_<variant>_<probe>
  preds_mortality.parquet   stay_id, y, pred_<variant>_<probe>
  mi_action.parquet         stay_id, y, the 25 variant A columns and D's two replaced columns
  points.json               point AUROCs and notebook MI values (aggregates)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
NB = REPO / "notebook" / "Sepsis_RL_SOFA_Leakage_Experiments.ipynb"
RUN_CELLS = [3, 5, 7, 9, 11, 12, 14, 18, 19, 21, 24, 28, 31, 33]
CUTS = {
    21: "exp2_results, exp2_best, exp2_gap = run_experiment2(",
    24: "exp6_results, exp6_best = run_experiment6(",
    33: "def _evaluate_variant(",
}
VARIANTS = ["A_full", "B_no_total_sofa", "C_no_cardio_sofa", "D_treatment_decomposed",
            "E_physiology_only", "F_disentangled"]
PROBES = ["logreg", "rf", "gb"]


def cell_sources(nb_path: Path = NB) -> dict[int, str]:
    nb = json.loads(nb_path.read_text())
    out = {}
    for i in RUN_CELLS:
        cell = nb["cells"][i]
        assert cell["cell_type"] == "code", f"cell {i} is not code; notebook structure changed"
        src = "".join(cell["source"])
        if i in CUTS:
            assert src.count(CUTS[i]) == 1, f"cut marker for cell {i} not found exactly once"
            src = src.split(CUTS[i])[0]
        out[i] = src
    return out


def open_readonly_backend(db_path: str, threads: int, mem: str, tmp: str):
    sys.path.insert(0, str(REPO / "scripts"))
    import duckdb
    import duckdb_backend as sail_db
    Path(tmp).mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path, read_only=True)
    con.execute(f"SET threads = {threads}")
    con.execute(f"SET memory_limit = '{mem}'")
    con.execute(f"SET temp_directory = '{tmp}'")
    con.execute("ATTACH ':memory:' AS pcscratch")
    sail_db.SCRATCH_SCHEMA = "pcscratch"
    sail_db._con = con
    return sail_db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    out = args.out
    (out / "results").mkdir(parents=True, exist_ok=True)
    os.environ["SAIL_BACKEND"] = "duckdb"
    os.environ.setdefault("SAIL_REPO", str(REPO))
    sail_db = open_readonly_backend(os.path.expanduser(os.environ.get("SAIL_DUCKDB", "~/orcd/scratch/sail/mimic4.db")),
                                    int(os.environ.get("SAIL_THREADS", "8")), os.environ.get("SAIL_MEM", "32GB"),
                                    str(out / "duckdb_tmp"))
    print(f"read-only DB {sail_db.DB_PATH}; scratch catalog {sail_db.SCRATCH_SCHEMA}", flush=True)
    os.chdir(out)  # the notebook writes to ./results; nothing goes into the repo
    ns: dict = {"__name__": "__sail_notebook__"}
    t0 = time.time()
    for i, src in cell_sources().items():
        print(f"[cell {i}] start {time.time() - t0:.0f}s", flush=True)
        exec(compile(src, f"<cell {i}>", "exec"), ns)
    print(f"cells done {time.time() - t0:.0f}s", flush=True)

    cv_predict, probes = ns["cv_predict"], ns["PROBES"]
    act = ns["variants"]
    mort = ns["mortality_variants"]
    assert list(act) == VARIANTS and list(mort) == VARIANTS, (list(act), list(mort))
    state_4h = ns["state_4h"]
    y_a, g_a = ns["y_action"], ns["groups"]
    y_m, g_m = ns["y_mortality"], ns["groups_mortality"]

    pa = pd.DataFrame({"stay_id": g_a, "bin": state_4h["bin"].values, "y": y_a})
    pm = pd.DataFrame({"stay_id": g_m, "y": y_m})
    points = {"n_action_rows": int(len(y_a)), "n_action_stays": int(len(np.unique(g_a))),
              "n_mortality_rows": int(len(y_m)), "n_cohort_stays": int(len(ns["stay_ids"])),
              "action_auroc": {}, "mortality_auroc": {}, "mutual_info": {}}
    from sklearn.metrics import roc_auc_score
    for axis, V, y, g, frame in (("action", act, y_a, g_a, pa), ("mortality", mort, y_m, g_m, pm)):
        for v in VARIANTS:
            for p in PROBES:
                t1 = time.time()
                pred = cv_predict(V[v], y, g, probes[p], n_splits=5)
                frame[f"pred_{v}_{p}"] = pred
                auc = float(roc_auc_score(y, pred))
                points[f"{axis}_auroc"][f"{v}|{p}"] = auc
                print(f"{axis:9s} {v:24s} {p:6s} AUROC={auc:.6f} ({time.time() - t1:.0f}s)", flush=True)
    for v in VARIANTS[:5]:
        points["mutual_info"][v] = float(ns["mutual_information_estimate"](act[v], y_a))
    pa.to_parquet(out / "preds_action.parquet", index=False)
    pm.to_parquet(out / "preds_mortality.parquet", index=False)

    fn = ns["feature_names"]
    mi = pd.DataFrame(act["A_full"], columns=fn)
    xd = act["D_treatment_decomposed"]
    mi["D__sofa_cardio"] = xd[:, fn.index("sofa_cardio")]
    mi["D__sofa_total"] = xd[:, fn.index("sofa_total")]
    mi.insert(0, "y", y_a)
    mi.insert(0, "stay_id", g_a)
    mi.to_parquet(out / "mi_action.parquet", index=False)
    points["feature_names"] = fn
    (out / "points.json").write_text(json.dumps(points, indent=2))
    print(f"ALL_DONE {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
