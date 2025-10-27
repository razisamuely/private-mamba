#!/bin/bash
### sbatch config parameters must start with #SBATCH and must precede any other command. 
### To ignore a line, add another # (like ##SBATCH)

#SBATCH --time=7-00:00:00
#SBATCH --mem=64G
#SBATCH --job-name=smac_test_cost_term_3s_vs_4z_combined
#SBATCH --output=smac_test_cost_term_3s_vs_4z_combined-id-%J.out
#SBATCH --error=smac_test_cost_term_3s_vs_4z_combined-id-%J.err
#SBATCH --mail-user=razshmue@post.bgu.ac.il
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --partition=rtx3090
#SBATCH --gpus=rtx_3090:1
##SBATCH --tasks=1

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

# Run training with safer CUDA memory handling
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# parser.add_argument("--env", type=str, default="starcraft", help="Flatland or SMAC env")
# parser.add_argument("--env_name", type=str, default="8m", help="Specific setting")
# parser.add_argument("--cost_type", type=str, default="dead_allies_incremental", help="Specific setting")
python train.py --env starcraft --env_name 8m --cost_type dead_allies_incremental --cost_limit -8

# Deactivate environment
deactivate

echo "Job finished at: $(date)"
