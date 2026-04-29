#!/usr/bin/env python3
"""
fetch_results.py — Fetch Safe Dreamers results from a wandb_runs.json definition.

PYTHON: /home/corsound/workspace/overleaf/thesis/venv/bin/python3

USAGE:
  python3 fetch_results.py --exp docs/experiments/6-lag-real-episode-cost
  python3 fetch_results.py --exp docs/experiments/6-lag-real-episode-cost --cost-fn dead_allies_incremental
  python3 fetch_results.py --exp docs/experiments/6-lag-real-episode-cost --map 8m
  python3 fetch_results.py --exp docs/experiments/6-lag-real-episode-cost --out docs/results/safe_dreamers_runs.csv

Set WANDB_API_KEY env var before running.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from results_helpers import (
    DEFAULT_TARGET_STEP,
    aggregate_seeds,
    fetch_run_at_step,
    get_api,
)

RESULTS_CSV = Path(__file__).parent.parent / "safe_dreamers_runs.csv"


def load_runs(
    exp_path: str,
    cost_fn: str | None = None,
    map_filter: str | None = None,
) -> tuple[list[dict], str]:
    """Load run definitions from wandb_runs.json in experiment folder."""
    runs_file = Path(exp_path) / "wandb_runs.json"
    if not runs_file.exists():
        print(f"ERROR: {runs_file} not found")
        sys.exit(1)
    with open(runs_file) as f:
        data = json.load(f)
    runs = data["runs"]
    if cost_fn:
        runs = [r for r in runs if r["cost_fn"] == cost_fn]
    if map_filter:
        runs = [r for r in runs if r["map"] == map_filter]
    return runs, data.get("experiment", "unknown")


def update_csv(csv_path: str, results_by_seed: dict) -> None:
    """Update safe_dreamers_runs.csv with fetched score/cost/winrate values."""
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    updated = 0
    for row in rows:
        key = (row["map"], int(row["cost_limit"]), int(row["seed"]))
        if key in results_by_seed:
            r = results_by_seed[key]
            if r["score"] is not None:
                row["score"] = r["score"]
                row["cost"] = r["cost"]
                row["winrate"] = r["winrate"]
                updated += 1

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nUpdated {updated} rows in {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", required=True, help="Path to experiment folder")
    parser.add_argument("--cost-fn", help="Filter by cost function")
    parser.add_argument("--map", help="Filter by map name")
    parser.add_argument("--out", help="CSV path to update")
    parser.add_argument("--target-step", type=int, default=DEFAULT_TARGET_STEP)
    args = parser.parse_args()

    runs, exp_name = load_runs(args.exp, args.cost_fn, args.map)
    print(f"Experiment: {exp_name}  |  {len(runs)} runs")
    print()

    api = get_api()
    seed_data: dict = defaultdict(list)
    results_by_seed: dict = {}

    for r in runs:
        map_name, cost_limit, cost_fn, seed, run_id = (r["map"], r["cost_limit"], r["cost_fn"], r["seed"], r["run_id"])
        print(f"{map_name} cost={cost_limit} [{cost_fn}] seed={seed} ...", end=" ", flush=True)
        try:
            result = fetch_run_at_step(api, run_id, target_step=args.target_step)
        except Exception as e:
            print(f"[ERROR: {e}]")
            continue
        print(f"[{result['status']}] score={result['score']}  cost={result['cost']}  wr={result['winrate']}")

        if result["score"] is not None:
            seed_data[(map_name, cost_limit, cost_fn)].append((result["score"], result["cost"], result["winrate"]))
            results_by_seed[(map_name, cost_limit, seed)] = result

    print("\n" + "=" * 60)
    print("AGGREGATED (mean ± std across seeds)")
    print("=" * 60)
    for (map_name, cost_limit, cost_fn), vals in sorted(seed_data.items()):
        agg = aggregate_seeds(vals)
        print(f"{map_name} cost={cost_limit} [{cost_fn}] (n={len(vals)}):")
        print(f"  score:   {agg['score_mean']} ± {agg['score_std']}")
        print(f"  cost:    {agg['cost_mean']} ± {agg['cost_std']}")
        print(f"  winrate: {agg['winrate_mean']} ± {agg['winrate_std']}")

    csv_path = args.out or str(RESULTS_CSV)
    if os.path.exists(csv_path):
        update_csv(csv_path, results_by_seed)
    else:
        print(f"\nSkipping CSV update — {csv_path} not found")


if __name__ == "__main__":
    main()
