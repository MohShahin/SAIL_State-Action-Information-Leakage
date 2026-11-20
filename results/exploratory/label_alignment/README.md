# Label alignment decomposition

**Exploratory, not pre-registered; does not change the H3 decision.** L2 and L3 follow Decision 6
(a) and (b) and are **provisional, pending the project lead's definitions**.

## What this answers

1. The reviewer attack ranked most damaging in docs/PI_DEFENSE_PREP.md: "isn't this just Off by a
   Beat?" (Tang, Yao, Wiens, Parbhoo, npj Digital Medicine 9, 360, 2026: 49 of 57 sepsis RL papers
   pair each action with a state that already reflects it).
2. FORMAL_ANALYSIS.md section 1.1 says `action_next` is built from treatment events strictly after
   the state window closes, "with zero overlap".

## Setup

- Code: `scripts/exp_label_alignment.py` (+ `scripts/exp_label_alignment.sbatch`,
  `tests/test_label_alignment.py`), commit 73affff on branch exp-label-alignment.
- Cohorts: primary 13,192 stays (state rows and variants from the notebook run of 1d3f170,
  run_25065533) and sensitivity 11,354 stays (published sepsis3 table, run of ff530e0, run_25029926).
  Infusions re-extracted read-only from the DuckDB v3.1 build with the notebook's cell 9 filters.
  Check: the rebuilt L1 equals the notebook's `action_next` on every row (198,890 of 198,890 and
  170,299 of 170,299).
- Slurm jobs sail-labalign_25079754 (primary, 4 min 45 s) and sail-labalign_25079755 (sensitivity, 3 min 57 s), 32 CPUs.
- States: A (full, 25 features), E (physiology only: A without sofa_cardio and sofa_total), I (the
  six-drug "infusion running at tau" indicator, used directly as a score), A minus E.
- Probe: logreg as in H3 (notebook cv_predict, GroupKFold 5 by stay_id); gb as a check. Offset 0.
- CIs: paired patient bootstrap, 2,000 resamples, seed 42. One patient resample per replicate is
  shared by every label and score, so differences between labels are paired too.
- Time: tau = 4 x (bin + 1) h after ICU admission. State window [tau-4, tau). Label drugs: all six.

| Label | Definition | Rows |
|---|---|---|
| L0 contemporaneous | an infusion active in [tau-4, tau), the state's own bin (Tang et al.'s misaligned convention) | all |
| L1 published | an infusion active in [tau, tau+4) (`action_next`) | all |
| L2 initiation (6a, provisional) | L1 | no label drug running at tau |
| L3 continuation (6b, provisional) | an infusion running at tau+4 | all |
| L4 new start | L1, counting only per-drug infusion episodes that start in [tau, tau+4). Rows that touch are merged first, because a rate change splits one infusion into several MIMIC rows | all |
| L4_any_drug (extra) | as L4 with episodes merged across all six drugs, so adding a second drug to a running one is not a new start | all |

## Headline (logreg; AUROC with 95% CI; gb in brackets)

Primary cohort, 13,192 stays, 198,890 rows:

| Label | Prev. | A | E | I | A minus E |
|---|---|---|---|---|---|
| L0 | 0.485 | 0.914 (0.911, 0.917) [0.940] | 0.722 [0.795] | 0.922 | 0.191 (0.187, 0.196) [0.145] |
| L1 | 0.461 | 0.881 (0.878, 0.885) [0.907] | 0.727 [0.791] | 0.944 | 0.154 (0.150, 0.159) [0.116] |
| L2 (117,333 rows) | 0.087 | 0.693 (0.687, 0.699) [0.796] | 0.671 [0.778] | n/a (constant) | 0.022 (0.019, 0.025) [0.019] |
| L3 | 0.392 | 0.866 (0.863, 0.870) [0.886] | 0.723 [0.778] | 0.901 | 0.143 (0.139, 0.147) [0.108] |
| L4 | 0.101 | 0.632 (0.627, 0.636) [0.718] | 0.621 [0.709] | 0.546 | 0.011 (0.009, 0.013) [0.010] |
| L4_any_drug | 0.074 | 0.610 [0.722] | 0.584 [0.681] | 0.446 | 0.026 (0.022, 0.030) [0.041] |

Sensitivity cohort, 11,354 stays, 170,299 rows:

| Label | Prev. | A | E | I | A minus E |
|---|---|---|---|---|---|
| L0 | 0.471 | 0.905 (0.902, 0.909) [0.932] | 0.722 [0.795] | 0.918 | 0.183 (0.179, 0.188) [0.137] |
| L1 | 0.446 | 0.874 (0.870, 0.877) [0.900] | 0.727 [0.791] | 0.942 | 0.147 (0.143, 0.152) [0.109] |
| L2 (103,179 rows) | 0.085 | 0.697 (0.690, 0.703) [0.796] | 0.679 [0.779] | n/a (constant) | 0.018 (0.015, 0.022) [0.017] |
| L3 | 0.375 | 0.859 (0.856, 0.863) [0.880] | 0.722 [0.778] | 0.899 | 0.137 (0.133, 0.142) [0.103] |
| L4 | 0.101 | 0.640 (0.636, 0.645) [0.722] | 0.631 [0.711] | 0.553 | 0.009 (0.007, 0.011) [0.011] |
| L4_any_drug | 0.075 | 0.612 [0.722] | 0.590 [0.687] | 0.456 | 0.023 (0.019, 0.026) [0.035] |

The L1 gb numbers (A 0.907, E 0.791, A minus E 0.116), the indicator (0.944) and the L2 numbers
reproduce the published Experiment 2 and Exp 8 results, so the rows, states and probes are the same.

## Decomposition (primary cohort, logreg; paired CIs; sensitivity cohort in brackets)

| Component | Comparison | Change in A | Change in E | Change in A minus E |
|---|---|---|---|---|
| Alignment leakage | L0 minus L1 | +0.032 (0.031, 0.034) [+0.031] | -0.005 [-0.005] | +0.037 (0.036, 0.039) [+0.036] |
| Continuation | L1 minus L4 | +0.250 (0.245, 0.254) [+0.233] | +0.106 [+0.095] | +0.143 (0.139, 0.148) [+0.138] |
| Continuation | L1 (all rows) minus L2 (rows off at tau) | +0.188 (0.183, 0.194) [+0.177] | +0.056 [+0.048] | +0.132 (0.128, 0.137) [+0.129] |
| SOFA construction | A minus E within L1 / L2 / L4 | | | 0.154 / 0.022 / 0.011 [0.147 / 0.018 / 0.009] |

gb agrees: alignment +0.029 on A minus E, continuation L1 minus L4 +0.107, L1 minus L2 +0.097.

## Overlap between the state window and the label's infusion

The two time windows never overlap: the state uses [tau-4, tau) and the label uses [tau, tau+4).
But the infusions that make the label positive do cross tau. Of the L1-positive rows:

| | Primary (91,758 positive rows) | Sensitivity (75,926) |
|---|---|---|
| a label infusion episode started before tau, so it also overlaps the state window | 81,460 (88.8%) | 67,043 (88.3%) |
| that infusion is a dose-scored drug, so it is in the state's own dose features and sofa_cardio | 60,295 (65.7%) | 47,615 (62.7%) |
| positive only because of an episode started before tau (L1 = 1, L4 = 0) | 71,643 (78.1%) | 58,650 (77.2%) |

Also: P(L1 | running at tau) = 1.000 and P(L1 | not running) = 0.087; P(L1 | L0) = 0.882.

## Plain reading

- **Not Off by a Beat.** The published label is correctly indexed: the state window closes at tau
  and the label window opens at tau. Switching to the misaligned, same-bin label (L0), which is
  what Tang et al. describe, raises A by only 0.03 and A minus E by 0.04. So the SAIL signal is not
  the indexing error; that error would add a little on top.
- **"Zero overlap" holds for windows, not for infusions.** For about 89% of positive rows the
  infusion that makes the label positive started before tau and is still running, so the same
  infusion appears in both windows. For about 66% it is a dose-scored drug that sets sofa_cardio in
  the state directly. Section 1.1's sentence needs to say that the windows are disjoint but the
  label mostly records an infusion already present in the state window.
- **Continuation carries almost all of it.** If only new starts count (L4), A falls from 0.881 to
  0.632 and A minus E falls from 0.154 to 0.011: about 93% of the SOFA gap is persistence of a
  running infusion. Restricting to rows with nothing running (L2) gives the same picture (0.022).
  This is the Decision 6 pattern at offset 0, measured here, not the H3 decay test itself.
- **SOFA construction is small but not zero once continuation is removed.** A minus E is 0.011 for
  new starts and 0.022 for initiation rows, with CIs above zero in both cohorts and both probes.
- **The still-running label (L3) behaves like L1**: A minus E 0.143, because a label defined by a
  running infusion is again mostly readable from the running infusion in the state.
- Both cohorts agree on every comparison within about 0.01 to 0.02.

## Caveats

- Labels differ in prevalence and meaning, so AUROC changes across labels compare tasks, not one
  model. L1 versus L2 also compares different row sets.
- L4 depends on how rows are merged into episodes; per drug is primary, all six drugs merged is
  shown as L4_any_drug and gives the same reading.
- Offset 0 only. This does not test the H3 decay curve; it does not replace Decision 6, whose
  definitions are still pending.
