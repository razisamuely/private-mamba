# 6-aamas-exports — WandB history exports for the AAMAS 2027 revision

**Date**: 2026-10-04. Branch `feat/aamas-8m-ablation`.
**GitHub issue**: [#3](https://github.com/razisamuely/private-mamba/issues/3)

Runs, Slurm IDs, and job tracking moved to [`7-aamas-8m-ablation/notes.md`](../7-aamas-8m-ablation/notes.md).

## Exports (`export_histories.py`, output in `csv/<group>/`)

| Group | Selection | Purpose |
|---|---|---|
| `pid_mamujoco` | regex `Velocity-v0_s[0-9]+_pid_` | PID at tight MAMuJoCo limits |
| `basic_mamujoco_tight` | regex `_lag(1e-05\|0.0001)_(0.2\|1.0\|5.0)_Safety` | basic-dual baselines for the same limits |
| `smac_8m_old` | `ids_smac_8m_old.txt` | check that beta stayed ~0 at d=4 under the old update |
| `smac_training_cost` | `ids_smac_training_cost.txt` (`--skip-lag`) | cost paid during the first 100k interactions, CA-MAMBA vs MACPO vs MAPPO-Lag |
| `smac_8m_new` | regex `_4.0_8m_s[123].*_feat-aamas` | the 12 new runs |
| `macpo_mamujoco_tight` | regex `safepo_macpo_.*cost_limit=(0.2\|1.0\|5.0)_Safety` | MACPO at 1M on the tight limits (existing 10M runs) |
| `mappolag_mamujoco_tight` | regex `safepo_mappolag_.*cost_limit=(0.2\|1.0\|5.0)_Safety` | new MAPPO-Lag tight-limit runs (CPU, 9 jobs) |

The id lists are generated from the paper repo's `data/new_experiments_tracking_100k.csv` and
`1-mappo-lag-all-envs/csv/mappolag_smac_per_seed_100k.csv`.

## Data extraction

- [x] Fixed `wandb_config.py` project name (`anonymous/...` -> `raz-shmueli-corsound-ai/...`)
- [x] Filled 37 empty d>0 rows in `safe_dreamers_runs_adapted.csv` using `extract_metrics.py`
- [x] Verified: multi-step table already had correct measured-cost aggregated values (delta < 0.001)

## Status

- [ ] exports run
- [ ] exports committed
