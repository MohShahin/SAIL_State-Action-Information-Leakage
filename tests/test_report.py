import json

from sail.detectors.base import LeakageFinding
from sail.report import LeakageReport


def test_report_summary_and_json_roundtrip():
    report = LeakageReport()
    report.add(LeakageFinding(
        category="construction_leakage_1a", flagged=True,
        explanation="test explanation", evidence={"n": 4},
    ))
    report.add(LeakageFinding(
        category="reconstruction_leakage", flagged=False,
        explanation="clean", evidence={},
    ))
    report.skip("temporal_overlap", "window_col not provided")

    summary = report.summary()
    assert "construction_leakage_1a" in summary
    assert "reconstruction_leakage" in summary
    assert "temporal_overlap" in summary

    parsed = json.loads(report.to_json())
    assert len(parsed["findings"]) == 2
    assert parsed["skipped"]["temporal_overlap"] == "window_col not provided"
