---
name: results-skills
description: Skills for fetching Safe Dreamers experiment results from wandb and updating the results table.
---

# Results Skills

## Environment

- **Python**: `/home/corsound/workspace/overleaf/thesis/venv/bin/python3`
  (requires pandas >= 1.0 for parquet support — do NOT use the project venv)
- **wandb API key**: in `/home/corsound/workspace/overleaf/.env` as `WEIGHT_AND_BIASES`
- **Project**: `raz-shmueli-corsound-ai/private-mamba`

---

## Fast recipes

### List available experiments

```bash
ls docs/experiments/
# Each folder with wandb_runs.json is fetchable
ls docs/experiments/6-lag-real-episode-cost/wandb_runs.json
```

### Inspect an experiment's runs

```bash
cat docs/experiments/6-lag-real-episode-cost/wandb_runs.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d['runs']: print(r['map'], r['cost_fn'], r['cost_limit'], r['seed'])
"
```

### Fetch all runs from an experiment

```bash
export WANDB_API_KEY=$(grep WEIGHT_AND_BIASES /home/corsound/workspace/overleaf/.env | cut -d= -f2)
/home/corsound/workspace/overleaf/thesis/venv/bin/python3 \
  docs/results/scripts/fetch_results.py \
  --exp docs/experiments/6-lag-real-episode-cost
```

### Fetch only dead_allies_incremental runs

```bash
export WANDB_API_KEY=$(grep WEIGHT_AND_BIASES /home/corsound/workspace/overleaf/.env | cut -d= -f2)
/home/corsound/workspace/overleaf/thesis/venv/bin/python3 \
  docs/results/scripts/fetch_results.py \
  --exp docs/experiments/6-lag-real-episode-cost \
  --cost-fn dead_allies_incremental
```

### Fetch and update CSV

```bash
export WANDB_API_KEY=$(grep WEIGHT_AND_BIASES /home/corsound/workspace/overleaf/.env | cut -d= -f2)
/home/corsound/workspace/overleaf/thesis/venv/bin/python3 \
  docs/results/scripts/fetch_results.py \
  --exp docs/experiments/6-lag-real-episode-cost \
  --cost-fn dead_allies_incremental \
  --out docs/results/safe_dreamers_runs.csv
```

---

## How data flows

```
wandb (parquet artifact)
  └─► fetch_results.py        reads wandb_runs.json, downloads artifact, extracts at 100k
        └─► safe_dreamers_runs.csv    per-seed results
              └─► table3_performance_comparison.tex   aggregated mean±std
```

## SafeDreamers vs MACPO data path

| Algorithm | Storage | How to read |
|-----------|---------|-------------|
| SafeDreamers | `wandb-history` parquet artifact | `get_history_from_artifact(run)` → filter by `steps` column |
| MACPO (SafePO) | Regular wandb history | `run.history(keys=['steps','main/score',...])` |

Both use `steps` (env steps) as x-axis, not `_step` (training steps).

## Adding a new experiment

1. Create `docs/experiments/N-name/wandb_runs.json` with this schema:
```json
{
  "experiment": "N-name",
  "branch": "feat/branch-name",
  "runs": [
    {
      "map": "8m",
      "cost_fn": "dead_allies_incremental",
      "cost_limit": 0,
      "seed": 1,
      "run_id": "wandb_run_id_here"
    }
  ]
}
```
2. Tell me: "fetch exp N, cost_fn X" — I'll run the skill.

## Critical rules

- Always use the **overleaf venv** — project venv has pandas 0.25 (too old for parquet)
- `main/score` is NOT in regular wandb history for SafeDreamers — only in the parquet artifact
- `steps` = environment steps (what we care about), `_step` = training update steps (ignore)
- Target step for table: **100k** for all maps
- Window: [95k, 100k] — average over last 5k steps before target

## Files

```
docs/results/
  scripts/
    SKILL.md                  ← this file
    results_helpers.py        ← core functions (get_api, fetch_run_at_step, aggregate_seeds)
    fetch_results.py          ← CLI skill (reads wandb_runs.json, fetches, updates CSV)
  safe_dreamers_runs.csv      ← per-seed results (fill wandb_run_id, script fills metrics)
  table3_performance_comparison.tex  ← LaTeX table (Safe Dreamers rows to fill)

docs/experiments/
  6-lag-real-episode-cost/
    wandb_runs.json           ← machine-readable run definitions
    runs.md                   ← human-readable run log
```
