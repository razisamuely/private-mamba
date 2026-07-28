#!/usr/bin/env python3
"""Extract MACPO + MAPPO-Lag at 1M env steps (same-budget comparison) -> append to main CSV.

Incremental pattern: reuses the experiment-8 pipeline's extraction/aggregation.
Sources are relabeled "MACPO Run (1M)" / "MAPPO-Lag Run (1M)".

Usage:
  python extract_baselines_1m.py            # extract + save per-seed CSV here
  python extract_baselines_1m.py --append   # also back up + append aggregated rows to main CSV
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "../../tmp/extraction/scripts"
sys.path.insert(0, str(SCRIPTS))

from extract_metrics import (
    average_metrics_in_env_step_window,
    extract_run_id_from_url,
    fetch_run_history_as_dataframe,
)
from extraction_config import TABLE_COL_COST, TABLE_COL_SCORE, WINDOW_SIZE
from mamujoco_pipeline_experiment8 import (
    COL_ENV,
    COL_LAGLR,
    COL_SOURCE,
    COL_STEPS,
    INPUT_CSV,
    aggregate,
)
from wandb_config import WANDB_PROJECT, WANDB_TIMEOUT

import wandb

TARGET = 1_000_000
MAIN_CSV = HERE / "../../tmp/tables/mamujoco_comparison_experiment8/comparison_table_real_20260628_144800.csv"
PER_SEED_CSV = HERE / "baselines_1m_per_seed.csv"
SOURCE_LABELS = {"MACPO": "MACPO Run (1M)", "MAPPO-Lag": "MAPPO-Lag Run (1M)"}
COST_LIMIT = 25.0


def load_baseline_runs() -> list[dict]:
    df = pd.read_csv(INPUT_CSV)
    runs = []
    for _, row in df.iterrows():
        if row["algorithm"] not in SOURCE_LABELS or float(row["cost_limit"]) != COST_LIMIT:
            continue
        run_id = extract_run_id_from_url(row["wandb_link"])
        if not run_id:
            print(f"skip (no link): {row['algorithm']} {row['env']} s{row['seed']}")
            continue
        runs.append(
            {
                "run_id": run_id,
                "env": row["env"],
                "algorithm": row["algorithm"],
                "seed": int(row["seed"]),
            }
        )
    return runs


def extract(api, runs: list[dict]) -> pd.DataFrame:
    rows = []
    for exp in runs:
        print(f"Extracting {exp['algorithm']} {exp['env']} s{exp['seed']} @ {TARGET}...")
        import urllib.parse

        run = api.run(f"{WANDB_PROJECT}/{urllib.parse.unquote(exp['run_id'])}")
        df = fetch_run_history_as_dataframe(run, TARGET)
        result = average_metrics_in_env_step_window(df, TARGET, WINDOW_SIZE)
        rows.append(
            {
                COL_ENV: exp["env"],
                "cost_limit": COST_LIMIT,
                COL_SOURCE: SOURCE_LABELS[exp["algorithm"]],
                "seed": exp["seed"],
                COL_STEPS: TARGET,
                TABLE_COL_SCORE: result.get("avg_score"),
                TABLE_COL_COST: result.get("avg_cost"),
                "reached_target": result.get("reached_target"),
            }
        )
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--append", action="store_true", help="append aggregated rows to main CSV")
    args = parser.parse_args()

    api = wandb.Api(timeout=WANDB_TIMEOUT)
    per_seed = extract(api, load_baseline_runs())
    per_seed.to_csv(PER_SEED_CSV, index=False)
    print(f"\nPer-seed ({len(per_seed)} rows) -> {PER_SEED_CSV.name}")

    agg = aggregate(per_seed.drop(columns=["reached_target"]))
    agg[COL_LAGLR] = ""
    print(agg.to_string(index=False))

    if args.append:
        main_df = pd.read_csv(MAIN_CSV)
        backup = MAIN_CSV.with_name(MAIN_CSV.stem + "_pre_baselines1m_backup.csv")
        main_df.to_csv(backup, index=False)
        combined = pd.concat([main_df, agg[main_df.columns.tolist()]], ignore_index=True)
        combined.to_csv(MAIN_CSV, index=False)
        print(f"\nBacked up -> {backup.name}; main CSV {len(main_df)} -> {len(combined)} rows")


if __name__ == "__main__":
    main()
