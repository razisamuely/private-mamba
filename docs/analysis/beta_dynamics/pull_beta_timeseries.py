#!/usr/bin/env python3
"""Pull (step, beta, cost) time series from SafeDreamer WandB runs -> CSV.

Reads runs_config.json; outputs data/<label>_s<i>.csv per run.

Usage:
  python pull_beta_timeseries.py
"""

import json
import sys
from pathlib import Path

import wandb

sys.path.insert(0, str(Path(__file__).resolve().parent / "../../tmp/extraction/scripts"))

from extract_metrics import download_parquet_as_dataframe, find_history_artifact
from extraction_config import STEP_COL
from wandb_config import WANDB_PROJECT, WANDB_TIMEOUT

BETA_KEY = "Agent/Lagrangian"
COST_KEY = "main/cost"
WANDB_STEP_COL = "_step"

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"


def pull_run(api, run_name: str, output: Path) -> int:
    run = api.run(f"{WANDB_PROJECT}/{run_name}")
    artifact = find_history_artifact(run)
    if artifact is None:
        raise RuntimeError(f"no history artifact for {run_name}")
    df = download_parquet_as_dataframe(artifact)
    if BETA_KEY not in df.columns or COST_KEY not in df.columns:
        raise RuntimeError(f"missing {BETA_KEY} or {COST_KEY} in {run_name}")

    # Beta rows carry only wandb's internal _step; map _step -> env steps by
    # interpolating over the rows where the env step counter is present.
    import numpy as np

    anchor = df[[WANDB_STEP_COL, STEP_COL]].dropna().sort_values(WANDB_STEP_COL)
    out = df[[WANDB_STEP_COL, BETA_KEY, COST_KEY]].dropna(how="all", subset=[BETA_KEY, COST_KEY])
    out = out.sort_values(WANDB_STEP_COL)
    out["step"] = np.interp(out[WANDB_STEP_COL], anchor[WANDB_STEP_COL], anchor[STEP_COL])
    out = out.rename(columns={BETA_KEY: "beta", COST_KEY: "cost"})
    out = out[["step", "beta", "cost"]].reset_index(drop=True)
    out.to_csv(output, index=False)
    return len(out)


def main():
    config = json.loads((HERE / "runs_config.json").read_text())
    DATA_DIR.mkdir(exist_ok=True)
    api = wandb.Api(timeout=WANDB_TIMEOUT)
    for env, spec in config["envs"].items():
        for seed_idx, run_name in enumerate(spec["runs"], start=1):
            output = DATA_DIR / f"{spec['label']}_s{seed_idx}.csv"
            try:
                n = pull_run(api, run_name, output)
                print(f"[{output.name}] {n} rows")
            except Exception as e:
                print(f"[{output.name}] FAILED: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
