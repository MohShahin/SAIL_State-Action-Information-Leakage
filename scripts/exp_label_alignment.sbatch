#!/bin/bash
# Label alignment decomposition (exploratory, not pre-registered; does not change the H3 decision).
#   sbatch --export=ALL,RUN_DIR=<notebook run dir>,COHORT=<tag> scripts/exp_label_alignment.sbatch
# Reads the run's exp5_checkpoint_inputs.pkl and the DuckDB build read-only; writes one aggregate JSON.
#SBATCH --job-name=sail-labalign
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/exploratory/exp-label-alignment/logs/%x_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/exploratory/exp-label-alignment/logs/%x_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
REPO=${SAIL_REPO:-$HOME/orcd/pool/code/sail-exp-label-alignment}
OUT=${OUT_DIR:-$HOME/orcd/scratch/sail/exploratory/exp-label-alignment/results}
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) cohort $COHORT run $RUN_DIR"
python "$REPO/scripts/exp_label_alignment.py" --run-dir "$RUN_DIR" --db "${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}" \
  --out-dir "$OUT" --cohort "$COHORT" --n-boot 2000 --seed 42 --n-jobs ${N_JOBS:-24}
echo "end $(date)"
