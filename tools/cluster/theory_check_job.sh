#!/bin/bash
### CA-MAMBA on MAMuJoCo with local logging and transition diagnostics; no WandB account needed.
### Submit (conda env deactivated), one seed:
###   sbatch --export=ALL,SEED=1,ENV_NAME=Safety2x3HalfCheetahVelocity-v0,COST_LIMIT=25.0,MAX_STEPS=1000000 tools/cluster/theory_check_job.sh
### Seeds 1-3 as a job array (SEED defaults to the array task id):
###   sbatch --array=1-3 --export=ALL,ENV_NAME=...,COST_LIMIT=5.0,LAGLR=0,LAG_INIT=1.0,TAG=fixed1 tools/cluster/theory_check_job.sh
### Multiplier: LAGLR (default 1e-5) is the dual step size; LAG_INIT (default: config value) the
### initial beta. LAGLR=0 with LAG_INIT=b fixes beta at b; LAGLR=1e-5 with LAG_INIT=1.0 starts the
### measured-cost dual at parity.
#SBATCH --partition main
#SBATCH --time 2-00:00:00
#SBATCH --job-name camamba_theory
#SBATCH --output camamba_theory-id-%J.out
#SBATCH --gpus=rtx_3090:1
#SBATCH --mem=32G

set -eo pipefail  # no -u: conda's activation scripts reference unset variables
SEED="${SEED:-${SLURM_ARRAY_TASK_ID:-1}}"
ENV_NAME="${ENV_NAME:-Safety2x3HalfCheetahVelocity-v0}"
COST_LIMIT="${COST_LIMIT:-25.0}"
MAX_STEPS="${MAX_STEPS:-1000000}"
LAGLR="${LAGLR:-1e-5}"
LAG_INIT="${LAG_INIT:-}"
TAG="${TAG:-theory}"
REPO_DIR="${REPO_DIR:-$HOME/camamba/private-mamba}"
ENV_DIR="${ENV_DIR:-$HOME/camamba/env}"
OUT_DIR="$HOME/camamba/runs/${TAG}_${ENV_NAME}_d${COST_LIMIT}_s${SEED}_${SLURM_JOB_ID}"

LAG_ARGS=(--laglr "$LAGLR")
if [ -n "$LAG_INIT" ]; then
    LAG_ARGS+=(--lag_init "$LAG_INIT")
fi

echo "job $SLURM_JOB_ID on $(hostname), seed $SEED, $ENV_NAME, d=$COST_LIMIT, max_steps=$MAX_STEPS, ${LAG_ARGS[*]}, tag=$TAG"
nvidia-smi -L || true

module load anaconda
source activate "$ENV_DIR"
export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"
export WANDB_MODE=offline
export WANDB_DIR="$OUT_DIR"
export PYTHONUNBUFFERED=TRUE
mkdir -p "$OUT_DIR"
cd "$REPO_DIR"

python -u train.py \
    --env safety_gym \
    --env_name "$ENV_NAME" \
    --cost_limit "$COST_LIMIT" \
    "${LAG_ARGS[@]}" \
    --seed "$SEED" \
    --n_workers 4 \
    --max_steps "$MAX_STEPS" \
    --slurm_id "$SLURM_JOB_ID" \
    --branch "$TAG" \
    --local_log "$OUT_DIR/metrics.jsonl"

echo "finished $(date)"
