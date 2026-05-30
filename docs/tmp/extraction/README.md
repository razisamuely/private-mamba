# Extraction

## Overview
Extracts metrics from WandB runs at target env steps, aggregates across seeds, and renders LaTeX/PDF tables.

Two pipelines exist:
- **`collision_pipeline.py`** — SafeDreamer vs MACPO, collision cost
- **`dead_allies_pipeline.py`** — SafeDreamer vs SafePO, dead_allies_incremental cost (appendix table)

Both call `extract_metrics.py` internally.

---

## Technical Notes

### SafeDreamer vs MACPO — step axis difference
| | SafeDreamer | MACPO |
|--|-------------|-------|
| History storage | Parquet artifact (`wandb-history` type) | Regular `run.history()` |
| Step column | `steps` (env steps) ✓ | `_step` = env steps for MACPO ✓ |
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

### Collision pipeline
```bash
cd scripts
# SafeDreamer 100k vs MACPO 5M (default)
python collision_pipeline.py

# Custom targets
python collision_pipeline.py --sd-target 200000 --macpo-target 5000000
python collision_pipeline.py --macpo-target 100000

# Test with fake data (no WandB)
python collision_pipeline.py --test
```
Output: `../tables/collision_comparison/collision_safedreamer_{sd}k_vs_macpo_{mp}.pdf`

### Dead allies pipeline (appendix table)
```bash
cd scripts
python dead_allies_pipeline.py

# Test with fake data
python dead_allies_pipeline.py --test
```
Output:
- `../tables/appendix_full_comparison/appendix_table_corrected.pdf` (standalone)
- `../tables/appendix_full_comparison/appendix_table_corrected_thesis.tex` (for Overleaf `\input`)

### Push to Overleaf thesis
```bash
cp ../tables/appendix_full_comparison/appendix_table_corrected_thesis.tex \
   /home/corsound/workspace/overleaf/thesis/generated_appendix_complete_100k_reordered.tex
cd /home/corsound/workspace/overleaf/thesis
git add generated_appendix_complete_100k_reordered.tex
git commit -m "fix(appendix): update corrected table"
git push
```

### Raw extraction (no pipeline)
```bash
cd scripts
/home/corsound/workspace/overleaf/thesis/venv/bin/python3 extract_metrics.py \
    --output ../inputs/safe_dreamers_runs_adapted.csv \
    2>/dev/null | tee extracted_output.txt
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
| File | Description |
|------|-------------|
| `all_agg_corrected.csv` | SafeDreamer + SafePO dead_allies at 100k (corrected step axis) |
| `all_agg_150k.csv` | SafeDreamer + SafePO at 150k |
| `all_agg_200k.csv` | SafeDreamer + SafePO at 200k |
| `collision_agg.csv` | Latest collision pipeline output |
| `dead_allies_agg.csv` | Latest dead_allies pipeline output |
| `new_agg.csv` | Old SafeDreamer-only aggregation (superseded) |

### scripts/
| File | Description |
|------|-------------|
| `extract_metrics.py` | Core: fetches metrics from WandB at target env step |
| `collision_pipeline.py` | End-to-end collision: extract → aggregate → PDF |
| `dead_allies_pipeline.py` | End-to-end dead_allies: extract → merge SafePO → PDF |
| `extraction_config.py` | Constants: window size, metric keys, column names, map orders |
| `paths_config.py` | File path constants |
| `wandb_config.py` | WandB project + timeout |
| `map_steps_config.json` | Per-map, per-algorithm target env steps |

---

## Operational Cheatsheet

### Check which runs reached target steps
```python
import wandb, pandas as pd
api = wandb.Api()
df = pd.read_csv('inputs/safe_dreamers_runs_adapted.csv')
df['run_id'] = df['wandb_link'].str.split('/runs/').str[-1]
for _, row in df.dropna(subset=['wandb_link']).iterrows():
    run = api.run(f"raz-shmueli-corsound-ai/private-mamba/{row['run_id']}")
    steps = run.summary.get('steps', 0)
    print('✓' if steps >= 100_000 else '✗', row['map'], row['cost_limit'], row['seed'], steps)
```

### Verify all WandB links exist
```python
import wandb, pandas as pd
api = wandb.Api()
df = pd.read_csv('inputs/safe_dreamers_runs_adapted.csv')
df['run_id'] = df['wandb_link'].str.split('/runs/').str[-1]
for _, row in df.dropna(subset=['wandb_link']).iterrows():
    try:
        api.run(f"raz-shmueli-corsound-ai/private-mamba/{row['run_id']}")
    except:
        print(f"MISSING: {row['map']} cl={row['cost_limit']} s{row['seed']}")
```

### Check Slurm queue
```bash
ssh slurm.bgu.ac.il "squeue -u razshmue --format='%.10i %.35j %.8T %.10M'"
```

### Cancel jobs
```bash
ssh slurm.bgu.ac.il "scancel 17336238 17336240 ..."
```

### WandB run ID truncation
WandB truncates run IDs in URLs. If a link returns "not found", the actual run ID may use `dai` instead of `dead_allies_incremental` in the name. Match by slurm job ID embedded in the run name (e.g. `_17336255_`).

---

## Current Status (2026-05-06)

### Dead allies (appendix table)
- cost_limit=0: all 36 runs ✓ done
- cost_limit=1: 17/18 done (3m s1 still running ~74k)
- cost_limit=4: 13/18 done (8m ×3, bane_vs_bane ×3, MMM s3 still running ~85k)
- Table pushed to Overleaf with 8 `—` entries; re-run pipeline when remaining jobs finish

### Collision
- SafeDreamer: all 30 runs ✓ done (100k+)
- MACPO: 23/30 at 5M; remaining: bane_vs_bane ×3, 3s5z_vs_3s6z s3 still running
- Tables generated at 100k, 1M, 2M, 3M, 5M MACPO checkpoints
