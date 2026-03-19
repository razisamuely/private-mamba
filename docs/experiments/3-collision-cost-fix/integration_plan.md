# Integration Plan: Collision Cost Fix

## 1. Replay Buffer Modification
Target File: `agent/memory/PrioritizedReplay.py` (or similar)
- Logic: Add a secondary weight based on `info['cost']`.
- Integration: Ensure `SafeDreamer` can toggle this weight during the world model update.

## 2. Configuration Injection
Target File: `configs/dreamer/DreamerAgentConfig.py`
- Add `COST_PRIORITY_RATIO: float = 0.15`.
- Add `LAGRANGIAN_LR: float = 1e-3`.

## 3. Trainer Logic
Target File: `agent/learners/DreamerLearner.py`
- Ensure the `lagrange.update()` call is using a batch that includes prioritized samples.
- Verify that the cost loss is logging correctly to help debug prediction errors.

## 4. Automation update
Target File: `sbatch_scripts/submit_experiments.py`
- Update the parameters to include the new Fix experiment branch.

## 5. Cluster Sync Protocol (Mandatory)
Before submitting jobs via `submit_experiments.py`, the following workflow **must** be followed:
1. **Push**: All local code changes must be committed and pushed to the current branch (`feat/issue-2-collision-cost-fix`).
2. **Pull**: SSH into the BGU cluster and run `git checkout [branch]` and `git pull`.
3. **Reasoning**: The submission script only uploads the `.sbatch` configuration, not the actual Python logic. Failure to sync the cluster codebase will result in jobs running old code.
