#!/usr/bin/env python3
"""Theorem 1 empirical check — MAMuJoCo or SMAC SafeDreamer runs.

Pulls model-error and cost metrics from existing WandB logs (zero new
compute), converts real and imagined costs to a common 15-step discounted
scale, and computes the Theorem 1 bound Delta = 15*eps_c + 105*c_max*TV
(TV via Pinsker from the prior/posterior KL). See plan.md and notes.md.

Usage:
  python extract_theorem1.py --env mamujoco   # Exp 8 SafeDreamer runs
  python extract_theorem1.py --env smac       # SMAC SafeDreamer runs
"""

import argparse
import math
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import wandb

# ---------------------------------------------------------------------------
# Per-environment config
# ---------------------------------------------------------------------------
ENV_CONFIGS = {
    "mamujoco": {
        "prefixes": ("safedreamer_dai_safety_gym", "fix-logprob_dai_safety_gym"),
        "exclude": "_nocomm",
        "regex": re.compile(
            r"(?:safedreamer|fix-logprob)_dai_safety_gym_"
            r"lag(?P<laglr>[\d.e-]+)_(?P<limit>[\d.]+)_"
            r"(?P<env>Safety\w+-v0)_s(?P<seed>\d)_"
        ),
        "env_field": "env",
        "c_max": 1.0,
        "group_cols": ["env", "cost_limit", "laglr"],
    },
    "smac": {
        "prefixes": ("safedreamer_dead_allies_incremental_starcraft",),
        "exclude": "_nocomm",
        "regex": re.compile(
            r"safedreamer_dead_allies_incremental_starcraft_"
            r"lag(?P<laglr>[\d.e-]+)_(?P<limit>[\d.]+)_"
            r"(?P<env>[A-Za-z0-9_]+)_s(?P<seed>\d)_"
        ),
        "env_field": "env",
        "c_max": 1.0,  # dead_allies_incremental: 0 or 1 per step
        "group_cols": ["env", "cost_limit", "laglr"],
    },
}

# --- WandB ------------------------------------------------------------------
ENTITY_PROJECT = "raz-shmueli-corsound-ai/private-mamba"

# --- Metric keys ------------------------------------------------------------
STEP_KEY = "steps"
EPS_C_KEY = "Model/cost_loss"
KL_KEY = "Model/div"
IMAG_COST_KEY = "Value/Cost"
REAL_COST_KEY = "main/cost"

# --- Theorem 1 constants ---------------------------------------------------
GAMMA = 0.99
HORIZON = 15
DISCOUNT_SUM = sum(GAMMA**t for t in range(HORIZON))  # ~13.9
LINEAR_FACTOR = HORIZON  # 15
QUADRATIC_FACTOR = HORIZON * (HORIZON - 1) // 2  # 105

# --- Extraction window ------------------------------------------------------
TAIL_FRACTION = 0.1
HISTORY_SAMPLES = 10000

OUT_DIR = Path(__file__).parent


def _tv_from_kl(kl: float) -> float:
    return math.sqrt(max(kl, 0.0) / 2.0)


def _episode_length(steps: pd.Series) -> float:
    diffs = steps.sort_values().diff().dropna()
    diffs = diffs[diffs > 0]
    return float(diffs.mean()) if not diffs.empty else float("nan")


def _tail_mean(run: "wandb.apis.public.Run", key: str) -> float:
    hist = run.history(keys=[key], pandas=True, samples=HISTORY_SAMPLES)
    if hist is None or hist.empty or key not in hist.columns:
        return float("nan")
    values = hist.dropna(subset=[key])[key]
    if values.empty:
        return float("nan")
    n_tail = max(1, int(len(values) * TAIL_FRACTION))
    return float(values.tail(n_tail).mean())


def _delta_bound(eps_c: float, kl: float, c_max: float) -> float:
    return LINEAR_FACTOR * eps_c + QUADRATIC_FACTOR * c_max * _tv_from_kl(kl)


def _windowed_cost(per_step_cost: float) -> float:
    return per_step_cost * DISCOUNT_SUM


def extract_run(run: "wandb.apis.public.Run", cfg: dict) -> Optional[dict]:
    match = cfg["regex"].match(run.name)
    if match is None:
        return None

    step_hist = run.history(keys=[STEP_KEY], pandas=True, samples=HISTORY_SAMPLES)
    if step_hist is None or step_hist.empty or STEP_KEY not in step_hist.columns:
        return None
    steps = step_hist.dropna(subset=[STEP_KEY])[STEP_KEY]

    eps_c = _tail_mean(run, EPS_C_KEY)
    kl = _tail_mean(run, KL_KEY)
    imag_cost_step = _tail_mean(run, IMAG_COST_KEY)
    real_cost_episode = _tail_mean(run, REAL_COST_KEY)
    ep_len = _episode_length(steps)

    real_cost_step = real_cost_episode / ep_len if ep_len > 0 else float("nan")
    real_15 = _windowed_cost(real_cost_step)
    imag_15 = _windowed_cost(imag_cost_step)

    return {
        "env": match[cfg["env_field"]],
        "cost_limit": float(match["limit"]),
        "laglr": match["laglr"],
        "seed": int(match["seed"]),
        "run_name": run.name,
        "state": run.state,
        "last_step": float(steps.max()),
        "episode_length": ep_len,
        "eps_c": eps_c,
        "kl_div": kl,
        "tv_proxy": _tv_from_kl(kl),
        "imag_cost_15step": imag_15,
        "real_cost_15step": real_15,
        "observed_gap": abs(real_15 - imag_15),
        "delta_bound": _delta_bound(eps_c, kl, cfg["c_max"]),
    }


def aggregate(per_run: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    value_cols = [
        "eps_c",
        "kl_div",
        "tv_proxy",
        "imag_cost_15step",
        "real_cost_15step",
        "observed_gap",
        "delta_bound",
    ]
    agg = per_run.groupby(group_cols)[value_cols].agg(["mean", "std"])
    agg.columns = ["_".join(c) for c in agg.columns]
    agg["n_seeds"] = per_run.groupby(group_cols)["seed"].count()
    return agg.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description="Theorem 1 empirical check")
    parser.add_argument(
        "--env", required=True, choices=list(ENV_CONFIGS.keys()), help="Environment type: mamujoco or smac"
    )
    args = parser.parse_args()

    cfg = ENV_CONFIGS[args.env]
    per_run_csv = OUT_DIR / f"theorem1_{args.env}_per_run.csv"
    agg_csv = OUT_DIR / f"theorem1_{args.env}_agg.csv"

    api = wandb.Api(timeout=60)
    records = []
    for prefix in cfg["prefixes"]:
        runs = api.runs(ENTITY_PROJECT, filters={"display_name": {"$regex": f"^{prefix}"}})
        for run in runs:
            if cfg["exclude"] in run.name:
                continue
            row = extract_run(run, cfg)
            if row is not None:
                records.append(row)
                print(f"extracted: {run.name}")

    per_run = pd.DataFrame(records).sort_values(cfg["group_cols"] + ["seed"])
    per_run.to_csv(per_run_csv, index=False)
    agg = aggregate(per_run, cfg["group_cols"])
    agg.to_csv(agg_csv, index=False)
    print(f"\n{len(per_run)} runs -> {per_run_csv.name}, {len(agg)} groups -> {agg_csv.name}")
    print(agg.to_string())


if __name__ == "__main__":
    main()
