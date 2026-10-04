r"""Theory quantities from local JSON-lines logs (``train.py --local_log``), no WandB needed.

For each run, over the last ``tail`` fraction of environment steps:

* ``eps_c_loss``: mean ``Model/cost_loss`` (smooth-l1 training loss of the cost head; a
  scale for :math:`\epsilon_c`, not an absolute error).
* ``kl_per_categorical`` = mean ``Model/div``; ``kl_per_agent`` = :math:`K` times it,
  :math:`K` the number of categorical variables per latent (32).  ``pinsker_bound`` =
  :math:`\sqrt{\mathrm{kl\_per\_agent}/2}`, an upper bound on the per-agent transition
  TV that cannot certify a small error even for an exact model.
* ``imag_window`` = mean ``Value/Cost`` (imagined team cost per step) times
  :math:`W=\sum_{t<15}0.99^t`; ``real_window`` = total episode cost / total episode
  length over the tail episodes, times :math:`W`.  ``abs_gap`` and ``rel_gap`` compare
  them: an estimate of the left-hand side of Theorem 1(i).
* ``bv_signed``, ``bv_abs``, ``v_post``, ``tv_post_prior``, ``tv_max_agent``: means of the
  ``Diag/*`` diagnostics (agent/optim/diagnostics.py); ``bv_rel`` = ``bv_abs`` / |``v_post``|.
* ``beta_final``: last ``Agent/Lagrangian``.

Rows carry no environment step except the episode rows (``steps``); every other row's
step is interpolated from its line position between episode rows.

Usage:
  python tools/theory_check.py RUN_DIR_OR_JSONL [...] --out theory_check.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np

GAMMA = 0.99
HORIZON = 15
WINDOW = sum(GAMMA**t for t in range(HORIZON))  # discounted 15-step window, ~13.994
N_CATEGORICALS = 32
STEP = "steps"
EPISODE_COST = "main/cost"


@dataclass(frozen=True)
class RunSummary:
    run: str
    max_steps: float
    tail_episodes: int
    eps_c_loss: Optional[float]
    kl_per_categorical: Optional[float]
    kl_per_agent: Optional[float]
    pinsker_bound: Optional[float]
    imag_window: Optional[float]
    real_window: Optional[float]
    abs_gap: Optional[float]
    rel_gap: Optional[float]
    bv_signed: Optional[float]
    bv_abs: Optional[float]
    v_post: Optional[float]
    bv_rel: Optional[float]
    tv_post_prior: Optional[float]
    tv_max_agent: Optional[float]
    beta_final: Optional[float]


def read_jsonl(path: Path) -> list[dict[str, float]]:
    rows = []  # [num_log_calls]
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:  # a crash can truncate the last line
                print(f"warning: {path}:{number}: skipped unreadable line ({exc})", file=sys.stderr)
    if not rows:
        raise ValueError(f"{path} has no log rows")
    return rows


def _interpolated_steps(rows: Sequence[dict[str, float]]) -> np.ndarray:
    anchors = [(i, r[STEP]) for i, r in enumerate(rows) if STEP in r]  # [num_anchor_rows]
    if len(anchors) < 2:
        raise ValueError("need at least two rows with 'steps' to place the other rows")
    a = np.asarray(anchors, dtype=float)  # [num_anchor_rows, 2]
    assert np.all(np.diff(a[:, 1]) >= 0), "environment steps must not decrease"
    return np.interp(np.arange(len(rows), dtype=float), a[:, 0], a[:, 1])  # [num_rows]


def _tail_mean(rows, steps, start, key) -> Optional[float]:
    values = [r[key] for r, s in zip(rows, steps) if s >= start and key in r and math.isfinite(r[key])]
    return statistics.fmean(values) if values else None


def summarize_run(path: Path, tail: float = 0.1) -> RunSummary:
    assert 0.0 < tail <= 1.0
    rows = read_jsonl(path)
    steps = _interpolated_steps(rows)  # [num_rows]
    max_steps = float(steps.max())
    start = (1.0 - tail) * max_steps

    episodes = [(r[STEP], r[EPISODE_COST]) for r in rows if STEP in r and EPISODE_COST in r]  # [num_episodes]
    lengths = np.diff([0.0] + [s for s, _ in episodes])  # [num_episodes]
    tail_eps = [(c, n) for (s, c), n in zip(episodes, lengths) if s >= start and n > 0]
    real_per_step = sum(c for c, _ in tail_eps) / sum(n for _, n in tail_eps) if tail_eps else None

    imag_per_step = _tail_mean(rows, steps, start, "Value/Cost")
    kl = _tail_mean(rows, steps, start, "Model/div")
    kl_agent = None if kl is None else N_CATEGORICALS * kl
    imag_window = None if imag_per_step is None else WINDOW * imag_per_step
    real_window = None if real_per_step is None else WINDOW * real_per_step
    gap = None if imag_window is None or real_window is None else imag_window - real_window
    bv_abs = _tail_mean(rows, steps, start, "Diag/bv_abs")
    v_post = _tail_mean(rows, steps, start, "Diag/v_post")
    betas = [r["Agent/Lagrangian"] for r in rows if "Agent/Lagrangian" in r]
    return RunSummary(
        run=str(path),
        max_steps=max_steps,
        tail_episodes=len(tail_eps),
        eps_c_loss=_tail_mean(rows, steps, start, "Model/cost_loss"),
        kl_per_categorical=kl,
        kl_per_agent=kl_agent,
        pinsker_bound=None if kl_agent is None else math.sqrt(kl_agent / 2.0),
        imag_window=imag_window,
        real_window=real_window,
        abs_gap=None if gap is None else abs(gap),
        rel_gap=None if gap is None or not real_window else gap / real_window,
        bv_signed=_tail_mean(rows, steps, start, "Diag/bv_signed"),
        bv_abs=bv_abs,
        v_post=v_post,
        bv_rel=None if bv_abs is None or not v_post else bv_abs / abs(v_post),
        tv_post_prior=_tail_mean(rows, steps, start, "Diag/tv_post_prior"),
        tv_max_agent=_tail_mean(rows, steps, start, "Diag/tv_post_prior_max_agent"),
        beta_final=betas[-1] if betas else None,
    )


def _resolve(inputs: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        p = Path(item)
        paths.extend(sorted(p.rglob("metrics.jsonl")) if p.is_dir() else [p])
    if not paths:
        raise SystemExit("no metrics.jsonl files found")
    return paths


def aggregate(summaries: Sequence[RunSummary]) -> dict[str, tuple[float, float, int]]:
    """Mean, sample sd (0 for one run) and count per numeric field, ignoring missing values."""
    out = {}
    for field in RunSummary.__dataclass_fields__:
        if field == "run":
            continue
        values = [getattr(s, field) for s in summaries if getattr(s, field) is not None]
        if values:
            sd = statistics.stdev(values) if len(values) > 1 else 0.0
            out[field] = (statistics.fmean(values), sd, len(values))
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="metrics.jsonl files or directories containing them")
    parser.add_argument("--tail", type=float, default=0.1, help="fraction of the run averaged (default 0.1)")
    parser.add_argument("--out", type=Path, default=None, help="per-run CSV output")
    args = parser.parse_args(argv)
    summaries = [summarize_run(p, args.tail) for p in _resolve(args.inputs)]
    if args.out:
        with args.out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(RunSummary.__dataclass_fields__))
            writer.writeheader()
            for s in summaries:
                writer.writerow(asdict(s))
    print(f"{len(summaries)} run(s); window W = {WINDOW:.3f}; tail = {args.tail}")
    for field, (mean, sd, n) in aggregate(summaries).items():
        print(f"  {field:20s} {mean:12.5g} +- {sd:<10.3g} (n={n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
