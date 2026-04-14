#!/bin/bash
### sbatch config parameters must start with #SBATCH and must precede any other command.

#SBATCH --time=7-00:00:00
#SBATCH --mem=64G
#SBATCH --job-name={{JOB_NAME}}
#SBATCH --output={{JOB_NAME}}-id-%J.out
#SBATCH --error={{JOB_NAME}}-id-%J.err
#SBATCH --mail-user=razshmue@post.bgu.ac.il
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --partition=rtx4090
#SBATCH --qos=normal
#SBATCH --gpus=1

### Print job info ###
echo "SLURM_JOBID=$SLURM_JOBID"
echo "SLURM_JOB_NODELIST=$SLURM_JOB_NODELIST"

### Environment setup ###
module load anaconda
export SC2PATH="$HOME/StarCraftII"

# Activate virtual environment
source /home/razshmue/workspace/private-mamba/venv/bin/activate

# Go to project directory
cd /home/razshmue/workspace/private-mamba/

# Run training
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python train.py \
    --env {{ENV}} \
    --env_name {{ENV_NAME}} \
    --cost_type {{COST_TYPE}} \
    --cost_limit {{COST_LIMIT}} \
    --seed {{SEED}} \
    --n_workers {{N_WORKERS}} \
    --algo_name {{ALGO}} \
    --laglr {{LAGRANGIAN_LR}} \
    --cost_priority {{COST_PRIORITY}} \
    --slurm_id $SLURM_JOB_ID \
    --branch {{BRANCH_NAME}}

# Deactivate environment
deactivate

echo "Job finished at: $(date)"
