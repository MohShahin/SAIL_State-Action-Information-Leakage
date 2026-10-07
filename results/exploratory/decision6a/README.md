# Decision 6(a): the H3 decay test on rows with nothing running at tau

**Exploratory, outside the H3 decision rule; does not change the H3 decision.** Decision 6 outputs
were seen before the definitions were approved (docs/DECISIONS_H3.md, 2026-10-07 amendment), so
this analysis is not blind.

## What and why

Decision 6(a) asks whether the H3 decay, Delta = AUROC(0) - AUROC(8), survives on rows where no
label drug is running at the decision time. If most of the decay comes from a running infusion
that simply continues, it should shrink on those rows. The guard in Decision 6: if Prediction A
holds on all rows but the decay disappears here, the result is reported as "decay attributable to
continuation structure", not as support for H3.

## How

- Code: `scripts/exp_decision6a.py` (+ `scripts/exp_decision6a.sbatch`, `tests/test_decision6a.py`).
- Inputs: the saved per-row predictions of the approved fixed run (ff530e0) at offsets 0 and 8,
  bin-index offsets, logreg, grouped 5-fold CV. **Scoring only: nothing is refit.** Sensitivity
  cohort: the 11,354-stay run from the same commit.
- Off at tau: no infusion of the six label drugs with start <= tau < end, tau = 4 x (bin + 1) h
  after ICU admission. This is the approved definition and the L2 row set of
  `results/exploratory/label_alignment` (PR #5); the infusions are re-extracted with the same query.
  Check: the rebuilt label equals `action_next` on every row (198,890 and 170,299), and the
  off-at-tau counts match PR #5 (117,333 and 103,179).
- Row identity: in bins mode a row is the state `(stay_id, bin)` at every offset; offset 8 only
  relabels it with the action of bin + 8. Common rows are the pairs present at both offsets. The
  indicator is taken at the state's own tau (the offset-0 decision time) and the same rows are
  dropped at both offsets.
- Test: `paired_cluster_bootstrap` from `scripts/h3_paired_bootstrap.py`, unchanged: patient-level
  paired bootstrap, 2,000 resamples, seed 42, percentile 95% CI. Rule (Decision 5): Prediction A
  if the CI lower bound is above 0 and Delta >= 0.10.
- Sanity check: the same code on the unrestricted common rows reproduces the saved H3 result to 4
  decimals (13,192: Delta 0.1475, CI 0.1407 to 0.1542; 11,354: 0.1434, CI 0.1357 to 0.1506).

## Result

| Cohort | Rows | Row count | Patients | AUROC(0) | AUROC(8) | Delta (95% CI) | Rule |
|---|---|---|---|---|---|---|---|
| 13,192 | all, common (H3 primary) | 93,630 | 12,940 | 0.861 | 0.714 | 0.147 (0.141, 0.154) | A |
| 13,192 | off at tau, common (6a) | 46,476 | 10,245 | 0.614 | 0.576 | 0.039 (0.027, 0.050) | B |
| 13,192 | off at tau, own rows | 117,333 / 46,476 | 12,159 | 0.665 | 0.576 | 0.090 (0.079, 0.100) | B |
| 11,354 | all, common | 79,692 | 11,146 | 0.851 | 0.708 | 0.143 (0.136, 0.151) | A |
| 11,354 | off at tau, common (6a) | 40,451 | 8,967 | 0.612 | 0.579 | 0.033 (0.020, 0.046) | B |
| 11,354 | off at tau, own rows | 103,179 / 40,451 | 10,563 | 0.665 | 0.579 | 0.087 (0.075, 0.098) | B |

No bootstrap replicate was skipped. Full numbers, AUROC CIs and prevalences are in
`decision6a_13192.json` and `decision6a_11354.json`.

## Plain reading

- On rows with nothing running at tau, Delta falls from 0.147 to 0.039 (about three quarters
  smaller) and no longer meets the 0.10 threshold, in both cohorts. A small decay remains, with a
  CI above zero.
- Under the Decision 6 guard, the decay that meets Prediction A is mostly attributable to
  continuation structure. How to word the small residual decay is the project lead's call.
- Own rows give a larger Delta (0.090) because offset 0 then keeps all off-at-tau rows, which
  have a lower prevalence (0.087 vs 0.144 on the common rows); it still fails the threshold.

## Caveats

- The probes were fitted on all rows; these rows are only scored. A probe refit on off-at-tau
  rows scores higher at offset 0 (PR #5: 0.693 vs 0.665 here), so these AUROCs are not the best a
  probe could do on this subset.
- Off at tau is taken at the offset-0 decision time only; an infusion may be running at the
  offset-8 decision time.
- Per-patient predictions and indicators stay on the cluster; only these aggregates are committed.
