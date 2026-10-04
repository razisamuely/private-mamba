#!/bin/bash
### CA-MAMBA on MAMuJoCo with local logging and transition diagnostics; no WandB account needed.
### Submit (conda env deactivated):
###   sbatch --export=ALL,SEED=1,ENV_NAME=Safety2x3HalfCheetahVelocity-v0,COST_LIMIT=25.0,MAX_STEPS=1000000 tools/cluster/theory_check_job.sh
#SBATCH --partition main
#SBATCH --time 2-00:00:00
#SBATCH --job-name camamba_theory
#SBATCH --output camamba_theory-id-%J.out
#SBATCH --gpus=rtx_3090:1
#SBATCH --mem=32G

set -eo pipefail  # no -u: conda's activation scripts reference unset variables
SEED="${SEED:-1}"
ENV_NAME="${ENV_NAME:-Safety2x3HalfCheetahVelocity-v0}"
COST_LIMIT="${COST_LIMIT:-25.0}"
MAX_STEPS="${MAX_STEPS:-1000000}"
REPO_DIR="${REPO_DIR:-$HOME/camamba/private-mamba}"
ENV_DIR="${ENV_DIR:-$HOME/camamba/env}"
OUT_DIR="$HOME/camamba/runs/${ENV_NAME}_d${COST_LIMIT}_s${SEED}_${SLURM_JOB_ID}"

echo "job $SLURM_JOB_ID on $(hostname), seed $SEED, $ENV_NAME, d=$COST_LIMIT, max_steps=$MAX_STEPS"
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
    --laglr 1e-5 \
    --seed "$SEED" \
    --n_workers 4 \
    --max_steps "$MAX_STEPS" \
    --slurm_id "$SLURM_JOB_ID" \
    --branch theory-check \
    --local_log "$OUT_DIR/metrics.jsonl"

echo "finished $(date)"
