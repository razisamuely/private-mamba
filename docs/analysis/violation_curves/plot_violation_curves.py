#!/usr/bin/env python3
"""
Plot cumulative cost curves from cached cost time series CSVs.

Reads CSVs (step, cost) grouped by algorithm, computes cumulative cost
(scaled by episodes_per_point for batch-averaged logs like MACPO).

Outputs one PDF per env showing SD (clipped at max_steps) vs MACPO (full range).

Usage:
  python plot_violation_curves.py --config runs_config.json --output-dir figures/
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_and_compute(csv_path: str, max_steps: float, episodes_per_point: int, cost_limit: float = 0) -> pd.DataFrame:
    """Load a (step, cost) CSV, clip to max_steps, scale cost, compute cumulative."""
    df = pd.read_csv(csv_path)
    df = df.sort_values("step").reset_index(drop=True)
    df = df[df["step"] <= max_steps]
    df["total_cost"] = df["cost"] * episodes_per_point
    df["cum_cost"] = df["total_cost"].cumsum()
    df["excess"] = np.maximum(df["cost"] - cost_limit, 0) * episodes_per_point
    df["cum_excess"] = df["excess"].cumsum()
    return df


def interpolate_to_grid(df: pd.DataFrame, grid: np.ndarray, col: str = "cum_cost") -> np.ndarray:
    """Interpolate a column to a common step grid. Flat after last data point."""
    if df.empty:
        return np.zeros_like(grid)
    steps = df["step"].values
    cum = df[col].values
    result = np.interp(grid, steps, cum)
    # Flat after last data point (don't extrapolate)
    last_step = steps[-1]
    last_val = cum[-1]
    result[grid > last_step] = last_val
    return result


def plot_comparison(config_entry: dict, output_dir: Path):
    """Generate one cumulative cost figure for one env comparison."""
    env = config_entry["env"]
    cost_limit = config_entry["cost_limit"]
    groups = config_entry["groups"]

    # Grid goes to max of all groups' max_steps
    global_max = max(g["max_steps"] for g in groups.values())
    grid = np.linspace(0, global_max, 2000)

    plot_cfgs = [
        ("cum_cost", "Cumulative Cost (all)", "Cumulative Cost"),
        ("cum_excess", f"Cumulative Excess Cost (above d={cost_limit})", "Cumulative Excess"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(f"Training Cost — {env}  (d = {cost_limit})", fontsize=14)

    colors = plt.cm.tab10.colors

    for ax_idx, (col, title, ylabel) in enumerate(plot_cfgs):
        ax = axes[ax_idx]

        for group_idx, (label, group_cfg) in enumerate(groups.items()):
            csv_files = group_cfg["files"]
            max_steps = group_cfg["max_steps"]
            epp = group_cfg["episodes_per_point"]

            seed_curves = []
            for f in csv_files:
                df = load_and_compute(f, max_steps, epp, cost_limit)
                seed_curves.append(interpolate_to_grid(df, grid, col))

            arr = np.array(seed_curves)
            mean = arr.mean(axis=0)
            std = arr.std(axis=0)
            color = colors[group_idx % len(colors)]

            # Only plot up to this group's max_steps
            mask = grid <= max_steps
            ax.plot(grid[mask], mean[mask], label=label, color=color, linewidth=2)
            ax.fill_between(grid[mask], (mean - std)[mask], (mean + std)[mask], alpha=0.2, color=color)

        ax.axvline(x=1_000_000, color="gray", linestyle="--", alpha=0.5, label="SD training ends (1M)")
        ax.set_title(title)
        ax.set_xlabel("Environment Steps")
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    safe_env = env.replace("/", "_").replace(" ", "_")
    out_path = output_dir / f"{safe_env}_cumulative_cost.pdf"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Plot cumulative cost curves")
    parser.add_argument("--config", type=str, required=True, help="JSON config file")
    parser.add_argument("--output-dir", type=str, default="figures", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config) as f:
        config = json.load(f)

    for entry in config["comparisons"]:
        plot_comparison(entry, output_dir)


if __name__ == "__main__":
    main()
