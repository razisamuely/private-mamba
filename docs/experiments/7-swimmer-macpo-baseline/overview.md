# Experiment 7 — Multi-Env Baseline Comparison

**Goal**: SafeDreamer vs MACPO on MAMuJoCo environments. Previous MACPO run on Swimmer (cost_limit=1) failed to converge. SafeDreamer converged.

**Envs**:
- `Safety2x1SwimmerVelocity-v0` (simplest, 2 agents × 1 joint, 2D)
- `Safety2x3HalfCheetahVelocity-v0` (2 agents × 3 joints, 2D)
- `Safety2x4AntVelocity-v0` (2 agents × 4 joints, 3D)

**Branch**: `feat/swimmer-baseline-comparison` (private-mamba), `feat/collision-cost-comparison` (SafePO)
**Seeds**: 1, 2 (HalfCheetah/Ant), 1, 2, 3 (Swimmer)
**Cost limits**: 25, 10 (Swimmer), 25 (HalfCheetah/Ant)

## Paper Reference (MACPO, arXiv:2110.02793)

- Tested on HalfCheetah (2x3, 3x2, 6x1) and Ant (2x3, 3x2, 6x1, 2x4d, 4x2) — **no Swimmer**
- Upstream default `cost_limit: 25` (`safepo/multi_agent/marl_cfg/macpo/config.yaml`, commit before our changes)
- Cost is binary per-step (c_t = 0 or 1) based on distance threshold from origin
- Convergence around 800k–1M steps (x-axis to 1M)
- Our config.yaml shows `cost_limit: 0` but that was changed by us (commit `2d4ccec`), original upstream was 25

## Fixes Required

1. `train.py` — switched import from `SafetyGymWrapper` to `SwimmerWrapper` (old wrapper had env registration error)
2. `train.py` — dynamic `IN_DIM`/`ACTION_SIZE` from env (was hardcoded 152/9)

## Config

**MACPO** (upstream defaults for mamujoco):

| Param | Swimmer | HalfCheetah / Ant |
|-------|---------|-------------------|
| cost_limit | 25, 10 | 25 |
| n_rollout_threads | 10 | 10 |
| num_env_steps | 10M | 10M |
| episode_length | 1000 | 1000 |
| partition | CPU | CPU |

**SafeDreamer**:

| Param | Swimmer | HalfCheetah / Ant |
|-------|---------|-------------------|
| cost_limit | 25, 10 | 25 |
| laglr | 1e-05 | 1e-05 |
| n_workers | 4 | 4 |
| partition | rtx3090 (GPU) | rtx3090 (GPU) |

## Prior Runs

| Algo | Run | Cost Limit | Status |
|------|-----|-----------|--------|
| SafeDreamer | `safedreamer_..._s23_date03-25-hr21-09-13` | 25 | Converged |
| MACPO | `safepo_macpo_..._cost_limit=1.0_...` | 1 | Failed |

## Cluster State

| Repo | Branch | Up to date |
|------|--------|-----------|
| `workspace/private-mamba` | `feat/swimmer-baseline-comparison` | Yes |
| `workspace/Safe-Policy-Optimization-Modified` | `feat/collision-cost-comparison` | Yes (sbatch files SCPed) |
