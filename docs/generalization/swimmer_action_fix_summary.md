






































# Swimmer Action Fix & Safety Calibration Summary

**Branch**: `feat/swimmer-action-fix`  
**Status**: Logic Implemented & Locally Verified (Math/Script)  
**Date**: 2026-04-10

## 🛠️ Work Completed

### 1. Swimmer Environment Porting
- Integrated `Safety2x1SwimmerVelocity-v0` via `env/safety_gym/SwimmerWrapper.py`.
- Implemented **Discrete-to-Continuous action mapping** (9 discrete actions -> 2D continuous space) to maintain compatibility with the existing Dreamer controller.
- Verified observation parity with SafePO/MACPO baseline.

### 2. Safety Calibration (Horizon Scaling Fix)
- **Problem**: The agent was comparing a 15-step discounted imagination cost return (~2.5) against a 1000-step episode budget (25), causing the Lagrangian multiplier ($\lambda$) to stay at zero.
- **Solution**: Implemented **Horizon Scaling** in `agent/learners/DreamerLearner.py`.
- **Logic**: `scaled_limit = cost_limit * (effective_horizon / MAX_STEPS)`, where `effective_horizon = 1/(1-gamma) = 100`.
- **Result**: For Swimmer (limit 25, steps 1000), the scaled limit is **2.5**, allowing $\lambda$ to react to safety violations in imagination.

### 3. Pipeline Fixes
- **`train.py`**: Added `MAX_STEPS` configuration for both StarCraft and Safety Gym.
- **Run Names**: Implemented truncation (limit 120 chars) for WandB run names to avoid 400 Errors.
- **Debug Mode**: Enabled `debug=True` in `train_dreamer` when `n_workers=0` for easier local testing.

## 🛑 Where We Stopped
- **Logic Verification**: The scaling math was verified using `verify_scaling.py`.
- **Pilot Runs**: A local pilot was attempted but hit OOM (32GB RAM exhausted).
- **Cluster Submission**: Attempted to submit to `slurm.bgu.ac.il` but timed out.

## ⏭️ Future Steps
1. Push these changes to the remote branch once the cluster/network is stable.
2. Launch verification experiments using `sbatch_scripts/submit_experiments.py`.
