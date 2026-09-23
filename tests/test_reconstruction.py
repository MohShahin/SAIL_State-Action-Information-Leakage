import pandas as pd

from sail.detectors.reconstruction import ReconstructionLeakageDetector
from sail.specs.sofa_cardio import sofa_cardio_decomposed


def test_theorem2_sofa_cardio_reconstructible():
    """Theorem 2: sofa_total = sofa_cardio + the other five subscores, so
    sofa_cardio is exactly recoverable from sofa_total minus the rest --
    construct rows using the project's own cardio scoring function and
    confirm the identity holds exactly (algebraic, not approximate)."""
    # map, dopamine, dobutamine, epi, norepi, resp, coag, liver, renal, cns
    rows = [
        (65, 6, 0, 0, 0, 2, 1, 0, 1, 0),
        (80, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (50, 0, 0, 0.2, 0, 3, 2, 1, 2, 1),
        (72, 0, 3, 0, 0, 1, 0, 2, 0, 2),
    ]
    records = []
    for map_val, dopa, dobu, epi, norepi, resp, coag, liver, renal, cns in rows:
        _, _, cardio = sofa_cardio_decomposed(map_val, dopa, dobu, epi, norepi)
        total = cardio + resp + coag + liver + renal + cns
        records.append({
            "sofa_cardio": cardio, "sofa_resp": resp, "sofa_coag": coag,
            "sofa_liver": liver, "sofa_renal": renal, "sofa_cns": cns,
            "sofa_total": total,
        })
    df = pd.DataFrame(records)

    finding = ReconstructionLeakageDetector().run(df, {
        "total_col": "sofa_total",
        "component_cols": ["sofa_resp", "sofa_coag", "sofa_liver", "sofa_renal", "sofa_cns"],
        "target_col": "sofa_cardio",
    })
    assert finding.flagged is True
    assert finding.category == "reconstruction_leakage"
    assert finding.evidence["max_abs_error"] == 0.0


def test_total_without_target_not_flagged():
    """Negative case: a 'total' that never included the target component in
    the first place should NOT be flagged as reconstructible."""
    df = pd.DataFrame({
        "sofa_cardio": [3, 0, 4, 2],
        "sofa_resp": [1, 2, 0, 3],
        "sofa_coag": [0, 1, 2, 0],
        "other_total": [1, 3, 2, 3],  # deliberately excludes sofa_cardio
    })
    finding = ReconstructionLeakageDetector().run(df, {
        "total_col": "other_total",
        "component_cols": ["sofa_resp", "sofa_coag"],
        "target_col": "sofa_cardio",
    })
    assert finding.flagged is False
