#!/bin/bash
# Exploratory persistence control (scripts/exp_persistence.py); not pre-registered, does not change
# the H3 decision. Reads a finished notebook run's exp5_checkpoint_inputs.pkl and the DuckDB build
# (read-only); writes one aggregate JSON. Per-patient predictions are never written.
#   COHORT=13192 CKPT=~/orcd/scratch/sail/run_25065533/notebook/results/exp5_checkpoint_inputs.pkl \
#     sbatch scripts/orcd_exp_persistence.sbatch
#SBATCH --job-name=sail-persist
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/exploratory/exp-persistence/logs/persist_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/exploratory/exp-persistence/logs/persist_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
REPO=${SAIL_REPO:-$HOME/orcd/pool/code/sail-exp-persistence}
OUT=${OUT:-$HOME/orcd/scratch/sail/exploratory/exp-persistence/persistence_${COHORT}.json}
export SAIL_THREADS=8 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) cohort $COHORT ckpt $CKPT"
python "$REPO/scripts/exp_persistence.py" --checkpoint "$CKPT" --db "${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}" \
  --cohort "$COHORT" --out "$OUT" --n-boot ${N_BOOT:-2000} --seed 42 --n-jobs ${N_JOBS:-16}
echo "end $(date)"
