#!/usr/bin/env python3
"""Extract SMAC MAPPO-Lag Batch B runs (jobs 19601155-173) from WandB.

Batch B = run names matching safepo_mappolag_dead_allies* with
time_20260728_0710* timestamp (winrate logging enabled).

Metrics: main/score, main/cost, main/winrate at target 5M env steps
(window-average over the last WINDOW steps before target; fallback to
last 3 logged rows). Outputs per-seed and aggregated CSVs next to this file.

Usage: python extract_mappolag_smac.py
"""

import re
import sys
from pathlib import Path

import pandas as pd

import wandb

ENTITY_PROJECT = "raz-shmueli-corsound-ai/private-mamba"
NAME_PREFIX = "safepo_mappolag_dead_allies"
BATCH_B_TS = "time_20260728_0710"
TARGET_STEP = 5_000_000
WINDOW = 50_000  # logging cadence is sparse; wider window than SafeDreamer's 5k
METRICS = ["main/score", "main/cost", "main/winrate"]
STEP = "steps"

NAME_RE = re.compile(
    r"safepo_mappolag_dead_allies_incremental_cost_limit=(?P<limit>[\d.]+)_"
    r"(?P<map>.+)_(?P<seed>\d)_time_(?P<ts>\d{8}_\d{6})"
)

OUT_DIR = Path(__file__).parent


def extract_run(run):
    hist = run.history(keys=[STEP] + METRICS, pandas=True, samples=10000)
    if hist is None or hist.empty or STEP not in hist.columns:
        return None
    hist = hist.dropna(subset=[STEP])
    win = hist[(hist[STEP] >= TARGET_STEP - WINDOW) & (hist[STEP] <= TARGET_STEP)]
    if win.empty:
        win = hist.sort_values(STEP).tail(3)
    row = {m.split("/")[-1]: win[m].mean() for m in METRICS if m in win.columns}
    row["step_at_extract"] = win[STEP].max()
    row["n_rows_in_window"] = len(win)
    return row


def main():
    api = wandb.Api(timeout=60)
    runs = api.runs(ENTITY_PROJECT, filters={"display_name": {"$regex": NAME_PREFIX}})
    records = []
    for run in runs:
        if BATCH_B_TS not in run.name:
            continue
        m = NAME_RE.match(run.name)
        if not m:
            print(f"SKIP (name parse failed): {run.name}", file=sys.stderr)
            continue
        if m["map"] == "bane_vs_bane":
            print(f"SKIP (bane OOM, parked): {run.name}")
            continue
        print(f"Extracting: {run.name} [{run.state}]")
        metrics = extract_run(run)
        if metrics is None:
            print(f"  WARNING: no history for {run.name}", file=sys.stderr)
            continue
        records.append(
            {
                "map": m["map"],
                "algorithm": "MAPPO-Lag",
                "cost_limit": float(m["limit"]),
                "seed": int(m["seed"]),
                "wandb_state": run.state,
                "wandb_id": run.id,
                **metrics,
            }
        )

    df = pd.DataFrame(records).sort_values(["map", "cost_limit", "seed"])
    per_seed_path = OUT_DIR / "mappolag_smac_per_seed.csv"
    df.to_csv(per_seed_path, index=False)
    print(f"\nWrote {per_seed_path} ({len(df)} rows)")

    agg = (
        df.groupby(["map", "algorithm", "cost_limit"])
        .agg(
            score_mean=("score", "mean"),
            score_std=("score", "std"),
            cost_mean=("cost", "mean"),
            cost_std=("cost", "std"),
            winrate_mean=("winrate", "mean"),
            winrate_std=("winrate", "std"),
            n_seeds=("seed", "nunique"),
        )
        .round(3)
        .reset_index()
    )
    agg_path = OUT_DIR / "mappolag_smac_agg.csv"
    agg.to_csv(agg_path, index=False)
    print(f"Wrote {agg_path} ({len(agg)} rows)")
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
