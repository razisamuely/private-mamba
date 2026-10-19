#!/usr/bin/env python3
"""Check whether the beta-trajectory figures were drawn from the reported runs.

Issue #32 says the figures come from older runs than the ones the paper
reports. There is no run manifest yet (#29), so this script decides the
question from the figure data itself: it applies the paper's reading rule to
the series behind each figure and compares the result with the published cell.
A match on both the mean and the sample standard deviation over three seeds
identifies the runs, because the series and the table would otherwise have to
agree by coincidence to one decimal on six numbers.

Reading rule (ground rule 4): mean over each run's episodes in the last 5k
interactions before the checkpoint, then mean and sample standard deviation
over runs.

Usage, from the private-mamba root with the thesis repo beside it:

    python docs/experiments/12-aamas-remaining-work/32-beta-trajectories/\
verify_beta_provenance.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[4]
THESIS = REPO_ROOT.parent / "overleaf" / "thesis"

MUJOCO_BETA_DIR = REPO_ROOT / "docs" / "analysis" / "beta_dynamics" / "data"
SMAC_BETA_DIR = THESIS / "data" / "smac_beta"
PHASE5_CSV = THESIS / "data" / "mamujoco_experiment8_phase5_full.csv"
LOCAL_ENDPOINTS_CSV = THESIS / "data" / "local_runs_endpoints.csv"

WINDOW = 5_000
SEEDS = (1, 2, 3)

# label -> (phase5 env name, pretty name)
MUJOCO = {
    "hc2x3": ("Safety2x3HalfCheetahVelocity-v0", "HalfCheetah 2x3"),
    "ant2x4": ("Safety2x4AntVelocity-v0", "Ant 2x4"),
    "ant4x2": ("Safety4x2AntVelocity-v0", "Ant 4x2"),
}
MUJOCO_CHECKPOINT = 1_000_000

# CSV label -> map name as the appendix spells it
SMAC = {
    "mmm": "MMM",
    "1c3s5z": "1c3s5z",
    "3m": "3m",
    "2m-vs-1z": "2m_vs_1z",
    "8m": "8m",
}
SMAC_CHECKPOINT = 100_000

# beta endpoints the appendix quotes, as printed
QUOTED_BETA = {"8m": 0.54, "MMM": 0.50, "1c3s5z": 0.30, "3m": 0.13, "2m_vs_1z": 0.025}


def endpoint(path: Path, column: str, checkpoint: int) -> float | None:
    """Mean of ``column`` over steps in [checkpoint-5k, checkpoint]."""
    frame = pd.read_csv(path).dropna(subset=[column])
    window = frame[(frame["step"] >= checkpoint - WINDOW) & (frame["step"] <= checkpoint)]
    return None if window.empty else float(window[column].mean())


def last_value(path: Path, column: str, checkpoint: int) -> float | None:
    """Last ``column`` value logged at or before ``checkpoint``."""
    frame = pd.read_csv(path).dropna(subset=[column])
    upto = frame[frame["step"] <= checkpoint]
    return None if upto.empty else float(upto[column].iloc[-1])


def aggregate(values: list[float | None]) -> tuple[float | None, float | None, int]:
    present = [value for value in values if value is not None]
    if len(present) < 2:
        return (present[0] if present else None), None, len(present)
    return float(np.mean(present)), float(np.std(present, ddof=1)), len(present)


def check_mujoco() -> bool:
    phase5 = pd.read_csv(PHASE5_CSV)
    reported = phase5[
        (phase5.source == "SafeDreamer (lr=1e-5)")
        & (phase5.cost_limit == 25.0)
        & (phase5.target_steps == MUJOCO_CHECKPOINT)
    ]

    print("MAMuJoCo beta figures at d=25, cost at 1M")
    print("  reconstructed from the figure series vs the published cell\n")
    print(f"  {'task':16s} {'from figure data':22s} {'published':16s} seeds  verdict")
    agreed = True
    for label, (env, pretty) in MUJOCO.items():
        row = reported[reported.env == env]
        if row.empty:
            print(f"  {pretty:16s} no published row found")
            agreed = False
            continue
        published_mean = float(row.cost_mean.iloc[0])
        published_std = float(row.cost_std.iloc[0])

        per_seed = [endpoint(MUJOCO_BETA_DIR / f"{label}_s{seed}.csv", "cost", MUJOCO_CHECKPOINT) for seed in SEEDS]
        mean, std, count = aggregate(per_seed)
        if mean is None:
            print(f"  {pretty:16s} no series data")
            agreed = False
            continue

        # One decimal is the published precision, so compare at that scale.
        same_mean = abs(round(mean, 1) - published_mean) <= 0.051
        same_std = std is not None and abs(round(std, 1) - published_std) <= 0.051
        if count == len(SEEDS):
            verdict = "MATCH" if same_mean and same_std else "DIFFERS"
        else:
            verdict = f"partial ({count}/3 seeds reach 1M)"
            agreed = agreed and same_mean
        agreed = agreed and (verdict == "MATCH" or verdict.startswith("partial"))

        shown_std = "  n/a" if std is None else f"{std:5.2f}"
        print(
            f"  {pretty:16s} {mean:7.2f} +- {shown_std:>5s}      "
            f"{published_mean:5.1f} +- {published_std:4.1f}   {count}/3    {verdict}"
        )
        print(f"  {'':16s} per seed: {[None if v is None else round(v, 2) for v in per_seed]}")
    return agreed


def check_smac() -> bool:
    print("\nSMAC beta endpoints at d=0, 100k")
    print("  recomputed from the series behind the figures vs the quoted value\n")
    print(f"  {'map':10s} {'from series':14s} {'quoted':8s} verdict")
    agreed = True
    for label, name in SMAC.items():
        per_seed = [last_value(SMAC_BETA_DIR / f"{label}_s{seed}.csv", "beta", SMAC_CHECKPOINT) for seed in SEEDS]
        mean, _, _ = aggregate(per_seed)
        quoted = QUOTED_BETA[name]
        decimals = 3 if quoted < 0.1 else 2
        same = mean is not None and abs(round(mean, decimals) - quoted) <= 10**-decimals / 2
        verdict = "MATCH" if same else "DIFFERS"
        agreed = agreed and same
        print(f"  {name:10s} {mean:12.4f}  {quoted:8.3f} {verdict}")
    return agreed


def check_smac_8m_against_reported() -> None:
    """The 8m series and the reported 8m runs are different runs; show both."""
    endpoints = pd.read_csv(LOCAL_ENDPOINTS_CSV, comment="#")
    reported = endpoints[(endpoints.tag == "d0measured") & (endpoints.env == "8m")]
    mean = float(reported.beta_end.mean())
    print("\n8m: the series behind data/smac_beta is not the reported run")
    print(f"  reported runs {sorted(reported.slurm_id.tolist())}")
    print(f"    beta_end per seed {[round(v, 4) for v in reported.beta_end.tolist()]}")
    print(f"    mean {mean:.4f} -> prints as {round(mean, 2)}")
    series = [last_value(SMAC_BETA_DIR / f"8m_s{seed}.csv", "beta", SMAC_CHECKPOINT) for seed in SEEDS]
    series_mean = float(np.mean(series))
    print(f"  series in data/smac_beta/8m_s*.csv")
    print(f"    beta_end per seed {[round(v, 4) for v in series]}")
    print(f"    mean {series_mean:.4f} -> would print as {round(series_mean, 2)}")


def main() -> int:
    for path in (MUJOCO_BETA_DIR, SMAC_BETA_DIR, PHASE5_CSV, LOCAL_ENDPOINTS_CSV):
        if not path.exists():
            print(f"missing input: {path}", file=sys.stderr)
            return 2
    mujoco_ok = check_mujoco()
    smac_ok = check_smac()
    check_smac_8m_against_reported()
    print()
    print(f"MAMuJoCo figures drawn from the reported runs: {mujoco_ok}")
    print(f"SMAC quoted endpoints reproduce from their series: {smac_ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
