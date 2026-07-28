#!/usr/bin/env python3
"""Plot beta (Lagrange multiplier) and episode cost vs training steps.

One figure per env: top panel beta, bottom panel cost with the limit line.
Seeds are interpolated onto a common step grid and averaged (mean +- std band).

Usage:
  python plot_beta_dynamics.py
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


def seed_series(csv_path: Path, column: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df[["step", column]].dropna()


def mean_band(files, column, grid):
    """Interpolate each seed onto grid; return mean and std arrays."""
    curves = []
    for f in files:
        s = seed_series(f, column)
        if s.empty:
            continue
        # Only cover the range this seed actually reached.
        vals = np.interp(grid, s["step"], s[column], left=np.nan, right=np.nan)
        vals[grid > s["step"].max()] = np.nan
        curves.append(vals)
    stack = np.vstack(curves)
    return np.nanmean(stack, axis=0), np.nanstd(stack, axis=0)


def plot_env(label: str, title: str, cost_limit: float):
    files = sorted(DATA_DIR.glob(f"{label}_s*.csv"))
    grid = np.linspace(0, MAX_STEPS, GRID_POINTS)

    fig, (ax_beta, ax_cost) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)

    beta_mean, beta_std = mean_band(files, "beta", grid)
    ax_beta.plot(grid, beta_mean, color="tab:blue")
    ax_beta.fill_between(grid, beta_mean - beta_std, beta_mean + beta_std, color="tab:blue", alpha=0.2)
    ax_beta.set_ylabel(r"$\beta$ (multiplier)")
    ax_beta.set_title(f"{title} (d={cost_limit:g})")
    ax_beta.grid(alpha=0.3)

    cost_mean, cost_std = mean_band(files, "cost", grid)
    ax_cost.plot(grid, cost_mean, color="tab:red")
    ax_cost.fill_between(grid, cost_mean - cost_std, cost_mean + cost_std, color="tab:red", alpha=0.2)
    ax_cost.axhline(cost_limit, color="black", linestyle="--", linewidth=1, label=f"limit d={cost_limit:g}")
    ax_cost.set_ylabel("episode cost")
    ax_cost.set_xlabel("environment steps")
    ax_cost.legend()
    ax_cost.grid(alpha=0.3)

    fig.tight_layout()
    out = FIG_DIR / f"{label}_beta_dynamics.pdf"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out.name}")


def main():
    config = json.loads((HERE / "runs_config.json").read_text())
    FIG_DIR.mkdir(exist_ok=True)
    for env, spec in config["envs"].items():
        plot_env(spec["label"], ENV_TITLES[env], spec["cost_limit"])


if __name__ == "__main__":
    main()
