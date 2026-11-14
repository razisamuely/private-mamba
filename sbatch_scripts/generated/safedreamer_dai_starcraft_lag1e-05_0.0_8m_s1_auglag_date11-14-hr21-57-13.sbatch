#!/bin/bash
#SBATCH --time=7-00:00:00
#SBATCH --mem=64G
#SBATCH --job-name=safedreamer_dai_starcraft_lag1e-05_0.0_8m_s1_auglag_date11-14-hr21-57-13
#SBATCH --output=safedreamer_dai_starcraft_lag1e-05_0.0_8m_s1_auglag_date11-14-hr21-57-13-id-%J.out
#SBATCH --error=safedreamer_dai_starcraft_lag1e-05_0.0_8m_s1_auglag_date11-14-hr21-57-13-id-%J.err
#SBATCH --mail-user=razshmue@post.bgu.ac.il
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --partition=rtx3090
#SBATCH --gpus=1

echo "SLURM_JOBID=$SLURM_JOBID"
echo "SLURM_JOB_NODELIST=$SLURM_JOB_NODELIST"

module load anaconda
export SC2PATH="$HOME/StarCraftII"
source /home/razshmue/workspace/private-mamba/venv/bin/activate
cd /home/razshmue/workspace/private-mamba/

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONPATH=$PYTHONPATH:/home/razshmue/workspace/private-mamba/safety-gymnasium-main
python train.py \
    --env starcraft \
    --env_name 8m \
    --cost_type dead_allies_incremental \
    --cost_limit 0.0 \
    --seed 1 \
    --n_workers 4 \
    --algo_name safedreamer \
    --laglr 1e-05 \
    --slurm_id $SLURM_JOB_ID \
    --branch feat-cost-he \
    --lag_mode augmented \
    --max_steps 105000

deactivate
echo "Job finished at: $(date)"
