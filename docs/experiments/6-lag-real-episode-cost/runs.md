# Experiment 6 — Submitted Runs

**Branch**: `feat/lag-real-episode-cost`  
**Date**: 2026-04-11  
**Cluster**: `slurm.bgu.ac.il`  
**Config**: `8m`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, seeds 1 & 2

## Submission Steps
1. Committed & pushed branch `feat/lag-real-episode-cost`
2. SSH to cluster: `git checkout feat/lag-real-episode-cost -f && git pull`
3. Submitted via `sbatch_scripts/submit_experiments.py`

| Cost Limit | Seed | Slurm ID | Notes |
|-----------|------|----------|-------|
| 0.1 | 1 | ~~16963067~~ → ~~16963070~~ → 16983660 | Resubmitted post-maintenance, 7d wall time |
| 0.1 | 2 | ~~16963068~~ → ~~16963071~~ → 16983661 | Resubmitted post-maintenance, 7d wall time |
| 0.1 | 3 | 16983662 | |
| 0.0 | 1 | 16983654 | Baseline (no constraint) |
| 0.0 | 2 | 16983658 | Baseline (no constraint) |
| 0.0 | 3 | 16983659 | Baseline (no constraint) |

| 0.5 | 1 | 16983666 | |
| 0.5 | 2 | 16983667 | |
| 0.5 | 3 | 16983668 | |

**Status**: All 9 jobs submitted — 2026-04-14
