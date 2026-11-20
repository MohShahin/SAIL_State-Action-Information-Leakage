"""Command line for sail-leakage: ``sail check``, ``sail requirements``, ``sail demo``.

Exit codes (``sail check``): 0 pass, 1 a gated condition was found (see ``--fail-on``),
2 usage or input error, 3 nothing could be tested.
"""

import argparse
import importlib
import sys
from typing import Optional, Sequence


def _load_table(path: str):
    import pandas as pd

    if path.endswith((".parquet", ".pq")):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _parse_intervals(text: str) -> list:
    out = []
    for part in text.split(","):
        a, _, b = part.partition(":")
        out.append((float(a), float(b)))
    return out


def _load_callable(ref: str):
    mod, _, name = ref.partition(":")
    if not mod or not name:
        raise ValueError("--scoring-fn must look like module:function")
    return getattr(importlib.import_module(mod), name)


def _demo_table():
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(0)
    n = 200
    t = np.arange(n, dtype=float)
    a = rng.integers(0, 2, n).astype(float)
    b = rng.normal(size=n)
    c = rng.normal(size=n)
    return pd.DataFrame({
        "t": t, "action_start": t + 1.0, "feat_a": a, "feat_b": b, "feat_c": c,
        "total": a + b + c, "removed": a,
    })


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sail", description="Check a table for state-action information leakage.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="run the checks the given inputs support")
    c.add_argument("table", help="CSV or Parquet file; read locally, never uploaded")
    c.add_argument("--state-cols", nargs="*", default=[], help="columns that make up the state")
    c.add_argument("--action-col")
    c.add_argument("--timestamp-col", help="decision time / state window end")
    c.add_argument("--action-start-col", help="action window start (timing check)")
    c.add_argument("--window-col", help="per-row window length (temporal overlap)")
    c.add_argument("--treatment-intervals", help="start:end,start:end (temporal overlap)")
    c.add_argument("--total-col"); c.add_argument("--component-cols", nargs="*"); c.add_argument("--target-col")
    c.add_argument("--scoring-fn", help="module:function taking a row; enables the construction check")
    c.add_argument("--signal-col"); c.add_argument("--treatment-cols", nargs="*")
    c.add_argument("--treatment-bins", type=int, help="bin continuous doses for the construction check")
    c.add_argument("--persistence-auroc", type=float); c.add_argument("--full-state-auroc", type=float)
    c.add_argument("--json", action="store_true", help="print the JSON report instead of text")
    c.add_argument("--output", help="also write the JSON report to this file")
    c.add_argument("--fail-on", choices=("leakage", "any", "never"), default="leakage")

    sub.add_parser("requirements", help="print what each check needs")
    sub.add_parser("demo", help="run the checks on a small built-in synthetic table")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    import sail

    if args.cmd == "requirements":
        print(sail.requirements())
        return 0

    try:
        if args.cmd == "demo":
            df = _demo_table()
            report = sail.check(
                df, state_cols=["feat_a", "feat_b", "feat_c"], action_col="removed",
                timestamp_col="t", action_start_col="action_start",
                reconstruction_spec={"total_col": "total", "component_cols": ["feat_b", "feat_c"],
                                     "target_col": "feat_a"},
                persistence_auroc=0.91, full_state_auroc=0.90,
            )
            print("Synthetic demo table, 200 rows. Nothing here is patient data.\n")
            print(report.summary())
            return 0

        df = _load_table(args.table)
        kw = dict(state_cols=args.state_cols, action_col=args.action_col,
                  timestamp_col=args.timestamp_col, action_start_col=args.action_start_col,
                  window_col=args.window_col,
                  persistence_auroc=args.persistence_auroc, full_state_auroc=args.full_state_auroc)
        if args.treatment_intervals:
            kw["treatment_intervals"] = _parse_intervals(args.treatment_intervals)
        if args.total_col and args.component_cols and args.target_col:
            kw["reconstruction_spec"] = {"total_col": args.total_col,
                                         "component_cols": args.component_cols,
                                         "target_col": args.target_col}
        if args.scoring_fn and args.signal_col:
            spec = {"scoring_fn": _load_callable(args.scoring_fn), "signal_col": args.signal_col,
                    "treatment_cols": args.treatment_cols or []}
            if args.treatment_bins:
                spec["treatment_bins"] = args.treatment_bins
            kw["construction_spec"] = spec
        report = sail.check(df, **kw)
    except (KeyError, ValueError, OSError, ImportError, AttributeError) as e:
        print(f"sail: error: {e}", file=sys.stderr)
        return 2

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report.to_json())
    print(report.to_json() if args.json else report.summary())
    return report.exit_code(args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
