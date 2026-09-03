# Curated results

**Everything in this folder is aggregate, cohort-level statistics — counts, percentages, AUROCs.
Nothing here is a per-patient or per-decision-point row.** See [`../DATA_ACCESS.md`](../DATA_ACCESS.md)
for why that distinction matters under the MIMIC-IV Data Use Agreement.

This folder is a deliberately small, hand-picked subset of what the notebook actually produces in
its own local `results/` output directory. Most of that output (e.g.
`experiment3_window_provenance.csv`, one row per decision point) stays off GitHub entirely — it's
gitignored by default, and stays that way. Only the files below have been reviewed and are
confirmed aggregate-only:

| File | What it is |
|---|---|
| `experiment1_sofa_decomposition_summary.json` | Cohort-wide dose-determined percentages (Experiment 1) |
| `experiment2_action_recoverability_best_probe.csv` | 5 rows — one per state variant (A–E), best-probe AUROC/F1/ECE/MI |
| `experiment3_summary.json` | Cohort-wide window-overlap statistics (Experiment 3) |
| `experiment6_mortality_best_probe.csv` | 5 rows — one per state variant (A–E), best-probe mortality-prediction AUROC + CI at a fixed 24h decision point (Experiment 6) |
| `experiment6_mortality_vs_action_recoverability.json` | Side-by-side comparison: action-recoverability AUROC gap (0.109) vs. mortality-predictive-validity AUROC gap (0.011) across the same five variants |

Both the current (verified 2026-08-16) figures and the manuscript draft's original figures are
included side by side where they differ, with a note on why — see `ROADMAP.md` for the full
diagnostic history behind each correction.

**Before adding any new file here:** confirm it has no `stay_id`, `subject_id`, or per-timestep
rows — see the pre-commit checklist in `../DATA_ACCESS.md`.
