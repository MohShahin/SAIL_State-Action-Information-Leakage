# Synthetic ground truth for the H3 decision rule ("Experiment G")

**Exploratory, not pre-registered; does not change the H3 decision.**

## What

`docs/PI_DEFENSE_PREP.md` (section 5, Experiment G) asks whether SAIL's metric can be checked against a
known truth. This asks the narrower H3 question: can the pre-registered rule (Prediction A if
Delta = AUROC(0) - AUROC(8) has a 95% CI lower bound above 0 and Delta >= 0.10) tell the
SOFA-construction mechanism apart from plain treatment persistence?

`scripts/simulate_sail.py` simulates ICU stays on the notebook's grid (18 bins of 4h):

- a hidden severity process (AR(1) plus a patient level and a drift)
- MAP, generated from severity plus the drug's effect by dose tier
- a clinician policy that starts a vasopressor when MAP is low; each infusion then runs for a length
  drawn when it starts (the persistence knob)
- a SOFA-like cardiovascular score with a switchable treatment branch:
  - `on`: the dose tier sets the score once a dose-scored drug runs, as in real SOFA
  - `off`: the score comes from MAP < 70 only, and the drug still raises MAP
  - `off_pure`: MAP only, and the drug is invisible in every feature

Labels follow the notebook: `action_next` is whether an infusion runs in the next bin, and
`on_tau` (running at the decision time) implies the label. Every setting goes through the
**unchanged** `scripts/h3_paired_bootstrap.py` functions:

- bins mode, common rows primary
- logreg probe with the notebook's grouped 5-fold `cv_predict`
- 2,000 patient resamples, seed 42

Three predictors are scored per setting: variant A (all features), variant E (no `sofa_cardio`, no
`sofa_total`), and the on-at-tau indicator on its own.

## Cohort and calibration

The free parameters were fitted by differential evolution to **aggregates only** of the real
13,192-stay primary cohort (`calibration_aggregates.json`). These came from
`scripts/sim_calibration_aggregates.py`, which reads the notebook inputs of the full run at
1d3f170 plus the six label drugs' intervals from the DuckDB build, opened read-only. No patient
row left the cluster. The fitted parameters are in `sim_params.json`. The same parameters are
used for every branch, and only the persistence multiplier changes.

| Aggregate | Real | Simulated (branch on) |
|---|---|---|
| Rows with a label drug running at tau | 0.410 | 0.409 |
| Next-action prevalence | 0.461 | 0.464 |
| Label rate when off at tau | 0.087 | 0.093 |
| Infusion occupied in bin 0 / stays ever on | 0.600 / 0.946 | 0.647 / 0.886 |
| Mean infusion run length (bins, 18-bin grid) | 6.81 | 6.35 |
| P(label at t+1), given label at t = 1 / 0 | 0.883 / 0.050 | 0.872 / 0.079 |
| P(label at t+8), given label at t = 1 / 0 | 0.520 / 0.186 | 0.489 / 0.214 |
| MAP mean on / off at tau (clipped 20 to 200) | 72.8 / 77.2 | 74.3 / 78.9 |
| MAP lag-1 / lag-8 correlation | 0.66 / 0.34 | 0.64 / 0.29 |
| Rows with MAP < 70 | 0.320 | 0.313 |
| On-at-tau rows with a dose-set cardio score | 0.763 | 0.761 |

**Face validity (AUROCs were not calibration targets).** These are AUROC(0) / AUROC(8) / Delta on
common rows.

| Predictor | Real cohort | Simulated, branch on, realistic persistence |
|---|---|---|
| Variant A | 0.861 / 0.714 / 0.147 | 0.848 / 0.673 / 0.176 |
| Variant E | 0.696 / 0.660 / 0.035 | 0.687 / 0.648 / 0.039 |
| On-at-tau indicator | 0.938 / 0.667 / 0.271 | 0.929 / 0.631 / 0.298 |

The real E and indicator rows were computed with the same frozen functions. The real A row is the
run's own H3 output.

## Grid and settings

The grid crosses three branches with five persistence levels and three seeds, for 45 settings. Each
setting has 12,000 stays. The persistence levels multiply the fitted mean extra run length by 0, 0.5,
1, 2 and 4. At 0, every infusion lasts one bin. The grid ran on ORCD from commit 2ebc5e4 in one
16-CPU job of 28 minutes. Per-seed rows are in `grid_results.csv` and seed means in
`grid_results_mean.csv`. The figure is `delta_vs_persistence.png`, with the real cohort as black
markers. The figure was redrawn from `grid_results.csv` after a plotting-only
change that added those markers.

The table shows means over 3 seeds. "A?" is the number of seeds meeting Prediction A. The CI
column gives the lowest lower bound and the highest upper bound across seeds.

| Branch | Persistence | Mean run (bins) | A: Delta | A: CI | A? | E: Delta | E: A? | Indicator: Delta | Indicator: A? | A minus E at offset 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| on | none | 1.3 | 0.242 | 0.231 to 0.257 | 3/3 | 0.246 | 3/3 | 0.000 | 0/3 | 0.000 |
| on | short | 4.4 | 0.178 | 0.167 to 0.189 | 3/3 | 0.062 | 0/3 | 0.301 | 3/3 | 0.133 |
| on | **realistic** | 6.4 | **0.176** | 0.165 to 0.185 | **3/3** | 0.039 | 0/3 | 0.298 | 3/3 | 0.174 |
| on | long | 8.7 | 0.172 | 0.162 to 0.181 | 3/3 | 0.030 | 0/3 | 0.282 | 3/3 | 0.205 |
| on | very long | 10.9 | 0.156 | 0.146 to 0.166 | 3/3 | 0.012 | 0/3 | 0.258 | 3/3 | 0.230 |
| off | none | 1.3 | 0.246 | 0.235 to 0.259 | 3/3 | 0.246 | 3/3 | 0.000 | 0/3 | 0.000 |
| off | short | 4.4 | 0.062 | 0.050 to 0.076 | 0/3 | 0.062 | 0/3 | 0.301 | 3/3 | 0.000 |
| off | **realistic** | 6.4 | **0.040** | 0.028 to 0.051 | **0/3** | 0.039 | 0/3 | 0.298 | 3/3 | 0.001 |
| off | long | 8.7 | 0.032 | 0.025 to 0.040 | 0/3 | 0.030 | 0/3 | 0.282 | 3/3 | 0.003 |
| off | very long | 10.9 | 0.015 | 0.006 to 0.025 | 0/3 | 0.012 | 0/3 | 0.258 | 3/3 | 0.004 |
| off_pure | none | 1.5 | 0.245 | 0.233 to 0.259 | 3/3 | 0.245 | 3/3 | 0.000 | 0/3 | 0.000 |
| off_pure | short | 4.7 | 0.093 | 0.082 to 0.106 | 0/3 | 0.093 | 0/3 | 0.297 | 3/3 | 0.000 |
| off_pure | realistic | 6.8 | 0.070 | 0.058 to 0.080 | 0/3 | 0.070 | 0/3 | 0.295 | 3/3 | 0.000 |
| off_pure | long | 9.1 | 0.061 | 0.053 to 0.069 | 0/3 | 0.061 | 0/3 | 0.281 | 3/3 | 0.000 |
| off_pure | very long | 11.2 | 0.042 | 0.032 to 0.053 | 0/3 | 0.042 | 0/3 | 0.257 | 3/3 | 0.001 |

## How to read it

1. **Key readout.** With the treatment branch OFF at realistic persistence, Delta is 0.040, which
   is Prediction B in 3/3 seeds. The drug-invisible variant gives 0.070, also B. With the branch ON,
   Delta is 0.176, which is Prediction A in 3/3 seeds. At the persistence fitted to the real cohort,
   persistence on its own did not produce Prediction A. Only a state carrying the dose-coded score
   did.
2. **What Prediction A detects is broader than SOFA.** The on-at-tau indicator involves no SOFA, only
   continuation. It gives Delta of about 0.26 to 0.30 in every branch with persistence, which is
   Prediction A. The real cohort shows the same, at 0.271. Prediction A therefore marks a state that
   encodes the currently running treatment while that treatment persists. The SOFA dose branch is one
   such encoding, and the rule cannot tell it apart from any other encoding.
3. **Prediction A without any treatment encoding.** With no persistence, every infusion lasts one
   bin and the policy reacts to the observed MAP. Prediction A then appears in all three branches,
   including `off_pure`, where Delta is about 0.245 for both A and E. The physiology-only state predicts
   a reactive policy's next action, and that predictability fades as MAP decorrelates over 32 hours.
   This regime is far from the real cohort (P(label at t+1 given label at t) is 0.88 there). It still
   shows the rule can fire with no leak at all.
4. **Delta is not a monotone leakage measure.** Under ON, the dose score's own contribution (A minus E
   at offset 0) rises from 0.133 to 0.230 as persistence grows. Over the same range, Delta falls from
   0.178 to 0.156. A minus E is 0.000 to 0.004 in every OFF setting and 0.13 or more in every ON setting
   with persistence. In this simulator, the variant contrast separates the mechanisms and Delta alone
   does not. This fails property (2) of `PI_DEFENSE_PREP.md` section 4 for Delta. With no persistence,
   the dose score carries no next-action information (A minus E is 0). The SOFA-construction leak and
   persistence are not two alternatives, because the leak works through persistence.

Limitations:

- One latent severity factor drives everything.
- Run lengths are fixed when an infusion starts, and are not tied to MAP recovery.
- There are no missing bins or imputation, so rows mode equals bins mode.
- There is one probe, and the fitted drug effect on MAP is small (about 2 to 4 mmHg).
- The fit misses "stays ever on" (0.886 vs 0.946).

These conclusions hold for this data-generating process only.
