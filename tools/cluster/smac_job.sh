#!/bin/bash
### CA-MAMBA on SMAC with local logging (no WandB account needed); needs tools/cluster/setup_sc2_job.sh once.
### Seeds 1-3 as a job array (SEED defaults to the array task id), from the repo root, env deactivated:
###   sbatch --array=1-3 --export=ALL,MAP=8m,COST_LIMIT=0.0,LAGLR=1e-5,TAG=measured tools/cluster/smac_job.sh
### LAGLR is the dual step size; LAG_INIT (optional) the initial beta; LAGLR=0 with LAG_INIT=b fixes beta.
#SBATCH --partition main
#SBATCH --time 2-00:00:00
#SBATCH --job-name camamba_smac
#SBATCH --output camamba_smac-id-%J.out
#SBATCH --gpus=rtx_3090:1
#SBATCH --mem=48G

set -eo pipefail  # no -u: conda's activation scripts reference unset variables
SEED="${SEED:-${SLURM_ARRAY_TASK_ID:-1}}"
MAP="${MAP:-8m}"
COST_LIMIT="${COST_LIMIT:-0.0}"
MAX_STEPS="${MAX_STEPS:-105000}"
LAGLR="${LAGLR:-1e-5}"
LAG_INIT="${LAG_INIT:-}"
TAG="${TAG:-smac}"
REPO_DIR="${REPO_DIR:-$HOME/camamba/private-mamba}"
ENV_DIR="${ENV_DIR:-$HOME/camamba/env}"
export SC2PATH="${SC2PATH:-$HOME/camamba/StarCraftII}"
OUT_DIR="$HOME/camamba/runs/${TAG}_${MAP}_d${COST_LIMIT}_s${SEED}_${SLURM_JOB_ID}"

LAG_ARGS=(--laglr "$LAGLR")
if [ -n "$LAG_INIT" ]; then
    LAG_ARGS+=(--lag_init "$LAG_INIT")
fi

echo "job $SLURM_JOB_ID on $(hostname), seed $SEED, map $MAP, d=$COST_LIMIT, max_steps=$MAX_STEPS, ${LAG_ARGS[*]}, tag=$TAG, SC2PATH=$SC2PATH"
nvidia-smi -L || true
test -d "$SC2PATH/Maps/SMAC_Maps" || { echo "SC2 maps missing under $SC2PATH"; exit 1; }

module load anaconda
source activate "$ENV_DIR"
export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"
export WANDB_MODE=offline
export WANDB_DIR="$OUT_DIR"
export PYTHONUNBUFFERED=TRUE
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p "$OUT_DIR"
cd "$REPO_DIR"

python -u train.py \
    --env starcraft \
    --env_name "$MAP" \
    --cost_type dead_allies_incremental \
    --cost_limit "$COST_LIMIT" \
    "${LAG_ARGS[@]}" \
    --seed "$SEED" \
    --n_workers 4 \
    --max_steps "$MAX_STEPS" \
    --slurm_id "$SLURM_JOB_ID" \
    --branch "$TAG" \
    --local_log "$OUT_DIR/metrics.jsonl"

echo "finished $(date)"
