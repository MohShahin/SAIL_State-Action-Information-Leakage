"""
Local bridge the SAIL extension spawns as a subprocess. Reads one JSON request from stdin, writes one
JSON response to stdout, and does nothing else -- runs on the user's own machine only, and nothing it
reads or returns leaves this process except back to the extension that spawned it.

Protocol: stdin is one JSON object, `{"cmd": ...}`. Exactly one line, the marker below, is printed
followed by exactly one line of JSON; anything printed before the marker (a stray warning from a
library) is ignored by the extension.
"""
import json
import sys

MARKER = "##SAIL_BRIDGE_RESULT##"


def _ok(data):
    return {"ok": True, "data": data}


def _err(message):
    return {"ok": False, "error": message}


def _load(path):
    import pandas as pd

    if path.lower().endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def cmd_probe(_req):
    import sail

    return _ok({"version": sail.__version__})


def cmd_columns(req):
    df = _load(req["path"])
    return _ok({"columns": [str(c) for c in df.columns], "nRows": int(len(df))})


def _report_payload(report):
    # Only plain str/bool fields -- never `evidence` here, which can hold numpy scalars that
    # `json.dumps` chokes on (that is exactly what `LeakageReport.to_json()`'s `default=str` is for;
    # this bridge sidesteps the question entirely by not sending evidence at all in this phase).
    return {
        "findings": [
            {"category": f.category, "flagged": bool(f.flagged), "explanation": f.explanation}
            for f in report.findings
        ],
        "skipped": dict(report.skipped),
        "summary": report.summary(),
    }


def cmd_check(req):
    """The generic path, for an arbitrary user file mapped to four generic fields (stay/time/action/
    reward). Those four fields do not carry enough information for most of sail.check()'s categories
    (a scoring function, retained/removed component columns, treatment intervals, and fitted AUROC
    numbers are not derivable from column *names* alone) -- sail.check() itself reports each such
    category as "not run" rather than guessing, and this bridge relies on exactly that behaviour."""
    import sail

    df = _load(req["path"])
    field_map = req["map"]
    kwargs = {"state_cols": list(df.columns), "action_col": field_map["action"]}
    if field_map.get("time"):
        kwargs["timestamp_col"] = field_map["time"]
    if field_map.get("action"):
        kwargs["treatment_col"] = field_map["action"]
    report = sail.check(df, **kwargs)
    return _ok(_report_payload(report))


def cmd_check_example(req):
    """The exact worked example from SAIL_PACKAGE_README.md's Quickstart: Theorem 1's own case plus
    this project's Experiment 8 numbers -- a real, independently verified result, not a fabricated
    demo. `checks` (check id -> bool) lets the wizard's toggles turn a category off: the corresponding
    spec is simply not passed, so sail.check() reports that category as not run."""
    import pandas as pd
    import sail
    from sail.specs.sofa_cardio import sofa_cardio_row

    enabled = req.get("checks") or {}

    def on(check_id):
        return enabled.get(check_id, True)

    df = pd.DataFrame({
        "map": [40, 55, 70, 90], "dopamine": [6, 6, 6, 6], "dobutamine": [0, 0, 0, 0],
        "epi": [0, 0, 0, 0], "norepi": [0, 0, 0, 0], "sofa_resp": [2, 0, 1, 3],
        "sofa_coag": [1, 0, 2, 0], "sofa_liver": [0, 0, 1, 2], "sofa_renal": [1, 0, 0, 1],
        "sofa_cns": [0, 0, 1, 0], "t": [10.0, 34.0, 58.0, 82.0],
        "action_start": [10.0, 34.0, 58.0, 82.0], "action_next": [1, 0, 1, 0],
        "window_hours": [4.0, 4.0, 4.0, 4.0],
    })
    df["sofa_cardio"] = df.apply(sofa_cardio_row, axis=1)
    df["sofa_total"] = (
        df["sofa_cardio"] + df["sofa_resp"] + df["sofa_coag"] + df["sofa_liver"] + df["sofa_renal"] + df["sofa_cns"]
    )

    kwargs = {
        "state_cols": ["map", "sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns", "sofa_total"],
        "action_col": "action_next",
    }
    if on("c3") or on("c4"):
        kwargs["timestamp_col"] = "t"
    if on("c1"):
        kwargs["treatment_col"] = "dopamine"
        kwargs["construction_spec"] = {"scoring_fn": sofa_cardio_row, "signal_col": "map"}
    if on("c2"):
        kwargs["reconstruction_spec"] = {
            "total_col": "sofa_total",
            "component_cols": ["sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns"],
            "target_col": "sofa_cardio",
        }
    if on("c3"):
        kwargs["window_col"] = "window_hours"
        kwargs["treatment_intervals"] = [(8.0, 10.0)]
    if on("c4"):
        kwargs["action_start_col"] = "action_start"
    if on("c5"):
        kwargs["persistence_auroc"] = 0.914
        kwargs["full_state_auroc"] = 0.900

    report = sail.check(df, **kwargs)
    return _ok(_report_payload(report))


COMMANDS = {
    "probe": cmd_probe,
    "columns": cmd_columns,
    "check": cmd_check,
    "check_example": cmd_check_example,
}


def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw) if raw.strip() else {}
        handler = COMMANDS.get(req.get("cmd"))
        result = handler(req) if handler else _err(f"unknown command: {req.get('cmd')!r}")
    except Exception as exc:  # noqa: BLE001 -- report every failure back to the extension, never crash silently
        result = _err(f"{type(exc).__name__}: {exc}")
    print(MARKER)
    print(json.dumps(result))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
