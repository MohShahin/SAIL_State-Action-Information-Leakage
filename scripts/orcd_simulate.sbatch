#!/bin/bash
# Synthetic ground-truth experiment for H3 (exploratory, not pre-registered; does not change the
# H3 decision). Three stages, chosen with SAIL_SIM_STAGE:
#   targets  aggregates of the real 13,192 cohort (cluster only; writes one aggregate JSON)
#   calib    fit the simulator's free parameters to those aggregates (no patient data involved)
#   grid     branch x persistence x seed grid through the frozen H3 functions, then the summary
#   sbatch --export=ALL,SAIL_SIM_STAGE=targets scripts/orcd_simulate.sbatch   # from the repo root
#SBATCH --job-name=sail-sim
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/logs/sim_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/logs/sim_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
REPO=${SAIL_REPO:-$PWD}
OUT=${SAIL_SIM_OUT:-$HOME/orcd/scratch/sail/exploratory/exp-simulation}
RUN=${SAIL_SIM_RUN:-$HOME/orcd/scratch/sail/run_25065533/notebook/results}
DEST=$REPO/results/exploratory/simulation
mkdir -p "$OUT" "$DEST"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
echo "start $(date) host $(hostname) commit $(git -C "$REPO" rev-parse --short HEAD) stage ${SAIL_SIM_STAGE:-grid}"
case "${SAIL_SIM_STAGE:-grid}" in
  targets)
    python "$REPO/scripts/sim_calibration_aggregates.py" --pkl "$RUN/exp5_checkpoint_inputs.pkl" \
      --h3-json "$RUN/experiment5_h3_paired_bootstrap_bins.json" \
      --db "${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}" --out "$DEST/calibration_aggregates.json" ;;
  calib)
    python "$REPO/scripts/simulate_sail.py" calib --targets "$DEST/calibration_aggregates.json" --dest "$DEST" \
      --workers ${SLURM_CPUS_PER_TASK:-8} ;;
  grid)
    python "$REPO/scripts/simulate_sail.py" grid --params "$DEST/sim_params.json" --out "$OUT/grid" \
      --workers ${SLURM_CPUS_PER_TASK:-8} --n-stays ${SAIL_SIM_NSTAYS:-12000} --n-boot ${SAIL_SIM_NBOOT:-2000}
    python "$REPO/scripts/simulate_sail.py" summarize --out "$OUT/grid" --dest "$DEST" ;;
esac
echo "end $(date)"
