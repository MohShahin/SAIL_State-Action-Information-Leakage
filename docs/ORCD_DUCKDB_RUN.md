# Running the notebook on MIT ORCD with DuckDB (no BigQuery)

The published pipeline reads MIMIC-IV v3.1 from BigQuery. This branch adds a second backend so
the same notebook runs unchanged against a local DuckDB build of the same release.

1. Build the database once (compute node, about 1 to 2 h, 16 CPUs, 120 GB):
   `MIMIC_MAKE_CONCEPTS=true bash mimic-code/mimic-iv/buildmimic/duckdb/build_mimic.sh <mimiciv/3.1 dir> ~/orcd/scratch/sail/mimic4.db`
   with mimic-code at the commit noted in the run log. The derived schema includes `sepsis3`, which
   `queries/01_cohort.sql` needs. The source csv.gz files are read in place and never copied.
2. Env: conda `sail` (python 3.11) with duckdb, pandas, numpy, scikit-learn, matplotlib, pillow,
   nbformat, nbclient, ipykernel, pyarrow. Install the repo hooks: `pre-commit install`.
3. Run: `sbatch scripts/orcd_run_notebook.sbatch`. The job sets `SAIL_BACKEND=duckdb` and
   `SAIL_DUCKDB`; cell 3 then imports `scripts/duckdb_backend.py`, which rewrites the notebook's
   BigQuery SQL on the fly (table ids, backticks, `UNNEST([STRUCT ...])`, `TIMESTAMP_DIFF` as
   unit-boundary counting, which is how the published BigQuery run behaved on MIMIC's DATETIME columns). The hand-ported equivalents are in `queries/duckdb/` for review.
4. Checksums to confirm before trusting anything downstream: the default run on a v3.1 build gives
   13,192 stays (mimic-code's v3.1 sepsis3). The published 11,354 comes from BigQuery's sepsis3,
   which was built from MIMIC-IV v2.2; reproduce it with step 7 (`SAIL_COHORT_STAYS`), where it
   gives 351,720 dose rows, 4,850,246 physiology rows, 170,299 modeling rows and passes the
   Experiment 3 asserts with `SAIL_STRICT_EXP3=1`. Report the count and the mimic-code commit.
5. Experiment 3's three hard asserts on the published numbers are enforced only with
   `SAIL_STRICT_EXP3=1`; otherwise a deviation is printed and the run continues to Experiments 8
   and 5.
6. Outputs land in `~/orcd/scratch/sail/run_<jobid>/notebook/results/` (the run folder mirrors the repo
   layout so cells 24 and 33 find the committed `../results/` files). Per-patient prediction files from
   Experiment 5b stay there. Copy only the aggregate JSON files to `results/` in the repo; they are
   allowlisted at the bottom of `.gitignore`.
7. Sensitivity cohort: `SAIL_COHORT_STAYS=<parquet or csv with a stay_id column> sbatch scripts/orcd_run_notebook.sbatch`
   keeps every cell 5 condition (adult, first ICU stay, LOS >= 1 day, vasopressor) and takes Sepsis-3
   membership from that list instead of `mimiciv_derived.sepsis3`. With the Sepsis-3 stay_ids of a
   mimic-code DuckDB build of MIMIC-IV v2.2 it gives the 11,354-stay BigQuery cohort on the v3.1
   database. Keep the stay list on scratch, never in the repo. Unset, nothing changes.
