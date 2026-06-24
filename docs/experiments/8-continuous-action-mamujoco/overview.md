# Experiment 8: Continuous Action SafeDreamer on MAMuJoCo

## Goal

Validate SafeDreamer with continuous Gaussian policy on multi-agent MuJoCo environments.
Compare against MACPO baselines from Experiment 7.

## Background

- Experiment 7 (`feat/swimmer-baseline-comparison`) ran discrete SafeDreamer vs MACPO.
  SafeDreamer failed on all envs (crashed ~1M steps, cost ~430 vs limit 25).
- Branch `feat/continuous-action-support` added Gaussian policy (Normal + tanh squash).
- Initial runs showed policy collapse at ~55k steps (entropy death).
- Branch `fix/tanh-logprob-correction` fixed root cause: PPO log-prob was evaluated at
  tanh-squashed action instead of pre-tanh sample, breaking the importance ratio.
- Local pilot: HalfCheetah reward ~1170, no collapse.

## Environments

| Env Name | Agents | Actions/Agent | Obs Dim |
|----------|--------|---------------|---------|
| Safety2x3HalfCheetahVelocity-v0 | 2 | 3 | 19 |
| Safety2x4AntVelocity-v0 | 2 | 4 | 29 |
| Safety4x2AntVelocity-v0 | 4 | 2 | 31 |

Note: `Safety2x3AntVelocity-v0` doesn't exist (invalid partitioning).

## Config

Baseline config from `fix/tanh-logprob-correction`:
- actor_lr=3e-5, model_lr=1e-4, value_lr=1e-4
- grad_clip=10, grad_clip_policy=5
- ppo_epochs=5, epochs=4, horizon=15
- cost_limit=25, lagrangian_lr=1e-5

## MACPO Baselines (from Experiment 7)

| Env | Reward (10M steps) | Cost |
|-----|-------------------|------|
| HalfCheetah 2x3 | 1314-1435 | 19-25 |
| Ant 2x4 | 921-1142 | 13-17 |

## Status

See `runs.md` for job tracking.
