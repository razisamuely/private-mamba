# 7-aamas-8m-ablation — 8m multiplier ablation for AAMAS 2027 revision

**Date**: 2026-10-04. Branch `feat/aamas-8m-ablation`.
**GitHub issue**: [#3](https://github.com/razisamuely/private-mamba/issues/3)

## Why

The SMAC runs in the paper (Oct 2025 – Jan 2026) updated the multiplier from imagined cost.
The paper describes measured cost (entered Apr 2026). This ablation puts 5 multiplier rules
on 8m d=4 under the current code to compare.

## Arms (8m, d=4, seeds 1-3, --max_steps 105000)

| Arm | Flags |
|---|---|
| Measured-cost basic dual | `--laglr 1e-5` |
| PID dual | `--lag_mode pid --pid_kp 1.0 --pid_ki 1e-5 --pid_kd 1.0` |
| Fixed penalty λ=1 | `--laglr 0 --lag_init 1.0` |
| Cost-blind λ=0 | `--laglr 0 --lag_init 0.0` |
| Imagined-cost basic dual | `--laglr 1e-5 --lag_signal imagined` |

## Slurm IDs (submitted 2026-10-04)

| Arm | Slurm IDs | Status |
|---|---|---|
| Measured-cost basic | 22156904, 22156905, 22156906 | RUNNING |
| PID | 22156909, 22156910, 22156912 | 3/3 COMPLETED |
| Fixed λ=1 | 22156913, 22156917, 22156918 | 1/3 COMPLETED, 2 RUNNING |
| Cost-blind λ=0 | 22156920, 22156922, 22156923 | RUNNING |
| Imagined-cost basic | 22156924, 22156926, 22156927 | RUNNING (started late, were queued) |

## MAPPO-Lag tight-limit MAMuJoCo (10M steps, seeds 1-3)

| Env | d | Slurm IDs | Status |
|---|---|---|---|
| Ant 2x4 | 0.2 | 22157940, 22157941, 22157942 | partially COMPLETED |
| Ant 4x2 | 1.0 | 22157945, 22157946, 22157947 | RUNNING |
| HC 2x3 | 5.0 | 22157832, 22157833, 22157939 | 3/3 COMPLETED |

## Auto-stop (`--max_steps 105000`)

Confirmed working. PID arm stopped at ~105k env steps. Stdout `Samples` runs slightly
ahead of `cur_steps` (WandB `steps`) due to worker buffering — use WandB `steps` as ground truth.

## Paper table swap (measured-cost data)

- Filled 37 empty d>0 rows in `safe_dreamers_runs_adapted.csv`
- Verified multi-step table (`dead_allies_all_steps.csv`) already had correct measured-cost values
- Swapped paper input CSV (`overleaf/thesis/data/new_experiments_tracking_100k.csv`)
- Regenerated `full_results.tex`, `representative_results.tex`, `main_results.tex`
- Updated prose (abstract + experiments): 23→24 winrate, 17/16→18/18 vs 5M, 5→6 feasible, eight→ten
- Committed and pushed to thesis repo (`737e5a6`)

## Status

- [x] 15 SMAC 8m jobs submitted, verified alive
- [x] 9 MAPPO-Lag jobs submitted
- [x] `--max_steps` auto-stop confirmed
- [x] Paper tables swapped to measured-cost data
- [x] Paper prose updated with new aggregate counts
- [ ] All jobs completed
- [ ] Exports (`export_histories.py`) run
- [ ] Exports committed
