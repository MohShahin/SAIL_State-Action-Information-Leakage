# Persistence control across offsets (exploratory)

**Exploratory, not pre-registered; does not change the H3 decision** (docs/DECISIONS_H3.md).

## What
This adds the A_{t-1}-only baseline that docs/PI_DEFENSE_PREP.md (section 8) calls "the single cheapest,
highest-value addition". It compares that baseline with the full state across the H3 offsets, to answer
one question: can offset decay tell the SOFA mechanism apart from plain treatment persistence?

Feature sets, all computed at bin t (window [4t, 4t+4), decision time tau = 4(t+1)):
- **P**: previous action alone. Any of the six label drugs active in bin t's window. This is exactly the
  notebook's label rule one bin earlier, checked on every row (0 mismatches in both cohorts).
- **P_dose**: P plus a one-hot of the dose-only SOFA cardio tier (0/2/3/4) of that window.
- **I**: on-at-tau. Any of the six drugs running at tau, as in `exp8_validation.on_at_tau_all_drugs`.
- **P+I**: P and I together.
- **A**: the notebook's full state.
- **E**: `E_physiology_only`, identical to the notebook's variants (checked).
- **E+P, E+I, A+I**: the combinations named.

Label: bin-index offsets {0,1,2,4,8}, built with `h3_paired_bootstrap.offset_frames(offset_mode="bins")`.

## Settings
- **Primary probe (logreg):** the notebook's `PROBES["logreg"]` and `cv_predict`, copied verbatim
  (StandardScaler, class_weight balanced, max_iter 2000, GroupKFold 5 by stay_id). It is fitted once per
  feature set and offset, on that offset's own rows.
- **Check probe (gb):** run at offsets 0 and 8 only.
- **Bootstrap:** paired patient bootstrap, 2,000 resamples, seed 42, with the same draws as
  `h3_paired_bootstrap.paired_cluster_bootstrap`. All AUROCs in one row universe share those draws.
- **Row universes:** **common** (rows present at offsets 0 and 8; primary) and **own** (each offset's own
  rows; secondary).
- **Reproduction check:** A's common/own Delta reproduces the notebook runs' own H3 JSON exactly
  (13,192: 0.1475, CI 0.1407 to 0.1542; 11,354: 0.1434, CI 0.1357 to 0.1506).
  - The committed `results/experiment5_h3_paired_bootstrap_bins.json` comes from the pinned run under
    Decision 4 (198,891 rows). It differs from run_25065533 (198,890 rows) in the fourth decimal.

## Sources
- Code: `scripts/exp_persistence.py` at 0890095. Figure: `scripts/exp_persistence_figure.py`.
- Inputs: notebook checkpoints from ORCD run_25065533 (13,192 stays, repo 1d3f170) and run_25029926
  (11,354 stays, repo ff530e0), plus the DuckDB MIMIC-IV v3.1 build (read-only).
- ORCD jobs job_25080333 (11 min) and job_25080334 (9 min), at 16 CPUs each.

## Files
- `persistence_13192.json`, `persistence_11354.json`: each holds the AUROC with n and CI per feature set,
  probe, offset and universe; Delta(0 minus k); the contrasts; and the checks.
- `persistence_decay_curves.png`: logreg decay curves for P, I, E, A, A+I and E+I, both cohorts and both
  row universes.

## Headline (logreg, common rows; 95% patient-bootstrap CIs)

AUROC at offset 0 and offset 8, with Delta = AUROC(0) minus AUROC(8):

| Set | 13,192 AUROC 0 / 8 | 13,192 Delta | 11,354 AUROC 0 / 8 | 11,354 Delta |
|---|---|---|---|---|
| P | 0.888 / 0.632 | 0.255 [0.249, 0.262] | 0.887 / 0.627 | 0.259 [0.252, 0.267] |
| P_dose | 0.911 / 0.689 | 0.222 [0.215, 0.229] | 0.909 / 0.685 | 0.224 [0.217, 0.231] |
| I | 0.936 / 0.665 | 0.272 [0.265, 0.278] | 0.937 / 0.661 | 0.276 [0.269, 0.283] |
| E | 0.696 / 0.660 | 0.035 [0.028, 0.042] | 0.693 / 0.660 | 0.032 [0.025, 0.040] |
| A | 0.861 / 0.714 | 0.147 [0.141, 0.154] | 0.851 / 0.708 | 0.143 [0.136, 0.151] |
| E+I | 0.953 / 0.723 | 0.230 [0.224, 0.236] | 0.952 / 0.719 | 0.232 [0.226, 0.239] |
| A+I | 0.953 / 0.729 | 0.224 [0.218, 0.231] | 0.952 / 0.725 | 0.227 [0.219, 0.233] |

Contrasts, as differences in AUROC:

| Contrast | 13,192 | 11,354 |
|---|---|---|
| A minus E, offset 0 | 0.165 [0.160, 0.171] | 0.159 [0.153, 0.164] |
| A minus E, offset 8 | 0.053 [0.048, 0.058] | 0.048 [0.042, 0.053] |
| (A+I) minus (E+I), offset 0 | 0.000 [-0.000, 0.001] | 0.000 [-0.001, 0.001] |
| (A+I) minus (E+I), offsets 1 to 8 | 0.007 to 0.008, all CIs above 0 | 0.005 to 0.007, all CIs above 0 |
| A minus P, offset 0 / 8 | -0.027 [-0.031, -0.023] / 0.081 [0.075, 0.088] | -0.035 [-0.040, -0.031] / 0.081 [0.073, 0.088] |
| A minus I, offset 0 / 8 | -0.075 [-0.079, -0.072] / 0.049 [0.043, 0.055] | -0.086 [-0.090, -0.082] / 0.047 [0.039, 0.054] |
| Delta(A) minus Delta(P) | -0.108 [-0.115, -0.102] | -0.116 [-0.123, -0.109] |

**Own rows** give the same picture. For 13,192: A 0.881 vs P 0.910 vs I 0.943 at offset 0, and
(A+I) minus (E+I) = 0.003 at offset 0.

**gb at offsets 0 and 8** gives the same picture:
- 13,192 common rows: A 0.886, P 0.887, I 0.936 at offset 0.
- (A+I) minus (E+I) = 0.002 at offset 0 and 0.009 at offset 8.

## How to read it
- **Previous action and on-at-tau beat the full state at offset 0.**
  - The previous bin's action alone matches or beats A: 0.888 vs 0.861 with logreg, and 0.887 vs 0.886
    with gb.
  - The on-at-tau indicator alone is higher still (0.936).
- **The SOFA terms add almost nothing once on-at-tau is present.**
  - (A+I) minus (E+I) is 0.000 at offset 0 and under 0.01 at every offset.
  - So the A minus E gap (0.165 at offset 0) is, at offset 0, all carried by the current-treatment
    indicator.
- **A's decay looks like a diluted persistence curve.**
  - P and I decay faster than A: Delta about 0.26 to 0.27, against 0.147.
  - E is nearly flat (Delta 0.035).
  - A sits between the two because its SOFA cardio and total terms carry the dose tier of the current
    window, i.e. persistence.
- **Adding on-at-tau to physiology reproduces A+I at every offset.** E+I and A+I have the same decay
  (0.230 vs 0.224).
- **The SOFA-specific residual is small and does not decay.** (A+I) minus (E+I) is positive with CIs above
  0 at offsets 1 to 8, but only about 0.005 to 0.009. It is near 0 at offset 0, so it adds nothing to
  the decay.
- **Overall reading:** the predictability and its decay are consistent with continuation (treatment
  persistence) structure, not a SOFA-specific mechanism.
- **Against H3:** A still meets Prediction A (Delta 0.147, CI above 0.10). This exploratory result
  supports the Decision 6 guard's reading, "decay attributable to continuation structure". It does not
  replace the Decision 6 (a)/(b) analyses, whose definitions are still pending the project lead.
