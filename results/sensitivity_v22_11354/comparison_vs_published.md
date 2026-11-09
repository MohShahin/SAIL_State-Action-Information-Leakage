# Sensitivity cohort (11,354 stays): comparison with the published values

Run: ORCD, commit ff530e0, `SAIL_COHORT_STAYS` (Sepsis-3 stays of a mimic-code DuckDB
build of MIMIC-IV v2.2) and `SAIL_STRICT_EXP3=1`. Published values are origin/main at 99c33a1.

Match uses the published value's own rounding: "exact" means our value rounds to it, "within 0.005"
means it does not but the absolute difference is at most 0.005. Result: 57 exact, 21 within 0.005,
0 differ. The Experiment 3 asserts pass with `SAIL_STRICT_EXP3=1`, and every published count
(cohort, dose rows, physiology rows, modeling rows, Experiment 3 decision points, Experiment 6 and
Experiment 7 counts, Experiment 8 row counts) is identical.

Freshly computed here: every value in the table except two kinds. Experiment 8's A and D reference
AUROCs (0.900 / 0.792 action, 0.793 / 0.784 mortality) and the Experiment 2 column of the
Experiment 6 comparison are read back from the committed `results/` files, so the Experiment 8
drift and recovered-gap values are this run's F minus the published D.

Differences above 0.002:
- Experiment 3, >50% overlap at 4h: 0.3406 vs 0.343. The 0.343 appears only in FORMAL_ANALYSIS.md,
  quoted next to the 28.7 to 30.8% range "across runs"; every input to Experiment 3 reproduces
  exactly and the 24h values match to full precision, so 0.343 is most likely from an earlier run
  (before the union fix), not the verified one.
- Experiment 6 mortality, E AUROC 0.7855 vs 0.782 and three CI bounds (up to 0.0042). The inputs
  are identical (n 11,336, 18 excluded, rate 20.0%) and the cell code is unchanged since the
  published run, so the remaining difference is at the model level (library versions: this run used
  scikit-learn 1.9.1, numpy 2.4.6); Experiment 6 has one row per patient, so it is the experiment
  most sensitive to that.

| Quantity | Published | Source | Ours (11,354) | Abs diff | Match |
|---|---|---|---|---|---|
| Cohort stays | 11,354 | results/experiment1_sofa_decomposition_summary.json, results/experiment3_summary.json | 11,354 | 0 | exact |
| Vitals/labs/FiO2 rows (verified) | 4,850,246 | ROADMAP.md | 4,850,246 | 0 | exact |
| Vasopressor dose rows (verified) | 351,720 | ROADMAP.md | 351,720 | 0 | exact |
| Exp 2 modeling rows | 170,299 | results/experiment8_variant_f_summary.json n_action_rows; manuscript | 170,299 | 0 | exact |
| Positive rate action_next (%) | 44.6 | manuscript; ROADMAP.md | 44.6 | 0.0 pts | exact |
| Exp 1 dose-determined 4h | 0.323 | results/experiment1_sofa_decomposition_summary.json | 0.3235 | 0.0005 | exact |
| Exp 1 dose-determined 24h | 0.286 | results/experiment1_sofa_decomposition_summary.json | 0.2861 | 0.0001 | exact |
| Exp 1 among treated 4h | 1.0 | results/experiment1_sofa_decomposition_summary.json | 1.0000 | 0.0000 | exact |
| Exp 1 among treated 24h | 1.0 | results/experiment1_sofa_decomposition_summary.json | 1.0000 | 0.0000 | exact |
| Exp 2 A gb AUROC | 0.9 | results/experiment2_action_recoverability_best_probe.csv | 0.9000 | 0.0000 | exact |
| Exp 2 B gb AUROC | 0.9 | results/experiment2_action_recoverability_best_probe.csv | 0.8996 | 0.0004 | exact |
| Exp 2 C gb AUROC | 0.885 | results/experiment2_action_recoverability_best_probe.csv | 0.8846 | 0.0004 | exact |
| Exp 2 D gb AUROC | 0.792 | results/experiment2_action_recoverability_best_probe.csv (manuscript says 0.791) | 0.7910 | 0.0010 | within 0.005 |
| Exp 2 E gb AUROC | 0.791 | results/experiment2_action_recoverability_best_probe.csv | 0.7908 | 0.0002 | exact |
| Exp 2 A logreg AUROC | 0.874 | manuscript Table 3 | 0.8737 | 0.0003 | exact |
| Exp 2 B logreg AUROC | 0.869 | manuscript Table 3 | 0.8689 | 0.0001 | exact |
| Exp 2 C logreg AUROC | 0.845 | manuscript Table 3 | 0.8443 | 0.0007 | within 0.005 |
| Exp 2 D logreg AUROC | 0.733 | manuscript Table 3 | 0.7321 | 0.0009 | within 0.005 |
| Exp 2 E logreg AUROC | 0.727 | manuscript Table 3 | 0.7265 | 0.0005 | exact |
| Exp 2 A rf AUROC | 0.892 | manuscript Table 3 | 0.8928 | 0.0008 | within 0.005 |
| Exp 2 B rf AUROC | 0.893 | manuscript Table 3 | 0.8931 | 0.0001 | exact |
| Exp 2 C rf AUROC | 0.855 | manuscript Table 3 | 0.8544 | 0.0006 | within 0.005 |
| Exp 2 D rf AUROC | 0.779 | manuscript Table 3 | 0.7790 | 0.0000 | exact |
| Exp 2 E rf AUROC | 0.779 | manuscript Table 3 | 0.7787 | 0.0003 | exact |
| Exp 2 A gb macro F1 | 0.83 | results/experiment2_action_recoverability_best_probe.csv | 0.8290 | 0.0010 | within 0.005 |
| Exp 2 A gb ECE | 0.011 | results/experiment2_action_recoverability_best_probe.csv | 0.0119 | 0.0009 | within 0.005 |
| Exp 2 A gb MI | 0.031 | results/experiment2_action_recoverability_best_probe.csv | 0.0313 | 0.0003 | exact |
| Exp 2 B gb macro F1 | 0.828 | results/experiment2_action_recoverability_best_probe.csv | 0.8283 | 0.0003 | exact |
| Exp 2 B gb ECE | 0.012 | results/experiment2_action_recoverability_best_probe.csv | 0.0119 | 0.0001 | exact |
| Exp 2 B gb MI | 0.026 | results/experiment2_action_recoverability_best_probe.csv | 0.0257 | 0.0003 | exact |
| Exp 2 C gb macro F1 | 0.811 | results/experiment2_action_recoverability_best_probe.csv | 0.8108 | 0.0002 | exact |
| Exp 2 C gb ECE | 0.034 | results/experiment2_action_recoverability_best_probe.csv | 0.0338 | 0.0002 | exact |
| Exp 2 C gb MI | 0.023 | results/experiment2_action_recoverability_best_probe.csv | 0.0231 | 0.0001 | exact |
| Exp 2 D gb macro F1 | 0.711 | results/experiment2_action_recoverability_best_probe.csv | 0.7106 | 0.0004 | exact |
| Exp 2 D gb ECE | 0.015 | results/experiment2_action_recoverability_best_probe.csv | 0.0140 | 0.0010 | within 0.005 |
| Exp 2 D gb MI | 0.018 | results/experiment2_action_recoverability_best_probe.csv | 0.0177 | 0.0003 | exact |
| Exp 2 E gb macro F1 | 0.711 | results/experiment2_action_recoverability_best_probe.csv | 0.7105 | 0.0005 | exact |
| Exp 2 E gb ECE | 0.015 | results/experiment2_action_recoverability_best_probe.csv | 0.0153 | 0.0003 | exact |
| Exp 2 E gb MI | 0.017 | results/experiment2_action_recoverability_best_probe.csv | 0.0169 | 0.0001 | exact |
| Exp 2 gap A minus E | 0.109 | results/experiment6_mortality_vs_action_recoverability.json | 0.1090 | 0.0000 | exact |
| Exp 3 n decision points 24h | 204,372 | results/experiment3_summary.json | 204,372 | 0 | exact |
| Exp 3 mean overlap 24h | 0.310513 | notebook cell 29 assert (json 0.311) | 0.310513 | 0.0000 | exact |
| Exp 3 median overlap 24h | 0.124306 | notebook cell 29 assert (json 0.124) | 0.124306 | 0.0000 | exact |
| Exp 3 >50% overlap 24h | 0.28709412248253185 | notebook cell 29 assert (json 0.287) | 0.28709412248253185 | 0 | exact |
| Exp 3 >50% overlap 4h | 0.343 | FORMAL_ANALYSIS.md:292 | 0.3406 | 0.0024 | within 0.005 |
| Exp 5 offset 0 AUROC (logreg) | 0.874 | src/status.html | 0.8737 | 0.0003 | exact |
| Exp 5 offset 8 AUROC (logreg) | 0.703 | src/status.html | 0.7026 | 0.0004 | exact |
| Exp 6 n | 11,336 | results/experiment6_mortality_vs_action_recoverability.json | 11,336 | 0 | exact |
| Exp 6 excluded | 18 | results/experiment6_mortality_vs_action_recoverability.json | 18 | 0 | exact |
| Exp 6 mortality rate (%) | 20.0 | results/experiment6_mortality_vs_action_recoverability.json | 20.0 | 0.0 pts | exact |
| Exp 6 A gb mortality AUROC | 0.793 | results/experiment6_mortality_best_probe.csv | 0.7925 | 0.0005 | exact |
| Exp 6 A gb CI lo | 0.782 | results/experiment6_mortality_best_probe.csv | 0.7818 | 0.0002 | exact |
| Exp 6 A gb CI hi | 0.803 | results/experiment6_mortality_best_probe.csv | 0.8019 | 0.0011 | within 0.005 |
| Exp 6 B gb mortality AUROC | 0.79 | results/experiment6_mortality_best_probe.csv | 0.7917 | 0.0017 | within 0.005 |
| Exp 6 B gb CI lo | 0.779 | results/experiment6_mortality_best_probe.csv | 0.7812 | 0.0022 | within 0.005 |
| Exp 6 B gb CI hi | 0.801 | results/experiment6_mortality_best_probe.csv | 0.8017 | 0.0007 | within 0.005 |
| Exp 6 C gb mortality AUROC | 0.788 | results/experiment6_mortality_best_probe.csv | 0.7871 | 0.0009 | within 0.005 |
| Exp 6 C gb CI lo | 0.776 | results/experiment6_mortality_best_probe.csv | 0.7751 | 0.0009 | within 0.005 |
| Exp 6 C gb CI hi | 0.797 | results/experiment6_mortality_best_probe.csv | 0.7971 | 0.0001 | exact |
| Exp 6 D gb mortality AUROC | 0.784 | results/experiment6_mortality_best_probe.csv | 0.7830 | 0.0010 | within 0.005 |
| Exp 6 D gb CI lo | 0.773 | results/experiment6_mortality_best_probe.csv | 0.7710 | 0.0020 | within 0.005 |
| Exp 6 D gb CI hi | 0.796 | results/experiment6_mortality_best_probe.csv | 0.7923 | 0.0037 | within 0.005 |
| Exp 6 E gb mortality AUROC | 0.782 | results/experiment6_mortality_best_probe.csv | 0.7855 | 0.0035 | within 0.005 |
| Exp 6 E gb CI lo | 0.77 | results/experiment6_mortality_best_probe.csv | 0.7742 | 0.0042 | within 0.005 |
| Exp 6 E gb CI hi | 0.793 | results/experiment6_mortality_best_probe.csv | 0.7948 | 0.0018 | within 0.005 |
| Exp 7 ever ventilated | 0.826 | results/experiment7_respiratory_sofa_summary.json | 0.8260 | 0.0000 | exact |
| Exp 7 eligible PF timesteps | 52,896 | results/experiment7_respiratory_sofa_summary.json | 52,896 | 0 | exact |
| Exp 7 PF-only differs from official | 0.047 | results/experiment7_respiratory_sofa_summary.json | 0.0473 | 0.0003 | exact |
| Exp 7 in ambiguous zone | 0.621 | results/experiment7_respiratory_sofa_summary.json | 0.6214 | 0.0004 | exact |
| Exp 7 ambiguous zone ventilated | 0.934 | results/experiment7_respiratory_sofa_summary.json | 0.9344 | 0.0004 | exact |
| Exp 7 collision not-vent scored 2 | 1,382 | results/experiment7_respiratory_sofa_summary.json | 1,382 | 0 | exact |
| Exp 7 collision vent scored 3 | 16,978 | results/experiment7_respiratory_sofa_summary.json | 16,978 | 0 | exact |
| Exp 8 F action AUROC (gb) | 0.914 | results/experiment8_variant_f_summary.json | 0.9141 | 0.0001 | exact |
| Exp 8 F mortality AUROC (gb) | 0.79 | results/experiment8_variant_f_summary.json | 0.7897 | 0.0003 | exact |
| Exp 8 drift toward A (F minus committed D) | 0.122 | results/experiment8_variant_f_summary.json | 0.1221 | 0.0001 | exact |
| Exp 8 mortality gap recovered (F minus committed D) | 0.006 | results/experiment8_variant_f_summary.json | 0.0057 | 0.0003 | exact |
| Exp 8 n action rows | 170,299 | results/experiment8_variant_f_summary.json | 170,299 | 0 | exact |
| Exp 8 n mortality rows | 11,336 | results/experiment8_variant_f_summary.json | 11,336 | 0 | exact |
