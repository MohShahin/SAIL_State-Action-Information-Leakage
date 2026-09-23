from sail.detectors.persistence import PersistenceDominanceDetector


def test_variant_f_real_result_flags_dominance():
    """This project's own real, verified Experiment 8 result: Variant F's
    action-recoverability AUROC (0.914) exceeded the full state's (0.900).
    Numbers taken directly from
    results/experiment8_variant_f_summary.json -- not invented."""
    finding = PersistenceDominanceDetector().run(None, {
        "persistence_auroc": 0.914,
        "full_state_auroc": 0.900,
    })
    assert finding.flagged is True
    assert finding.category == "persistence_dominance"
    assert "Not leakage" in finding.explanation
    assert finding.evidence["gap"] == 0.900 - 0.914


def test_persistence_far_below_full_state_not_flagged():
    """Negative case: persistence baseline nowhere close to the full state's
    predictive power -- the state's power isn't explained by persistence."""
    finding = PersistenceDominanceDetector().run(None, {
        "persistence_auroc": 0.60,
        "full_state_auroc": 0.90,
    })
    assert finding.flagged is False
    assert "Not leakage" not in finding.explanation  # not-flagged wording never claims leakage either
    assert "isn't readily explained" in finding.explanation


def test_margin_boundary_is_inclusive():
    """gap == margin exactly should still flag ("within margin OF" is
    inclusive, matching the >= definition, not a strict >)."""
    finding = PersistenceDominanceDetector().run(None, {
        "persistence_auroc": 0.88,
        "full_state_auroc": 0.90,
        "margin": 0.02,
    })
    assert finding.flagged is True
