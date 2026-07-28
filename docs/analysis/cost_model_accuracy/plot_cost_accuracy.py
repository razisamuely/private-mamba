#!/usr/bin/env python3
"""Plot predicted vs actual average cost of the world model over training.

One figure per env: both curves overlaid (seed mean +- std), clipped at 1M steps.

Usage:
  python plot_cost_accuracy.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
FIG_DIR = HERE / "figures"

GRID_POINTS = 500
MAX_STEPS = 1_000_000  # paper budget; runs kept training past it
ENV_TITLES = {
    "Safety2x4AntVelocity-v0": "Ant 2x4",
    "Safety4x2AntVelocity-v0": "Ant 4x2",
    "Safety2x3HalfCheetahVelocity-v0": "HalfCheetah 2x3",
}


def mean_band(files, column, grid):
    curves = []
    for f in files:
        s = pd.read_csv(f)[["step", column]].dropna()
        if s.empty:
            continue
        vals = np.interp(grid, s["step"], s[column], left=np.nan, right=np.nan)
        vals[grid > s["step"].max()] = np.nan
        curves.append(vals)
    stack = np.vstack(curves)
    return np.nanmean(stack, axis=0), np.nanstd(stack, axis=0)


def plot_env(label: str, title: str):
    files = sorted(DATA_DIR.glob(f"{label}_s*.csv"))
    grid = np.linspace(0, MAX_STEPS, GRID_POINTS)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    for column, color, name in (
        ("actual", "tab:red", "actual cost"),
        ("predicted", "tab:blue", "predicted cost"),
    ):
        mean, std = mean_band(files, column, grid)
        ax.plot(grid, mean, color=color, label=name)
        ax.fill_between(grid, mean - std, mean + std, color=color, alpha=0.2)

    ax.set_title(title)
    ax.set_xlabel("environment steps")
    ax.set_ylabel("average cost (training batches)")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()
    out = FIG_DIR / f"{label}_cost_accuracy.pdf"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out.name}")


def main():
    config = json.loads((HERE / "runs_config.json").read_text())
    FIG_DIR.mkdir(exist_ok=True)
    for env, spec in config["envs"].items():
        plot_env(spec["label"], ENV_TITLES[env])


if __name__ == "__main__":
    main()
