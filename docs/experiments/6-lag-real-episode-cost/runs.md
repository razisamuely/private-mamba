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

## Planned: bane_vs_bane

**Map**: `bane_vs_bane`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, seeds 1,2,3  
**Rationale**: Banelings naturally cluster → collision cost more meaningful. `cost_limit=0` is a clean unconstrained baseline on a different map.

| Cost Limit | Seed | Slurm ID | Notes |
|-----------|------|----------|-------|
| 0.0 | 1 | ~~17105141~~ → ~~17105257~~ → 17105339 | Resubmitted with n_workers=2 (OOM) |
| 0.0 | 2 | ~~17105146~~ → ~~17105258~~ → 17105344 | Resubmitted with n_workers=2 (OOM) |
| 0.0 | 3 | ~~17105147~~ → ~~17105259~~ → 17105351 | Resubmitted with n_workers=2 (OOM) |

**Status**: Submitted — 2026-04-20

## Planned → Dropped: bane_vs_bane
Attempted 3 times, all OOM (10.9GB GPU, 24 agents too large for batch_size=40). Dropped in favour of `3s_vs_3z`.

## bane_vs_bane (retry with n_workers=4, qos=razshmue)

**Map**: `bane_vs_bane`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17209119 |
| 0.0 | 2 | 17209120 |
| 0.0 | 3 | 17209121 |

**Status**: Submitted — 2026-04-26 (retry with qos=razshmue; monitoring for OOM)

## 3s_vs_3z (replacement for bane_vs_bane)

**Map**: `3s_vs_3z`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17105855 |
| 0.0 | 2 | 17105856 |
| 0.0 | 3 | 17105857 |
| 0.5 | 1 | 17106290 |
| 0.5 | 2 | 17106291 |
| 0.5 | 3 | 17106292 |

**Status**: Submitted — 2026-04-20

## 3s5z_vs_3s6z

**Map**: `3s5z_vs_3s6z`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17136802 |
| 0.0 | 2 | 17136803 |
| 0.0 | 3 | 17136804 |

**Status**: Submitted — 2026-04-23

## MMM

**Map**: `MMM`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=2`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17177168 |
| 0.0 | 2 | 17177170 |
| 0.0 | 3 | 17177171 |

**Status**: Submitted — 2026-04-25

## MMM — dead_allies_incremental

**Map**: `MMM`, `dead_allies_incremental`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=2`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17198319 |
| 0.0 | 2 | 17198320 |
| 0.0 | 3 | 17198321 |

**Status**: Submitted — 2026-04-26

## 8m — dead_allies_incremental

**Map**: `8m`, `dead_allies_incremental`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | ~~17208565~~ → ~~17208870~~ → 17209123 |
| 0.0 | 2 | ~~17208566~~ → ~~17208872~~ → 17209124 |
| 0.0 | 3 | ~~17208571~~ → ~~17208875~~ → 17209125 |

**Status**: Submitted — 2026-04-26 (resubmitted as dead_allies_incremental)

## bane_vs_bane — dead_allies_incremental

**Map**: `bane_vs_bane`, `dead_allies_incremental`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | ~~17209119~~ → 17209126 |
| 0.0 | 2 | ~~17209120~~ → 17209127 |
| 0.0 | 3 | ~~17209121~~ → 17209128 |

**Status**: Submitted — 2026-04-26 (resubmitted as dead_allies_incremental; monitoring for OOM)

## bane_vs_bane — collision

**Map**: `bane_vs_bane`, `collision`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17209726 |
| 0.0 | 2 | 17209727 |
| 0.0 | 3 | 17209728 |

**Status**: Submitted — 2026-04-26

## 3s_vs_5z — dead_allies_incremental

**Map**: `3s_vs_5z`, `dead_allies_incremental`, `laglr=1e-5`, `cost_priority=0.15`, `cost_limit=0.0`, `n_workers=4`, seeds 1,2,3

| Cost Limit | Seed | Slurm ID |
|-----------|------|----------|
| 0.0 | 1 | 17209696 |
| 0.0 | 2 | 17209697 |
| 0.0 | 3 | 17209698 |

**Status**: Submitted — 2026-04-26

## Batch submission — dead_allies_incremental, cost_limit=0.0, n_workers=4

Submitted 2026-04-29. All maps from `safe_dreamers_runs.csv` with cost_limit=0, resubmitting 3s_vs_5z.

| Map | Seed | Slurm ID |
|-----|------|----------|
| 1c3s5z | 1 | 17261571 |
| 1c3s5z | 2 | 17261572 |
| 1c3s5z | 3 | 17261573 |
| 2m_vs_1z | 1 | 17261575 |
| 2m_vs_1z | 2 | 17261576 |
| 2m_vs_1z | 3 | 17261577 |
| 2s3z | 1 | 17261578 |
| 2s3z | 2 | 17261579 |
| 2s3z | 3 | 17261580 |
| 2s_vs_1sc | 1 | 17261581 |
| 2s_vs_1sc | 2 | 17261582 |
| 2s_vs_1sc | 3 | 17261584 |
| 3m | 1 | 17261585 |
| 3m | 2 | 17261586 |
| 3m | 3 | 17261587 |
| 3s_vs_3z | 1 | 17261588 |
| 3s_vs_3z | 2 | 17261589 |
| 3s_vs_3z | 3 | 17261590 |
| 3s_vs_4z | 1 | 17261591 |
| 3s_vs_4z | 2 | 17261592 |
| 3s_vs_4z | 3 | 17261593 |
| 3s_vs_5z | 1 | 17261594 |
| 3s_vs_5z | 2 | 17261595 |
| 3s_vs_5z | 3 | 17261596 |
| 3s5z_vs_3s6z | 1 | 17261597 |
| 3s5z_vs_3s6z | 2 | 17261598 |
| 3s5z_vs_3s6z | 3 | 17261599 |

## Batch resubmission — dead_allies_incremental, cost_limit=0.0, n_workers=4 (fixed --cost_priority bug)

Submitted 2026-04-29. Previous batch (17261571-17261599) crashed due to `--cost_priority` arg removed from train.py but still in template.

| Map | Seed | Slurm ID |
|-----|------|----------|
| 1c3s5z | 1 | 17261617 |
| 1c3s5z | 2 | 17261618 |
| 1c3s5z | 3 | 17261619 |
| 2m_vs_1z | 1 | 17261620 |
| 2m_vs_1z | 2 | 17261621 |
| 2m_vs_1z | 3 | 17261622 |
| 2s3z | 1 | 17261623 |
| 2s3z | 2 | 17261624 |
| 2s3z | 3 | 17261625 |
| 2s_vs_1sc | 1 | 17261626 |
| 2s_vs_1sc | 2 | 17261627 |
| 2s_vs_1sc | 3 | 17261628 |
| 3m | 1 | 17261629 |
| 3m | 2 | 17261630 |
| 3m | 3 | 17261631 |
| 3s_vs_3z | 1 | 17261632 |
| 3s_vs_3z | 2 | 17261633 |
| 3s_vs_3z | 3 | 17261634 |
| 3s_vs_4z | 1 | 17261635 |
| 3s_vs_4z | 2 | 17261636 |
| 3s_vs_4z | 3 | 17261637 |
| 3s_vs_5z | 1 | 17261638 |
| 3s_vs_5z | 2 | 17261639 |
| 3s_vs_5z | 3 | 17261640 |
| 3s5z_vs_3s6z | 1 | 17261641 |
| 3s5z_vs_3s6z | 2 | 17261643 |
| 3s5z_vs_3s6z | 3 | 17261644 |

## 3s5z_vs_3s6z, bane_vs_bane, MMM — dead_allies_incremental, cost_limit=0.0, n_workers=4

Submitted 2026-04-30.

| Map | Seed | Slurm ID |
|-----|------|----------|
| 3s5z_vs_3s6z | 1 | 17273368 |
| 3s5z_vs_3s6z | 2 | 17273369 |
| 3s5z_vs_3s6z | 3 | 17273370 |
| bane_vs_bane | 1 | 17273371 |
| bane_vs_bane | 2 | 17273372 |
| bane_vs_bane | 3 | 17273373 |
| MMM | 1 | 17273374 |
| MMM | 2 | 17273375 |
| MMM | 3 | 17273376 |
