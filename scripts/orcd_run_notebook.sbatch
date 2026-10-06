#!/bin/bash
# Run the full notebook against the DuckDB build of MIMIC-IV v3.1 on MIT ORCD (CPU only).
#   sbatch scripts/orcd_run_notebook.sbatch            # from the repo root on the cluster
# Prerequisites: ~/orcd/scratch/sail/mimic4.db built by mimic-code's build_mimic.sh with
# MIMIC_MAKE_CONCEPTS=true; conda env `sail` with duckdb, scikit-learn, matplotlib, nbformat,
# nbclient, ipykernel. The notebook is copied to scratch first because the checkpointed runner
# rewrites the .ipynb in place; nothing patient-level is written inside the repo.
#SBATCH --job-name=sail-notebook
#SBATCH --partition=mit_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=11:00:00
#SBATCH --output=/home/%u/orcd/scratch/sail/logs/notebook_%j.out
#SBATCH --error=/home/%u/orcd/scratch/sail/logs/notebook_%j.err
set -euo pipefail
module load miniforge/24.3.0-0
source activate sail
REPO=${SAIL_REPO:-$HOME/orcd/pool/code/SAIL_State-Action-Information-Leakage}
RUN=${SAIL_RUN_DIR:-$HOME/orcd/scratch/sail/run_$SLURM_JOB_ID}
export SAIL_BACKEND=duckdb
export SAIL_DUCKDB=${SAIL_DUCKDB:-$HOME/orcd/scratch/sail/mimic4.db}
export SAIL_THREADS=${SLURM_CPUS_PER_TASK:-8}
export SAIL_MEM=${SAIL_MEM:-32GB}
export SAIL_REPO=$REPO
export MPLBACKEND=Agg
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
# Same layout as the repo: the notebook runs from $RUN/notebook (its OUT_DIR is notebook/results) and
# cells 24 and 33 read the committed curated files through ../results, so a COPY of the repo's
# results/ sits beside it. Nothing is written back into the repo.
mkdir -p "$RUN/notebook/results" "$HOME/orcd/scratch/sail/logs"
cp -r "$REPO/results" "$RUN/results"
cp "$REPO/notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb" "$RUN/notebook/"
cd "$RUN/notebook"
echo "start $(date) host $(hostname) repo $(git -C "$REPO" rev-parse --short HEAD) db $SAIL_DUCKDB"
if [ -n "${SAIL_COHORT_STAYS:-}" ]; then echo "cohort override SAIL_COHORT_STAYS=$SAIL_COHORT_STAYS"; fi
python -m ipykernel install --user --name python3 >/dev/null 2>&1 || true
python "$REPO/scripts/run_notebook_checkpointed.py" \
  --notebook "$RUN/notebook/Sepsis_RL_SOFA_Leakage_Experiments.ipynb" \
  --stop-index ${SAIL_STOP_INDEX:-47} --timeout ${SAIL_CELL_TIMEOUT:-10800}
echo "end $(date)"
ls -la "$RUN/notebook/results" | head -40
