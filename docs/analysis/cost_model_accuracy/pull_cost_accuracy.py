#!/usr/bin/env python3
"""Pull (step, predicted, actual) cost time series from SafeDreamer WandB runs -> CSV.

Reads runs_config.json; outputs data/<label>_s<i>.csv per run.

Usage:
  python pull_cost_accuracy.py
"""

import json
import sys
from pathlib import Path

import numpy as np

import wandb

sys.path.insert(0, str(Path(__file__).resolve().parent / "../../tmp/extraction/scripts"))

from extract_metrics import download_parquet_as_dataframe, find_history_artifact
from extraction_config import STEP_COL
from wandb_config import WANDB_PROJECT, WANDB_TIMEOUT

PRED_KEY = "Model/Predicted_average_cost"
ACTUAL_KEY = "Model/Actual_average_cost"
WANDB_STEP_COL = "_step"

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"


def pull_run(api, run_name: str, output: Path) -> int:
    run = api.run(f"{WANDB_PROJECT}/{run_name}")
    artifact = find_history_artifact(run)
    if artifact is None:
        raise RuntimeError(f"no history artifact for {run_name}")
    df = download_parquet_as_dataframe(artifact)
    for key in (PRED_KEY, ACTUAL_KEY):
        if key not in df.columns:
            raise RuntimeError(f"missing {key} in {run_name}")

    # These keys are logged on training rows carrying only wandb's internal
    # _step; map _step -> env steps by interpolating over anchor rows.
    anchor = df[[WANDB_STEP_COL, STEP_COL]].dropna().sort_values(WANDB_STEP_COL)
    out = df[[WANDB_STEP_COL, PRED_KEY, ACTUAL_KEY]].dropna(how="all", subset=[PRED_KEY, ACTUAL_KEY])
    out = out.sort_values(WANDB_STEP_COL)
    out["step"] = np.interp(out[WANDB_STEP_COL], anchor[WANDB_STEP_COL], anchor[STEP_COL])
    out = out.rename(columns={PRED_KEY: "predicted", ACTUAL_KEY: "actual"})
    out = out[["step", "predicted", "actual"]].reset_index(drop=True)
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
