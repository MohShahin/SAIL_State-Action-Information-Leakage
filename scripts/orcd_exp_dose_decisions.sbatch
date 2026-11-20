#!/bin/bash
# Exploratory on-vasopressor dose escalation/de-escalation/stop audit (scripts/exp_dose_decisions.py);
# not pre-registered, does not change the H3 decision. Reads exp5_checkpoint_inputs.pkl and DuckDB
# read-only and writes one aggregate JSON. Per-patient predictions are never written.
#   COHORT=13192 sbatch scripts/orcd_exp_dose_decisions.sbatch
#   COHORT=13192 TAG=_at_risk EXTRA=--at-risk sbatch scripts/orcd_exp_dose_decisions.sbatch
#SBATCH --job-name=sail-dose
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=06:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/runs/exploratory/exp-dose-decisions/dose_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/runs/exploratory/exp-dose-decisions/dose_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
REPO=${SAIL_REPO:-$HOME/orcd/pool/code/SAIL_State-Action-Information-Leakage}
OUT=${OUT_DIR:-$HOME/orcd/scratch/sail/runs/exploratory/exp-dose-decisions}
mkdir -p "$OUT"
if [ "${COHORT}" = "13192" ]; then
  CK=${CKPT:-$HOME/orcd/scratch/sail/runs/run_25065533/notebook/results/exp5_checkpoint_inputs.pkl}
  EXP="--expected-dose-rows 447713 --expected-on-rows 81557"
else
  CK=${CKPT:-$HOME/orcd/scratch/sail/runs/run_25029926/notebook/results/exp5_checkpoint_inputs.pkl}
  EXP="--expected-dose-rows 351720 --expected-on-rows 67120"
fi
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) cohort $COHORT ckpt $CK"
python "$REPO/scripts/exp_dose_decisions.py" --checkpoint "$CK" \
  --db "${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}" \
  --out "$OUT/dose_decisions_${COHORT}${TAG:-}.json" --cohort-tag "$COHORT" \
  $EXP --n-jobs "${N_JOBS:-32}" ${EXTRA:-}
echo "end $(date)"
