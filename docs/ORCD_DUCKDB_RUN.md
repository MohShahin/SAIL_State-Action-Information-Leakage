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
   BigQuery SQL on the fly (table ids, backticks, `UNNEST([STRUCT ...])`, `TIMESTAMP_DIFF` with
   BigQuery's truncation semantics). The hand-ported equivalents are in `queries/duckdb/` for review.
4. Checksums to confirm before trusting anything downstream: cohort 11,354 stays; Experiment 2
   AUROC 0.900 (variant A) and 0.791 (variant E). A different mimic-code version can shift the
   cohort by a few stays; report the count and the commit.
5. Experiment 3's three hard asserts on the published numbers are enforced only with
   `SAIL_STRICT_EXP3=1`; otherwise a deviation is printed and the run continues to Experiments 8
   and 5.
6. Outputs land in `~/orcd/scratch/sail/run_<jobid>/results/`. Per-patient prediction files from
   Experiment 5b stay there. Copy only the aggregate JSON files to `results/` in the repo; they are
   allowlisted at the bottom of `.gitignore`.
