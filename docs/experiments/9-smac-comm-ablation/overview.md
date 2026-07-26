# Experiment 9 — SMAC Communication Ablation

## Goal

Test whether inter-agent communication (cross-agent attention in RSSMTransition)
helps SafeDreamer on SMAC, mirroring the MAMuJoCo ablation (Experiment 8 Phase 5).

## Background

- Communication is blocked via `nn_mask = ~torch.eye(n_agents)` (True = blocked
  in PyTorch attention) — each agent attends only to itself.
- `--comm_mode none` flag added in Exp 8; wired for SMAC in `train.py`
  (`prepare_starcraft_configs` sets `config.COMM_MODE`).
- MAMuJoCo finding: comm helps 2-agent envs a lot; no benefit with 4 small agents.

## Hypothesis

- **8m** (8 homogeneous marines): comm may matter little (like Ant 4x2).
- **MMM** (10 heterogeneous units incl. Medivac): comm should matter more —
  role coordination (healing, focus fire).

## Setup

| Item | Value |
|------|-------|
| Branch | `fix/comm-mask-inversion` (contains exp-6 episode-cost logic — 1ef8faa is ancestor) |
| Maps | 8m, MMM |
| Cost type | dead_allies_incremental |
| Cost limit | 0.0 |
| laglr | 1e-5 |
| Seeds | 1, 2, 3 |
| comm_mode | none |
| Jobs | 6 |

## Baselines (full comm, Experiment 6)

From `docs/experiments/6-lag-real-episode-cost/` (`wandb_runs.json` has run IDs):

| Map | Slurm IDs |
|-----|-----------|
| 8m | 17209123, 17209124, 17209125 |
| MMM | 17198319, 17198320, 17198321 |

## Status

6 no-comm jobs submitted 2026-07-25 (Slurm 19539781-787), 5 running + 1 pending.
Local smoke test passed, logs confirmed `comm_mode=none, action_type=discrete`.
Waiting for completion → extract → compare.

Possible expansion (not yet submitted): 3s_vs_3z (3 agents, c=0.0 + c=0.5) and
3s5z_vs_3s6z (8 agents, c=0.0) — 9 more jobs, baselines exist in Exp 6.
