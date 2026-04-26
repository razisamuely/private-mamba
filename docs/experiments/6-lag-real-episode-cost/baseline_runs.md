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

**Status**: Submitted — queued (pending GPU slots)

## 8m
Pending submission — to be submitted after reviewing `3s_vs_3z` results.

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
| 0.0 | 3 | ~~17198327~~ → 17203413 |

**Status**: Submitted — 2026-04-26 (resubmitted with dead_allies_incremental cost type)
