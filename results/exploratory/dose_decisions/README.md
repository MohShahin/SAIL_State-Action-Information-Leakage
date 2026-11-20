# Dose decisions on rows already on a vasopressor (exploratory)

**Exploratory, not pre-registered; does not change the H3 decision.** The titration labels below are
this analysis's own definitions, not the project lead's.

## What

Theorem 1: once a dose-scored infusion runs, SOFA cardio equals the vasopressor dose tier. Under the
published label every row with any of the six label drugs running at tau is positive (checked here:
label rate 1.000 on those rows), so those rows carry no information about the action. This analysis
keeps only those rows and asks whether the SOFA cardio dose content helps predict the titration
decision actually made in the next 4h bin.

Labels, one-vs-rest on the on-at-tau rows:

- **STOP**: no label drug running at tau + 4h. (Under the notebook's overlap rule STOP would be 0 on
  every one of these rows, because an infusion running at tau overlaps the next bin by construction.)
- **UP / DOWN**: not STOP, and the dose tier moves up / down from bin t to the next bin, on three scales:
  - `tierW`: the notebook's SOFA cardio dose tier (cell 12 window max per drug, cell 14 thresholds),
    bin t against bin t + 1. Checked against the state: on every row with tier 2 or more,
    `sofa_cardio` equals this tier (0 mismatches in both cohorts).
  - `tierP`: same thresholds on the rates running at the instant, tau against tau + 4h. Sensitivity,
    because the next bin's window max still contains the infusion running at tau.
  - `NEE`: norepinephrine-equivalent dose, Goradia et al., J Crit Care 2021;61:233-240: NE + epi +
    phenylephrine / 10 + dopamine / 100 + vasopressin (U/min) x 2.5, so 0.04 U/min vasopressin = 0.1
    mcg/kg/min NE. Vasopressin is charted in units/hour in this extract (divided by 60 first);
    dobutamine is excluded (inotrope); 1 phenylephrine row in mcg/min is left out (no weight).
    Per bin, the sum of each drug's window max; five levels Komorowski-style (0 = none, 1 to 4 =
    quartiles of nonzero bins; cut points 0.051, 0.101, 0.225 mcg/kg/min in the 13,192 cohort).

## Cohort, commit, settings

- Cohorts: 13,192 primary (Experiment 5 checkpoint of the notebook run at 1d3f170) and 11,354
  sensitivity (checkpoint of the notebook run at ff530e0). Dose rows re-extracted read-only from the v3.1 DuckDB build with notebook cell 9's query;
  counts match the notebook runs exactly (447,713 and 351,720), and the on-at-tau rows match
  Exp 8 validation (81,557 rows in 10,881 stays; 67,120 rows in 9,296 stays).
- Code: `scripts/exp_dose_decisions.py`, test `tests/test_exp_dose_decisions.py`. Main runs at
  48eac56 (12 and 11 min on 16 CPUs, ORCD, 2026-10-06); at-risk runs at f099b97 (only the argument
  parser changed).
- Variants A, D, E from the notebook checkpoint; F = D + F1 + F2 (cell 31 definitions, recomputed).
- Probes: logreg (H3 settings: `LogisticRegression(max_iter=2000, class_weight="balanced")`) and gb
  (`GradientBoostingClassifier(random_state=42)`), both through the notebook's `cv_predict`
  (StandardScaler, GroupKFold 5 by stay).
- CIs: paired patient bootstrap from `h3_paired_bootstrap.paired_cluster_bootstrap` (2,000 resamples,
  seed 42, both AUROCs on identical rows).
- Offsets {0, 2, 4}, bins mode: features of the on-at-tau row at bin t, label of the on-at-tau row at
  bin t + k.
- "Current tier alone": AUROC of the current tier (tierW at t, or tierP at tau for tierP labels) with no
  fitting; "(inv.)" means the higher tier predicts the negative class and 1 minus AUROC is shown.

## Headline: offset 0, all on-at-tau rows

| Label | Cohort | Rows | Prev. | Probe | A | D | E | F | A minus E (95% CI) | A minus D (95% CI) | Current tier alone |
|---|---|---|---|---|---|---|---|---|---|---|---|
| STOP | 13,192 | 81,557 | 0.143 | logreg | 0.669 | 0.617 | 0.614 | 0.661 | +0.055 (+0.050, +0.060) | +0.052 (+0.048, +0.057) | 0.653 (inv.) |
| STOP | 13,192 | 81,557 | 0.143 | gb | 0.698 | 0.647 | 0.647 | 0.689 | +0.051 (+0.047, +0.055) | +0.051 (+0.047, +0.056) | 0.653 (inv.) |
| STOP | 11,354 | 67,120 | 0.150 | logreg | 0.665 | 0.624 | 0.620 | 0.661 | +0.045 (+0.040, +0.050) | +0.041 (+0.036, +0.046) | 0.649 (inv.) |
| STOP | 11,354 | 67,120 | 0.150 | gb | 0.694 | 0.646 | 0.647 | 0.686 | +0.047 (+0.042, +0.052) | +0.048 (+0.043, +0.053) | 0.649 (inv.) |
| UP_tierW | 13,192 | 81,557 | 0.037 | logreg | 0.649 | 0.576 | 0.572 | 0.616 | +0.077 (+0.068, +0.087) | +0.074 (+0.063, +0.084) | 0.676 (inv.) |
| UP_tierW | 13,192 | 81,557 | 0.037 | gb | 0.828 | 0.595 | 0.598 | 0.709 | +0.229 (+0.221, +0.238) | +0.233 (+0.224, +0.241) | 0.676 (inv.) |
| UP_tierW | 11,354 | 67,120 | 0.036 | logreg | 0.641 | 0.581 | 0.576 | 0.618 | +0.065 (+0.055, +0.076) | +0.060 (+0.049, +0.071) | 0.664 (inv.) |
| UP_tierW | 11,354 | 67,120 | 0.036 | gb | 0.826 | 0.600 | 0.602 | 0.707 | +0.224 (+0.214, +0.234) | +0.225 (+0.216, +0.235) | 0.664 (inv.) |
| DOWN_tierW | 13,192 | 81,557 | 0.061 | logreg | 0.788 | 0.564 | 0.553 | 0.917 | +0.235 (+0.226, +0.243) | +0.224 (+0.215, +0.233) | 0.744 |
| DOWN_tierW | 13,192 | 81,557 | 0.061 | gb | 0.799 | 0.582 | 0.583 | 0.961 | +0.216 (+0.207, +0.224) | +0.217 (+0.209, +0.225) | 0.744 |
| DOWN_tierW | 11,354 | 67,120 | 0.060 | logreg | 0.792 | 0.562 | 0.554 | 0.918 | +0.238 (+0.228, +0.247) | +0.230 (+0.220, +0.241) | 0.748 |
| DOWN_tierW | 11,354 | 67,120 | 0.060 | gb | 0.802 | 0.585 | 0.586 | 0.961 | +0.216 (+0.207, +0.225) | +0.216 (+0.207, +0.226) | 0.748 |
| UP_tierP | 13,192 | 81,557 | 0.043 | logreg | 0.566 | 0.560 | 0.555 | 0.665 | +0.011 (+0.004, +0.017) | +0.006 (-0.002, +0.013) | 0.643 (inv.) |
| UP_tierP | 13,192 | 81,557 | 0.043 | gb | 0.673 | 0.597 | 0.598 | 0.709 | +0.075 (+0.065, +0.085) | +0.077 (+0.066, +0.086) | 0.643 (inv.) |
| UP_tierP | 11,354 | 67,120 | 0.042 | logreg | 0.572 | 0.570 | 0.564 | 0.669 | +0.008 (+0.002, +0.014) | +0.002 (-0.006, +0.011) | 0.634 (inv.) |
| UP_tierP | 11,354 | 67,120 | 0.042 | gb | 0.671 | 0.600 | 0.604 | 0.715 | +0.068 (+0.057, +0.079) | +0.071 (+0.060, +0.082) | 0.634 (inv.) |
| DOWN_tierP | 13,192 | 81,557 | 0.068 | logreg | 0.768 | 0.538 | 0.539 | 0.656 | +0.229 (+0.220, +0.238) | +0.230 (+0.221, +0.239) | 0.771 |
| DOWN_tierP | 13,192 | 81,557 | 0.068 | gb | 0.773 | 0.553 | 0.552 | 0.699 | +0.221 (+0.212, +0.229) | +0.220 (+0.211, +0.229) | 0.771 |
| DOWN_tierP | 11,354 | 67,120 | 0.067 | logreg | 0.773 | 0.538 | 0.540 | 0.667 | +0.233 (+0.223, +0.243) | +0.235 (+0.225, +0.244) | 0.775 |
| DOWN_tierP | 11,354 | 67,120 | 0.067 | gb | 0.776 | 0.550 | 0.552 | 0.710 | +0.224 (+0.215, +0.234) | +0.226 (+0.217, +0.235) | 0.775 |
| UP_NEE | 13,192 | 81,557 | 0.084 | logreg | 0.611 | 0.563 | 0.554 | 0.608 | +0.057 (+0.050, +0.064) | +0.047 (+0.040, +0.055) | 0.604 (inv.) |
| UP_NEE | 13,192 | 81,557 | 0.084 | gb | 0.656 | 0.591 | 0.592 | 0.644 | +0.064 (+0.058, +0.071) | +0.065 (+0.059, +0.072) | 0.604 (inv.) |
| UP_NEE | 11,354 | 67,120 | 0.083 | logreg | 0.615 | 0.568 | 0.559 | 0.611 | +0.056 (+0.049, +0.063) | +0.047 (+0.039, +0.055) | 0.607 (inv.) |
| UP_NEE | 11,354 | 67,120 | 0.083 | gb | 0.655 | 0.592 | 0.592 | 0.643 | +0.063 (+0.056, +0.070) | +0.063 (+0.055, +0.069) | 0.607 (inv.) |
| DOWN_NEE | 13,192 | 81,557 | 0.131 | logreg | 0.579 | 0.575 | 0.563 | 0.619 | +0.016 (+0.012, +0.019) | +0.003 (-0.002, +0.008) | 0.540 |
| DOWN_NEE | 13,192 | 81,557 | 0.131 | gb | 0.621 | 0.594 | 0.593 | 0.685 | +0.027 (+0.024, +0.032) | +0.026 (+0.022, +0.031) | 0.540 |
| DOWN_NEE | 11,354 | 67,120 | 0.132 | logreg | 0.577 | 0.573 | 0.559 | 0.617 | +0.018 (+0.014, +0.022) | +0.004 (-0.001, +0.009) | 0.539 |
| DOWN_NEE | 11,354 | 67,120 | 0.132 | gb | 0.619 | 0.593 | 0.592 | 0.686 | +0.027 (+0.023, +0.032) | +0.026 (+0.022, +0.031) | 0.539 |

## At-risk sensitivity (offset 0): UP only below the top tier or level, DOWN only above zero

| Label | Cohort | Rows | Prev. | Probe | A | D | A minus E (95% CI) | A minus D (95% CI) | Current tier alone |
|---|---|---|---|---|---|---|---|---|---|
| UP_tierW | 13,192 | 47,245 | 0.064 | logreg | 0.674 | 0.642 | +0.034 (+0.027, +0.041) | +0.032 (+0.025, +0.039) | 0.576 |
| UP_tierW | 13,192 | 47,245 | 0.064 | gb | 0.691 | 0.669 | +0.021 (+0.014, +0.027) | +0.023 (+0.016, +0.029) | 0.576 |
| UP_tierW | 11,354 | 39,733 | 0.061 | logreg | 0.679 | 0.646 | +0.035 (+0.027, +0.042) | +0.032 (+0.025, +0.040) | 0.582 |
| UP_tierW | 11,354 | 39,733 | 0.061 | gb | 0.697 | 0.674 | +0.021 (+0.014, +0.028) | +0.023 (+0.016, +0.030) | 0.582 |
| DOWN_tierW | 13,192 | 62,250 | 0.080 | logreg | 0.716 | 0.579 | +0.150 (+0.141, +0.158) | +0.138 (+0.128, +0.147) | 0.657 |
| DOWN_tierW | 13,192 | 62,250 | 0.080 | gb | 0.730 | 0.584 | +0.148 (+0.139, +0.156) | +0.147 (+0.138, +0.155) | 0.657 |
| DOWN_tierW | 11,354 | 49,281 | 0.082 | logreg | 0.710 | 0.579 | +0.143 (+0.134, +0.154) | +0.131 (+0.121, +0.142) | 0.649 |
| DOWN_tierW | 11,354 | 49,281 | 0.082 | gb | 0.723 | 0.583 | +0.137 (+0.128, +0.148) | +0.139 (+0.130, +0.150) | 0.649 |
| UP_tierP | 13,192 | 53,682 | 0.065 | logreg | 0.681 | 0.639 | +0.050 (+0.041, +0.058) | +0.043 (+0.034, +0.051) | 0.555 |
| UP_tierP | 13,192 | 53,682 | 0.065 | gb | 0.712 | 0.670 | +0.041 (+0.034, +0.048) | +0.042 (+0.035, +0.049) | 0.555 |
| UP_tierP | 11,354 | 44,932 | 0.062 | logreg | 0.687 | 0.644 | +0.051 (+0.042, +0.060) | +0.043 (+0.034, +0.052) | 0.559 |
| UP_tierP | 11,354 | 44,932 | 0.062 | gb | 0.718 | 0.675 | +0.043 (+0.035, +0.051) | +0.043 (+0.035, +0.051) | 0.559 |
| DOWN_tierP | 13,192 | 60,847 | 0.091 | logreg | 0.688 | 0.532 | +0.159 (+0.150, +0.168) | +0.156 (+0.147, +0.166) | 0.686 |
| DOWN_tierP | 13,192 | 60,847 | 0.091 | gb | 0.696 | 0.542 | +0.156 (+0.147, +0.166) | +0.154 (+0.145, +0.164) | 0.686 |
| DOWN_tierP | 11,354 | 48,045 | 0.094 | logreg | 0.682 | 0.536 | +0.148 (+0.137, +0.158) | +0.146 (+0.135, +0.156) | 0.677 |
| DOWN_tierP | 11,354 | 48,045 | 0.094 | gb | 0.686 | 0.537 | +0.154 (+0.143, +0.164) | +0.149 (+0.139, +0.160) | 0.677 |
| UP_NEE | 13,192 | 58,582 | 0.117 | logreg | 0.597 | 0.588 | +0.019 (+0.014, +0.024) | +0.009 (+0.003, +0.015) | 0.520 (inv.) |
| UP_NEE | 13,192 | 58,582 | 0.117 | gb | 0.635 | 0.629 | +0.006 (+0.003, +0.008) | +0.006 (+0.003, +0.009) | 0.520 (inv.) |
| UP_NEE | 11,354 | 48,072 | 0.116 | logreg | 0.600 | 0.591 | +0.019 (+0.013, +0.025) | +0.009 (+0.002, +0.015) | 0.525 (inv.) |
| UP_NEE | 11,354 | 48,072 | 0.116 | gb | 0.632 | 0.627 | +0.005 (+0.002, +0.008) | +0.005 (+0.002, +0.009) | 0.525 (inv.) |
| DOWN_NEE | 13,192 | 80,674 | 0.133 | logreg | 0.578 | 0.577 | +0.014 (+0.010, +0.017) | +0.001 (-0.004, +0.006) | 0.537 |
| DOWN_NEE | 13,192 | 80,674 | 0.133 | gb | 0.620 | 0.595 | +0.025 (+0.021, +0.029) | +0.025 (+0.021, +0.029) | 0.537 |
| DOWN_NEE | 11,354 | 66,387 | 0.134 | logreg | 0.579 | 0.577 | +0.016 (+0.012, +0.020) | +0.002 (-0.003, +0.007) | 0.536 |
| DOWN_NEE | 11,354 | 66,387 | 0.134 | gb | 0.620 | 0.594 | +0.026 (+0.021, +0.030) | +0.026 (+0.022, +0.030) | 0.536 |

## Offsets (bins mode), A minus D

| Label | Cohort | Probe | A minus D, offset 0 | offset 2 | offset 4 | Rows at 0 / 2 / 4 |
|---|---|---|---|---|---|---|
| STOP | 13,192 | logreg | +0.052 (+0.048, +0.057) | +0.037 (+0.032, +0.043) | +0.032 (+0.026, +0.038) | 81,557 / 58,358 / 44,169 |
| STOP | 13,192 | gb | +0.051 (+0.047, +0.056) | +0.039 (+0.033, +0.044) | +0.024 (+0.018, +0.029) | 81,557 / 58,358 / 44,169 |
| STOP | 11,354 | logreg | +0.041 (+0.036, +0.046) | +0.031 (+0.025, +0.036) | +0.025 (+0.019, +0.031) | 67,120 / 47,399 / 35,559 |
| STOP | 11,354 | gb | +0.048 (+0.043, +0.053) | +0.037 (+0.031, +0.042) | +0.021 (+0.015, +0.027) | 67,120 / 47,399 / 35,559 |
| UP_tierW | 13,192 | logreg | +0.074 (+0.063, +0.084) | -0.004 (-0.011, +0.003) | +0.001 (-0.004, +0.006) | 81,557 / 58,358 / 44,169 |
| UP_tierW | 13,192 | gb | +0.233 (+0.224, +0.241) | +0.090 (+0.075, +0.105) | +0.033 (+0.020, +0.045) | 81,557 / 58,358 / 44,169 |
| UP_tierW | 11,354 | logreg | +0.060 (+0.049, +0.071) | -0.006 (-0.011, -0.001) | +0.011 (+0.002, +0.020) | 67,120 / 47,399 / 35,559 |
| UP_tierW | 11,354 | gb | +0.225 (+0.216, +0.235) | +0.082 (+0.066, +0.098) | +0.036 (+0.023, +0.050) | 67,120 / 47,399 / 35,559 |
| DOWN_tierW | 13,192 | logreg | +0.224 (+0.215, +0.233) | +0.140 (+0.129, +0.151) | +0.087 (+0.076, +0.099) | 81,557 / 58,358 / 44,169 |
| DOWN_tierW | 13,192 | gb | +0.217 (+0.209, +0.225) | +0.123 (+0.112, +0.134) | +0.083 (+0.072, +0.094) | 81,557 / 58,358 / 44,169 |
| DOWN_tierW | 11,354 | logreg | +0.230 (+0.220, +0.241) | +0.154 (+0.142, +0.168) | +0.103 (+0.090, +0.117) | 67,120 / 47,399 / 35,559 |
| DOWN_tierW | 11,354 | gb | +0.216 (+0.207, +0.226) | +0.135 (+0.124, +0.147) | +0.097 (+0.085, +0.109) | 67,120 / 47,399 / 35,559 |
| UP_tierP | 13,192 | logreg | +0.006 (-0.002, +0.013) | +0.009 (+0.001, +0.018) | +0.007 (-0.003, +0.017) | 81,557 / 58,358 / 44,169 |
| UP_tierP | 13,192 | gb | +0.077 (+0.066, +0.086) | +0.018 (+0.009, +0.027) | +0.022 (+0.011, +0.032) | 81,557 / 58,358 / 44,169 |
| UP_tierP | 11,354 | logreg | +0.002 (-0.006, +0.011) | +0.008 (-0.001, +0.018) | +0.018 (+0.006, +0.030) | 67,120 / 47,399 / 35,559 |
| UP_tierP | 11,354 | gb | +0.071 (+0.060, +0.082) | +0.027 (+0.016, +0.037) | +0.019 (+0.007, +0.030) | 67,120 / 47,399 / 35,559 |
| DOWN_tierP | 13,192 | logreg | +0.230 (+0.221, +0.239) | +0.125 (+0.114, +0.135) | +0.090 (+0.079, +0.100) | 81,557 / 58,358 / 44,169 |
| DOWN_tierP | 13,192 | gb | +0.220 (+0.211, +0.229) | +0.118 (+0.108, +0.128) | +0.102 (+0.091, +0.114) | 81,557 / 58,358 / 44,169 |
| DOWN_tierP | 11,354 | logreg | +0.235 (+0.225, +0.244) | +0.129 (+0.117, +0.140) | +0.088 (+0.076, +0.100) | 67,120 / 47,399 / 35,559 |
| DOWN_tierP | 11,354 | gb | +0.226 (+0.217, +0.235) | +0.127 (+0.116, +0.138) | +0.091 (+0.079, +0.103) | 67,120 / 47,399 / 35,559 |
| UP_NEE | 13,192 | logreg | +0.047 (+0.040, +0.055) | +0.033 (+0.026, +0.040) | +0.022 (+0.015, +0.030) | 81,557 / 58,358 / 44,169 |
| UP_NEE | 13,192 | gb | +0.065 (+0.059, +0.072) | +0.044 (+0.035, +0.051) | +0.028 (+0.019, +0.037) | 81,557 / 58,358 / 44,169 |
| UP_NEE | 11,354 | logreg | +0.047 (+0.039, +0.055) | +0.030 (+0.022, +0.037) | +0.018 (+0.010, +0.026) | 67,120 / 47,399 / 35,559 |
| UP_NEE | 11,354 | gb | +0.063 (+0.055, +0.069) | +0.044 (+0.036, +0.053) | +0.024 (+0.015, +0.034) | 67,120 / 47,399 / 35,559 |
| DOWN_NEE | 13,192 | logreg | +0.003 (-0.002, +0.008) | +0.006 (+0.003, +0.010) | +0.002 (-0.001, +0.005) | 81,557 / 58,358 / 44,169 |
| DOWN_NEE | 13,192 | gb | +0.026 (+0.022, +0.031) | +0.017 (+0.012, +0.022) | +0.010 (+0.005, +0.015) | 81,557 / 58,358 / 44,169 |
| DOWN_NEE | 11,354 | logreg | +0.004 (-0.001, +0.009) | +0.004 (+0.001, +0.008) | +0.002 (-0.002, +0.006) | 67,120 / 47,399 / 35,559 |
| DOWN_NEE | 11,354 | gb | +0.026 (+0.022, +0.031) | +0.015 (+0.011, +0.020) | +0.005 (-0.002, +0.011) | 67,120 / 47,399 / 35,559 |

## Reading

1. **A beats D and E on most titration labels, so the mechanism is not inert here; but what A adds is
   the current dose tier itself.** D and E are nearly identical everywhere (A minus E and A minus D
   agree to about 0.01), and the current tier alone, unfitted, gets close to A on STOP and DOWN
   (STOP 0.653 inv. vs A 0.669; DOWN_tierP 0.771 vs A 0.768).
2. **Where it bites: DOWN on the SOFA tier scale.** A minus D is +0.22 to +0.24 (both probes, both
   cohorts), +0.13 to +0.16 once rows that cannot go down are removed, and still +0.08 to +0.10 at
   offset 4. The state carries the tier and the label is a move on that same tier scale, so the gap is
   largely the label and the feature sharing a scale.
3. **Modest for STOP and UP.** STOP: +0.04 to +0.05 at offset 0, +0.02 to +0.03 at offset 4. UP:
   gb's +0.23 on `UP_tierW` is mostly the ceiling (tier 4 cannot go up). Restricted to rows that can
   move up it is +0.02 to +0.04 on tier scales and +0.005 to +0.009 for NEE.
4. **Practically inert for de-escalation in NE-equivalent dose.** For DOWN_NEE, logreg A minus D is
   +0.003 (13,192) and +0.004 (11,354), CIs including 0; gb +0.026, falling to +0.005 to +0.010 by
   offset 4.
5. **F (D plus treatment history, no SOFA dose content) recovers most of A's edge** on STOP
   (0.661 vs 0.669) and UP_NEE (0.608 vs 0.611), and exceeds A on DOWN_NEE (0.619 vs 0.579; logreg,
   13,192). F above A on `DOWN_tierW` (0.92 to 0.96)
   comes from the window-max definition: F2 sees a tier change inside bin t before tau, which then
   carries into the next bin's window max. On `tierP` this disappears (F 0.656 vs A 0.768). So
   `tierW` DOWN partly measures a decrease that already happened, and `tierP` is the cleaner reading.
6. **Against H3 and Decision 6.** This does not touch the H3 test. It complements Decision 6(a)
   (provisional, pending the project lead's definitions). On off rows, A minus E is about 0.02. On on
   rows with an informative label it is 0.05 for STOP, around 0.2 for tier-scale DOWN, and about 0 for
   NE-equivalent DOWN. STOP is the complement of Decision 6(b)'s "still running at tau + 4h",
   restricted to on rows.

All figures are aggregates; no stay or subject identifiers, per-row predictions or row-level tables
leave the cluster.
