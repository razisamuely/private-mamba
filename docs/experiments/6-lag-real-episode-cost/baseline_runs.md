# Experiment 6 — MACPO Baseline Runs

**Repo**: `Safe-Policy-Optimization-Modified` (cluster) / `Safe-Policy-Optimization` (local)  
**Branch**: main  
**Date**: 2026-04-20  
**Cluster**: `slurm.bgu.ac.il`  
**Config**: `collision`, `num-envs=5`, `total-steps=10M`, GPU keepalive enabled

## 3s_vs_3z

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17106427 |
| 0.0 | 2 | 17106428 |
| 0.0 | 3 | 17106430 |
| 0.5 | 1 | 17106431 |
| 0.5 | 2 | 17106432 |
| 0.5 | 3 | 17106434 |

**Status**: Submitted — 2026-04-20

## 8m — dead_allies_incremental

**Config**: `dead_allies_incremental`, `num-envs=5`, `total-steps=10M`, GPU keepalive enabled

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | ~~17208572~~ → ~~17208931~~ → 17209129 |
| 0.0 | 2 | ~~17208574~~ → ~~17208947~~ → 17209130 |
| 0.0 | 3 | ~~17208575~~ → ~~17208963~~ → 17209131 |

**Status**: Submitted — 2026-04-26 (resubmitted as dead_allies_incremental)

## bane_vs_bane — dead_allies_incremental

**Config**: `dead_allies_incremental`, `num-envs=5`, `total-steps=10M`, GPU keepalive enabled

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17209132 |
| 0.0 | 2 | 17209133 |
| 0.0 | 3 | 17209134 |

**Status**: Submitted — 2026-04-26

## bane_vs_bane — collision

**Config**: `collision`, `num-envs=5`, `total-steps=10M`, GPU keepalive enabled

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17209729 |
| 0.0 | 2 | 17209730 |
| 0.0 | 3 | 17209731 |

**Status**: Submitted — 2026-04-26

## 3s_vs_5z — dead_allies_incremental

**Config**: `dead_allies_incremental`, `num-envs=5`, `total-steps=10M`, GPU keepalive enabled

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17209699 |
| 0.0 | 2 | 17209700 |
| 0.0 | 3 | 17209701 |

**Status**: Submitted — 2026-04-26

## 3s5z_vs_3s6z

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17136805 |
| 0.0 | 2 | 17136806 |
| 0.0 | 3 | 17136807 |

**Status**: Submitted — 2026-04-23

## MMM

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17177172 |
| 0.0 | 2 | 17177173 |
| 0.0 | 3 | 17177174 |

**Status**: Submitted — 2026-04-25

## MMM — dead_allies_incremental

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | ~~17198324~~ → 17203401 |
| 0.0 | 2 | ~~17198325~~ → 17203412 |
| 0.0 | 3 | ~~17198327~~ → ~~17203413~~ → 17208987 |

**Status**: Submitted — 2026-04-26 (seed 3 resubmitted with qos=razshmue)
