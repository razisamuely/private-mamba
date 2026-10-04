#!/bin/bash
# One-time environment for running CA-MAMBA on MAMuJoCo without WandB.
# Run on the Slurm login node (environment management only): bash tools/cluster/setup_env.sh
# Creates a conda environment at $ENV_DIR and checks that train.py imports.
set -eo pipefail  # no -u: conda's activation scripts reference unset variables

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_DIR="${ENV_DIR:-$HOME/camamba/env}"

module load anaconda
if [ ! -d "$ENV_DIR" ]; then
    conda create -y -p "$ENV_DIR" python=3.10
fi
source activate "$ENV_DIR"

pip install --upgrade pip
# Core training stack (CUDA 12.1 wheels run on the cluster's RTX 3090/6000 nodes).
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install "numpy<2" "ray[default]" imageio pandas matplotlib networkx
# MAMuJoCo tasks.
pip install safety-gymnasium mujoco
# Imported by train.py even for MAMuJoCo runs.
pip install git+https://github.com/oxwhirl/smac.git
pip install vmas
pip install recordtype msgpack msgpack-numpy svgutils timeout-decorator "importlib-resources<2" graphviz "gym==0.26.2"
# env/flatland uses the flatland-rl 3.x API (line_generators); the bundled flatland-2.2.2 lacks it.
# --no-deps keeps its pins from replacing the stack above; it needs pkg_resources (setuptools<70).
pip install --no-deps "flatland-rl==3.0.15"
pip install "setuptools<70"
# pysc2 (via smac) pins protobuf 3.20; wandb 0.16 is the last series that imports with it.
pip install "wandb==0.16.6" "protobuf==3.20.3"

export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"
cd "$REPO_DIR"
python -c "import train; import safety_gymnasium; print('imports ok')"
conda deactivate
