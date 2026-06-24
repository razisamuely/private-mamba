# Experiment 8 — Runs

**Branch**: `fix/tanh-logprob-correction`

## Phase 1: HalfCheetah (fix validation + config sweep)

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

| # | Env | Config | Seed | Slurm ID | WandB Run | Status |
|---|-----|--------|------|----------|-----------|--------|
| 1 | HalfCheetah 2x3 | Baseline | 1 | 18174008 | | RUNNING |
| 2 | HalfCheetah 2x3 | Baseline | 2 | 18174009 | | RUNNING |
| 3 | HalfCheetah 2x3 | Baseline | 3 | 18174010 | | RUNNING |
| 4 | HalfCheetah 2x3 | ppo_epochs=2 | 1 | 18174011 | | PENDING |
| 5 | HalfCheetah 2x3 | ppo=2 ep=2 | 1 | 18174012 | | PENDING |
| 6 | HalfCheetah 2x3 | ppo_epochs=3 | 1 | 18174013 | | PENDING |
| 7 | HalfCheetah 2x3 | gcp=1.0 | 1 | 18174014 | | PENDING |
| 8 | HalfCheetah 2x3 | alr=1e-4 | 1 | 18174015 | | PENDING |

## Phase 2: Ant (baseline config, 3 seeds each)

Note: `Safety2x3AntVelocity-v0` doesn't exist (invalid partitioning).
Valid Ant configs: 2x4 (2 agents, 4 actions) and 4x2 (4 agents, 2 actions).

### GPU runs

| # | Env | Config | Seed | Slurm ID | WandB Run | Status |
|---|-----|--------|------|----------|-----------|--------|
| 9 | Ant 2x4 | Baseline | 1 | 18362835 | | SUBMITTED |
| 10 | Ant 2x4 | Baseline | 2 | 18362836 | | SUBMITTED |
| 11 | Ant 2x4 | Baseline | 3 | 18362838 | | SUBMITTED |
| 12 | Ant 4x2 | Baseline | 1 | 18362839 | | SUBMITTED |
| 13 | Ant 4x2 | Baseline | 2 | 18362840 | | SUBMITTED |
| 14 | Ant 4x2 | Baseline | 3 | 18362841 | | SUBMITTED |

### CPU runs

| # | Env | Config | Seed | Slurm ID | WandB Run | Status |
|---|-----|--------|------|----------|-----------|--------|
| 15 | Ant 2x4 | Baseline | 1 | 18362844 | | SUBMITTED |
| 16 | Ant 2x4 | Baseline | 2 | 18362845 | | SUBMITTED |
| 17 | Ant 2x4 | Baseline | 3 | 18362846 | | SUBMITTED |
| 18 | Ant 4x2 | Baseline | 1 | 18362847 | | SUBMITTED |
| 19 | Ant 4x2 | Baseline | 2 | 18362850 | | SUBMITTED |
| 20 | Ant 4x2 | Baseline | 3 | 18362852 | | SUBMITTED |
