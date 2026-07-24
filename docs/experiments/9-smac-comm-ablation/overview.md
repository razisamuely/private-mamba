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

Setup done: COMM_MODE wired for SMAC, local smoke test passed (comm_mode=none,
discrete actions, episodes ran). Jobs not yet submitted.
