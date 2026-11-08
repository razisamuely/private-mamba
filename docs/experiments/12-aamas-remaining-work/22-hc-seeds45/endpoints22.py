"""Endpoints of the 22 #22 reruns, each diffed against the thesis row it became.

Reads the W&B episode exports with the repo's rule -- mean over episode rows with
``S-5000 <= steps <= S``, ``S = 1e6`` -- independently of
``overleaf/thesis/scripts/analyze_exports.py``, and prints every run next to the
row it produced in whichever of the two CSVs Table 6 reads.  A mismatch means the
thesis numbers and this extraction disagree and one of them is wrong.

A run's row is decided by its display name, which is the only record of its flags:
``lag<laglr>_<d>_<env>_s<seed>[_init<lag_init>][_imag][_pid]``.  Note three traps:

* W&B caps a display name at 128 characters, so ``_feat-aamas`` can arrive
  truncated to ``_feat-aa`` or ``_feat-a``; nothing may key off the branch suffix.
* ``--lag_init 1e-4`` only restates ``LAGRANGIAN_MULTIPLIER_INIT``, the code's own
  default, so the four imagined reruns carry an ``_init0.0001`` their published
  seeds 1-3 do not.  It is not a different setting.
* ``23739394`` and ``23739395`` were meant as the d=25 fixed-beta=1 seeds but were
  submitted with ``--cost_limit 5``.  Their names say ``_5.0`` and that is what
  they trained on, and seeds 4 and 5 of that cell already exist, so the two runs
  are UNFILED -- they are duplicates of a cell, not runs of the one they were for.
  Reported here so the gap is on the record.
"""

import csv
import re
import statistics
from pathlib import Path
from typing import NamedTuple

ROOT = Path("/home/corsound/workspace")
CSV_DIR = ROOT / ("private-mamba/docs/experiments/11-thesis-ablations/6-aamas-revision/csv/hc_issue22")
LOCAL_CSV = ROOT / "overleaf/thesis/data/local_runs_endpoints.csv"
ABLATION_CSV = ROOT / "overleaf/thesis/data/hc_ablation_endpoints.csv"
ENV = "Safety2x3HalfCheetahVelocity-v0"
CHECKPOINT = 1_000_000
WINDOW = 5_000

NAME = re.compile(
    rf"_lag(?P<laglr>[\d.e-]+)_(?P<limit>[\d.]+)_{ENV}"
    r"_s(?P<seed>\d+)(?:_init(?P<init>[\d.e-]+))?(?P<mode>_imag|_pid)?_date"
)
DEFAULT_LAG_INIT = 1e-4
# The two runs whose cost limit is not the one they were submitted for.
UNFILED = frozenset({"23739394", "23739395"})
# Row key -> (its CSV, that CSV's tag column, the row's value there).  Mirrors
# ROW_SOURCES of scripts/generate_hc_multiplier_table.py.
ROW_SOURCES = {
    "learned": (LOCAL_CSV, "tag", "theory"),
    "parity": (LOCAL_CSV, "tag", "warm1"),
    "imagined": (ABLATION_CSV, "arm", "imagined"),
    "pid": (ABLATION_CSV, "arm", "pid"),
    "fixed1_b": (ABLATION_CSV, "arm", "fixed1"),
    "fixed0": (ABLATION_CSV, "arm", "fixed0"),
}


class Run(NamedTuple):
    """One rerun's endpoint, in the column order of ``rerun_endpoints.csv``."""

    row: str
    cost_limit: float
    seed: int
    slurm_id: str
    n_episodes: int
    score: float
    cost: float


def row_of(laglr: str, init: str | None, mode: str | None) -> str:
    """The Table 6 row a run belongs to, from the flags its display name records."""

    beta_0 = None if init is None or float(init) == DEFAULT_LAG_INIT else float(init)
    if mode == "_imag":
        return "imagined"
    if mode == "_pid":
        return "pid"
    if float(laglr) == 0.0:
        # Both fixed beta=1 rows are the same setting from different batches; the
        # new runs join (B), which is the row the ablation CSV holds.
        return "fixed1_b" if beta_0 == 1.0 else "fixed0"
    return "parity" if beta_0 == 1.0 else "learned"


def window_mean(stem: str) -> tuple[int, float, float]:
    rows = []
    with (CSV_DIR / f"{stem}_episodes.csv").open() as handle:
        for row in csv.DictReader(handle):
            if CHECKPOINT - WINDOW <= float(row["steps"]) <= CHECKPOINT:
                rows.append((float(row["main/score"]), float(row["main/cost"])))
    assert rows, stem
    return len(rows), statistics.fmean(s for s, _ in rows), statistics.fmean(c for _, c in rows)


def filed(row: str, limit: float, seed: int) -> tuple[float, float] | None:
    """The (score, cost) the thesis CSV of ``row`` holds for this run, if any."""

    path, column, value = ROW_SOURCES[row]
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for entry in csv.DictReader(handle):
            if (
                entry["env"] == ENV
                and entry[column] == value
                and float(entry["cost_limit"]) == limit
                and int(entry["seed"]) == seed
            ):
                return float(entry["score"]), float(entry["cost"])
    return None


runs = []
for name_file in sorted(CSV_DIR.glob("*.name")):
    display = name_file.read_text().strip()
    match = NAME.search(display)
    assert match, display
    episodes, score, cost = window_mean(name_file.stem)
    runs.append(
        Run(
            row=row_of(match["laglr"], match["init"], match["mode"]),
            cost_limit=float(match["limit"]),
            seed=int(match["seed"]),
            slurm_id=display.rsplit("_", 1)[0].rsplit("_", 1)[-1],
            n_episodes=episodes,
            score=round(score, 4),
            cost=round(cost, 4),
        )
    )
assert len(runs) == 22, len(runs)
runs.sort(key=lambda r: (r.row, r.cost_limit, r.seed))

print(f"{'row':10} {'d':>3} {'seed':>4} {'slurm':>9} {'eps':>4} {'reward':>9} {'cost':>8}  filed")
mismatches = 0
for run in runs:
    thesis = None if run.slurm_id in UNFILED else filed(run.row, run.cost_limit, run.seed)
    if run.slurm_id in UNFILED:
        verdict = "no (submitted at d=5, not d=25)"
    elif thesis is None:
        verdict = "MISSING from its CSV"
        mismatches += 1
    elif (round(thesis[0], 2), round(thesis[1], 2)) != (
        round(run.score, 2),
        round(run.cost, 2),
    ):
        verdict = f"DIFFERS: CSV has {thesis[0]:.2f} / {thesis[1]:.2f}"
        mismatches += 1
    else:
        verdict = "yes, matches"
    print(
        f"{run.row:10} {run.cost_limit:3g} {run.seed:4d} {run.slurm_id:>9} "
        f"{run.n_episodes:4d} {run.score:9.1f} {run.cost:8.2f}  {verdict}"
    )
print(f"\n{len(runs) - len(UNFILED)} runs filed, {len(UNFILED)} unfiled, {mismatches} mismatch(es)")

out = Path(__file__).with_name("rerun_endpoints.csv")
with out.open("w", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(Run._fields)
    writer.writerows(runs)
print(f"wrote {out}")
