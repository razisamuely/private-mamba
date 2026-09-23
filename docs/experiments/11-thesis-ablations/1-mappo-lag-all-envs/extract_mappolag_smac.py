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
from pathlib import Path

import pandas as pd
import wandb

ENTITY_PROJECT = "raz-shmueli-corsound-ai/private-mamba"
NAME_PREFIX = "safepo_mappolag_dead_allies"
BATCH_TIMESTAMPS = ["time_20260728_0710", "time_20260901_", "time_20260903_"]
CHECKPOINTS = {
    "100k": (100_000, 10_000),
    "500k": (500_000, 25_000),
    "1M": (1_000_000, 50_000),
    "2M": (2_000_000, 50_000),
    "5M": (5_000_000, 50_000),
}
DEFAULT_CHECKPOINT = "5M"
METRICS = ["main/score", "main/cost", "main/winrate"]
STEP = "steps"

NAME_RE = re.compile(
    r"safepo_mappolag_dead_allies_incremental_cost_limit=(?P<limit>[\d.]+)_"
    r"(?P<map>.+)_(?P<seed>\d)_time_(?P<ts>\d{8}_\d{6})"
)

OUT_DIR = Path(__file__).parent


def extract_run(run, target_step, window):
    hist = run.history(keys=[STEP] + METRICS, pandas=True, samples=10000)
    if hist is None or hist.empty or STEP not in hist.columns:
        return None
    hist = hist.dropna(subset=[STEP])
    win = hist[(hist[STEP] >= target_step - window) & (hist[STEP] <= target_step)]
    if win.empty:
        win = hist.sort_values(STEP).tail(3)
    row = {m.split("/")[-1]: win[m].mean() for m in METRICS if m in win.columns}
    row["step_at_extract"] = win[STEP].max()
    row["n_rows_in_window"] = len(win)
    return row


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="all", help="Which checkpoint: 500k, 1M, 5M, or 'all' (default)")
    args = parser.parse_args()

    if args.checkpoint == "all":
        targets = list(CHECKPOINTS.items())
    else:
        targets = [(args.checkpoint, CHECKPOINTS[args.checkpoint])]

    api = wandb.Api(timeout=60)
    runs_list = list(api.runs(ENTITY_PROJECT, filters={"display_name": {"$regex": NAME_PREFIX}}))

    # Filter runs once
    valid_runs = []
    for run in runs_list:
        if not any(ts in run.name for ts in BATCH_TIMESTAMPS):
            continue
        m = NAME_RE.match(run.name)
        if not m:
            continue
        if run.state == "crashed" and "time_20260903_" not in run.name:
            continue
        valid_runs.append((run, m))

    print(f"Found {len(valid_runs)} valid runs\n")

    for ckpt_name, (target_step, window) in targets:
        print(f"=== Extracting at {ckpt_name} (step={target_step}, window={window}) ===")
        records = []
        for run, m in valid_runs:
            metrics = extract_run(run, target_step, window)
            if metrics is None:
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
        df = df.drop_duplicates(subset=["map", "cost_limit", "seed"], keep="last")

        suffix = f"_{ckpt_name}" if ckpt_name != "5M" else ""
        per_seed_path = OUT_DIR / f"mappolag_smac_per_seed{suffix}.csv"
        df.to_csv(per_seed_path, index=False)
        print(f"Wrote {per_seed_path} ({len(df)} rows)")

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
        agg_path = OUT_DIR / f"mappolag_smac_agg{suffix}.csv"
        agg.to_csv(agg_path, index=False)
        print(f"Wrote {agg_path} ({len(agg)} rows)\n")


if __name__ == "__main__":
    main()
