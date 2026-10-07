# Within-fold scaler sensitivity

Exploratory, not pre-registered. It does not replace any pinned or reported result.

## What

The notebook's `cv_predict` fits `StandardScaler` on the full feature matrix and only then splits
it with `GroupKFold(5)` by stay. Each held-out fold is therefore scaled with means and SDs that
already saw its own rows. This is a mild leak. Here every logistic regression result built through
`cv_predict` is rerun with the scaler fit on the training folds only and applied to the held-out
fold. Nothing else changes: same folds, same probe (`LogisticRegression(max_iter=2000,
class_weight="balanced")`), seed 42, 2,000 patient-level paired bootstrap resamples for H3, 300
clustered resamples for the other CIs. Nothing is refit inside a bootstrap resample, in either arm.

Covered: H3 (`scripts/h3_paired_bootstrap.run_h3`, unchanged, bins primary and rows sensitivity,
common rows primary and own rows sensitivity), Experiment 2 logreg (variants A to E), Experiment 5
controls (shuffled labels, placebo feature), Experiment 6 logreg (A to E) and Experiment 8 variant F
logreg (both axes). Random forest and gradient boosting are not rerun: tree ensembles give the same
splits after a per-feature linear rescaling, so the scaler cannot change them.

## How

`scripts/exp_scaler_within_fold.py` (run with `scripts/orcd_exp_scaler_within_fold.sbatch`, ORCD,
CPU, logs scaler_25145883 for 13,192 and scaler_25145884 for 11,354). H3, Exp 2 and Exp 5 read the notebook's own
`exp5_checkpoint_inputs.pkl` from the ff530e0 runs (run_25029925 and run_25029926). Exp 6 and Exp 8 rebuild
their matrices by running the notebook's own cells against a read-only DuckDB. The `full_matrix` arm
is a verbatim copy of `cv_predict` and reproduces the reported runs (largest difference 1.5e-7,
H3 identical); see `sanity_full_matrix_reproduces_reported` in each JSON. Code version: the commit
that adds these files, on top of 177aa96.

## Result

The scaler location does not matter. H3 primary (bins, common rows):

| Cohort | Scaler | AUROC(0) | AUROC(8) | Delta | 95% CI |
|---|---|---|---|---|---|
| 13,192 | full matrix | 0.8610 | 0.7135 | 0.1475 | 0.1407 to 0.1542 |
| 13,192 | within fold | 0.8612 | 0.7135 | 0.1477 | 0.1410 to 0.1545 |
| 11,354 | full matrix | 0.8512 | 0.7078 | 0.1434 | 0.1357 to 0.1506 |
| 11,354 | within fold | 0.8513 | 0.7079 | 0.1435 | 0.1358 to 0.1507 |

Delta moves by less than 0.0004 in every H3 cell (both cohorts, both offset modes, both row sets) and
Prediction A stays supported everywhere. Every Exp 2, 5, 6 and 8 logreg AUROC moves by less than 0.0004.
The best-probe estimands are unchanged, since gradient boosting is the best probe there.
