"""Loud failures, report schema, gating and the command line (launch-prep)."""
import json

import numpy as np
import pandas as pd
import pytest

import sail
from sail.cli import main
from sail.detectors.construction import ConstructionLeakageDetector
from sail.detectors.persistence import PersistenceDominanceDetector
from sail.detectors.reconstruction import ReconstructionLeakageDetector
from sail.detectors.temporal_overlap import TemporalOverlapDetector
from sail.detectors.timing_violation import TimingViolationDetector


def test_reconstruction_all_nan_is_inconclusive_not_clean():
    df = pd.DataFrame({"tot": [np.nan] * 3, "a": [1.0, 2.0, 3.0], "tgt": [1.0, 2.0, 3.0]})
    f = ReconstructionLeakageDetector().run(df, {"total_col": "tot", "component_cols": ["a"], "target_col": "tgt"})
    assert f.inconclusive and not f.flagged
    assert "not a clean result" in f.explanation


def test_reconstruction_partial_nan_excluded_and_reported():
    df = pd.DataFrame({"tot": [3.0, np.nan, 5.0], "a": [1.0, 1.0, 2.0], "tgt": [2.0, 9.0, 3.0]})
    f = ReconstructionLeakageDetector().run(df, {"total_col": "tot", "component_cols": ["a"], "target_col": "tgt"})
    assert f.flagged and f.evidence["n_missing"] == 1 and f.evidence["n_rows"] == 2


def test_timing_all_nan_is_inconclusive():
    df = pd.DataFrame({"end": [np.nan, np.nan], "start": [1.0, 2.0]})
    f = TimingViolationDetector().run(df, {"state_end_col": "end", "action_start_col": "start"})
    assert f.inconclusive and not f.flagged


def test_temporal_overlap_nan_rows_excluded_and_all_nan_inconclusive():
    df = pd.DataFrame({"t": [np.nan, 5.0], "w": [4.0, 4.0]})
    f = TemporalOverlapDetector().run(df, {"treatment_intervals": [(0, 10)], "time_col": "t", "window_col": "w"})
    assert f.flagged and f.evidence["n_missing"] == 1
    df2 = pd.DataFrame({"t": [np.nan], "w": [4.0]})
    f2 = TemporalOverlapDetector().run(df2, {"treatment_intervals": [(0, 10)], "time_col": "t", "window_col": "w"})
    assert f2.inconclusive


def test_construction_continuous_dose_is_inconclusive_then_testable_with_bins():
    rng = np.random.default_rng(1)
    n = 300
    dose = rng.uniform(0.1, 1.0, n)          # continuous: every dose value is unique
    mapv = rng.uniform(40, 100, n)
    df = pd.DataFrame({"dose": dose, "map": mapv})
    fn = lambda r: 3.0 if r["dose"] < 0.4 else (4.0 if r["dose"] < 0.7 else 5.0)  # set by dose alone
    spec = {"scoring_fn": fn, "signal_col": "map", "treatment_cols": ["dose"]}
    f = ConstructionLeakageDetector().run(df, spec)
    assert f.inconclusive and not f.flagged
    f2 = ConstructionLeakageDetector().run(df, {**spec, "treatment_bins": 3})
    assert f2.flagged and f2.category == "construction_leakage_1a"


def test_persistence_validates_inputs_and_is_a_diagnostic():
    d = PersistenceDominanceDetector()
    with pytest.raises(ValueError):
        d.run(pd.DataFrame(), {"persistence_auroc": 1.7, "full_state_auroc": 0.9})
    with pytest.raises(ValueError):
        d.run(pd.DataFrame(), {"persistence_auroc": 0.9, "full_state_auroc": 0.9, "margin": -1})
    f = d.run(pd.DataFrame(), {"persistence_auroc": 0.91, "full_state_auroc": 0.90})
    assert f.flagged and f.kind == "diagnostic"


def test_check_rejects_empty_table():
    with pytest.raises(ValueError):
        sail.check(pd.DataFrame({"a": []}), state_cols=["a"])


def _frame():
    return pd.DataFrame({"t": [0.0, 1.0, 2.0], "s": [1.0, 2.0, 3.0], "x": [1.0, 1.0, 1.0],
                         "y": [0.0, 1.0, 2.0], "tot": [2.0, 3.0, 4.0]})


def test_report_json_schema_and_fingerprint_without_row_values():
    r = sail.check(_frame(), state_cols=["s"], timestamp_col="t", action_start_col="s")
    p = json.loads(r.to_json(generated_at="2026-01-01T00:00:00Z"))
    assert p["schema_version"] == "1" and p["sail_version"] == sail.__version__
    assert p["generated_at"] == "2026-01-01T00:00:00Z"
    assert p["input"]["n_rows"] == 3 and len(p["input"]["sha256"]) == 64
    assert "values" not in p["input"]
    assert {"kind", "inconclusive"} <= set(p["findings"][0])
    assert set(p["result"]) == {"leakage_flagged", "diagnostics_flagged", "inconclusive", "not_run"}


def test_fingerprint_changes_with_content_and_is_stable():
    a = sail.check(_frame(), state_cols=["s"]).meta["sha256"]
    assert a == sail.check(_frame(), state_cols=["s"]).meta["sha256"]
    df = _frame(); df.loc[0, "s"] = 99.0
    assert a != sail.check(df, state_cols=["s"]).meta["sha256"]


def test_exit_codes_gate_on_leakage_not_diagnostics():
    persist_only = sail.check(_frame(), state_cols=["s"], persistence_auroc=0.9, full_state_auroc=0.9)
    assert persist_only.exit_code("leakage") == 0 and persist_only.exit_code("any") == 1
    leak = sail.check(_frame(), state_cols=["s"], timestamp_col="t", action_start_col="y",
                      reconstruction_spec={"total_col": "tot", "component_cols": ["s"], "target_col": "x"})
    assert leak.leakage_flagged and leak.exit_code() == 1
    nothing = sail.LeakageReport()
    assert nothing.exit_code() == 3


def test_summary_separates_inconclusive_and_labels_diagnostics():
    df = pd.DataFrame({"end": [np.nan], "start": [1.0], "k": [1.0]})
    r = sail.check(df, state_cols=["k"], timestamp_col="end", action_start_col="start",
                   persistence_auroc=0.9, full_state_auroc=0.9)
    s = r.summary()
    assert "INCONCLUSIVE (1)" in s and "(diagnostic, not leakage)" in s


def test_cli_demo_requirements_and_check(tmp_path, capsys):
    assert main(["requirements"]) == 0
    assert main(["demo"]) == 0
    csv = tmp_path / "d.csv"
    pd.DataFrame({"end": [5.0, 6.0], "start": [1.0, 2.0]}).to_csv(csv, index=False)
    out = tmp_path / "r.json"
    code = main(["check", str(csv), "--timestamp-col", "end", "--action-start-col", "start", "--output", str(out)])
    assert code == 1
    assert json.loads(out.read_text())["result"]["leakage_flagged"] == 1
    assert main(["check", str(csv), "--timestamp-col", "end", "--action-start-col", "start", "--fail-on", "never"]) == 0


def test_cli_errors_exit_2_and_never_traceback(tmp_path, capsys):
    assert main(["check", str(tmp_path / "missing.csv")]) == 2
    assert "sail: error" in capsys.readouterr().err
    csv = tmp_path / "d.csv"
    pd.DataFrame({"a": [1.0]}).to_csv(csv, index=False)
    assert main(["check", str(csv), "--state-cols", "nope"]) == 2
