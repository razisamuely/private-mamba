# Integration Plan: Generalization to Swimmer

## Hooks & Modifications

### 1. `train.py`
- Add import for `SwimmerWrapper`.
- Update `prepare_safety_gym_configs` to use the new wrapper.
- Ensure `--env safety_gym` and `--env_name Safety2x1SwimmerVelocity-v0` are handled.

### 2. `agent/workers/DreamerWorker.py`
- Verify reward/cost extraction for the new environment.
- (Initial check shows it uses `info['cost']`, which matches our wrapper's structure).

### 3. `env/safety_gym/SwimmerWrapper.py` [NEW]
- Implement full `step()` and `reset()` logic for MuJoCo.
- Handle agent observation conversion.

### 4. Safety Constraint Calibration: Horizon Scaling [Upcoming]
- **Bug**: The agent compares a 15-step imagination cost against a 1000-step episode budget.
- **Fix**: Normalize the `cost_limit` in `DreamerLearner.py` using `scaled_limit = limit * (HORIZON / MAX_STEPS)`.
- **Impact**: Ensures the Lagrangian multiplier ($\lambda$) increases when the agent violates safety in its short imagination window.

## Cluster Sync
- Sync the new `env/safety_gym/` folder to the cluster via the submission archive.
- Ensure `safety-gymnasium` is available on the remote SLURM nodes.
