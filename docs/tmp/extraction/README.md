# Extraction

## Overview
Extracts metrics from WandB runs at target env steps, aggregates across seeds, and renders LaTeX/PDF tables.

Three pipelines exist:
- **`collision_pipeline.py`** — SafeDreamer vs MACPO, collision cost
- **`dead_allies_pipeline.py`** — SafeDreamer vs SafePO vs MAPPO-Lag, dead_allies_incremental cost (appendix table)
- **`extract_mappolag_smac.py`** — MAPPO-Lag SMAC extraction at multiple checkpoints (lives in `docs/experiments/11-thesis-ablations/1-mappo-lag-all-envs/`)

Both `collision_pipeline.py` and `dead_allies_pipeline.py` call `extract_metrics.py` internally.

---

## Technical Notes

### SafeDreamer vs MACPO — step axis difference
| | SafeDreamer | MACPO |
|--|-------------|-------|
| History storage | Parquet artifact (`wandb-history` type) | Regular `run.history()` |
| Step column | `steps` (env steps) | `_step` = env steps for MACPO |
| Target | Configurable per algorithm in `map_steps_config.json` | Same |

### Extraction logic (`extract_metrics.py`)
1. Try parquet artifact → use `steps` column (SafeDreamer)
2. Fallback to `run.history()` with target-aware window (MACPO)
3. Window: `[target - 5000, target]` env steps; fallback to last 3 rows if empty

### Key params (`extraction_config.py`)
| Param | Value | Meaning |
|-------|-------|---------|
| `WINDOW_SIZE` | 5000 | Steps before target to average over |
| `DEFAULT_TARGET_STEP` | 500,000 | Fallback if map not in config |
| `METRIC_KEYS` | score, cost, winrate | Metrics extracted |
| `STEP_COL` | `steps` | Env step column (SafeDreamer parquet) |
| `FALLBACK_STEP_COL` | `_step` | WandB internal step (MACPO fallback) |

### `map_steps_config.json` format
Per-algorithm targets per map:
```json
{ "3m": { "SafeDreamers": 100000, "MACPO": 5000000 } }
```
Pipelines patch this file temporarily before calling `extract_metrics.py`.

---

## How to Run

### Dead allies pipeline (appendix table)
```bash
cd scripts

# Full extraction from WandB + render
python dead_allies_pipeline.py

# Render from existing aggregated CSV (no WandB)
python dead_allies_pipeline.py --render-only

# Render from a custom CSV (e.g. multi-step comparison)
python dead_allies_pipeline.py --csv ../aggregated/smac/dead_allies_all_steps.csv

# Custom output path
python dead_allies_pipeline.py --csv input.csv --output /path/to/output.tex

# Test with fake data (no WandB)
python dead_allies_pipeline.py --test
```
Output (default): `../tables/appendix_full_comparison/appendix_table_corrected.pdf`

The `--csv` flag auto-detects all algorithm names in the CSV and renders them dynamically (no hardcoded algo list).

### Collision pipeline
```bash
cd scripts
python collision_pipeline.py
python collision_pipeline.py --sd-target 200000 --macpo-target 5000000
python collision_pipeline.py --test
```
Output: `../tables/collision_comparison/collision_safedreamer_{sd}k_vs_macpo_{mp}.pdf`

### MAPPO-Lag SMAC extraction
```bash
# From repo root:
python docs/experiments/11-thesis-ablations/1-mappo-lag-all-envs/extract_mappolag_smac.py

# Single checkpoint
python extract_mappolag_smac.py --checkpoint 100k

# All checkpoints (100k, 500k, 1M, 2M, 5M)
python extract_mappolag_smac.py --checkpoint all
```
Output: `docs/experiments/11-thesis-ablations/1-mappo-lag-all-envs/csv/` (per-seed + aggregated CSVs)

### Push to Overleaf thesis
```bash
cp ../tables/appendix_full_comparison/appendix_table_corrected_thesis.tex \
   ~/workspace/overleaf/thesis/generated_appendix_complete_100k_reordered.tex
cd ~/workspace/overleaf/thesis
git add generated_appendix_complete_100k_reordered.tex
git commit -m "fix(appendix): update corrected table"
git push
```

---

## Files

### inputs/
| File | Description |
|------|-------------|
| `new_experiments_tracking_100k.csv` | Original tracking CSV — **never modify** |
| `safe_dreamers_runs_adapted.csv` | SafeDreamer dead_allies runs, all 72 (cost_limit 0/1/4, 12 maps, 3 seeds) |
| `collision_runs_adapted.csv` | SafeDreamer + MACPO collision runs, 60 runs |

### aggregated/
Organized by environment type:
```
aggregated/
├── smac/
│   ├── dead_allies_agg.csv         — Main SMAC table (SD + SafePO + MAPPO-Lag)
│   ├── all_agg_corrected.csv       — SafePO source data (extracted at 5M)
│   ├── collision_agg.csv           — Collision pipeline output
│   └── dead_allies_all_steps.csv   — Multi-step comparison (all algo checkpoints)
└── mamujoco/
    ├── mamujoco_agg_experiment8.csv
    └── mamujoco_agg_experiment8_real_20260628_144800.csv
```

### scripts/
| File | Description |
|------|-------------|
| `extract_metrics.py` | Core: fetches metrics from WandB at target env step |
| `collision_pipeline.py` | End-to-end collision: extract → aggregate → PDF |
| `dead_allies_pipeline.py` | End-to-end dead_allies: extract → merge → PDF. Supports `--csv`, `--output`, `--render-only` |
| `extraction_config.py` | Constants: window size, metric keys, column names, map orders |
| `paths_config.py` | File path constants (aggregated CSVs under `smac/` and `mamujoco/`) |
| `wandb_config.py` | WandB project + timeout |
| `map_steps_config.json` | Per-map, per-algorithm target env steps |

---

## Current Status (2026-09-15)

### Dead allies (appendix table)
- SafeDreamer: all maps extracted at 100k
- SafePO (MACPO): all maps extracted at 5M; 100k test done
- MAPPO-Lag: all maps extracted at 100k, 500k, 1M, 5M; bane_vs_bane pending (128G jobs running)
- Remaining extractions: MACPO at 500k/1M/2M, MAPPO-Lag at 2M

### Collision
- SafeDreamer: all 30 runs done (100k+)
- MACPO: tables generated at 100k, 1M, 2M, 3M, 5M

### MAMuJoCo (Experiment 8)
- SafeDreamer vs MACPO vs MAPPO-Lag: complete (120 rows, phases 1-5)
- Pipeline: `mamujoco_pipeline_experiment8.py`
