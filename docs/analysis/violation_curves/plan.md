# Violation Curves Analysis — Plan

## Goal

Show that Safe Dreamers accumulates fewer safety violations during training
than MACPO, supporting the paper's "proactive safety" claim.

Addresses reviewer 1QgC: "Provide stronger evidence that the proposed framework
meaningfully reduces the number of safety violations encountered during training."

## Output metrics (per run)

Given a vector of per-episode costs `C = [c_1, c_2, ..., c_K]` and limit `d`:
- **Cumulative cost**: `cumsum(C)`
- **V_K** (violation count): `cumsum(C > d)` — how many episodes violated
- **E_K** (cumulative excess): `cumsum(max(C - d, 0))` — how much over the limit

## Package structure

```
docs/analysis/violation_curves/
├── plan.md                    # This file
├── pull_cost_timeseries.py    # Step 1: pull full cost time series from WandB → CSV
├── plot_violation_curves.py   # Step 2: read CSVs → compute metrics → plot
├── data/                      # Cached CSVs (one per run, avoid re-pulling)
├── figures/                   # Output PDFs
└── README.md                  # Run list, what the plots show
```

## Interfaces

### pull_cost_timeseries.py

**Input**: WandB run ID (or URL), output path
**Output**: CSV file with columns `step, cost` (all logged data points, no sampling)
**Reuses from** `docs/tmp/extraction/scripts/`:
  - `extract_metrics.py`: `extract_run_id_from_url()`, `find_history_artifact()`,
    `download_parquet_as_dataframe()`, `fetch_run_history_as_dataframe()`
  - `wandb_config.py`: `WANDB_PROJECT`, `WANDB_TIMEOUT`
  - `extraction_config.py`: `STEP_COL`, `METRIC_KEYS`

**CLI**:
```bash
python pull_cost_timeseries.py --run-id <wandb_run_id> --output data/<name>.csv
python pull_cost_timeseries.py --input-csv <runs.csv> --output-dir data/
```

**Algorithm-agnostic**: works for SafeDreamer (parquet artifact) and MACPO (scan_history).
No filtering, no windowing — pulls the full time series.

### plot_violation_curves.py

**Input**: directory of CSVs + config (which CSVs belong to which algo/env/seed, cost limit)
**Output**: PDF plots in `figures/`

**CLI**:
```bash
python plot_violation_curves.py --data-dir data/ --config runs_config.json --output-dir figures/
```

**Config format** (`runs_config.json`):
```json
{
  "comparisons": [
    {
      "env": "Safety2x4AntVelocity-v0",
      "cost_limit": 25.0,
      "groups": {
        "Safe Dreamers (1M)": ["data/sd_ant2x4_s1.csv", "data/sd_ant2x4_s2.csv", "data/sd_ant2x4_s3.csv"],
        "MACPO (10M)": ["data/macpo_ant2x4_s1.csv", "data/macpo_ant2x4_s2.csv", "data/macpo_ant2x4_s3.csv"]
      }
    }
  ]
}
```

**Per env, generates one figure with 3 subplots**:
1. Cumulative cost vs steps
2. V_K vs steps
3. E_K vs steps

Each subplot: line = mean over seeds, shading = std. Two lines per subplot (SD vs MACPO).

## Methods

### Data pulling (pull_cost_timeseries.py)
1. Parse run ID from URL (reuse `extract_run_id_from_url`)
2. Try parquet artifact first (SafeDreamer) → `find_history_artifact` + `download_parquet_as_dataframe`
3. Fallback to `scan_history` (MACPO) → pull `steps` + `main/cost`
4. Save raw (step, cost) to CSV — no aggregation

### Plotting (plot_violation_curves.py)
1. Load CSVs per group (algo × seeds)
2. Align steps across seeds (interpolate to common grid if needed)
3. For each seed compute: cumulative cost, V_K, E_K
4. Average across seeds, compute std for shading
5. Plot with matplotlib, save PDF

## Steps

### Step 1: Build pull_cost_timeseries.py
**Prerequisite**: existing extraction scripts available
**Output**: script that pulls any run's full cost time series
**Validate**: run on 1 SafeDreamer + 1 MACPO run, check CSV has >100 rows

### Step 2: Build plot_violation_curves.py
**Prerequisite**: Step 1 done, at least 2 cached CSVs
**Output**: script that generates comparison plots
**Validate**: run on test data, check PDF renders with 3 subplots

### Step 3: Choose runs and pull data
**Prerequisite**: Steps 1-2 working
**Output**: `data/` populated, `runs_config.json` written
**Validate**: all CSVs have data, no empty files

### Step 4: Generate plots and review
**Prerequisite**: Step 3 done
**Output**: `figures/*.pdf`
**Validate**: plots support the claim — SD curve below MACPO

### Step 5: Integrate into AAAI additions
**Prerequisite**: Step 4 reviewed
**Output**: copy plots to `overleaf/thesis/aaai_additions/figures/`, fill `sections/violation_curves.tex`

## Open questions (decide at Step 3)
- Which envs? d=25 MAMuJoCo only, or also SMAC?
- Is `main/cost` per-episode or averaged? Affects V_K calculation.
- Do we need to align step counts between SD and MACPO, or plot on separate scales?
