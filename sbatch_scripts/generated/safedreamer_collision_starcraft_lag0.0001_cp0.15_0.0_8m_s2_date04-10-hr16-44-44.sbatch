#!/bin/bash
### sbatch config parameters must start with #SBATCH and must precede any other command.

#SBATCH --time=7-00:00:00
#SBATCH --mem=64G
#SBATCH --job-name=safedreamer_collision_starcraft_lag0.0001_cp0.15_0.0_8m_s2_date04-10-hr16-44-44
#SBATCH --output=safedreamer_collision_starcraft_lag0.0001_cp0.15_0.0_8m_s2_date04-10-hr16-44-44-id-%J.out
#SBATCH --error=safedreamer_collision_starcraft_lag0.0001_cp0.15_0.0_8m_s2_date04-10-hr16-44-44-id-%J.err
#SBATCH --mail-user=razshmue@post.bgu.ac.il
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --partition=rtx3090
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
    --env starcraft \
    --env_name 8m \
    --cost_type collision \
    --cost_limit 0.0 \
    --seed 2 \
    --n_workers 4 \
    --algo_name safedreamer \
    --laglr 0.0001 \
    --cost_priority 0.15 \
    --slurm_id $SLURM_JOB_ID \
    --branch feat-lag-real-cost-fix

# Deactivate environment
deactivate

echo "Job finished at: $(date)"
