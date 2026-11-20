# H3 freeze checklist (draft)

Draft for the project lead. **This file does not amend `docs/DECISIONS_H3.md`.** Its last section is
proposed amendment text that the project lead can adopt, edit or reject. Every number below comes
from a committed aggregate file, quoted to 4 decimals. The headline is rounded to 3 decimals, as in
the 2026-10-07 amendment. Prepared 2026-11-09.

Where the files are: the H3 JSONs are on `h3-paired-bootstrap` (PR #2), and the exploratory
results are on their own branches (PRs #4 to #9, plus `exp-decision6a`, which has no PR yet). None
of them is on main yet.

## 1. Numbers to freeze

### 1.1 H3 primary (decision rule, Decision 5)

| Item | Value | Source |
|---|---|---|
| Delta = AUROC(0) - AUROC(8) | **0.147** (0.1468) | `results/experiment5_h3_paired_bootstrap_bins.json`, `restricted` |
| 95% percentile CI | **0.140 to 0.154** (0.1401 to 0.1536) | same |
| AUROC(0) / AUROC(8) | 0.8610 / 0.7142 | same |
| Rows / patients | 93,629 common rows / 12,940 patients | same |
| Bootstrap | 2,000 resamples, seed 42, 0 single-class skips | same |
| Decision | Prediction A (CI lower bound > 0 and Delta >= 0.10) | Decision 5 |
| Run | pinned run, hash 29fb4ec (bins, common rows, logreg, 13,192 stays) | 2026-10-07 amendment |

**Watch for two versions of this number.** The post-pin run from `ff530e0` gives 0.1475 (0.1407 to
0.1542), which rounds to **0.147 (0.141 to 0.154)**. It is the version in PR #2's body and in every
exploratory README (decision6a, persistence, scaler). The amendment keeps the pinned run as
primary, so the frozen CI is 0.140 to 0.154. Any text quoting "0.141" refers to the post-pin
run and should say so.

| Run | Rows | Delta | CI | File |
|---|---|---|---|---|
| Pinned 29fb4ec (primary) | 93,629 | 0.1468 | 0.1401 to 0.1536 | `results/experiment5_h3_paired_bootstrap_bins.json` |
| Post-pin ff530e0 | 93,630 | 0.1475 | 0.1407 to 0.1542 | `results/h3_post_pin_ff530e0/experiment5_h3_paired_bootstrap_bins.json` |

### 1.2 H3 sensitivities (all report Prediction A)

| Variant | Delta | CI | File |
|---|---|---|---|
| 13,192, bins, own rows | 0.1673 | 0.1612 to 0.1735 | pinned `..._bins.json`, `unrestricted_sensitivity` |
| 13,192, row-shift, common rows | 0.1449 | 0.1386 to 0.1515 | pinned `..._rows.json`, `restricted` |
| 13,192, row-shift, own rows | 0.1725 | 0.1664 to 0.1786 | pinned `..._rows.json`, `unrestricted_sensitivity` |
| 11,354, bins, common rows | 0.1434 | 0.1357 to 0.1506 | `results/sensitivity_v22_11354/..._bins.json` |
| 11,354, bins, own rows | 0.1659 | 0.1594 to 0.1729 | same, `unrestricted_sensitivity` |
| 11,354, row-shift, common rows | 0.1409 | 0.1333 to 0.1484 | `results/sensitivity_v22_11354/..._rows.json` |
| 11,354, row-shift, own rows | 0.1711 | 0.1645 to 0.1783 | same, `unrestricted_sensitivity` |

The 11,354 files come from the `ff530e0` rerun (commit 7fb0193), not from a pinned run. The 13,192
primary was restored to the pinned run (f89dc51). The freeze should say this explicitly.

### 1.3 Persistence controls (exploratory, PR #4)

From `results/exploratory/persistence/persistence_{13192,11354}.json` (logreg, common rows, 2,000
patient-bootstrap resamples). These use the post-pin runs, so A's Delta here is 0.1475, not 0.1468.

| Set | 13,192 Delta [CI] | 11,354 Delta [CI] |
|---|---|---|
| P, previous action only | 0.255 [0.249, 0.262] | 0.259 [0.252, 0.267] |
| I, on at tau | 0.272 [0.265, 0.278] | 0.276 [0.269, 0.283] |
| E, physiology only | 0.035 [0.028, 0.042] | 0.032 [0.025, 0.040] |
| A, full state | 0.147 [0.141, 0.154] | 0.143 [0.136, 0.151] |

| Contrast | 13,192 | 11,354 |
|---|---|---|
| AUROC(0): A vs P | 0.861 vs 0.888 | 0.851 vs 0.887 |
| (A+I) minus (E+I), offset 0 | 0.000 [-0.000, 0.001] | 0.000 [-0.001, 0.001] |
| (A+I) minus (E+I), offsets 1 to 8 | 0.007 to 0.008, CIs above 0 | 0.005 to 0.007, CIs above 0 |
| Delta(A) minus Delta(P) | -0.108 [-0.115, -0.102] | -0.116 [-0.123, -0.109] |

### 1.4 Decision 6(a) (exploratory, branch `exp-decision6a`, commit c70edbe)

| Cohort | Rows | Delta (95% CI) | Rule |
|---|---|---|---|
| 13,192 | off at tau, common (46,476 rows, 10,245 patients) | **0.039 (0.027, 0.050)** | B |
| 13,192 | off at tau, own rows | 0.090 (0.079, 0.100) | B |
| 11,354 | off at tau, common (40,451 rows, 8,967 patients) | **0.033 (0.020, 0.046)** | B |
| 11,354 | off at tau, own rows | 0.087 (0.075, 0.098) | B |

The Decision 6 guard applies. Prediction A holds on all rows, and on off-at-tau rows the decay falls
by about three quarters, below the 0.10 threshold, though a small decay remains with its CI above
zero. Scoring only; the probes were fitted on all rows of the post-pin run.

### 1.5 Within-fold scaler sensitivity (exploratory, PR #9, commit 5d03325)

H3 primary cell: 13,192 within-fold 0.1477 (0.1410 to 0.1545) vs full-matrix 0.1475; 11,354 0.1435
(0.1358 to 0.1507) vs 0.1434. Every H3 cell and every Exp 2/5/6/8 logreg AUROC moves by less than
0.0004. Prediction A is unchanged everywhere.

## 2. Status of the two requested follow-ups

| Follow-up | Branch | Result files | Complete? | What remains |
|---|---|---|---|---|
| 6(a): off at tau, offsets 0 and 8, scoring only, both cohorts | `exp-decision6a` | `results/exploratory/decision6a/decision6a_{13192,11354}.json` + README | **Yes.** Both cohorts; 2,000/2,000 resamples used; no null or NaN fields; sanity check reproduces the post-pin H3 to 4 decimals | Open a PR (none exists). Optional: rescore on the pinned run (see 3.2) |
| Within-fold scaler sensitivity | `exp-scaler-within-fold` (PR #9) | `results/exploratory/scaler_within_fold/scaler_within_fold_{13192,11354}.json` + README | **Yes.** H3 (bins/rows x common/own), Exp 2, 5, 6, 8 logreg, both cohorts | Nothing required. Optional: pinned-run rerun (see 3.2) |

## 3. Open items

1. **Decision 6(b) across offsets has not been run.** The amendment approves L3 ("an infusion
   running at tau + 4") as the 6(b) label. PR #5 measures it at offset 0 only, and its README says it
   "does not test the H3 decay curve". No script yet computes Delta = AUROC(0) - AUROC(8) on the L3
   label. It needs a new script modelled on `scripts/exp_decision6a.py`, run on ORCD by the
   collaborator who holds the DuckDB build and the per-patient predictions. Unlike 6(a), this is
   probably a refit, not a rescoring, because the label changes. The project lead should confirm
   that before it is written.
2. **Runs feeding the exploratory results.** 6(a), the scaler sensitivity and the persistence
   control all use post-pin (`ff530e0`) runs, while the primary is the pinned 29fb4ec run. They
   differ by one row and in the fourth decimal. Either accept this and state it in the freeze, or
   rerun 6(a) on the pinned run (ORCD, collaborator):

   ```
   sbatch --export=ALL,RUN_DIR=<pinned 29fb4ec run dir>,COHORT=13192 scripts/exp_decision6a.sbatch
   ```

   The pinned run directory is not recorded in the repo; the collaborator must supply it. The scaler
   job hard-codes the post-pin runs (`run_25029925`, `run_25029926` in
   `scripts/orcd_exp_scaler_within_fold.sbatch`), so a pinned rerun needs that path changed.
   Given the 0.0004 sensitivity, accepting is reasonable.
3. **11,354 sensitivity has no pinned run.** Its H3 files are from the `ff530e0` rerun. State it.
4. **Wording of the residual 6(a) decay** (0.039, CI above 0): the project lead's call.
5. **PR #2 body is stale.** It still lists `ff530e0` as "pending approval"; the amendment records
   it as approved after the final run.

## 4. Proposed amendment text (not applied)

> ## Freeze (proposed, date of adoption)
>
> - H3 primary, frozen: Prediction A. Delta = 0.147, 95% CI [0.140, 0.154] (0.1468; 0.1401 to
>   0.1536), pinned run 29fb4ec, `results/experiment5_h3_paired_bootstrap_bins.json`. The post-pin
>   `ff530e0` value 0.147 [0.141, 0.154] is a reproduction, not the primary.
> - Sensitivities as listed in docs/H3_FREEZE_CHECKLIST.md section 1.2. All support Prediction A.
>   The 11,354 sensitivity comes from the `ff530e0` rerun.
> - Decision 6(a), run (exploratory): on rows with no label drug running at tau, Delta = 0.039
>   [0.027, 0.050] (13,192) and 0.033 [0.020, 0.046] (11,354), below 0.10. Under the Decision 6
>   guard, the H3 decay is reported as attributable to continuation structure, with a small
>   residual decay.
> - Persistence control (exploratory): previous action alone (0.888) and on-at-tau (0.936) beat the
>   full state (0.861) at offset 0; SOFA terms add 0.000 at offset 0 once on-at-tau is included.
> - Within-fold scaler: no H3 cell moves by 0.0004 or more; the full-matrix scaler stays accepted.
> - Open at freeze: Decision 6(b) across offsets 0 and 8 on the L3 label.
