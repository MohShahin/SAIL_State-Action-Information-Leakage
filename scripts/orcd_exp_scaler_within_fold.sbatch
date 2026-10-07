#!/bin/bash
# Exploratory, not pre-registered: within-fold StandardScaler sensitivity (scripts/exp_scaler_within_fold.py).
#   COHORT=13192 sbatch scripts/orcd_exp_scaler_within_fold.sbatch   # primary, ff530e0 run_25029925
#   COHORT=11354 sbatch scripts/orcd_exp_scaler_within_fold.sbatch   # sensitivity, ff530e0 run_25029926
# Patient-level files (predictions, rebuilt matrices) stay under ~/orcd/scratch/sail/exploratory/scaler-within-fold/.
#SBATCH --job-name=sail-scaler
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=56G
#SBATCH --time=05:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/exploratory/scaler-within-fold/logs/scaler_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/exploratory/scaler-within-fold/logs/scaler_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
REPO=${SAIL_REPO:-$HOME/orcd/scratch/sail/wt-scaler}
WORK=$HOME/orcd/scratch/sail/exploratory/scaler-within-fold/$COHORT
mkdir -p "$WORK"
export SAIL_REPO=$REPO SAIL_DUCKDB=${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}
export SAIL_THREADS=${SLURM_CPUS_PER_TASK:-8} SAIL_MEM=${SAIL_MEM:-24GB} MPLBACKEND=Agg
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export SAIL_H3_NBOOT=${SAIL_H3_NBOOT:-2000}
case "$COHORT" in
  13192) unset SAIL_COHORT_STAYS; RUN=$HOME/orcd/scratch/sail/run_25029925 ;;
  11354) export SAIL_COHORT_STAYS=$HOME/orcd/scratch/sail/cohorts/v22_sepsis3_stays.parquet
         RUN=$HOME/orcd/scratch/sail/run_25029926 ;;
  *) echo "COHORT must be 13192 or 11354"; exit 1 ;;
esac
REF=$RUN/notebook/results
CK=$REF/exp5_checkpoint_inputs.pkl
PTS=$HOME/orcd/scratch/sail/exploratory/exp-paired-cis/$COHORT/points.json
S="$REPO/scripts/exp_scaler_within_fold.py"
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) cohort $COHORT ref $RUN"
[ -f "$WORK/checkpoint_part.json" ] || python "$S" checkpoint --work "$WORK" --checkpoint "$CK"
[ -f "$WORK/matrices.pkl" ] || python "$S" matrices --work "$WORK"
[ -f "$WORK/exp68_part.json" ] || python "$S" exp68 --work "$WORK" --checkpoint "$CK"
python "$S" report --work "$WORK" --cohort "$COHORT" --ref-dir "$REF" --ref-points "$PTS" \
  --out "$WORK/scaler_within_fold_$COHORT.json"
echo "end $(date)"
