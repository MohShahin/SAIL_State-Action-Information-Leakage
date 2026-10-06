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
| `experiment0_cohort_duckdb_diagnostics.json` | Cohort diagnostics of the DuckDB reproduction (ORCD, MIMIC-IV v3.1): stage counts, anchor_year_group counts, derived-table sizes, Experiment 2 best-probe AUROCs, all against the published figures. Counts only |
| `experiment5_h3_paired_bootstrap_bins.json` | H3 pre-registered test (FORMAL_ANALYSIS.md section 7, decisions in docs/DECISIONS_H3.md), PRIMARY, final run from the decision-note commit 29fb4ec (script as pinned at f81e61d): bin-index offsets, 13,192 cohort; offset-decay AUROCs with n per offset and the paired cluster bootstrap of Delta = AUROC(0) - AUROC(8) (2,000 patient resamples, seed 42) on common rows (primary) and on each offset's own rows (sensitivity). Aggregate only; the per-patient prediction files it names stay on the cluster |
| `experiment5_h3_paired_bootstrap_rows.json` | Same test with the notebook's row-shift offsets (cell 35 construction), sensitivity, same run |
| `h3_post_pin_ff530e0/` | The same two H3 files rerun after the post-pin change ff530e0 (DuckDB TIMESTAMP_DIFF boundary counting, which reproduces the published counts exactly). H3 script unchanged. Reported only as a listed change pending the project lead's approval under Decision 4; files: `experiment5_h3_paired_bootstrap_bins.json`, `experiment5_h3_paired_bootstrap_rows.json` |
| `primary_13192/` | PRIMARY COHORT, 13,192 stays: the full notebook on the MIMIC-IV v3.1 Sepsis-3 cohort, DuckDB on ORCD, run from 1d3f170 whose extraction includes the post-pin change ff530e0 (TIMESTAMP_DIFF boundary counting); that change is pending the project lead's approval for H3 under Decision 4, and the non-H3 experiments here are not under the H3 freeze. The pinned H3 result stays the top-level `experiment5_h3_paired_bootstrap_*.json`. Files: experiment1_summary.json (Exp 1 dose-determined fractions by window, severity band and bin), experiment2_action_recoverability_full.csv (Exp 2, 5 variants x 3 probes), experiment2_action_recoverability_best_probe.csv, experiment3_summary.json (Exp 3 overlap fractions), experiment5_negative_controls.json (shuffled labels, offset decay with CIs, placebo), experiment6_mortality_full.csv, experiment6_mortality_best_probe.csv, experiment6_vs_experiment2_comparison.csv, experiment7_respiratory_sofa_summary.json, experiment8_variant_f_summary.json, experiment8_variant_f_comparison.csv, table3_all_metrics.json. In the Exp 6 vs Exp 2 comparison and the Exp 8 files, the Exp 2 column and the A and D reference AUROCs are read back from the committed published files by the notebook, not recomputed. The per-row Exp 1 decomposition and Exp 3 window provenance CSVs are row-level and stay on the cluster. Aggregate only |
| `experiment8_validation.json` | Independent validation of Experiment 8: F1 and F2 recomputed from information available at the decision time and compared with the notebook's values (2,000 sampled rows), plus the ablation D vs D + 1[on vasopressor at tau] vs D + F1 + F2 (logreg, clustered CI) with the label rate given the indicator; the indicator's standalone AUROC and variants A and E evaluated on off-at-tau rows only (logreg and gb), for both the four dose-scored drugs (F1 definition) and all six label drugs |
| `sensitivity_v22_11354/` | SENSITIVITY ANALYSIS, not the primary cohort: the full notebook on the published 11,354-stay cohort (Sepsis-3 stays of a MIMIC-IV v2.2 build applied to the v3.1 cohort query via SAIL_COHORT_STAYS), DuckDB on ORCD. Notebook aggregates for Experiments 1, 2, 3, 5 (incl. H3 bins and rows), 6, 7 and 8 plus `comparison_vs_published.md`. Run from ff530e0 with SAIL_COHORT_STAYS (3781b3e), both post-pin changes pending approval under Decision 4. Files: experiment1_summary.json, experiment2_action_recoverability_full.csv, experiment3_summary.json, experiment5_negative_controls.json, experiment5_h3_paired_bootstrap_bins.json, experiment5_h3_paired_bootstrap_rows.json, experiment6_mortality_full.csv, experiment7_respiratory_sofa_summary.json, experiment8_variant_f_summary.json, experiment8_validation.json, comparison_vs_published.md. Aggregate only |
| `experiment7_respiratory_sofa_summary.json` | Cohort-wide statistics on the respiratory-SOFA ventilatory-support conditional (Experiment 7) — the current-vs-official disagreement rate, ambiguous-PF-zone prevalence, and the collision-zone counts |

Both the current (verified 2026-08-16) figures and the manuscript draft's original figures are
included side by side where they differ, with a note on why — see `ROADMAP.md` for the full
diagnostic history behind each correction.

**Before adding any new file here:** confirm it has no `stay_id`, `subject_id`, or per-timestep
rows — see the pre-commit checklist in `../DATA_ACCESS.md`.
