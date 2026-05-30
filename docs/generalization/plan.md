# Technical Plan: Generalization to Swimmer Environment

> [!NOTE]
> **Definition of Done (DoD)**: This plan is "Done" when the `Safety2x1SwimmerVelocity-v0` environment is fully integrated into Safe Dreamer, and a **Pilot Run** (single seed) has successfully logged data to WandB. This plan covers **Integration & Verification**, not full experimental comparisons.

## 🎯 Goal
Generalize Safe Dreamer (private-mamba) to support non-StarCraft multi-agent environments from the SafePO library, starting with the simplest one: **Swimmer**.

## 🚀 Target
The target of this plan is to establish the **architectural plumbing** for MuJoCo support in Safe Dreamer:
- **Architecture Generalized**: Update Safe Dreamer to load and interact with `Safety-Gymnasium` environments.
- **Environment Verified**: Confirm that reward/cost signals are correctly processed in a continuous physics environment.
- **Ready for Experiments**: Ensure `sbatch` generation works for the new environment, enabling future comparison grids.

## 📋 Task Checklist

### Phase A: Draft & Integration
- [x] Create `docs/generalization/draft.md` (Grid & Requirements)
- [x] Create `docs/generalization/integration_plan.md` (File mapping & hooks)

### Phase B: Implementation (Phased)
- [x] **Phase 1: Skeleton**
    - [x] Create dummy `env/safety_gym/` wrapper.
    - [x] Wire it into `train.py`.
    - [x] Run **Skeleton Run** (0 steps) to verify `sbatch` generation and sync.
- [x] **Phase 2: Logic & Verification**
    - [x] Implement full `SwimmerWrapper` logic.
    - [x] Verify reward/cost scales against MACPO baseline.
    - [x] Run **Pilot Run** (single seed) to verify data flow.

### Phase C: Refinement & Integration
- [x] **Metric Alignment**: Update `DreamerWorker.py` to use `total_episode_reward` instead of Win-Flag for `SAFETY_GYM` envs.
- [ ] **Code Refactoring**: Clean up `train.py` dynamic initialization and move to helpers.
- [ ] **Submission Setup**: Verify `sbatch` generation works for the cluster with the new environment.
- [ ] **Full Pilot**: Run 10k steps and verify WandB logging.

## 🏗️ Implementation Details

### Environment: `Safety2x1SwimmerVelocity-v0`
- **Agents**: 2
- **Goal**: Locomotion speed (Reward) + Safety (Cost)
- **Scale**: Needs verification against SD's 15-step horizon.

### Phase D: Safety Calibration (CRITICAL)
- [ ] **Cost Scaling**: Fix the mismatch between 15-step imagination cost and 1000-step episode limit in `DreamerLearner.py`.
- [ ] **Verification**: Verify that $\lambda$ (Lagrangian multiplier) increases when the agent violates safety in pilot runs.

---

## 📈 Progress Log

- **2026-03-24 (Step 2081)**: Identified "Scale Mismatch" bug: The agent compares a 15-step cost against a 1000-step budget. Designing a fix to normalize the `cost_limit` in the learner.
- **2026-03-24**: Initial plan created and branch `feat/generalization-swimmer-port` initialized in `private-mamba`.
