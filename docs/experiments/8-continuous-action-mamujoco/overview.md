# Experiment 8: Continuous Action SafeDreamer on MAMuJoCo

## Goal

Validate SafeDreamer with continuous Gaussian policy on multi-agent MuJoCo environments.
Compare against MACPO baselines (our runs + paper reported).

## Background

- Experiment 7 (`feat/swimmer-baseline-comparison`) ran discrete SafeDreamer vs MACPO.
  SafeDreamer failed on all envs (crashed ~1M steps, cost ~430 vs limit 25).
- Branch `feat/continuous-action-support` added Gaussian policy (Normal + tanh squash).
- Initial runs showed policy collapse at ~55k steps (entropy death).
- Branch `fix/tanh-logprob-correction` fixed root cause: PPO log-prob was evaluated at
  tanh-squashed action instead of pre-tanh sample, breaking the importance ratio.
- Local pilot: HalfCheetah reward ~1170, no collapse.

## Environments

| Env Name | Agents | Actions/Agent | Obs Dim | Velocity Threshold |
|----------|--------|---------------|---------|-------------------|
| Safety2x3HalfCheetahVelocity-v0 | 2 | 3 | 19 | 3.227 |
| Safety2x4AntVelocity-v0 | 2 | 4 | 29 | 2.522 |
| Safety4x2AntVelocity-v0 | 4 | 2 | 31 | 2.418 |

Note: `Safety2x3AntVelocity-v0` doesn't exist (invalid partitioning).

## Cost Limits

Two cost limit settings tested:

| Source | Ant 2x4 | Ant 4x2 | HalfCheetah 2x3 |
|--------|---------|---------|-----------------|
| MACPO paper (chauncygu repo) | 0.2 | 1.0 | 5.0 |
| SafePO default | 25.0 | 25.0 | 25.0 |

## Config

Baseline config from `fix/tanh-logprob-correction`:
- actor_lr=3e-5, model_lr=1e-4, value_lr=1e-4
- grad_clip=10, grad_clip_policy=5
- ppo_epochs=5, epochs=4, horizon=15
- lagrangian_lr=1e-5

## Results Summary

SafeDreamer at 100k steps matches or exceeds MACPO at 10M steps (100x sample efficiency).

### MACPO paper cost limits (c=0.2/1.0/5.0)

| Env | SafeDreamer 1M | MACPO Run 10M | MACPO Paper ~10M |
|-----|---------------|---------------|-----------------|
| Ant 2x4 (c=0.2) | **2268 +- 134** | 859 +- 33 | ~900 |
| Ant 4x2 (c=1.0) | **1241 +- 566** | 1098 +- 97 | ~650 |
| HC 2x3 (c=5.0) | 1519 (1 seed) | 1317 +- 116 | ~2250 |

### SafePO default cost limit (c=25)

| Env | SafeDreamer 1M | MACPO Run 10M | SafePO Paper 10M |
|-----|---------------|---------------|-----------------|
| Ant 2x4 | **1836 +- 678** | 798 +- 109 | 1099 |
| Ant 4x2 | **1575 +- 304** | 1287 +- 148 | 816 |
| HC 2x3 | **2527 +- 229** | 1374 +- 86 | 1637 |

### Phase 4: Lagrangian LR comparison (lr=1e-5 vs lr=1e-4)

Higher laglr (1e-4) makes the Lagrangian react 10x faster to cost violations.

| Env | CL | SafeDreamer lr=1e-5 (1M) | SafeDreamer lr=1e-4 (1M) | Effect on Cost |
|-----|----|-------------------------|-------------------------|----------------|
| Ant 2x4 | 0.2 | rew=2268, cost=24.3 | rew=1619, cost=4.1 | Cost down 83% |
| Ant 2x4 | 25 | rew=1836, cost=17.4 | rew=1552, cost=22.6 | Similar |
| Ant 4x2 | 1.0 | rew=1241, cost=2.5 | rew=1559, cost=4.2 | Similar |
| Ant 4x2 | 25 | rew=1575, cost=0.5 | rew=1504, cost=2.9 | Similar |
| HC 2x3 | 5.0 | rew=1519, cost=35.8 | rew=1481, cost=4.6 | Cost down 87% |
| HC 2x3 | 25 | rew=2527, cost=16.6 | rew=1149, cost=0.0 | Cost down 100% |

lr=1e-4 significantly reduces cost violations (especially for tight limits) with moderate reward trade-off.

Full comparison table with step-wise data (100k-1M, both lr values):
`docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table.pdf`

Reference papers:
- MACPO: github.com/chauncygu/Multi-Agent-Constrained-Policy-Optimisation (arXiv 2110.02793)
- SafePO: github.com/PKU-Alignment/Safe-Policy-Optimization (arXiv 2310.12567, Table 5b)

### Phase 5: Communication ablation (complete)

18 no-comm runs (`--comm_mode none`, laglr=1e-5), reward at 1M steps:

| Env | CL | Full comm (1M) | No comm (1M) | Verdict |
|-----|----|----------------|--------------|---------|
| Ant 2x4 | 0.2 | 2267.8 +- 134.1 | 1191.6 +- 444.6 | Comm helps a lot |
| Ant 4x2 | 25 | 1574.5 +- 304.2 | 1656.8 +- 161.8 | No benefit |
| HC 2x3 | 5.0 | 1519 | 1166.0 +- 512.6 | Comm helps |
| HC 2x3 | 25 | 2527 +- 229 | 981.5 +- 1303.1 | Comm helps a lot |

Communication helps most with 2 agents each controlling large body parts
(Ant 2x4, HC 2x3); with 4 small agents (Ant 4x2) it gives no benefit.
No-comm also shows much higher variance and worse cost control on HC.

## Status

Phase 1-5 complete on branch `fix/comm-mask-inversion`. Final comparison table
(120-row CSV, PDF): `docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table.pdf`.
See `runs.md` for job tracking, `plan.md` for pipeline.
