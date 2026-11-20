# Replicate the results

Three levels, from "anyone, in a minute" to "full pipeline". Every headline number on the website and in
the paper draft maps to a committed file below.

## Level 1: no data needed

```bash
git clone https://github.com/MohShahin/SAIL_State-Action-Information-Leakage
cd SAIL_State-Action-Information-Leakage
make install
make test      # the test suite
make demo      # the five checks on a built-in synthetic table
make verify    # every committed result file matches results/MANIFEST.json (SHA-256)
```

`make verify` proves the result files you are reading are the ones the project committed. It does not
re-run the analysis.

## Level 2: check a number against its file

| Claim | File | Where in the file | Value |
| --- | --- | --- | --- |
| AUROC drop, offset 0 vs 8 (H3) | `results/experiment5_h3_paired_bootstrap_bins.json` | `restricted.delta`, `delta_ci_lo`, `delta_ci_hi` | 0.1468 [0.1401, 0.1536] |
| Rows and patients behind it | same | `restricted.n_rows_a`, `n_patients` | 93,629 rows, 12,940 patients |
| Decay curve, offsets 0, 1, 2, 4, 8 (all rows) | same | `decay_curve[].auroc` | 0.8816, 0.8523, 0.8272, 0.7850, 0.7142 |
| Gap with no infusion running | `results/exploratory/decision6a/decision6a_13192.json` | `common_rows_off_at_tau.delta` and CI | 0.0387 [0.0270, 0.0502] |
| Previous action alone vs full state | `results/exploratory/persistence/README.md` and `persistence_13192.json` | table row "P" | 0.888 vs 0.861 |
| Primary cohort | `docs/COHORT_RECONCILIATION.md` | table | 13,192 stays, MIMIC-IV v3.1, recomputed Sepsis-3 |

The unrestricted re-computation in `decision6a_13192.json` (`sanity_unrestricted_H3_common_rows`) gives
0.1475 [0.1407, 0.1542] on 93,630 rows. It differs from the committed H3 run by one row and about
0.0007 AUROC; both are within each other's confidence interval.

## Reproduce the primary result

This level needs credentialed access to MIMIC-IV v3.1 (see `DATA_ACCESS.md`), roughly 120 GB of disk and
a few hours of compute. It follows `docs/ORCD_DUCKDB_RUN.md`.

1. Get credentialed access to MIMIC-IV on PhysioNet and sign the data use agreement. Never copy patient
   data into this repository.
2. Build a local DuckDB database with `mimic-code` (`MIMIC_MAKE_CONCEPTS=true`, `build_mimic.sh`), at the
   `mimic-code` commit recorded in the run log.
3. Create an environment with Python 3.11 and `duckdb pandas numpy scikit-learn matplotlib pillow nbformat nbclient ipykernel pyarrow`.
4. Run the notebook with `SAIL_BACKEND=duckdb` and `SAIL_DUCKDB=<path to the database>`
   (`scripts/orcd_run_notebook.sbatch` shows the exact environment).
5. Confirm the cohort size is 13,192 stays before trusting anything downstream. Set `SAIL_STRICT_EXP3=1`
   for the hard checks on Experiment 3.
6. Run `scripts/h3_paired_bootstrap.py` on the notebook's run folder to produce the H3 aggregates. Run the
   exploratory scripts (`exp_persistence.py`, `exp_decision6a.py`, `paired_cis.py`, ...) the same way.
7. Compare your aggregate JSON with the committed files in Level 2. Copy only reviewed aggregate files
   into `results/`, add them to the allow-list in `.gitignore`, then run `make manifest` and
   `make privacy-check`.

## Expected results

Small differences are normal: bootstrap seeds, library versions and one-row differences in the common-row
set. Differences larger than about 0.005 AUROC, or a cohort size other than 13,192, mean something differs
in your build; please open an issue with your `mimic-code` commit and package versions.

## What cannot be replicated without credentialed access

All real-data results. The synthetic demo and the test suite are the only parts open to everyone.
