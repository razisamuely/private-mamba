#!/usr/bin/env python3
"""
results_helpers.py — Core skill for fetching Safe Dreamers results from wandb.

PYTHON: /home/corsound/workspace/overleaf/thesis/venv/bin/python3
        (requires pandas >= 1.0 for parquet support)

HOW IT WORKS:
  SafeDreamers logs main/score, main/cost, main/winrate to a wandb-history
  parquet artifact (not regular history). This skill downloads that artifact
  and extracts metrics at a target step window.

  MACPO (SafePO) logs directly to wandb history — use run.history() instead.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pandas as pd

import wandb

# Constants
WANDB_PROJECT = "raz-shmueli-corsound-ai/private-mamba"
DEFAULT_TARGET_STEP = 100_000
DEFAULT_WINDOW = 5_000


def get_api() -> wandb.Api:
    """Create wandb API with safe timeout. Reads key from WANDB_API_KEY env var."""
    return wandb.Api(timeout=60)


def get_history_from_artifact(run: wandb.apis.public.Run) -> pd.DataFrame | None:
    """Download wandb-history parquet artifact and return as DataFrame.

    SafeDreamers stores full history in a parquet artifact, not in regular
    wandb history. This is the correct way to read per-step metrics.

    Returns DataFrame with columns including: steps, main/score, main/cost,
    main/winrate. Returns None if no artifact found.
    """
    for artifact in run.logged_artifacts():
        if artifact.type == "wandb-history":
            with tempfile.TemporaryDirectory() as d:
                artifact.download(root=d)
                parquet_files = [f for f in os.listdir(d) if f.endswith(".parquet")]
                if not parquet_files:
                    continue
                df = pd.read_parquet(os.path.join(d, parquet_files[0]))
                if "steps" in df.columns:
                    return df
    return None


def extract_at_step(
    df: pd.DataFrame,
    target_step: int = DEFAULT_TARGET_STEP,
    window: int = DEFAULT_WINDOW,
) -> tuple[float | None, float | None, float | None]:
    """Extract mean of main/score, main/cost, main/winrate near target_step.

    Uses window [target_step - window, target_step]. Falls back to last 3
    rows before target if window is empty.

    Returns (score, cost, winrate) or (None, None, None) if no data.
    """
    w = df[(df["steps"] >= target_step - window) & (df["steps"] <= target_step)]
    if w.empty:
        w = df[df["steps"] <= target_step].tail(3)
    if w.empty:
        return None, None, None

    def _mean(col: str) -> float | None:
        v = w[col].dropna().mean() if col in w.columns else float("nan")
        return float(v) if not np.isnan(v) else None

    return _mean("main/score"), _mean("main/cost"), _mean("main/winrate")


def fetch_run_at_step(
    api: wandb.Api,
    run_id: str,
    target_step: int = DEFAULT_TARGET_STEP,
    window: int = DEFAULT_WINDOW,
) -> dict:
    """Fetch metrics for a single run at target_step.

    Returns dict with keys: score, cost, winrate, max_step, status.
    """
    run = api.run(f"{WANDB_PROJECT}/{run_id}")
    df = get_history_from_artifact(run)
    if df is None:
        return {"score": None, "cost": None, "winrate": None, "max_step": None, "status": "no_artifact"}

    max_step = int(df["steps"].dropna().max())
    score, cost, wr = extract_at_step(df, target_step, window)
    status = "ok" if max_step >= target_step else f"only_{max_step}_steps"
    return {"score": score, "cost": cost, "winrate": wr, "max_step": max_step, "status": status}


def aggregate_seeds(results: list[tuple[float, float, float]]) -> dict:
    """Aggregate list of (score, cost, winrate) tuples across seeds.

    Returns dict with mean and std for each metric.
    """
    valid = [(s, c, w) for s, c, w in results if s is not None]
    if not valid:
        return {k: None for k in ("score_mean", "score_std", "cost_mean", "cost_std", "winrate_mean", "winrate_std")}
    scores, costs, wrs = zip(*valid)
    return {
        "score_mean": round(float(np.mean(scores)), 2),
        "score_std": round(float(np.std(scores)), 2),
        "cost_mean": round(float(np.mean(costs)), 2),
        "cost_std": round(float(np.std(costs)), 2),
        "winrate_mean": round(float(np.mean(wrs)), 2),
        "winrate_std": round(float(np.std(wrs)), 2),
    }
