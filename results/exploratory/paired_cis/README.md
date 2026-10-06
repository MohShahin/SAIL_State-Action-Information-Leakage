# Paired CIs for the reported AUROC gaps (exploratory)

**Exploratory, not pre-registered; does not change the H3 decision.** Not part of the H3 test in
docs/DECISIONS_H3.md; no Decision 6 definitions are used.

What: every gap the project reports as a difference of two AUROCs on the same patients
(Experiments 2, 6 and 8), with a paired patient-level bootstrap instead of two marginal CIs
(FORMAL_ANALYSIS.md section 7), plus CIs for the Experiment 2 mutual-information values, a Holm
correction (ROADMAP Phase 4, items 3.12 and the CI item), the ratio behind the site's "mortality gap is
roughly a tenth of the action gap", and the optimism of the notebook's best-probe choice.

Cohorts: 13,192 stays (primary, MIMIC-IV v3.1 DuckDB build) and 11,354 stays (sensitivity, Sepsis-3
stays of the v2.2 build via `SAIL_COHORT_STAYS`). Code at 4adf6c1 (pipeline identical to 1d3f170 and
ff530e0), one ORCD job per cohort (26 and 24 min, 16 CPUs each; job ids in the commit message).

Settings: out-of-fold predictions recreated by executing the notebook's own cells
(`scripts/paired_cis_predict.py`; only the training calls of cells 21, 24 and 33 are cut and replaced
by the notebook's own `cv_predict` and `PROBES`: GroupKFold 5 by stay_id, StandardScaler, seed 42),
variants A to F, probes logreg, rf, gb, both axes. Bootstrap (`scripts/paired_cis.py`): 2,000
resamples of stay_ids with replacement, seed 42, all rows of a drawn stay, ONE draw per replicate
shared by every AUROC (both members of a pair, both axes, all probes), percentile 95% CIs, two-sided
bootstrap p-values. Holm across the 15 action gaps {A-E, A-C, C-D, D-E, A-B} x {logreg, rf, gb}
against 0; with 2,000 resamples the smallest attainable p is 0.001, so the smallest Holm p is 0.015.
Predictions stay on the cluster; only the two aggregate JSONs are committed.

Point check before any bootstrap: all 30 Exp 2 / Exp 6 AUROCs, the two Exp 8 best-probe F AUROCs and
the five Exp 2 MI values equal the committed ones (13,192: run_25065533 results; 11,354:
results/sensitivity_v22_11354/) within 4.1e-07 (13,192) and 2.3e-06 (11,354), tolerance 1e-4. The F
logreg and rf AUROCs (not saved by the notebook) match its printed 3-decimal log values.

Best probe: gb for every variant on both axes and both cohorts, so the notebook's "best probe" column
equals the gb column below.

### 13192 cohort

| Gap (paired, same patients) | logreg | rf | gb (= notebook best probe) |
|---|---|---|---|
| Action A-E | +0.1542 [+0.1500, +0.1585], Holm p 0.015 | +0.1216 [+0.1180, +0.1251], Holm p 0.015 | +0.1162 [+0.1128, +0.1195], Holm p 0.015 |
| Action A-C | +0.0324 [+0.0308, +0.0338], Holm p 0.015 | +0.0398 [+0.0381, +0.0413], Holm p 0.015 | +0.0164 [+0.0156, +0.0173], Holm p 0.015 |
| Action C-D | +0.1169 [+0.1134, +0.1206], Holm p 0.015 | +0.0819 [+0.0795, +0.0845], Holm p 0.015 | +0.0997 [+0.0965, +0.1030], Holm p 0.015 |
| Action D-E | +0.0050 [+0.0041, +0.0060], Holm p 0.015 | -0.0001 [-0.0006, +0.0004], Holm p 1.000 | +0.0000 [-0.0003, +0.0003], Holm p 1.000 |
| Action A-B | +0.0046 [+0.0042, +0.0051], Holm p 0.015 | -0.0001 [-0.0005, +0.0002], Holm p 1.000 | +0.0001 [-0.0000, +0.0003], Holm p 0.328 |
| Action F-A | +0.0192 [+0.0179, +0.0206] | +0.0153 [+0.0147, +0.0160] | +0.0144 [+0.0138, +0.0151] |
| Action F-D | +0.1684 [+0.1642, +0.1727] | +0.1370 [+0.1333, +0.1408] | +0.1306 [+0.1271, +0.1340] |
| Mortality A-E | +0.0066 [+0.0039, +0.0093] | +0.0071 [+0.0032, +0.0109] | +0.0076 [+0.0041, +0.0111] |
| Mortality A-D | +0.0067 [+0.0040, +0.0094] | +0.0069 [+0.0031, +0.0105] | +0.0081 [+0.0045, +0.0116] |
| Mortality F-A | -0.0014 [-0.0035, +0.0006] | -0.0046 [-0.0074, -0.0017] | -0.0012 [-0.0041, +0.0018] |
| Ratio mortality A-E / action A-E | 0.043 [0.025, 0.061] | 0.058 [0.026, 0.091] | 0.065 [0.036, 0.095] |
| Best-probe optimism, action: gb minus fixed probe | +0.0207 to +0.0635 | +0.0067 to +0.0309 | gb best in 100% of replicates, every variant |
| Best-probe optimism, mortality: gb minus fixed probe | +0.0252 to +0.0286 | +0.0089 to +0.0142 | gb best in 100% of replicates, every variant |

Mutual information (Exp 2, variants A to E): A 0.0316 [0.0307, 0.0325]; B 0.0257 [0.0251, 0.0265]; C 0.0227 [0.0220, 0.0235]; D 0.0171 [0.0164, 0.0178]; E 0.0162 [0.0156, 0.0169]. Paired differences: A-E +0.0153 [+0.0150, +0.0157]; A-C +0.0089 [+0.0087, +0.0091]; C-D +0.0056 [+0.0055, +0.0058]; D-E +0.0009 [+0.0007, +0.0009]; A-B +0.0058 [+0.0056, +0.0060].

Point check: 42 values, max abs diff 4.1e-07. Rows 198,890 action (13,192 stays), 13,170 mortality.

### 11354 cohort

| Gap (paired, same patients) | logreg | rf | gb (= notebook best probe) |
|---|---|---|---|
| Action A-E | +0.1472 [+0.1429, +0.1520], Holm p 0.015 | +0.1141 [+0.1102, +0.1180], Holm p 0.015 | +0.1092 [+0.1057, +0.1129], Holm p 0.015 |
| Action A-C | +0.0294 [+0.0279, +0.0310], Holm p 0.015 | +0.0384 [+0.0366, +0.0402], Holm p 0.015 | +0.0154 [+0.0144, +0.0163], Holm p 0.015 |
| Action C-D | +0.1123 [+0.1084, +0.1161], Holm p 0.015 | +0.0754 [+0.0729, +0.0781], Holm p 0.015 | +0.0936 [+0.0904, +0.0969], Holm p 0.015 |
| Action D-E | +0.0055 [+0.0045, +0.0066], Holm p 0.015 | +0.0002 [-0.0003, +0.0007], Holm p 0.429 | +0.0002 [-0.0001, +0.0005], Holm p 0.339 |
| Action A-B | +0.0049 [+0.0043, +0.0054], Holm p 0.015 | -0.0003 [-0.0006, +0.0001], Holm p 0.358 | +0.0004 [+0.0002, +0.0006], Holm p 0.015 |
| Action F-A | +0.0191 [+0.0175, +0.0206] | +0.0150 [+0.0142, +0.0157] | +0.0141 [+0.0134, +0.0148] |
| Action F-D | +0.1608 [+0.1562, +0.1655] | +0.1288 [+0.1249, +0.1329] | +0.1231 [+0.1194, +0.1269] |
| Mortality A-E | +0.0063 [+0.0034, +0.0092] | +0.0070 [+0.0031, +0.0108] | +0.0071 [+0.0035, +0.0107] |
| Mortality A-D | +0.0066 [+0.0037, +0.0095] | +0.0074 [+0.0036, +0.0113] | +0.0095 [+0.0058, +0.0133] |
| Mortality F-A | -0.0016 [-0.0037, +0.0005] | -0.0048 [-0.0078, -0.0017] | -0.0028 [-0.0061, +0.0004] |
| Ratio mortality A-E / action A-E | 0.043 [0.023, 0.062] | 0.061 [0.027, 0.094] | 0.065 [0.032, 0.098] |
| Best-probe optimism, action: gb minus fixed probe | +0.0213 to +0.0642 | +0.0063 to +0.0302 | gb best in 100% of replicates, every variant |
| Best-probe optimism, mortality: gb minus fixed probe | +0.0245 to +0.0296 | +0.0095 to +0.0136 | gb best in 100% of replicates, every variant |

Mutual information (Exp 2, variants A to E): A 0.0313 [0.0304, 0.0322]; B 0.0257 [0.0250, 0.0265]; C 0.0231 [0.0222, 0.0239]; D 0.0177 [0.0170, 0.0185]; E 0.0169 [0.0162, 0.0176]. Paired differences: A-E +0.0144 [+0.0141, +0.0147]; A-C +0.0082 [+0.0080, +0.0084]; C-D +0.0053 [+0.0052, +0.0055]; D-E +0.0008 [+0.0008, +0.0009]; A-B +0.0056 [+0.0054, +0.0057].

Point check: 42 values, max abs diff 2.3e-06. Rows 170,299 action (11,354 stays), 11,336 mortality.

## How to read it

- Every action gap the project interprets is far from 0 on paired CIs in both cohorts (A-E, A-C, C-D,
  F-A, F-D), and survives Holm. The two "nothing happens" gaps are flat with the flexible probes: D-E
  and A-B are within +/-0.0005 for rf and gb (A-B gb in 11,354 is +0.0004, Holm-significant but
  negligible). Under logreg both are about +0.005 and significant, so "D removes everything" holds
  for the tree probes only.
- The gap sizes depend on the probe more than on the cohort: A-E is 0.154 (logreg) vs 0.116 (gb).
  The reported gb gap is the smallest of the three, so the best-probe choice does not inflate A-E.
- Mortality A-E and A-D are small but their paired CIs exclude 0 for every probe in both cohorts
  (+0.006 to +0.010, lower bounds +0.003 to +0.006). Variant F does not recover mortality AUROC above
  A: F-A is -0.001 to -0.005, significantly below 0 with rf, CI covering 0 with logreg and gb.
- Ratio: mortality A-E / action A-E is 0.065 [0.036, 0.095] (13,192) and 0.065 [0.032, 0.098]
  (11,354) with gb. "Roughly a tenth" is the upper edge: the published 0.011 / 0.109 = 0.10 sits just
  above both 95% CIs. The difference is the mortality E AUROC (published 0.782, DuckDB 0.7855 on the
  same 11,354 stays, already flagged in comparison_vs_published.md). "Between about 3% and 10%" is
  what the data support.
- Best-probe selection is done on the same out-of-fold predictions that are reported (max AUROC per
  variant in run_experiment2 / run_experiment6, no nested or held-out selection). The optimism is
  nil in practice: gb is the best probe in 100% of the 2,000 replicates for every variant, and its
  margin is +0.007 to +0.031 over rf and +0.021 to +0.064 over logreg (action), every CI excluding 0.
  This gap between probes is real, not a selection effect.
- Exp 8 wording: experiment8_variant_f_summary.json computes F's drift toward A and the recovered
  mortality gap against the committed published A and D values (0.900 / 0.792, 0.793 / 0.784), not
  the same run's A and D. On the same patients and run, F-D (action, gb) is +0.131 [+0.127, +0.134]
  (13,192) and +0.123 [+0.119, +0.127] (11,354).
- MI: every Exp 2 MI value and every adjacent MI difference has a tight CI that excludes 0
  (the notebook's quantile-binned mean MI, recomputed on each resample).
- Against H3 and Decision 6: nothing here touches the pre-registered H3 offset contrast. The Exp 2
  A-E gap measured here includes the continuation structure Decision 6 asks about (rows with an
  infusion already running); these CIs do not separate that part.

Limits: the bootstrap keeps the fitted out-of-fold predictions fixed (no refitting per replicate),
so model-training variability is not in the CIs. The family for Holm is the 15 action gaps; the F
gaps and mortality gaps are reported uncorrected (all F action CIs exclude 0 by a wide margin).

Files: `paired_cis_13192.json`, `paired_cis_11354.json` (all AUROCs with CIs, every pair per probe
with p-values, Holm, ratio, optimism, MI, the point check).
