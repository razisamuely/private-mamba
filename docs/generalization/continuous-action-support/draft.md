# Continuous Action Support for SafeDreamer

**Branch**: `feat/continuous-action-support`
**Status**: Implemented, local pilot passed, cluster sweep running (7 jobs)

## Problem

Discrete 9-bin action mapping kills SafeDreamer on continuous MuJoCo envs:

| Env | MACPO (continuous) | SafeDreamer (discrete) |
|-----|-------------------|----------------------|
| HalfCheetah | reward ~1400 | reward ~-5 to +12, crashed ~1M steps |
| Ant | reward ~1000 | reward ~3 to +31, crashed ~0.5-1.8M steps |
| Swimmer | reward ~2 | reward ~-14 to +19, crashed ~1M steps |

Root causes: (1) only 9 coarse actions, (2) agent 1's action ignored, (3) cost/horizon scaling broken (separate issue).

## Implementation

Added `ACTION_TYPE` config flag. Branches at 10 code locations:

| File | Change |
|------|--------|
| `configs/dreamer/DreamerAgentConfig.py` | `ACTION_TYPE`, `ENV_TYPE` fields |
| `networks/dreamer/action.py` | Gaussian sampling with NaN guards, mean/std clamping |
| `agent/controllers/DreamerController.py` | Skip action masking, Gaussian exploration |
| `networks/dreamer/rnns.py` | `rollout_policy` branches on action_type |
| `agent/optim/loss.py` | `_continuous_actor_loss` with Normal log-prob PPO |
| `agent/optim/utils.py` | `info_loss` skipped for continuous (CrossEntropy incompatible) |
| `agent/workers/DreamerWorker.py` | Pass raw tensors to env, zero-pad terminals |
| `agent/learners/DreamerLearner.py` | Pass action_type to Actor |
| `agent/models/DreamerModel.py` | Store `_action_type` |
| `env/safety_gym/SwimmerWrapper.py` | Multi-env support (Swimmer/HalfCheetah/Ant), continuous mode |
| `train.py` | Dynamic obs/action dims, `USE_AVAILABLE_ACTIONS=False` |

**Unchanged**: RSSM, world model, memory buffer, observation encoder/decoder.

## NaN Fix (Critical)

Local pilot v1/v2 crashed at ~15-18 episodes with NaN in actor output. Fix:
- `torch.nan_to_num` guard on mean/log_std before Normal distribution
- `torch.clamp(mean, -10, 10)` and `torch.clamp(log_std, -5, 2)`
- Lower LRs: actor 3e-5 (was 5e-4), model 1e-4 (was 2e-4)
- Tighter grad clips: model 10.0 (was 100.0), policy 5.0 (was 100.0)

## Local Pilot Results

**v3** (HalfCheetah, CPU, seed 1): Stable 67 episodes, 67k steps.
- Reward improved -290 → +284 (peak ep 55)
- Policy collapsed after ep 55 (reward → -350), did not recover
- Collapse cause: PPO updates too aggressive (ppo_epochs=5)

**v4** (HalfCheetah, CPU, seed 1): Running, correct WandB metric names.
- WandB: `safedreamer_cont_v4_*` run ID `dlmk4fvc` / latest

## Local Test Results (all passed)

| Test | Result |
|------|--------|
| Actor continuous output shape | PASS |
| Tanh squash in [-1,1] (1000 samples) | PASS |
| Log-prob no NaN/Inf | PASS |
| PPO importance ratio | PASS |
| Worker passes continuous tensors | PASS |
| Discrete mode regression | PASS |
| HalfCheetah e2e (3 episodes, train+collect) | PASS |
| Ant e2e (50 steps) | PASS |
| Swimmer e2e (50 steps) | PASS |
| Obs dims per env (Swimmer:10, HC:19, Ant:29) | PASS |

## Cluster Experiment Plan

See `runs.md` for job tracking.

## Ray Worker Fixes (Cluster Only)

Three plumbing fixes needed for the ray worker path (not hit locally in single-process mode):

1. **`DreamerController.dispatch_buffer`**: `avail_action` buffer was a numpy array of `None`s
   instead of `None` when `USE_AVAILABLE_ACTIONS=False`. Fixed to return `None` directly.
2. **`DreamerMemory.append`**: `self.av_actions` is `None` when `use_available_actions=False`,
   but the guard only checked `av_action` (the input), not `self.av_actions` (the storage).
   Added `self.av_actions is not None` guard.
3. **`DreamerWorker.run`**: `cost` was gated on `USE_AVAILABLE_ACTIONS` — set to `None` for
   continuous envs, causing IndexError in memory. Cost should always be stored.

## Open Issues

1. ~~**Policy collapse**: PPO too aggressive~~ — **RESOLVED**: Root cause was evaluating
   `Normal.log_prob(tanh(u))` instead of `Normal.log_prob(u)` in `_continuous_actor_loss`.
   Fix in branch `fix/tanh-logprob-correction` (commit `da52869`). Local HalfCheetah
   climbs to ~1170 reward, no collapse. Cluster validation running (8 jobs).
2. **Horizon/Lagrangian scaling**: Not addressed here (separate from action type)
3. ~~**Wrapper naming**: `SwimmerWrapper` handles all envs~~ — **RESOLVED**: Renamed to `MAMuJoCoWrapper`.
