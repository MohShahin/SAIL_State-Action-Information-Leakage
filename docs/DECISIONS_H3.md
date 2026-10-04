# H3 analysis decisions (frozen before the final run)

Date: 2026-10-04
Status of H3: still open. The project lead has seen no H3 output.

## Disclosure
On 4 Oct the collaborator ran the H3 cell twice in a pipeline check, saw aggregate outputs, and
compared row-shift and bin-index variants. He reports no code or settings changed afterward. The
choices below were made by the project lead after reading scripts/h3_paired_bootstrap.py (code
only, no outputs).

## Decisions
1. Primary cohort: 13,192 stays, all of MIMIC-IV v3.1, with Sepsis-3 recomputed from the derived
   sofa and suspicion_of_infection tables (queries/01c_cohort_recomputed_sepsis3.sql). The
   published mimiciv_3_1_derived.sepsis3 is a strict subset (32,899 vs 41,295 stays).
   Sensitivity: published table, 11,354 stays (effectively 2008-2019).
2. Rows: common rows primary (both AUROCs on rows present at offsets 0 and 8); each offset's own
   rows as sensitivity. Proposed in the initial H3 discussion, before the cohort discrepancy and
   before the disclosure.
3. Offsets: bin-index primary (matches "decision bins" in FORMAL_ANALYSIS section 7); row-shift
   (the published notebook cell 35 construction) as sensitivity. Run the primary in bins mode.
4. Fixed parameters, as in scripts/h3_paired_bootstrap.py at f81e61d43b323f69a8f0c0a0a2daac1801e69f2f: one probe (logreg) for every
   offset; offsets {0,1,2,4,8}; 5-fold CV grouped by stay_id; n_boot = 2000; seed = 42;
   percentile 95% CI on delta = AUROC(0) - AUROC(8); cluster = stay_id; single-class replicates
   skipped and counted. Any script change after this commit must be listed in the PR and
   approved by the project lead before the final run.
5. Decision rule (FORMAL_ANALYSIS section 7, unchanged), operationalised as: Prediction A if the
   lower bound of the delta CI is above 0 and the point estimate of delta is at least 0.10;
   otherwise Prediction B.
6. Exploratory, outside the decision rule: (a) rows with no infusion running at the decision time
   (initiation), with the published label; (b) a "still running at 4h after the decision time"
   label on all rows. Interpretation guard: if Prediction A is met but the decay disappears in
   (a), the result is reported as "decay attributable to continuation structure", not as support
   for H3.
7. Run: fresh, from the commit above, by the collaborator. All variants (both cohorts, both row
   sets, both offset constructions) are reported whatever the outcome. Per-patient predictions
   stay on the cluster.
