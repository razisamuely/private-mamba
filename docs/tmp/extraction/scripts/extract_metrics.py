#!/usr/bin/env python3
"""
Extract metrics at map-specific target steps from WandB runs.

Pulls score, cost, winrate from WandB experiments at per-map target env steps
defined in map_steps_config.json. Averages over a window of WINDOW_SIZE steps
before the target. Falls back to last 3 rows if window is empty.

Usage:
  python extract_metrics.py [--config map_steps_config.json] [--output tracking.csv]
"""

import argparse
import csv
import json
import os
import sys
import tempfile
import traceback
import urllib.parse
from pathlib import Path

import pandas as pd
from extraction_config import (
    CSV_COL_ALGORITHM,
    CSV_COL_COST_LIMIT,
    CSV_COL_MAP,
    CSV_COL_SEED,
    CSV_COL_WANDB_LINK,
    DEFAULT_TARGET_STEP,
    FALLBACK_STEP_COL,
    HISTORY_ARTIFACT_NAME_SUBSTR,
    HISTORY_ARTIFACT_TYPE,
    METRIC_KEYS,
    PARQUET_EXT,
    STEP_COL,
    WANDB_URL_MARKER,
    WANDB_URL_RUNS_SEGMENT,
    WINDOW_SIZE,
)
from paths_config import DEFAULT_CONFIG_JSON, DEFAULT_INPUT_CSV
from wandb_config import WANDB_PROJECT, WANDB_TIMEOUT

import wandb

# ── URL helpers ───────────────────────────────────────────────────────────────


def extract_run_id_from_url(url: str) -> str | None:
    """Extract run ID from a WandB URL of form .../runs/<run_id>.
    Returns None if URL is missing or not a valid WandB run URL.
    """
    if not url or WANDB_URL_MARKER not in url:
        return None
    if WANDB_URL_RUNS_SEGMENT in url:
        return urllib.parse.unquote(url.split(WANDB_URL_RUNS_SEGMENT)[-1])
    return None


# ── Artifact helpers ──────────────────────────────────────────────────────────


def find_history_artifact(run) -> object | None:
    """Return the wandb-history artifact for a run, or None if not found.
    Matches by artifact type == HISTORY_ARTIFACT_TYPE and name containing HISTORY_ARTIFACT_NAME_SUBSTR.
    """
    for artifact in run.logged_artifacts():
        if HISTORY_ARTIFACT_NAME_SUBSTR in artifact.name.lower() and artifact.type == HISTORY_ARTIFACT_TYPE:
            return artifact
    return None


def download_parquet_as_dataframe(artifact) -> pd.DataFrame:
    """Download a wandb artifact to a temp dir and return its parquet file as a DataFrame.
    Returns empty DataFrame if no parquet file is found.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        artifact_dir = artifact.download(root=tmpdir)
        parquet_files = [f for f in os.listdir(artifact_dir) if f.endswith(PARQUET_EXT)]
        if not parquet_files:
            return pd.DataFrame()
        return pd.read_parquet(os.path.join(artifact_dir, parquet_files[0]))


def filter_valid_metric_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with a valid env step value and at least one non-NaN metric.
    Returns empty DataFrame if STEP_COL is missing entirely.
    """
    if STEP_COL not in df.columns:
        return pd.DataFrame()
    df = df.dropna(subset=[STEP_COL])
    metric_cols = [c for c in METRIC_KEYS if c in df.columns]
    if metric_cols:
        df = df[df[metric_cols].notna().any(axis=1)]
    return df


def get_history_from_artifact(run) -> list[dict]:
    """Fetch metric history from a wandb-history parquet artifact (SafeDreamer format).

    SafeDreamer logs history to a parquet artifact rather than regular wandb history.
    Returns a list of row dicts with keys: STEP_COL + METRIC_KEYS.
    Returns empty list if no artifact found or on any error.
    """
    try:
        artifact = find_history_artifact(run)
        if artifact is None:
            return []
        df = download_parquet_as_dataframe(artifact)
        df = filter_valid_metric_rows(df)
        if df.empty:
            return []
        cols = [STEP_COL] + [c for c in METRIC_KEYS if c in df.columns]
        return df[cols].where(df[cols].notna(), other=None).to_dict("records")
    except Exception as e:
        print(f"Warning: Failed to get history from artifact: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return []


# ── CSV / config loaders ──────────────────────────────────────────────────────


def load_experiments_from_csv(csv_path: Path) -> list[dict]:
    """Load experiment metadata from a tracking CSV, keeping only rows with valid WandB links.

    Each returned dict has keys: run_id, map, algorithm, cost_limit, seed.
    Rows without a WandB link or with an unparseable URL are silently skipped.
    """
    experiments = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            wandb_link = row.get(CSV_COL_WANDB_LINK, "").strip()
            if wandb_link and WANDB_URL_MARKER in wandb_link:
                run_id = extract_run_id_from_url(wandb_link)
                if run_id:
                    experiments.append(
                        {
                            "run_id": run_id,
                            "map": row[CSV_COL_MAP],
                            "algorithm": row[CSV_COL_ALGORITHM],
                            "cost_limit": row[CSV_COL_COST_LIMIT],
                            "seed": row[CSV_COL_SEED],
                        }
                    )
    return experiments


def load_map_step_targets(config_path: Path) -> dict:
    """Load per-map target env step config from a JSON file.
    Returns empty dict (uses DEFAULT_TARGET_STEP for all maps) if file is missing.
    """
    try:
        with open(config_path) as f:
            config = json.load(f)
        print(f"Loaded step targets for {len(config)} maps from {config_path}")
        return config
    except FileNotFoundError:
        print("Warning: map_steps_config.json not found. Using default for all maps.")
        return {}


# ── History fetching ──────────────────────────────────────────────────────────


def fetch_run_history_as_dataframe(run, target_step: int = 100_000) -> pd.DataFrame:
    """Fetch full metric history for a run as a DataFrame with env STEP_COL column.

    Strategy (in order):
    1. Parquet artifact (SafeDreamer clean exit) — most complete, uses env 'steps' column.
    2. run.history() with 'steps' column (SafeDreamer killed mid-run) — real-time history
       also contains env 'steps', so correct axis is preserved.

    Returns DataFrame with columns: STEP_COL, main/score, main/cost, main/winrate.
    Raises RuntimeError if neither source has a valid 'steps' column.
    """
    artifact_history = get_history_from_artifact(run)
    if artifact_history:
        return pd.DataFrame(artifact_history)

    # Fallback: scan_history without keys filter, then aggregate by env steps.
    # SafeDreamer logs steps/winrate/cost in separate rows at the same env step.
    _FALLBACK_TARGET = target_step
    try:
        min_s, max_s = estimate_internal_step_range_for_env_steps(run, _FALLBACK_TARGET)
        rows = list(run.scan_history(min_step=min_s, max_step=max_s, page_size=10_000))
        if rows:
            df = pd.DataFrame(rows).dropna(subset=[STEP_COL])
            avail_metrics = [c for c in METRIC_KEYS if c in df.columns]
            if avail_metrics:
                df = df.groupby(STEP_COL)[avail_metrics].first().reset_index()
                if not df.empty:
                    return df
    except Exception as e:
        print(f"DEBUG fallback error: {e}", file=sys.stderr)

    raise RuntimeError(
        f"No env step axis found for run {run.id}. " "No parquet artifact and no 'steps' column in history."
    )


# ── Step window helpers ───────────────────────────────────────────────────────


def metric_key_to_result_key(metric_key: str) -> str:
    """Convert WandB metric key to result dict key: 'main/winrate' → 'avg_winrate'."""
    return f"avg_{metric_key.split('/')[1]}"


def resolve_step_column(df: pd.DataFrame) -> str:
    """Return the env step column name in df: STEP_COL if present, else FALLBACK_STEP_COL."""
    return STEP_COL if STEP_COL in df.columns else FALLBACK_STEP_COL


def estimate_internal_step_range_for_env_steps(run, target_env_step: int, sample_size: int = 200) -> tuple[int, int]:
    """Estimate the _step range that corresponds to env steps around target_env_step.

    Samples run history to build a _step → env_steps mapping, then finds the
    _step values that bracket [target - 2*WINDOW_SIZE, target + 2*WINDOW_SIZE].
    Returns (min_internal_step, max_internal_step).
    """
    df = run.history(samples=sample_size, keys=[STEP_COL]).dropna()
    if df.empty or STEP_COL not in df.columns:
        return 0, run.lastHistoryStep or 1_000_000
    df = df.sort_values(STEP_COL)
    lo_env = target_env_step - 2 * WINDOW_SIZE
    hi_env = target_env_step + 2 * WINDOW_SIZE
    # Find last _step before lo_env and first _step after hi_env
    before = df[df[STEP_COL] <= lo_env]
    after = df[df[STEP_COL] >= hi_env]
    lo_internal = int(before["_step"].max()) if not before.empty else 0
    hi_internal = int(after["_step"].min()) if not after.empty else (run.lastHistoryStep or 1_000_000)
    return max(0, lo_internal - 1000), hi_internal + 1000
    """Return the env step column name in df: STEP_COL if present, else FALLBACK_STEP_COL."""
    return STEP_COL if STEP_COL in df.columns else FALLBACK_STEP_COL


def drop_zero_and_null_step_rows(df: pd.DataFrame, step_col: str) -> pd.DataFrame:
    """Remove rows where step is NaN or zero (invalid env step values)."""
    return df.dropna(subset=[step_col]).pipe(lambda d: d[d[step_col] > 0])


def get_rows_in_step_window(df: pd.DataFrame, step_col: str, target: int, window: int) -> pd.DataFrame:
    """Return rows where env step is in [target - window, target]."""
    return df[df[step_col].between(target - window, target)]


def get_last_rows_before_step(df: pd.DataFrame, step_col: str, target: int, n: int = 3) -> pd.DataFrame:
    """Return the last n rows with env step <= target (used as fallback when window is empty)."""
    return df[df[step_col] <= target].tail(n)


def get_max_env_step(df: pd.DataFrame, step_col: str) -> int:
    """Return the maximum env step value in df, or 0 if df is empty."""
    return int(df[step_col].max()) if len(df) > 0 else 0


def average_metrics_in_env_step_window(df: pd.DataFrame, target_step: int, window_size: int) -> dict:
    """Average METRIC_KEYS over env steps in [target - window_size, target].

    Falls back to last 3 rows before target if the window contains no data.
    Returns dict with avg_score, avg_cost, avg_winrate, max_step, num_samples, reached_target.
    """
    step_col = resolve_step_column(df)
    df = drop_zero_and_null_step_rows(df, step_col)

    window = get_rows_in_step_window(df, step_col, target_step, window_size)
    if window.empty:
        window = get_last_rows_before_step(df, step_col, target_step)

    def _mean(col: str) -> float | str:
        vals = window[col].dropna() if col in window.columns else pd.Series(dtype=float)
        return float(vals.mean()) if len(vals) > 0 else "N/A"

    max_step = get_max_env_step(df, step_col)
    return {
        **{metric_key_to_result_key(key): _mean(key) for key in METRIC_KEYS},
        "max_step": max_step,
        "num_samples": len(window),
        "reached_target": max_step >= target_step,
    }


# ── Output ────────────────────────────────────────────────────────────────────


def print_experiment_result(exp: dict, target_step: int, result: dict) -> None:
    """Print a one-line summary of extracted metrics for a single experiment."""
    algo, mp, cost, seed = exp["algorithm"], exp["map"], exp["cost_limit"], exp["seed"]
    status = "✓" if result["reached_target"] else "✗"
    print(f"\n{algo} {mp} cost={cost} seed={seed}")
    print(f"  Target: {target_step:,} | {status} max={result['max_step']:,} ({result['num_samples']} samples)")
    print(f"  Score: {result['avg_score']}  Cost: {result['avg_cost']}  WR: {result['avg_winrate']}")


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default=None, help="Path to map_steps_config.json")
    parser.add_argument("--output", type=str, default=None, help="Path to input tracking CSV")
    args = parser.parse_args()

    api = wandb.Api(timeout=WANDB_TIMEOUT)
    map_step_targets = load_map_step_targets(Path(args.config) if args.config else DEFAULT_CONFIG_JSON)
    experiments = load_experiments_from_csv(Path(args.output) if args.output else DEFAULT_INPUT_CSV)
    print(f"Found {len(experiments)} experiments. Extracting metrics...\n{'='*80}")

    for exp in experiments:
        try:
            run = api.run(f"{WANDB_PROJECT}/{exp['run_id']}")
        except Exception:
            print(f"\n⚠ Skipped {exp['run_id']}: not found")
            continue
        try:
            map_cfg = map_step_targets.get(exp["map"], DEFAULT_TARGET_STEP)
            target_step = map_cfg.get(exp["algorithm"], DEFAULT_TARGET_STEP) if isinstance(map_cfg, dict) else map_cfg
            df = fetch_run_history_as_dataframe(run, target_step)
            result = average_metrics_in_env_step_window(df, target_step, WINDOW_SIZE)
            print_experiment_result(exp, target_step, result)
        except RuntimeError as e:
            print(f"\n⚠ Skipped {exp['run_id']}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error processing {exp['run_id']}: {e}")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
