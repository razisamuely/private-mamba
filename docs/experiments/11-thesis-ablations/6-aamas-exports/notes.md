# 6-aamas-exports — runs and data for the AAMAS 2027 revision

**Date**: 2026-10-04. Branch `feat/aamas-8m-ablation` (off `feat/pid-lagrangian`).

## Why

The SMAC casualty-cost results in the paper (runs Oct 2025 – Jan 2026, code `4311bf0`) updated
the multiplier from `cost_returns.mean()`, the mean *imagined* per-step cost return
(`DreamerLearner.py:283` at that commit). The paper's Eq. 5 describes the *measured* episode-cost
update, which entered on 2026-04-10/11 (`6c05450`, `1ef8faa`) and is what the MAMuJoCo and PID runs
use. The 8m runs below put four multiplier rules on the current code, next to the old runs.

## New runs (8m, d=4, seeds 1-3, stop at 105k env steps)

| Arm | Flags |
|---|---|
| Measured-cost basic dual | `--laglr 1e-5` |
| PID dual | `--lag_mode pid --pid_kp 1.0 --pid_ki 1e-5 --pid_kd 1.0` |
| Fixed penalty, lambda = 1 | `--laglr 0 --lag_init 1.0` |
| Cost-blind, lambda = 0 | `--laglr 0 --lag_init 0.0` |

Advantages are normalized to unit std (`NORMALIZE_ADVANTAGE=True`), so lambda = 1 weights
reward and cost advantages equally.

## Exports (`export_histories.py`, output in `csv/<group>/`)

| Group | Selection | Purpose |
|---|---|---|
| `pid_mamujoco` | regex `Velocity-v0_s[0-9]+_pid_` | PID at tight MAMuJoCo limits |
| `basic_mamujoco_tight` | regex `_lag(1e-05\|0.0001)_(0.2\|1.0\|5.0)_Safety` | basic-dual baselines for the same limits |
| `smac_8m_old` | `ids_smac_8m_old.txt` | check that beta stayed ~0 at d=4 under the old update |
| `smac_training_cost` | `ids_smac_training_cost.txt` (`--skip-lag`) | cost paid during the first 100k interactions, CA-MAMBA vs MACPO vs MAPPO-Lag |
| `smac_8m_new` | regex `_4.0_8m_s[123].*_feat-aamas` | the 12 new runs |

The id lists are generated from the paper repo's `data/new_experiments_tracking_100k.csv` and
`1-mappo-lag-all-envs/csv/mappolag_smac_per_seed_100k.csv`.

## Status

- [x] `--lag_init`, `--max_steps` + tests (9 passed); dry-run sbatch files checked for all four arms
- [ ] 12 jobs submitted
- [ ] exports committed
