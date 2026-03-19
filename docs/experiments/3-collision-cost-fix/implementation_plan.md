# Implementation Plan: Collision Cost Fix

This plan uses a tiered approach to debug and fix the world model's cost-prediction branch.

## Phase 1: Lagrangian Reactivity (Baseline Fix)
- [ ] Update `configs/dreamer/DreamerAgentConfig.py` to allow a per-experiment `laglr`.
- [ ] Run a test with `laglr=1e-3` (keeping current sampling) to see if raw multiplier growth can force the policy before the model is fixed.
- [ ] **Verification**: Monitor `Agent/Lagrangian` for aggressive growth in response to cost > limit.

## Phase 2: Cost-Prioritized Sampling (The Core Fix)
- [ ] Modify `agent/memory/ReplayBuffer.py` (or equivalent) to implement cost-weighted sampling.
- [ ] Update `train.py` to pass a `cost_priority` flag to the sampler.
- [ ] **Verification**: Monitor `Model/Predicted_average_cost` in WandB. Success is defined as the model predicting > 15.0 when reality is > 20.0.

## Phase 3: World Model Capacity (Scaling Fix)
- [ ] If prediction is still poor, increase the `REWARD_HIDDEN` and `REWARD_LAYERS` specifically for the `cost_model` in `agent/models/DreamerModel.py`.
- [ ] **Verification**: Check for reduced `Loss/Cost` in training logs.

## Phase 4: Full Experiment Re-Run
- [ ] Submit the `8m` grid (5.0 and 10.0 limits) with both Phase 1 and Phase 2 active.
