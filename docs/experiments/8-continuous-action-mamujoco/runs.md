# Experiment 8 — Runs

**Branch**: `fix/tanh-logprob-correction`

**Note**: All Phase 1-3 SafeDreamer runs use `laglr=1e-5` (default).
Phase 4 tests `laglr=1e-4`.

## Phase 1: HalfCheetah (fix validation + config sweep, cost_limit=25, laglr=1e-5)

### Pre-fix runs (branch `feat/continuous-action-support`) — COLLAPSED

All runs spiked at ~50k steps then collapsed permanently. Root cause: log-prob evaluated at
tanh(u) instead of u.

| # | Config | Seed | Slurm ID | Status | Peak Score |
|---|--------|------|----------|--------|------------|
| 1 | Baseline | 1 | 18077498 | COLLAPSED | +123 |
| 2 | Baseline | 2 | 18077499 | COLLAPSED | -30 |
| 3 | ppo_epochs=2 | 1 | 18077500 | COLLAPSED | +2 |
| 4 | ppo=2 ep=2 | 1 | 18077501 | COLLAPSED | -487 |
| 5 | ppo_epochs=3 | 1 | 18077506 | COLLAPSED | +49 |
| 6 | gcp=1.0 | 1 | 18077510 | COLLAPSED | +364 |
| 7 | alr=1e-4 | 1 | 18077511 | COLLAPSED | -47 |

### Post-fix runs (branch `fix/tanh-logprob-correction`)

| # | Env | Config | Seed | Slurm ID | Status |
|---|-----|--------|------|----------|--------|
| 1 | HC 2x3 | Baseline | 1 | 18174008 | DONE (crashed ~33M, score 2560) |
| 2 | HC 2x3 | Baseline | 2 | 18174009 | DONE (crashed ~34M, score 2212) |
| 3 | HC 2x3 | Baseline | 3 | 18174010 | DONE (crashed ~33M, score 2387) |
| 4 | HC 2x3 | ppo_epochs=2 | 1 | 18174011 | DONE |
| 5 | HC 2x3 | ppo=2 ep=2 | 1 | 18174012 | DONE |
| 6 | HC 2x3 | ppo_epochs=3 | 1 | 18174013 | DONE |
| 7 | HC 2x3 | gcp=1.0 | 1 | 18174014 | DONE |
| 8 | HC 2x3 | alr=1e-4 | 1 | 18174015 | DONE |

## Phase 2: Ant + MACPO baselines (cost_limit=25, laglr=1e-5)

### SafeDreamer GPU

| # | Env | Seed | Slurm ID | Status |
|---|-----|------|----------|--------|
| 9 | Ant 2x4 | 1 | 18362835 | DONE |
| 10 | Ant 2x4 | 2 | 18362836 | DONE |
| 11 | Ant 2x4 | 3 | 18362838 | DONE |
| 12 | Ant 4x2 | 1 | 18362839 | DONE |
| 13 | Ant 4x2 | 2 | 18362840 | DONE |
| 14 | Ant 4x2 | 3 | 18362841 | DONE |

### MACPO CPU (cost_limit=25)

| # | Env | Seed | Slurm ID | Status |
|---|-----|------|----------|--------|
| 15 | Ant 2x4 | 1 | 18366191 | DONE |
| 16 | Ant 2x4 | 2 | 18366192 | DONE |
| 17 | Ant 2x4 | 3 | 18366193 | DONE |
| 18 | Ant 4x2 | 1 | 18366194 | DONE |
| 19 | Ant 4x2 | 2 | 18366195 | DONE |
| 20 | Ant 4x2 | 3 | 18366196 | DONE |

## Phase 3: Paper Cost Limits (Ant 2x4=0.2, Ant 4x2=1.0, HC 2x3=5.0, laglr=1e-5)

Source: MACPO repo (github.com/chauncygu/Multi-Agent-Constrained-Policy-Optimisation).

### SafeDreamer GPU

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 21 | Ant 2x4 | 0.2 | 1 | 18367088 | DONE |
| 22 | Ant 2x4 | 0.2 | 2 | 18367089 | DONE |
| 23 | Ant 2x4 | 0.2 | 3 | 18367091 | DONE |
| 24 | Ant 4x2 | 1.0 | 1 | 18367092 | DONE |
| 25 | Ant 4x2 | 1.0 | 2 | 18367096 | DONE |
| 26 | Ant 4x2 | 1.0 | 3 | 18367097 | DONE |
| 27 | HC 2x3 | 5.0 | 1 | 18367101 | DONE |
| 28 | HC 2x3 | 5.0 | 2 | 18367102 | PENDING (GPU queue) |
| 29 | HC 2x3 | 5.0 | 3 | 18367104 | PENDING (GPU queue) |

### MACPO CPU

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 30 | Ant 2x4 | 0.2 | 1 | 18367114 | DONE |
| 31 | Ant 2x4 | 0.2 | 2 | 18367115 | DONE |
| 32 | Ant 2x4 | 0.2 | 3 | 18367116 | DONE |
| 33 | Ant 4x2 | 1.0 | 1 | 18367117 | DONE |
| 34 | Ant 4x2 | 1.0 | 2 | 18367136 | DONE |
| 35 | Ant 4x2 | 1.0 | 3 | 18367137 | DONE |
| 36 | HC 2x3 | 5.0 | 1 | 18367138 | DONE |
| 37 | HC 2x3 | 5.0 | 2 | 18367143 | DONE |
| 38 | HC 2x3 | 5.0 | 3 | 18367144 | DONE |

### MACPO HC c=25 (from Experiment 7, May 2026)

| # | Env | CL | Seed | Status |
|---|-----|----|------|--------|
| 39 | HC 2x3 | 25 | 1 | DONE (URL encoding issue in extraction) |
| 40 | HC 2x3 | 25 | 2 | DONE (URL encoding issue in extraction) |
| 41 | HC 2x3 | 25 | 3 | DONE (URL encoding issue in extraction) |

## Phase 4: Lagrangian LR sweep (laglr=1e-4)

All Phase 1-3 SafeDreamer runs used laglr=1e-5 (default, very slow to react to cost violations).
Phase 4 tests laglr=1e-4 (10x faster). MACPO baselines unchanged — reuse Phase 2-3 results.

### SafeDreamer GPU (paper cost limits, laglr=1e-4)

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 42 | Ant 2x4 | 0.2 | 1 | 18505909 | DONE |
| 43 | Ant 2x4 | 0.2 | 2 | 18505912 | DONE |
| 44 | Ant 2x4 | 0.2 | 3 | 18505915 | DONE |
| 45 | Ant 4x2 | 1.0 | 1 | 18505918 | DONE |
| 46 | Ant 4x2 | 1.0 | 2 | 18505920 | DONE |
| 47 | Ant 4x2 | 1.0 | 3 | 18505923 | DONE |
| 48 | HC 2x3 | 5.0 | 1 | 18505924 | DONE |
| 49 | HC 2x3 | 5.0 | 2 | 18505925 | DONE |
| 50 | HC 2x3 | 5.0 | 3 | 18505926 | DONE |

### SafeDreamer GPU (cost_limit=25, laglr=1e-4)

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 51 | Ant 2x4 | 25 | 1 | 18505927 | DONE |
| 52 | Ant 2x4 | 25 | 2 | 18505928 | DONE |
| 53 | Ant 2x4 | 25 | 3 | 18505929 | DONE |
| 54 | Ant 4x2 | 25 | 1 | 18505930 | DONE |
| 55 | Ant 4x2 | 25 | 2 | 18505931 | DONE |
| 56 | Ant 4x2 | 25 | 3 | 18505932 | DONE |
| 57 | HC 2x3 | 25 | 1 | 18505933 | DONE |
| 58 | HC 2x3 | 25 | 2 | 18505934 | DONE |
| 59 | HC 2x3 | 25 | 3 | 18505935 | DONE |

## Phase 5: Communication ablation (comm_mode=none, laglr=1e-5)

**Branch**: `fix/comm-mask-inversion`

All Phase 1-4 runs used full communication (nn_mask=None, all agents attend to all).
Phase 5 blocks all cross-agent attention (nn_mask=~eye, each agent attends only to itself).

### INVALID runs (wrong mask: eye instead of ~eye, cancelled)

Slurm 19063225-19063243 — used `torch.eye().bool()` which blocks self-attention
and allows cross-agent (opposite of intended). Killed and resubmitted with fix.

### SafeDreamer GPU (paper cost limits, no comm, laglr=1e-5)

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 60 | Ant 2x4 | 0.2 | 1 | 19122709 | RUNNING |
| 61 | Ant 2x4 | 0.2 | 2 | 19122710 | RUNNING |
| 62 | Ant 2x4 | 0.2 | 3 | 19122711 | RUNNING |
| 63 | Ant 4x2 | 1.0 | 1 | 19122712 | RUNNING |
| 64 | Ant 4x2 | 1.0 | 2 | 19122713 | RUNNING |
| 65 | Ant 4x2 | 1.0 | 3 | 19122715 | RUNNING |
| 66 | HC 2x3 | 5.0 | 1 | 19122716 | RUNNING |
| 67 | HC 2x3 | 5.0 | 2 | 19122717 | RUNNING |
| 68 | HC 2x3 | 5.0 | 3 | 19122718 | PENDING |

### SafeDreamer GPU (cost_limit=25, no comm, laglr=1e-5)

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 69 | Ant 2x4 | 25 | 1 | 19122719 | PENDING |
| 70 | Ant 2x4 | 25 | 2 | 19122720 | PENDING |
| 71 | Ant 2x4 | 25 | 3 | 19122721 | PENDING |
| 72 | Ant 4x2 | 25 | 1 | 19122722 | PENDING |
| 73 | Ant 4x2 | 25 | 2 | 19122723 | PENDING |
| 74 | Ant 4x2 | 25 | 3 | 19122724 | PENDING |
| 75 | HC 2x3 | 25 | 1 | 19122725 | PENDING |
| 76 | HC 2x3 | 25 | 2 | 19122726 | PENDING |
| 77 | HC 2x3 | 25 | 3 | 19122728 | PENDING |

## Extraction Pipeline

- Input CSV: `docs/tmp/extraction/inputs/mamujoco_runs_experiment8.csv`
- Pipeline: `docs/tmp/extraction/scripts/mamujoco_pipeline_experiment8.py`
- Output: `docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table.pdf`
- Backup: `comparison_table_real_20260628_144800.csv`
