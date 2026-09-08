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

Also checks the machine's sleep/hibernate timeouts before starting (Windows only, via `powercfg`)
and temporarily disables them if nonzero, restoring the exact prior values on exit -- including on
an exception -- so a crashed run never leaves sleep permanently off. Added after 4 of 6 Phase 4
execution attempts were silently killed by the machine sleeping for 9-18 hour stretches mid-run.
Every check and change this makes is printed to this script's own log output (search for
`[sleep_guard]`); if `powercfg` isn't available (non-Windows, no permission), it warns and the
notebook still runs without this protection.

Usage:
    python scripts/run_notebook_checkpointed.py                  # cells 0..(default stop) - 1
    python scripts/run_notebook_checkpointed.py --stop-index 25  # run cells 0..24
    python scripts/run_notebook_checkpointed.py --timeout 5400   # per-cell timeout, seconds

Cell indices are notebook-structure-specific and will shift if cells are inserted/removed above
the range you're running -- check with a quick `nbformat` cell listing before relying on a
specific --stop-index after editing the notebook's cell count.
"""
import argparse
import contextlib
import re
import subprocess
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

# Windows-only sleep/hibernate-timeout GUID aliases this guard checks and, if needed, temporarily
# clears. See sleep_guard() below -- added after 4 of 6 Phase 4 execution attempts were silently
# killed by the machine sleeping for 9-18 hour stretches mid-run (fixed manually via powercfg that
# time, not fixed structurally). "Sleep after" covers both plain sleep and the S4/hibernate-from-
# sleep path seen in that incident's Event Log.
_POWER_SETTINGS = [("STANDBYIDLE", "standby (sleep) timeout"), ("HIBERNATEIDLE", "hibernate timeout")]


def _run_powercfg(*args):
    return subprocess.run(["powercfg", *args], capture_output=True, text=True, check=True, timeout=30)


def _query_power_setting(alias):
    """Return (ac_seconds, dc_seconds) currently set for the given GUID alias, by parsing
    `powercfg /query SCHEME_CURRENT SUB_SLEEP` -- the query and /change commands use different
    units (seconds vs. minutes), so this reads and writes the raw index directly via
    /setacvalueindex /setdcvalueindex to avoid any lossy rounding when restoring."""
    out = _run_powercfg("/query", "SCHEME_CURRENT", "SUB_SLEEP").stdout
    blocks = out.split("Power Setting GUID:")
    for block in blocks:
        if f"GUID Alias: {alias}" not in block:
            continue
        ac = re.search(r"Current AC Power Setting Index:\s*0x([0-9a-fA-F]+)", block)
        dc = re.search(r"Current DC Power Setting Index:\s*0x([0-9a-fA-F]+)", block)
        if ac and dc:
            return int(ac.group(1), 16), int(dc.group(1), 16)
    raise RuntimeError(f"could not find GUID Alias: {alias} in powercfg /query output")


def _set_power_setting(alias, ac_seconds, dc_seconds):
    _run_powercfg("/setacvalueindex", "SCHEME_CURRENT", "SUB_SLEEP", alias, str(ac_seconds))
    _run_powercfg("/setdcvalueindex", "SCHEME_CURRENT", "SUB_SLEEP", alias, str(dc_seconds))
    _run_powercfg("/setactive", "SCHEME_CURRENT")


@contextlib.contextmanager
def sleep_guard():
    """Check sleep/hibernate timeouts before a long run; if any are nonzero, disable them for the
    run's duration and restore the *actual prior values* (not a hardcoded default) on the way out
    -- including on an exception, so a crashed run never leaves the machine with sleep permanently
    disabled. Every check and change is printed, matching this project's auditability standard for
    the rest of the pipeline. Never lets a powercfg failure (e.g. non-Windows, no permission) abort
    the actual notebook run -- this is a safety net, not a hard dependency."""
    changed = {}
    try:
        print("[sleep_guard] Checking current sleep/hibernate timeout settings (powercfg)...", flush=True)
        original = {alias: _query_power_setting(alias) for alias, _ in _POWER_SETTINGS}
        for alias, label in _POWER_SETTINGS:
            ac, dc = original[alias]
            print(f"[sleep_guard]   {label} ({alias}): AC={ac}s, DC={dc}s", flush=True)
        needs_disable = {alias: (ac, dc) for alias, (ac, dc) in original.items() if ac != 0 or dc != 0}
        if needs_disable:
            print(f"[sleep_guard] WARNING: {sorted(needs_disable)} nonzero -- the machine could sleep "
                  f"mid-run and silently kill this execution (this is exactly what happened to 4 of 6 "
                  f"Phase 4 attempts). Disabling for the duration of this run.", flush=True)
            for alias in needs_disable:
                _set_power_setting(alias, 0, 0)
                changed[alias] = needs_disable[alias]
                print(f"[sleep_guard]   {alias} set to AC=0s, DC=0s (was AC={needs_disable[alias][0]}s, "
                      f"DC={needs_disable[alias][1]}s)", flush=True)
        else:
            print("[sleep_guard] All checked timeouts already 0 (disabled) -- no change needed.", flush=True)
    except Exception as e:
        print(f"[sleep_guard] WARNING: could not check/set power settings ({type(e).__name__}: {e}) -- "
              f"proceeding without this guard. If this machine sleeps mid-run, the run may be killed.",
              flush=True)
    try:
        yield
    finally:
        for alias, (ac, dc) in changed.items():
            try:
                _set_power_setting(alias, ac, dc)
                print(f"[sleep_guard] Restored {alias} to AC={ac}s, DC={dc}s (the value found before this "
                      f"run changed it).", flush=True)
            except Exception as e:
                print(f"[sleep_guard] WARNING: failed to restore {alias} to AC={ac}s, DC={dc}s "
                      f"({type(e).__name__}: {e}) -- restore this manually via Settings > System > "
                      f"Power & battery, or `powercfg /setacvalueindex SCHEME_CURRENT SUB_SLEEP {alias} "
                      f"{ac}` / `/setdcvalueindex ... {dc}` followed by `powercfg /setactive "
                      f"SCHEME_CURRENT`.", flush=True)


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

    with sleep_guard(), client.setup_kernel():
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
