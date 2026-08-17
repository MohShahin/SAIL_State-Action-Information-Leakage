#!/usr/bin/env python3
"""
scripts/run_notebook_checkpointed.py

Executes notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb cell-by-cell via nbclient, saving the
notebook to disk after EVERY cell (not just at the end) so a hard kill -- a watcher/CI timeout,
the machine sleeping mid-run, anything short of losing the file itself -- loses at most the one
cell that was in flight, not the whole run.

Why this exists: a plain `jupyter nbconvert --execute` only writes the notebook back once the
entire run finishes (or is cleanly interrupted). Long BigQuery + sklearn cells here have run
anywhere from ~35 min to 90+ min depending on machine load, and a naive full-notebook execution
that dies two cells from the end throws away everything. This trades a small amount of I/O
overhead (one JSON write per cell) for that safety.

Requires a `python3` kernelspec registered for the interpreter you want cells to run under
(`python -m ipykernel install --user --name python3`), and that interpreter to have every package
the notebook imports (google-cloud-bigquery, db_dtypes, pandas, numpy, scikit-learn, ...).
Also skips the notebook's own `google.colab.auth` cell (index 2) by default -- that cell is
Colab-specific and not needed when running locally with `gcloud auth application-default login`
already set up (see scripts/check_setup.sh).

Usage:
    python scripts/run_notebook_checkpointed.py                  # cells 0..(default stop) - 1
    python scripts/run_notebook_checkpointed.py --stop-index 25  # run cells 0..24
    python scripts/run_notebook_checkpointed.py --timeout 5400   # per-cell timeout, seconds

Cell indices are notebook-structure-specific and will shift if cells are inserted/removed above
the range you're running -- check with a quick `nbformat` cell listing before relying on a
specific --stop-index after editing the notebook's cell count.
"""
import argparse
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NB_PATH = REPO_ROOT / "notebook" / "Sepsis_RL_SOFA_Leakage_Experiments.ipynb"

# Default stop index matches "through Section 9 / Experiment 3 plus the Experiment-5 checkpoint
# cell" as of the notebook structure when this script was written (cell 22 = checkpoint pickle,
# cell 24 = Experiment 3's code cell). Override with --stop-index if the notebook has changed.
DEFAULT_STOP_INDEX = 25
DEFAULT_SKIP_INDEX = {2}  # Colab-only google.colab.auth cell
DEFAULT_TIMEOUT = 5400  # seconds per cell


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NB_PATH, help="path to the .ipynb file")
    parser.add_argument("--stop-index", type=int, default=DEFAULT_STOP_INDEX,
                         help="exclusive upper bound on cell index to execute")
    parser.add_argument("--skip-index", type=int, nargs="*", default=sorted(DEFAULT_SKIP_INDEX),
                         help="cell indices to skip entirely (e.g. Colab-only auth cells)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="per-cell timeout in seconds")
    parser.add_argument("--kernel-name", default="python3", help="registered kernelspec name to execute under")
    args = parser.parse_args()

    skip_index = set(args.skip_index)
    nb_path = args.notebook
    nb = nbformat.read(nb_path, as_version=4)

    client = NotebookClient(
        nb,
        timeout=args.timeout,
        kernel_name=args.kernel_name,
        resources={"metadata": {"path": str(nb_path.parent)}},
    )

    print(f"Executing cells 0-{args.stop_index - 1} (skipping {sorted(skip_index)}); "
          f"leaving cells {args.stop_index}+ untouched", flush=True)

    with client.setup_kernel():
        for i, cell in enumerate(nb.cells):
            if i >= args.stop_index:
                break
            if cell.cell_type != "code":
                continue
            if i in skip_index:
                print(f"[cell {i}] SKIPPED (in --skip-index)", flush=True)
                continue
            t0 = time.time()
            print(f"[cell {i}] START", flush=True)
            try:
                client.execute_cell(cell, i)
            except Exception as e:
                dt = time.time() - t0
                print(f"[cell {i}] EXCEPTION after {dt:.1f}s: {type(e).__name__}: {e}", flush=True)
                nbformat.write(nb, nb_path)
                print("SAVED notebook (partial, up to the failing cell)", flush=True)
                raise
            dt = time.time() - t0
            print(f"[cell {i}] DONE in {dt:.1f}s", flush=True)
            for out in cell.get("outputs", []):
                if out.get("output_type") == "stream":
                    text = out.get("text", "").strip()
                    if text:
                        print(f"[cell {i} output] {text}", flush=True)
                elif out.get("output_type") == "error":
                    print(f"[cell {i} ERROR] {out.get('ename')}: {out.get('evalue')}", flush=True)
            # Crash-safe: persist progress after every cell, not just at the end, so a hard kill
            # (a watcher timeout, the machine sleeping mid-run) doesn't lose completed work.
            nbformat.write(nb, nb_path)
            print(f"[cell {i}] saved to disk", flush=True)

    print(f"ALL_DONE -- cells 0-{args.stop_index - 1} executed, cells {args.stop_index}+ left untouched", flush=True)


if __name__ == "__main__":
    main()
