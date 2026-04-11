# Experiment 6 — Submitted Runs

**Branch**: `feat/lag-real-episode-cost`  
**Date**: 2026-04-11  
**Cluster**: `slurm.bgu.ac.il`  
**Config**: `8m`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, seeds 1 & 2

## Submission Steps
1. Committed & pushed branch `feat/lag-real-episode-cost`
2. SSH to cluster: `git checkout feat/lag-real-episode-cost -f && git pull`
3. Submitted via `sbatch_scripts/submit_experiments.py`

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.1 | 1 | 16963067 |
| 0.1 | 2 | 16963068 |

**Status**: Pending
