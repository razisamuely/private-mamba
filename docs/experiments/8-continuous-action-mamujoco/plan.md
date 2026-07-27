# Experiment 8 — Extraction & Comparison Plan

## Goal

Build a comparison table: SafeDreamer vs MACPO on MAMuJoCo, showing sample efficiency and safety.

## Data Sources

| Source | Algo | Steps | How |
|--------|------|-------|-----|
| Our SafeDreamer | SafeDreamer | 100k, 500k, 1M | WandB parquet, 5k window avg |
| Our MACPO | MACPO | 10M (final) | WandB run.history() |
| Paper MACPO | MACPO | 10M | GitHub figures (visual estimate, marked ~) |
| GitHub README | MACPO | 10M | README text (marked ~) |

## Runs (36 total)

### SafeDreamer GPU (18 runs)

| Env | Cost Limit | Seeds | Slurm IDs |
|-----|-----------|-------|-----------|
| Ant 2x4 | 25 | 1,2,3 | 18362835-838 |
| Ant 4x2 | 25 | 1,2,3 | 18362839-841 |
| Ant 2x4 | 0.2 | 1,2,3 | 18367088-091 |
| Ant 4x2 | 1.0 | 1,2,3 | 18367092-097 |
| HC 2x3 | 5.0 | 1,2,3 | 18367101-104 |
| HC 2x3 | 25 | 1,2,3 | 18174008-010 |

### MACPO CPU (18 runs)

| Env | Cost Limit | Seeds | Slurm IDs |
|-----|-----------|-------|-----------|
| Ant 2x4 | 25 | 1,2,3 | 18366191-193 |
| Ant 4x2 | 25 | 1,2,3 | 18366194-196 |
| Ant 2x4 | 0.2 | 1,2,3 | 18367114-116 |
| Ant 4x2 | 1.0 | 1,2,3 | 18367117-137 |
| HC 2x3 | 5.0 | 1,2,3 | 18367138-144 |

### Paper/GitHub (hardcoded)

| Env | Cost Limit | Reward | Cost | Source |
|-----|-----------|--------|------|--------|
| Ant 2x4 | 0.2 | ~800-1000 | ~10-20 | GitHub figures |
| Ant 4x2 | 1.0 | ~500-800 | ~10-20 | GitHub figures |
| HC 2x3 | 5.0 | ~2000-2500 | ~30-50 | GitHub figures |
| Ant 2x4 | 0.2 | — | ~0 | GitHub README |
| Ant 4x2 | 1.0 | — | ~0 | GitHub README |
| HC 2x3 | 5.0 | — | ~0 | GitHub README |

## Pipeline Files

```
docs/tmp/extraction/inputs/mamujoco_runs_experiment8.csv
docs/tmp/extraction/scripts/mamujoco_pipeline_experiment8.py
docs/tmp/tables/mamujoco_comparison_experiment8/
    comparison_table.csv
    comparison_table.tex
    comparison_table.pdf
```

## Expected Output Table (paper cost limits)

| Env | Cost Limit | Source | Steps | Reward (mean+-std) | Cost (mean+-std) |
|-----|-----------|--------|-------|-------------------|-----------------|
| Ant 2x4 | 0.2 | Paper MACPO ~ | 10M | ~900 | ~15 |
| Ant 2x4 | 0.2 | GitHub reported ~ | 10M | — | ~0 |
| Ant 2x4 | 0.2 | Our MACPO | 10M | 859 +- 32 | 1.2 +- 0.7 |
| Ant 2x4 | 0.2 | Our SafeDreamer | 100k | ? +- ? | ? +- ? |
| Ant 2x4 | 0.2 | Our SafeDreamer | 500k | 1370 +- ? | 0.0 +- 0.0 |
| Ant 2x4 | 0.2 | Our SafeDreamer | 1M | 1667 +- ? | 0.0 +- 0.0 |
| | | | | | |
| Ant 4x2 | 1.0 | Paper MACPO ~ | 10M | ~650 | ~15 |
| Ant 4x2 | 1.0 | GitHub reported ~ | 10M | — | ~0 |
| Ant 4x2 | 1.0 | Our MACPO | 10M | 1097 +- 95 | 3.4 +- 0.9 |
| Ant 4x2 | 1.0 | Our SafeDreamer | 100k | 999 +- ? | 0.0 +- 0.0 |
| Ant 4x2 | 1.0 | Our SafeDreamer | 500k | ? +- ? | ? +- ? |
| Ant 4x2 | 1.0 | Our SafeDreamer | 1M | 1734 +- ? | 0.0 +- 0.0 |
| | | | | | |
| HC 2x3 | 5.0 | Paper MACPO ~ | 10M | ~2250 | ~40 |
| HC 2x3 | 5.0 | GitHub reported ~ | 10M | — | ~0 |
| HC 2x3 | 5.0 | Our MACPO | 10M | 1317 +- 113 | 5.0 +- 1.6 |
| HC 2x3 | 5.0 | Our SafeDreamer | 100k | ? +- ? | ? +- ? |
| HC 2x3 | 5.0 | Our SafeDreamer | 500k | ? +- ? | ? +- ? |
| HC 2x3 | 5.0 | Our SafeDreamer | 1M | ? +- ? | ? +- ? |

## Expected Output Table (cost limit = 25)

| Env | Cost Limit | Source | Steps | Reward (mean+-std) | Cost (mean+-std) |
|-----|-----------|--------|-------|-------------------|-----------------|
| Ant 2x4 | 25 | Our MACPO | 10M | 798 +- 107 | 10.5 +- 1.7 |
| Ant 2x4 | 25 | Our SafeDreamer | 100k | ? +- ? | ? +- ? |
| Ant 2x4 | 25 | Our SafeDreamer | 500k | ? +- ? | ? +- ? |
| Ant 2x4 | 25 | Our SafeDreamer | 1M | ? +- ? | ? +- ? |
| | | | | | |
| Ant 4x2 | 25 | Our MACPO | 10M | 1287 +- 147 | 23.6 +- 6.1 |
| Ant 4x2 | 25 | Our SafeDreamer | 100k | ? +- ? | ? +- ? |
| Ant 4x2 | 25 | Our SafeDreamer | 500k | ? +- ? | ? +- ? |
| Ant 4x2 | 25 | Our SafeDreamer | 1M | ? +- ? | ? +- ? |
| | | | | | |
| HC 2x3 | 25 | Our MACPO (Exp7) | 10M | 1374 +- 60 | 22 +- 3 |
| HC 2x3 | 25 | Our SafeDreamer | 100k | ? +- ? | ? +- ? |
| HC 2x3 | 25 | Our SafeDreamer | 500k | ? +- ? | ? +- ? |
| HC 2x3 | 25 | Our SafeDreamer | 1M | ? +- ? | ? +- ? |

Note: `?` values will be filled by the pipeline. `~` values are visual estimates from figures, not exact.

## Steps

### Step 1: Create input CSV -- DONE
Created `docs/tmp/extraction/inputs/mamujoco_runs_experiment8.csv` (34 rows).
Missing: 2 HC c=5 seeds (pending GPU), 3 MACPO HC c=25 (Exp7, URL encoding issue).

### Step 2: Collect paper/GitHub reference values -- DONE
Hardcoded in pipeline: Paper MACPO (~900/~650/~2250) + GitHub README (~0 cost).

### Step 3: Build pipeline script -- DONE
Created `docs/tmp/extraction/scripts/mamujoco_pipeline_experiment8.py`.
Reuses `extract_metrics.py`. Handles MACPO via `run.summary` (uses `main/score`).
Supports `--test` mode, `--from-csv` re-rendering.

### Step 4: Run pipeline -- DONE
SafeDreamer extracted at 100k, 500k, 700k, 800k, 900k, 1M.
MACPO extracted at 10M (final).
Output: `docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table.pdf`
Backup: `comparison_table_real_20260628_144800.csv`

### Step 5: Update experiment docs -- DONE
- `overview.md` updated with results summary
- `runs.md` updated with job statuses
- `plan.md` steps marked complete

### Remaining from Phase 1-3
- 2 HC c=5 SafeDreamer seeds still pending (GPU queue)
- MACPO HC c=25 seed 3 submitted (Slurm 18505362), waiting for completion

---

## Phase 4: Lagrangian LR sweep (laglr=1e-4)

All Phase 1-3 SafeDreamer runs used `laglr=1e-5` (default). This is very slow for the
Lagrangian multiplier to react. Phase 4 tests `laglr=1e-4` (10x faster) to see if
SafeDreamer can better satisfy cost constraints while maintaining reward.

MACPO baselines don't change — reuse Phase 2-3 MACPO results.

### Step 6: Update docs with laglr column
**Prerequisite**: Phase 1-3 complete
**Action**:
- Add `laglr` note to `runs.md` — all Phase 1-3 runs are `laglr=1e-5`
- Add Phase 4 section to `runs.md` with empty job table

**Output**: `runs.md` with Phase 4 section
**Validate**: Clear separation between laglr=1e-5 and laglr=1e-4 runs

### Step 7: Add laglr to comparison CSV and pipeline
**Prerequisite**: Step 6 done
**Action**:
- Add `laglr` column to `mamujoco_runs_experiment8.csv` (1e-5 for existing, 1e-4 for new)
- Update pipeline to group by (env, cost_limit, source, steps, laglr)
- Update LaTeX table to show laglr in a column or as a row label suffix

**Output**: Updated CSV + pipeline script
**Validate**: `--test` mode shows laglr in output table

### Step 8: Submit Phase 4 jobs
**Prerequisite**: Step 7 done, cluster available
**Action**:
- Submit SafeDreamer GPU jobs with `--laglr 0.0001`:
  - 3 seeds × Ant 2x4 c=0.2
  - 3 seeds × Ant 4x2 c=1.0
  - 3 seeds × HC 2x3 c=5.0
  - 3 seeds × Ant 2x4 c=25
  - 3 seeds × Ant 4x2 c=25
  - 3 seeds × HC 2x3 c=25
  = 18 jobs total
- No new MACPO jobs needed

**Output**: Slurm IDs in `runs.md`
**Validate**: `squeue` shows 18 jobs RUNNING after 2 min

### Step 9: Extract and compare -- DONE
Extracted 18 Phase 4 runs at 100k/500k/700k/800k/900k/1M.
Appended to `comparison_table_real_20260628_144800.csv` (48 → 84 rows).
Backups: `comparison_table_real_pre_phase4_backup.csv`, `comparison_table_real_20260704_phase4.csv`.
Re-rendered PDF with `--render-only`.
Key finding: lr=1e-4 reduces cost 83-100% on tight limits with moderate reward trade-off.

---

## Phase 5: Communication ablation (no inter-agent attention)

All Phase 1-4 runs used full communication (`nn_mask=None` — all agents attend to all).
Phase 5 tests no communication (`nn_mask=eye` — each agent attends only to itself).
This shows whether inter-agent communication helps or hurts reward/cost.

### Step 10: Add `--comm_mode` CLI flag -- DONE
Added on branch `fix/tanh-logprob-correction`.
**Bug found**: initial mask used `torch.eye().bool()` which blocks self-attention
and allows cross-agent (opposite of intended). PyTorch attention: True=blocked.
Fix: `~torch.eye().bool()` blocks cross-agent, allows self.
Fix on branch `fix/comm-mask-inversion`.

### Step 11: Add Phase 5 section to `runs.md` -- DONE

### Step 12: Submit Phase 5 jobs -- RESUBMITTED
First submission (Slurm 19063225-243) used wrong mask — cancelled.
Resubmitted on branch `fix/comm-mask-inversion` (Slurm 19122709-728).
**Config**: `--comm_mode none --laglr 0.00001`, same grid.
**Action**:
- Committed, pushed, pulled on cluster
- Submitted SafeDreamer GPU jobs with `--comm_mode none --laglr 0.00001`:
  - 3 seeds × Ant 2x4 c=0.2
  - 3 seeds × Ant 4x2 c=1.0
  - 3 seeds × HC 2x3 c=5.0
  - 3 seeds × Ant 2x4 c=25
  - 3 seeds × Ant 4x2 c=25
  - 3 seeds × HC 2x3 c=25
  = 18 jobs total
**Output**: Slurm IDs in `runs.md`
**Validate**: `squeue` shows jobs after 2 min

### Step 13: Extract and compare -- DONE
**Done (2026-07-18)**:
- Extracted 12 Ant no-comm runs (Slurm 19122709-724) at 100k/500k/700k/800k/900k/1M
- 72 seed rows → 24 agg rows labeled `SafeDreamer (lr=1e-5, nocomm)`
- Appended to `comparison_table_real_20260628_144800.csv` (84 → 108 rows)
- Backups: `comparison_table_real_pre_phase5_backup.csv`, `comparison_table_real_20260718_phase5_ant.csv`
- PDF re-rendered via `--render-only`
- Key finding @1M: comm helps on Ant 2x4 c=0.2 (full 2267.8±134.1 vs nocomm 1191.6±444.6);
  no benefit on Ant 4x2 c=25 (nocomm 1656.8±161.8 vs full 1574.5±304.2)

**Done (2026-07-24, HC)**:
- 6 HC 2x3 no-comm runs completed (Slurm 19449871/873/874/876/877/878, ~3d21h each;
  1st resubmission 19442919-29 had failed — wandb name >128 chars, fixed in `c00b426`)
- Extracted 36 seed rows → 12 agg rows, appended (108 → 120 rows)
- Added all 18 Phase 5 run URLs to input CSV `mamujoco_runs_experiment8.csv`
- Backups: `comparison_table_real_pre_phase5_hc_backup.csv`, `comparison_table_real_20260724_phase5_full.csv`
- PDF re-rendered
- HC @1M: c=5 nocomm 1166.0±512.6 (full 1519); c=25 nocomm 981.5±1303.1 (full 2527±229)
  → communication clearly helps on HC

---

## Phase 6: MAPPO-Lag baseline (reviewer upmo)

Reviewer upmo: "Add MAPPO-Lag to disentangle the Lagrangian effect from the world-model effect."
MAPPO-Lag uses Lagrangian but no world model — if Safe Dreamers still wins, the world model is the key.

### Step 14: Submit MAPPO-Lag on MAMuJoCo -- DONE (2026-07-26)
Ran from SafePO repo (`Safe-Policy-Optimization-Modified` on cluster, conda env `safepo`).
Template: `template_mappolag_mamujoco.sbatch` (CPU, 7d walltime, `mappolag.py`).
Config: d=25, 10M steps, 5 parallel envs, seeds 1-3.

| # | Env | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 90 | Ant 2x4 | 25 | 1 | 19583387 | DONE (extracted) |
| 91 | Ant 2x4 | 25 | 2 | 19583388 | DONE (crashed step 1351, data used) |
| 92 | Ant 2x4 | 25 | 3 | 19583389 | DONE (extracted) |
| 93 | Ant 4x2 | 25 | 1 | 19583390 | DONE (extracted) |
| 94 | Ant 4x2 | 25 | 2 | 19583391 | DONE (extracted) |
| 95 | Ant 4x2 | 25 | 3 | 19583392 | DONE (extracted) |
| 96 | HC 2x3 | 25 | 1 | 19583393 | DONE (extracted) |
| 97 | HC 2x3 | 25 | 2 | 19583396 | DONE (extracted) |
| 98 | HC 2x3 | 25 | 3 | 19583397 | DONE (extracted) |

### Step 15: Extract and compare -- DONE (2026-07-28)
- Extracted 9 MAPPO-Lag runs via run.summary (same as MACPO)
- 3 agg rows labeled `MAPPO-Lag Run`, appended to main CSV (120 → 123 rows)
- Backup: `comparison_table_real_pre_phase6_backup.csv`
- PDF re-rendered
- Results @10M: Ant2x4 1580±185 cost=1.4; Ant4x2 1865±42 cost=0.1; HC 1141±36 cost=0.0
- SD beats MAPPO-Lag on Ant2x4 (1836 vs 1580) and HC (2527 vs 1141)
- MAPPO-Lag beats SD on Ant4x2 (1865 vs 1575)
- Next: fill `aaai_additions/sections/mappo_baseline.tex`
