# Experiment 11 — Runs

**Branch**: `feat/thesis-experiments`

**Submission**: local `~/workspace/Safe-Policy-Optimization/sbatch_scripts/submit_baseline.py`
with `--template sbatch_scripts/template_mappolag_smac.sbatch --cost_type dead_allies_incremental`
(5M steps, CPU partition). Incremental: one map+limit (3 seeds) per batch,
user approval before each batch.

## Task 1: MAPPO-Lag — missing SMAC maps (easy → hard)

Planned order: 3m → 2s_vs_1sc → 2s3z → 3s_vs_3z → 3s_vs_4z → 3s_vs_5z →
1c3s5z c=4 → MMM → 3s5z_vs_3s6z → (bane_vs_bane after mem fix).

### Batch 1: 3m c=0.0 (submitted 2026-09-01)

| # | Map | Cost Limit | Seed | Slurm ID | Status |
|---|-----|-----------|------|----------|--------|
| 1 | 3m | 0.0 | 1 | 20816199 | RUNNING (verified healthy) |
| 2 | 3m | 0.0 | 2 | 20816200 | RUNNING (verified healthy) |
| 3 | 3m | 0.0 | 3 | 20816202 | RUNNING (verified healthy) |
