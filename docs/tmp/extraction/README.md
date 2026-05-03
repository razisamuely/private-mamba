# Step Axis Investigation

## CEO View
Old paper results were inflated by a measurement bug. We fixed it and re-measured at 100k/150k/200k env steps. Hard maps dropped significantly; easy maps are stable. Corrected tables are ready.

## High-Level View
The old CSV used WandB's internal log counter (`_step`) as x-axis. At `_step=100k`, the agent had already seen ~300k real env steps — so results were from a much later training point. We re-extracted using actual env steps.

## Technical View

### SafeDreamer vs MACPO — key difference
| | SafeDreamer | MACPO |
|--|-------------|-------|
| History storage | Parquet artifact (`wandb-history` type) | Regular `run.history()` |
| Step column | `steps` (env steps) ✓ | `_step` (internal counter) |
| Correctable? | Yes — reads `steps` from parquet | No — `_step` only, no correction possible |

### Extraction logic
1. Try parquet artifact → use `steps` column (SafeDreamer)
2. Fallback to `run.history()` → use `_step` (MACPO)
3. Window: `[target - 5000, target]` env steps; fallback to last 3 rows

### Key params (in `extraction_config.py`)
| Param | Value | Meaning |
|-------|-------|---------|
| `WINDOW_SIZE` | 5000 | Steps before target to average over |
| `HISTORY_SAMPLES` | 2,000,000 | Max rows fetched from wandb |
| `DEFAULT_TARGET_STEP` | 500,000 | Fallback if map not in config |
| `METRIC_KEYS` | score, cost, winrate | Metrics extracted |
| `STEP_COL` | `steps` | Env step column (SafeDreamer) |
| `FALLBACK_STEP_COL` | `_step` | WandB internal step (MACPO) |

### Paths (in `paths_config.py`)
| Constant | Path |
|----------|------|
| `DEFAULT_INPUT_CSV` | `new_experiments_tracking_100k.csv` (local copy, read-only) |
| `DEFAULT_CONFIG_JSON` | `map_steps_config.json` |
| `DEFAULT_OUTPUT_CSV` | `extracted_metrics.csv` |

### WandB (in `wandb_config.py`)
| Constant | Value |
|----------|-------|
| `WANDB_PROJECT` | `raz-shmueli-corsound-ai/private-mamba` |
| `WANDB_TIMEOUT` | 60s |

## How to Run

```bash
cd /home/corsound/workspace/private-mamba/docs/tmp/extraction/scripts

# 1. Set target step (edit map_steps_config.json)

# 2. Extract metrics
/home/corsound/workspace/overleaf/thesis/venv/bin/python3 extract_metrics.py \
    --config map_steps_config.json \
    2>/dev/null | tee extracted_Xk.txt

# 3. Parse output → aggregated CSV (adapt inline script from previous runs)
# 4. Render PDF (adapt render script from previous runs)
```

## Files

### inputs/
| File | Description |
|------|-------------|
| `new_experiments_tracking_100k.csv` | Original tracking CSV — **never modify** |
| `safe_dreamers_runs_adapted.csv` | SafeDreamers dead_allies_incremental runs (with wandb links) |
| `collision_runs_adapted.csv` | SafeDreamers + MACPO collision runs (with wandb links) |

### aggregated/
| File | Description |
|------|-------------|
| `all_agg_corrected.csv` | Aggregated at 100k env steps (SafeDreamer + MACPO) |
| `all_agg_150k.csv` | Aggregated at 150k |
| `all_agg_200k.csv` | Aggregated at 200k |
| `new_agg.csv` | Latest SafeDreamers dead_allies_incremental aggregated |

### ../tables/bug_fix_step_axis/
| File | Description |
|------|-------------|
| `bug_impact_100k.pdf` | Old (wrong _step=100k) vs corrected 100k env steps |
| `bug_impact_150k.pdf` | Old vs corrected 150k |
| `bug_impact_200k.pdf` | Old vs corrected 200k |

### ../tables/lag_fix_comparison/
| File | Description |
|------|-------------|
| `lag_cost_fix_vs_lag_episode_cost.pdf` | feat/lag-real-cost-fix vs feat/lag-real-episode-cost |
| `collision_safedreamer_vs_macpo.pdf` | SafeDreamers vs MACPO on collision cost |
