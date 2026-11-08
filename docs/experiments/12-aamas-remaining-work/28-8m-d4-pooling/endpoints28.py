"""Every 8m d=4 learned-multiplier run's endpoint, computed independently.

Three batches of ``8m`` at :math:`d=4` exist.  Only two of them may be pooled, so
this prints all three side by side with the pooled figure the tables now show:

* **2025** feeds the multiplier the mean **imagined** cost return, as SafeDreamer
  does.  It is a different method -- it is the ``SafeDreamers`` rows of
  ``data/new_experiments_tracking_100k.csv``, the left half of
  ``generated/smac_dual_input.tex`` -- and must never join the others.

  Its three runs are printed there as cost 5.25, but their exports read 4.09 at
  this window and no checkpoint on the grid 50k..339k reproduces the 6.248 the
  tracking CSV holds for the first of them.  Those runs reached 339k steps,
  where the measured-input runs stop at 105k, so the two sets' ``steps`` axes
  are probably not the same quantity.  Unresolved, and out of scope here: #28
  changes only the measured column.
* **Apr/May 2026** and **Oct 2026** both read the **measured** episode cost on the
  same training code (every difference between their commits is behind a flag
  whose default is the earlier behaviour), so they are one sample of six.

The Oct batch was launched as ``--seed 1, 2, 3``, the labels the Apr/May batch
already uses, and is read as seeds 4, 5, 6 (``MEASURED_RELABELLED_SEEDS`` of
``overleaf/thesis/scripts/analyze_exports.py``).  ``--seed`` only names a run --
it seeds neither Python, NumPy, Torch, the environments nor the Ray workers --
which is what makes the six interchangeable in the first place.

Runs are named one by one rather than matched by pattern: the export folders also
hold the PID, imagined and fixed-price arms of the same map and limit, and the
2025 batch predates the current display-name format.

Reads the repo's rule, mean over episode rows with ``S-5000 <= steps <= S``,
``S = 1e5``, so a disagreement with the printed cell means one of the two is
wrong.
"""

import csv
import statistics
from pathlib import Path

CSV_ROOT = Path("/home/corsound/workspace/private-mamba/docs/experiments" "/11-thesis-ablations/6-aamas-revision/csv")
CHECKPOINT = 100_000
WINDOW = 5_000
# (label, multiplier input, joins the pooled sample, folder, {run label: export stem})
BATCHES = (
    (
        "2025",
        "imagined",
        False,
        "smac_8m_old",
        {
            "seed 1": "dead_allies_incremental_starcraft_laglr=1e-05_cost_lim=4.0_8m_23_time_20251023_205553",
            "seed 2": "dead_allies_incremental_starcraft_laglr=1e-05_cost_lim=4.0_8m_2_time_20251127_095033",
            "seed 3": "dead_allies_incremental_starcraft_laglr=1e-05_cost_lim=4.0_8m_3_time_20251224_014514",
        },
    ),
    (
        "Apr/May 2026",
        "measured",
        True,
        "smac_measured_aprmay",
        {
            "17336298": "safedreamer_dai_starcraft_lag1e-05_4.0_8m_s1_date05-05-hr23-17-19_17336298_feat-lag-real-episod",
            "17336300": "safedreamer_dai_starcraft_lag1e-05_4.0_8m_s2_date05-05-hr23-17-19_17336300_feat-lag-real-episod",
            "17336301": "safedreamer_dai_starcraft_lag1e-05_4.0_8m_s3_date05-05-hr23-17-19_17336301_feat-lag-real-episod",
        },
    ),
    (
        "Oct 2026",
        "measured",
        True,
        "smac_8m_new",
        {
            "22156904": "safedreamer_dai_starcraft_lag1e-05_4.0_8m_s1_date10-04-hr22-13-46_22156904_feat-aamas",
            "22156905": "safedreamer_dai_starcraft_lag1e-05_4.0_8m_s2_date10-04-hr22-13-46_22156905_feat-aamas",
            "22156906": "safedreamer_dai_starcraft_lag1e-05_4.0_8m_s3_date10-04-hr22-13-46_22156906_feat-aamas",
        },
    ),
)


def window_mean(folder: str, stem: str) -> tuple[int, float, float, float]:
    """``(episodes, score, cost, win rate)`` over the window of one export."""

    path = CSV_ROOT / folder / f"{stem}_episodes.csv"
    name = CSV_ROOT / folder / f"{stem}.name"
    assert name.is_file(), name  # the export really is the run we think it is
    rows = []
    with path.open() as handle:
        for row in csv.DictReader(handle):
            if CHECKPOINT - WINDOW <= float(row["steps"]) <= CHECKPOINT:
                rows.append(
                    (
                        float(row["main/score"]),
                        float(row["main/cost"]),
                        float(row["main/winrate"]),
                    )
                )
    assert rows, path
    return (
        len(rows),
        statistics.fmean(r[0] for r in rows),
        statistics.fmean(r[1] for r in rows),
        statistics.fmean(r[2] for r in rows),
    )


def cell(values: list[float]) -> str:
    return f"{statistics.fmean(values):.2f} +- {statistics.stdev(values):.2f}"


pooled: dict[str, list[float]] = {"score": [], "cost": [], "win": []}
print(f"{'batch':13} {'input':9} {'run':>9} {'eps':>4} {'score':>7} {'cost':>7} {'win':>6}")
for label, signal, poolable, folder, stems in BATCHES:
    batch: dict[str, list[float]] = {"score": [], "cost": [], "win": []}
    for run, stem in stems.items():
        episodes, score, cost, win = window_mean(folder, stem)
        print(f"{label:13} {signal:9} {run:>9} {episodes:4d} {score:7.2f} {cost:7.3f} {win:6.3f}")
        for key, value in (("score", score), ("cost", cost), ("win", win)):
            batch[key].append(value)
            if poolable:
                pooled[key].append(value)
    print(f"{'':13} {'':9} {'3 runs':>9}      {cell(batch['score'])} | {cell(batch['cost'])} | {cell(batch['win'])}")

assert len(pooled["cost"]) == 6, pooled
print(f"\npooled over the {len(pooled['cost'])} measured-input runs, i.e. the printed cell:")
print(f"  score {cell(pooled['score'])}")
print(f"  cost  {cell(pooled['cost'])}")
print(f"  win   {cell(pooled['win'])}")
