#!/usr/bin/env python3
"""Pull beta timeseries from WandB and plot β dynamics for SMAC maps.

Outputs data/*.csv and figures/*.pdf in this directory.

Usage:
  python pull_and_plot_beta.py            # pull from WandB + plot
  python pull_and_plot_beta.py --plot-only # plot from existing data/
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import wandb

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
FIG_DIR = HERE / "figures"
CONFIG_FILE = HERE / "runs_config_smac.json"

ENTITY_PROJECT = "raz-shmueli-corsound-ai/private-mamba"

BETA_KEY = "Agent/Lagrangian"
COST_KEY = "main/cost"
STEP_KEY = "steps"
HISTORY_SAMPLES = 10000

MAX_STEPS = 100_000  # SafeDreamer SMAC runs are 100k
GRID_POINTS = 500


def pull_run(api, run_name: str, output: Path) -> int:
    """Find run by display name, pull beta + cost timeseries via history API."""
    runs = api.runs(ENTITY_PROJECT, filters={"display_name": run_name})
    run = None
    for r in runs:
        if r.name == run_name:
            run = r
            break
    if run is None:
        raise RuntimeError(f"run not found: {run_name}")

    # Pull beta and cost/steps separately (logged in different wandb.log calls)
    beta_hist = run.history(keys=[BETA_KEY], pandas=True, samples=HISTORY_SAMPLES)
    cost_hist = run.history(keys=[STEP_KEY, COST_KEY], pandas=True, samples=HISTORY_SAMPLES)

    rows = []
    if beta_hist is not None and BETA_KEY in beta_hist.columns:
        bdf = beta_hist.dropna(subset=[BETA_KEY])
        for _, r in bdf.iterrows():
            rows.append({"_step": r["_step"], "beta": r[BETA_KEY], "cost": np.nan})

    if cost_hist is not None and COST_KEY in cost_hist.columns:
        cdf = cost_hist.dropna(subset=[COST_KEY])
        if STEP_KEY in cdf.columns:
            for _, r in cdf.iterrows():
                rows.append({"_step": r["_step"], "env_step": r[STEP_KEY], "beta": np.nan, "cost": r[COST_KEY]})

    if not rows:
        raise RuntimeError(f"no beta or cost data for {run_name}")

    df = pd.DataFrame(rows).sort_values("_step")

    # Interpolate env steps for beta rows using cost rows as anchors
    anchor = df.dropna(subset=["env_step"]).sort_values("_step")
    if not anchor.empty:
        df["step"] = np.interp(df["_step"], anchor["_step"], anchor["env_step"])
    else:
        df["step"] = df["_step"]

    out = df[["step", "beta", "cost"]].reset_index(drop=True)
    out.to_csv(output, index=False)
    return len(out)


def pull_all(config: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    api = wandb.Api(timeout=60)
    for env, spec in config["envs"].items():
        for seed_idx, run_name in enumerate(spec["runs"], start=1):
            output = DATA_DIR / f"{spec['label']}_s{seed_idx}.csv"
            try:
                n = pull_run(api, run_name, output)
                print(f"[{output.name}] {n} rows")
            except Exception as e:
                print(f"[{output.name}] FAILED: {e}", file=sys.stderr)


def mean_band(files, column, grid):
    curves = []
    for f in files:
        df = pd.read_csv(f)
        s = df[["step", column]].dropna()
        if s.empty:
            continue
        vals = np.interp(grid, s["step"], s[column], left=np.nan, right=np.nan)
        vals[grid > s["step"].max()] = np.nan
        curves.append(vals)
    if not curves:
        return np.full_like(grid, np.nan), np.full_like(grid, np.nan)
    stack = np.vstack(curves)
    return np.nanmean(stack, axis=0), np.nanstd(stack, axis=0)


def plot_env(label: str, title: str, cost_limit: float):
    files = sorted(DATA_DIR.glob(f"{label}_s*.csv"))
    if not files:
        print(f"SKIP {label}: no data files")
        return
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


def plot_all(config: dict) -> None:
    FIG_DIR.mkdir(exist_ok=True)
    for env, spec in config["envs"].items():
        plot_env(spec["label"], env, spec["cost_limit"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot-only", action="store_true", help="Skip WandB pull, plot from existing data/")
    args = parser.parse_args()

    config = json.loads(CONFIG_FILE.read_text())

    if not args.plot_only:
        pull_all(config)

    plot_all(config)


if __name__ == "__main__":
    main()
