#!/usr/bin/env python3
"""
Pull full cost time series from WandB runs → CSV.

Algorithm-agnostic: works for SafeDreamer (parquet artifact) and MACPO (scan_history).
Outputs one CSV per run with columns: step, cost.

Usage:
  # Single run
  python pull_cost_timeseries.py --run-id <wandb_run_id> --output data/my_run.csv

  # Batch from CSV (columns: run_id, label)
  python pull_cost_timeseries.py --input-csv runs.csv --output-dir data/
"""

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

import wandb

# Add extraction scripts to path for reuse
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../tmp/extraction/scripts"))

from extract_metrics import (
    download_parquet_as_dataframe,
    extract_run_id_from_url,
    filter_valid_metric_rows,
    find_history_artifact,
)
from extraction_config import FALLBACK_STEP_COL, STEP_COL
from wandb_config import WANDB_PROJECT, WANDB_TIMEOUT

COST_KEY = "main/cost"


def fetch_full_history(run) -> pd.DataFrame:
    """Fetch full (step, cost) time series from a WandB run.

    Strategy:
    1. Parquet artifact (SafeDreamer) — full history, uses env 'steps' column.
    2. scan_history fallback (MACPO) — pulls all rows, no step filtering.

    Returns DataFrame with columns: step, cost. Sorted by step, NaNs dropped.
    """
    # Try parquet artifact first (SafeDreamer)
    artifact = find_history_artifact(run)
    if artifact is not None:
        df = download_parquet_as_dataframe(artifact)
        df = filter_valid_metric_rows(df)
        if not df.empty and COST_KEY in df.columns:
            out = df[[STEP_COL, COST_KEY]].dropna().copy()
            out.columns = ["step", "cost"]
            return out.sort_values("step").reset_index(drop=True)

    # Fallback: scan_history (MACPO / any algo without parquet)
    rows = list(run.scan_history(keys=[STEP_COL, COST_KEY], page_size=10_000))
    if not rows:
        # Try fallback step column
        rows = list(run.scan_history(keys=[FALLBACK_STEP_COL, COST_KEY], page_size=10_000))
        if rows:
            df = pd.DataFrame(rows).dropna(subset=[FALLBACK_STEP_COL, COST_KEY])
            df = df.rename(columns={FALLBACK_STEP_COL: "step", COST_KEY: "cost"})
        else:
            return pd.DataFrame(columns=["step", "cost"])
    else:
        df = pd.DataFrame(rows).dropna(subset=[STEP_COL, COST_KEY])
        df = df.rename(columns={STEP_COL: "step", COST_KEY: "cost"})

    return df[["step", "cost"]].sort_values("step").reset_index(drop=True)


def pull_single_run(api, run_id: str, output_path: Path) -> int:
    """Pull one run's cost time series and save to CSV. Returns row count."""
    run = api.run(f"{WANDB_PROJECT}/{run_id}")
    df = fetch_full_history(run)
    df.to_csv(output_path, index=False)
    return len(df)


def main():
    parser = argparse.ArgumentParser(description="Pull cost time series from WandB")
    parser.add_argument("--run-id", type=str, help="Single WandB run ID or URL")
    parser.add_argument("--output", type=str, help="Output CSV path (for single run)")
    parser.add_argument("--input-csv", type=str, help="Batch CSV with columns: run_id, label")
    parser.add_argument("--output-dir", type=str, default="data", help="Output dir (for batch)")
    args = parser.parse_args()

    api = wandb.Api(timeout=WANDB_TIMEOUT)

    if args.run_id:
        # Single run mode
        run_id = args.run_id
        if "wandb.ai" in run_id:
            run_id = extract_run_id_from_url(run_id)
        output = Path(args.output) if args.output else Path(args.output_dir) / f"{run_id}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        n = pull_single_run(api, run_id, output)
        print(f"Saved {n} rows → {output}")

    elif args.input_csv:
        # Batch mode
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(args.input_csv) as f:
            for row in csv.DictReader(f):
                run_id = row.get("run_id", "").strip()
                label = row.get("label", run_id).strip()
                if not run_id:
                    continue
                if "wandb.ai" in run_id:
                    run_id = extract_run_id_from_url(run_id)
                output = output_dir / f"{label}.csv"
                try:
                    n = pull_single_run(api, run_id, output)
                    print(f"[{label}] {n} rows → {output}")
                except Exception as e:
                    print(f"[{label}] FAILED: {e}", file=sys.stderr)
    else:
        parser.error("Provide --run-id or --input-csv")


if __name__ == "__main__":
    main()
