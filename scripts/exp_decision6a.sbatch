#!/bin/bash
# Decision 6(a): H3 decay test on rows off at tau (exploratory, outside the decision rule).
#   sbatch --export=ALL,RUN_DIR=<notebook run dir>,COHORT=<tag> scripts/exp_decision6a.sbatch
# Reads the run's saved offset 0 and 8 predictions, checkpoint and the DuckDB build read-only;
# writes one aggregate JSON.
#SBATCH --job-name=sail-d6a
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=56G
#SBATCH --time=04:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/exploratory/decision6a/logs/%x_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/exploratory/decision6a/logs/%x_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
REPO=${SAIL_REPO:-$HOME/orcd/scratch/sail/wt-d6a}
OUT=${OUT_DIR:-$HOME/orcd/scratch/sail/exploratory/decision6a/results}
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) cohort $COHORT run $RUN_DIR"
python "$REPO/scripts/exp_decision6a.py" --run-dir "$RUN_DIR" --db "${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}" \
  --out "$OUT/decision6a_$COHORT.json" --cohort "$COHORT" --n-boot 2000 --seed 42
echo "end $(date)"
