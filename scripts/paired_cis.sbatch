#!/bin/bash
# Exploratory, not pre-registered; does not change the H3 decision.
# Paired patient-level CIs for the Exp 2 / Exp 6 / Exp 8 AUROC gaps (scripts/paired_cis*.py).
#   COHORT=13192 sbatch scripts/paired_cis.sbatch     # primary cohort, mimic4.db (v3.1)
#   COHORT=11354 sbatch scripts/paired_cis.sbatch     # sensitivity cohort via SAIL_COHORT_STAYS
# Predictions (patient level) stay under ~/orcd/scratch/sail/exploratory/exp-paired-cis/<cohort>/.
#SBATCH --job-name=sail-paired-cis
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=110G
#SBATCH --time=06:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/exploratory/exp-paired-cis/logs/paired_cis_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/exploratory/exp-paired-cis/logs/paired_cis_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
REPO=${SAIL_REPO:-$HOME/orcd/pool/code/sail-exp-paired-cis}
OUT=$HOME/orcd/scratch/sail/exploratory/exp-paired-cis/$COHORT
mkdir -p "$OUT"
export SAIL_REPO=$REPO SAIL_DUCKDB=$HOME/orcd/scratch/sail/mimic4.db
export SAIL_THREADS=${SLURM_CPUS_PER_TASK:-8} SAIL_MEM=${SAIL_MEM:-48GB} MPLBACKEND=Agg
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
case "$COHORT" in
  13192) unset SAIL_COHORT_STAYS
         REF=$HOME/orcd/scratch/sail/run_25065533/notebook/results ;;
  11354) export SAIL_COHORT_STAYS=$HOME/orcd/scratch/sail/cohorts/v22_sepsis3_stays.parquet
         REF=$REPO/results/sensitivity_v22_11354 ;;
  *) echo "COHORT must be 13192 or 11354"; exit 1 ;;
esac
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) cohort $COHORT"
if [ ! -f "$OUT/points.json" ]; then
  python "$REPO/scripts/paired_cis_predict.py" --out "$OUT"
fi
python "$REPO/scripts/paired_cis.py" --preds-dir "$OUT" --cohort "$COHORT" --out "$OUT/paired_cis_$COHORT.json" \
  --ref-exp2 "$REF/experiment2_action_recoverability_full.csv" --ref-exp6 "$REF/experiment6_mortality_full.csv" \
  --ref-exp8 "$REF/experiment8_variant_f_summary.json" --n-boot ${N_BOOT:-2000} --seed 42 --n-jobs ${SLURM_CPUS_PER_TASK:-8}
echo "end $(date)"
