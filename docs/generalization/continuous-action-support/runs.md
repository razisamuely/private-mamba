# Cluster Runs — Continuous Action HalfCheetah Sweep

**Env**: `Safety2x3HalfCheetahVelocity-v0`
**Branch**: `feat/continuous-action-support`
**Base config**: actor_lr=3e-5, model_lr=1e-4, value_lr=1e-4, grad_clip=10, grad_clip_policy=5, cost_limit=25

## Jobs

| # | Config | Seed | Slurm ID | WandB Run | Status |
|---|--------|------|----------|-----------|--------|
| 1 | Baseline | 1 | 18077498 | | RUNNING |
| 2 | Baseline | 2 | 18077499 | | RUNNING |
| 3 | ppo_epochs=2 | 1 | 18077500 | | RUNNING |
| 4 | ppo_epochs=2, epochs=2 | 1 | 18077501 | | RUNNING |
| 5 | ppo_epochs=3 | 1 | 18077506 | | RUNNING |
| 6 | grad_clip_policy=1.0 | 1 | 18077510 | | RUNNING |
| 7 | actor_lr=1e-4 | 1 | 18077511 | | RUNNING |

Note: Earlier submissions (18077320-327, 18077351-363, 18077412-419) failed due to
plumbing bugs in the ray worker path (see draft.md "Ray Worker Fixes").

## Shared Config

| Param | Value |
|-------|-------|
| ACTION_TYPE | continuous |
| ACTOR_LR | 3e-5 (unless overridden) |
| MODEL_LR | 1e-4 |
| VALUE_LR | 1e-4 |
| GRAD_CLIP | 10.0 |
| GRAD_CLIP_POLICY | 5.0 |
| PPO_EPOCHS | 5 (unless overridden) |
| EPOCHS | 4 (unless overridden) |
| HORIZON | 15 |
| COST_LIMIT | 25.0 |
| LAGRANGIAN_LR | 1e-5 |
| USE_AVAILABLE_ACTIONS | False |
| partition | gpu (auto-assigned, no QOS) |

## Key Question

Does reducing PPO aggressiveness prevent the policy collapse seen at ~55 episodes locally?
