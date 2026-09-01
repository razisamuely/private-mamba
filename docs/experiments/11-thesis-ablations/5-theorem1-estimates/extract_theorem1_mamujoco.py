#!/usr/bin/env python3
"""Theorem 1 empirical check — MAMuJoCo (Exp 8 SafeDreamer full-comm runs).

Pulls model-error and cost metrics from existing WandB logs (zero new
compute), converts real and imagined costs to a common 15-step discounted
scale, and computes the Theorem 1 bound Delta = 15*eps_c + 105*c_max*TV
(TV via Pinsker from the prior/posterior KL). See plan.md and notes.md.

Outputs (next to this file):
  theorem1_mamujoco_per_run.csv  — one row per run
  theorem1_mamujoco_agg.csv      — mean/std per env x cost_limit x laglr

Usage: python extract_theorem1_mamujoco.py
"""

import math
import re
from pathlib import Path
from typing import Optional

import pandas as pd

import wandb

# --- WandB source -----------------------------------------------------------
ENTITY_PROJECT = "raz-shmueli-corsound-ai/private-mamba"
RUN_NAME_PREFIXES = ("safedreamer_dai_safety_gym", "fix-logprob_dai_safety_gym")
EXCLUDE_TOKEN = "_nocomm"

NAME_RE = re.compile(
    r"(?:safedreamer|fix-logprob)_dai_safety_gym_"
    r"lag(?P<laglr>[\d.e-]+)_(?P<limit>[\d.]+)_"
    r"(?P<env>Safety\w+-v0)_s(?P<seed>\d)_"
)

# --- Metric keys (see notes.md "MAMuJoCo check") ----------------------------
STEP_KEY = "steps"
EPS_C_KEY = "Model/cost_loss"  # cost-head error (eps_c)
KL_KEY = "Model/div"  # prior-vs-posterior KL (eps_P proxy)
IMAG_COST_KEY = "Value/Cost"  # imagined cost per dreamed step
REAL_COST_KEY = "main/cost"  # real episode total cost
ALL_KEYS = [STEP_KEY, EPS_C_KEY, KL_KEY, IMAG_COST_KEY, REAL_COST_KEY]

# --- Theorem 1 constants (chapters/04_theory.tex) ---------------------------
GAMMA = 0.99
HORIZON = 15
C_MAX = 1.0  # exact: binary velocity cost (see plan.md step 2)
DISCOUNT_SUM = sum(GAMMA**t for t in range(HORIZON))  # ~13.9
LINEAR_FACTOR = HORIZON  # 15, multiplies eps_c
QUADRATIC_FACTOR = HORIZON * (HORIZON - 1) // 2  # 105, multiplies c_max*TV

# --- Extraction window ------------------------------------------------------
TAIL_FRACTION = 0.1  # average metrics over the last 10% of logged rows
HISTORY_SAMPLES = 10000

OUT_DIR = Path(__file__).parent
PER_RUN_CSV = OUT_DIR / "theorem1_mamujoco_per_run.csv"
AGG_CSV = OUT_DIR / "theorem1_mamujoco_agg.csv"


def _tv_from_kl(kl: float) -> float:
    """Pinsker's inequality upper bound: TV <= sqrt(KL / 2)."""
    return math.sqrt(max(kl, 0.0) / 2.0)


def _episode_length(steps: pd.Series) -> float:
    """Mean episode length = mean positive diff of the cumulative step counter."""
    diffs = steps.sort_values().diff().dropna()
    diffs = diffs[diffs > 0]
    return float(diffs.mean()) if not diffs.empty else float("nan")


def _tail_mean(run: "wandb.apis.public.Run", key: str) -> float:
    """Mean of one metric over the last TAIL_FRACTION of its logged rows.

    Fetched per key: different metrics are logged in separate wandb.log
    calls and never share history rows.
    """
    hist = run.history(keys=[key], pandas=True, samples=HISTORY_SAMPLES)
    if hist is None or hist.empty or key not in hist.columns:
        return float("nan")
    values = hist.dropna(subset=[key])[key]  # history rows arrive in log order
    if values.empty:
        return float("nan")
    n_tail = max(1, int(len(values) * TAIL_FRACTION))
    return float(values.tail(n_tail).mean())


def _delta_bound(eps_c: float, kl: float) -> float:
    """Theorem 1 margin: 15*eps_c + 105*c_max*TV (undiscounted upper form)."""
    return LINEAR_FACTOR * eps_c + QUADRATIC_FACTOR * C_MAX * _tv_from_kl(kl)


def _windowed_cost(per_step_cost: float) -> float:
    """Cost per discounted 15-step window."""
    return per_step_cost * DISCOUNT_SUM


def extract_run(run: "wandb.apis.public.Run") -> Optional[dict]:
    match = NAME_RE.match(run.name)
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
        "env": match["env"],
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
        "delta_bound": _delta_bound(eps_c, kl),
    }


def aggregate(per_run: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["env", "cost_limit", "laglr"]
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
    api = wandb.Api(timeout=60)
    records = []
    for prefix in RUN_NAME_PREFIXES:
        runs = api.runs(ENTITY_PROJECT, filters={"display_name": {"$regex": f"^{prefix}"}})
        for run in runs:
            if EXCLUDE_TOKEN in run.name:
                continue
            row = extract_run(run)
            if row is not None:
                records.append(row)
                print(f"extracted: {run.name}")

    per_run = pd.DataFrame(records).sort_values(["env", "cost_limit", "laglr", "seed"])
    per_run.to_csv(PER_RUN_CSV, index=False)
    agg = aggregate(per_run)
    agg.to_csv(AGG_CSV, index=False)
    print(f"\n{len(per_run)} runs -> {PER_RUN_CSV.name}, {len(agg)} groups -> {AGG_CSV.name}")
    print(agg.to_string())


if __name__ == "__main__":
    main()
