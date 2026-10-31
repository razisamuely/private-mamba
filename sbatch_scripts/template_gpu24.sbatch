#!/bin/bash
### sbatch config parameters must start with #SBATCH and must precede any other command.
### Same as template.sbatch, but for runs long enough that a requeue is unaffordable.
###
### Two changes, both about where the job lands, not about the method:
###
### 1. --gres pins the GPU model. --gpus=1 takes any card, and several nodes in these
###    partitions carry 11 GB RTX 2080s; bane_vs_bane OOMs on those in under a minute
###    (jobs 23348308/23348309, and 23348310 after a requeue).
### There is no fix here for preemption, which is the other way these runs die: the
### `normal` QoS is preemptible by every lab QoS with PreemptMode=REQUEUE, and train.py
### cannot resume, so a preemption discards the whole run (23348310 lost 69k samples
### after 21 hours; 23423931 was preempted 8 times). The account's own `razshmue` QoS
### is not preemptible but is capped at `gres/gpu:rtx_3090=0` — one gtx_1080 and nothing
### else — so it cannot run this. Pinning the card at least keeps a requeue from landing
### on an 11 GB node and dying instantly.

#SBATCH --time=7-00:00:00
#SBATCH --mem=64G
#SBATCH --job-name={{JOB_NAME}}
#SBATCH --output={{JOB_NAME}}-id-%J.out
#SBATCH --error={{JOB_NAME}}-id-%J.err
#SBATCH --mail-user={{MAIL_USER}}
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --partition=rtx3090
#SBATCH --gres=gpu:rtx_3090:1

### Print job info ###
echo "SLURM_JOBID=$SLURM_JOBID"
echo "SLURM_JOB_NODELIST=$SLURM_JOB_NODELIST"

### Environment setup ###
module load anaconda
export SC2PATH="$HOME/StarCraftII"

# Activate virtual environment
source {{REMOTE_HOME}}/venv/bin/activate

# Go to project directory
cd {{REMOTE_HOME}}/

# Run training
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONPATH=$PYTHONPATH:{{REMOTE_HOME}}/safety-gymnasium-main
python train.py \
    --env {{ENV}} \
    --env_name {{ENV_NAME}} \
    --cost_type {{COST_TYPE}} \
    --cost_limit {{COST_LIMIT}} \
    --seed {{SEED}} \
    --n_workers {{N_WORKERS}} \
    --algo_name {{ALGO}} \
    --laglr {{LAGRANGIAN_LR}} \
    --slurm_id $SLURM_JOB_ID \
    --branch {{BRANCH_NAME}} \
    {{EXTRA_ARGS}}

# Deactivate environment
deactivate

echo "Job finished at: $(date)"
