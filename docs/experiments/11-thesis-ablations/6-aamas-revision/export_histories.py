#!/usr/bin/env python3
"""Dump the WandB histories needed for the AAMAS revision as CSV.

For every selected run, writes into ``csv/<group>/``:

* ``<run_id>_episodes.csv``: ``steps``, ``main/cost``, ``main/score``, ``main/winrate``,
  one row per logged episode (CA-MAMBA) or logging interval (SafePO baselines).
* ``<run_id>_lag.csv`` (unless ``--skip-lag``): ``_step``, ``steps`` (interpolated),
  ``Agent/Lagrangian``, ``Lag/mean_cost``, ``Lag/pid_p``, ``Lag/pid_i``, ``Lag/pid_d``,
  and the ``Diag/*`` transition-error diagnostics
  (whichever the run logged).
* ``<run_id>.name``: the run's display name.

The three episode metrics are logged in separate ``wandb.log`` calls that share
``steps``, so they are merged on ``steps``. Lagrangian metrics carry no ``steps``;
env steps are interpolated from the logged ``(_step, steps)`` pairs.

Usage (from this folder):
  python export_histories.py --group pid_mamujoco --regex "Velocity-v0_s[0-9]+_pid_"
  python export_histories.py --group basic_mamujoco_tight --regex "_lag(1e-05|0.0001)_(0.2|1.0|5.0)_Safety"
  python export_histories.py --group smac_8m_old --ids ids_smac_8m_old.txt
  python export_histories.py --group smac_training_cost --ids ids_smac_training_cost.txt --skip-lag
  python export_histories.py --group smac_8m_new --regex "_4.0_8m_s[123].*_feat-aamas"
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

import wandb

ENTITY_PROJECT = "raz-shmueli-corsound-ai/private-mamba"
SCAN_TIMEOUT = 60  # seconds; fall back to run.history() if scan_history hangs
STEP = "steps"
EPISODE_KEYS = ("main/cost", "main/score", "main/winrate")
LAG_KEYS = (
    "Agent/Lagrangian",
    "Lag/mean_cost",
    "Lag/pid_p",
    "Lag/pid_i",
    "Lag/pid_d",
    # transition-error diagnostics (agent/optim/diagnostics.py); present only in newer runs
    "Diag/tv_post_prior",
    "Diag/tv_post_prior_max_agent",
    "Diag/bv_signed",
    "Diag/bv_abs",
    "Diag/v_post",
)
PAGE_SIZE = 10_000
HERE = Path(__file__).resolve().parent


def _scan_with_timeout(run, keys, page_size=PAGE_SIZE, timeout=SCAN_TIMEOUT):
    """Try scan_history; if it hangs, fall back to run.history()."""

    def _scan():
        return [(r[keys[0]], r[keys[1]]) for r in run.scan_history(keys=keys, page_size=page_size)]

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_scan)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeout:
            future.cancel()
            df = run.history(samples=10000, keys=keys).dropna(subset=keys)
            return list(zip(df[keys[0]], df[keys[1]]))


def episode_frame(run) -> pd.DataFrame:
    """Episode metrics merged on env steps; raises if the run logged none."""
    merged: pd.DataFrame | None = None
    for key in EPISODE_KEYS:
        rows = _scan_with_timeout(run, [STEP, key])
        if not rows:
            continue
        df = pd.DataFrame(rows, columns=[STEP, key]).drop_duplicates(subset=[STEP], keep="last")
        if merged is None:
            merged = df
        else:
            merged = merged.drop_duplicates(subset=[STEP], keep="last").merge(df, on=STEP, how="outer")
    if merged is None:
        raise RuntimeError(f"no episode metrics in {run.id}")
    merged = merged.sort_values(STEP).reset_index(drop=True)  # [num_episodes, 1 + len(EPISODE_KEYS)]
    assert merged[STEP].is_monotonic_increasing, f"non-monotonic steps in {run.id}"
    return merged


def lag_frame(run) -> pd.DataFrame | None:
    """Multiplier metrics with interpolated env steps; None if the run logged none."""
    columns = {}
    for key in LAG_KEYS:
        rows = _scan_with_timeout(run, ["_step", key])
        if rows:
            columns[key] = (
                pd.DataFrame(rows, columns=["_step", key])
                .drop_duplicates(subset=["_step"], keep="last")
                .set_index("_step")[key]
            )
    if not columns:
        return None
    lag = pd.DataFrame(columns).sort_index().reset_index()  # [num_updates, 1 + num_present_keys]
    anchors = _scan_with_timeout(run, ["_step", STEP])
    if anchors:
        a = np.asarray(anchors, dtype=float)  # [num_anchor_rows, 2]
        lag[STEP] = np.interp(lag["_step"].to_numpy(dtype=float), a[:, 0], a[:, 1])
    return lag


def resolve_runs(api: wandb.Api, ids_file: Path | None, regex: str | None) -> Iterator:
    if ids_file is not None:
        for line in ids_file.read_text().splitlines():
            run_id = line.strip()
            if run_id and not run_id.startswith("#"):
                yield api.run(f"{ENTITY_PROJECT}/{run_id}")
    if regex is not None:
        yield from api.runs(ENTITY_PROJECT, filters={"display_name": {"$regex": regex}})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group", required=True, help="output subfolder under csv/")
    parser.add_argument("--ids", type=Path, default=None, help="file with one run id per line")
    parser.add_argument("--regex", default=None, help="display-name regex")
    parser.add_argument("--skip-lag", action="store_true", help="export episode metrics only")
    args = parser.parse_args()
    if args.ids is None and args.regex is None:
        parser.error("give --ids or --regex")
    ids_path = None if args.ids is None else (args.ids if args.ids.is_absolute() else HERE / args.ids)

    out_dir = HERE / "csv" / args.group
    out_dir.mkdir(parents=True, exist_ok=True)
    api = wandb.Api(timeout=120)
    n_ok, n_fail = 0, 0
    for run in resolve_runs(api, ids_path, args.regex):
        try:
            episodes = episode_frame(run)
            episodes.to_csv(out_dir / f"{run.id}_episodes.csv", index=False)
            if not args.skip_lag:
                lag = lag_frame(run)
                if lag is not None:
                    lag.to_csv(out_dir / f"{run.id}_lag.csv", index=False)
            (out_dir / f"{run.id}.name").write_text(run.name)
            print(f"[ok] {run.name}: {len(episodes)} episode rows, last step {episodes[STEP].iloc[-1]:.0f}")
            n_ok += 1
        except Exception as exc:  # noqa: BLE001 - report every failing run, keep going
            print(f"[FAIL] {getattr(run, 'id', run)}: {exc}", file=sys.stderr)
            n_fail += 1
    print(f"done: {n_ok} ok, {n_fail} failed -> {out_dir}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
