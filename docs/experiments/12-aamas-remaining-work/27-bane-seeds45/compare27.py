"""bane_vs_bane at 3 seeds vs 5, at each of its two limits.

Reads the CSV the tables read, so the three-seed column is the partition ``seed <= 3``
of one source rather than a second copy of the published numbers; it cannot drift from
what is rendered.
"""

import csv
import statistics
from pathlib import Path

MEASURED = Path("/home/corsound/workspace/overleaf/thesis/data/ca_mamba_measured_100k.csv")
MAP = "bane_vs_bane"


def rows():
    with MEASURED.open(encoding="utf-8-sig") as handle:
        return sorted(
            (
                {
                    "limit": int(float(r["cost_limit"])),
                    "seed": int(r["seed"]),
                    "slurm": r["slurm_job_id"],
                    "score": float(r["score"]),
                    "cost": float(r["cost"]),
                    "winrate": float(r["winrate"]),
                }
                for r in csv.DictReader(handle)
                if r["map"] == MAP
            ),
            key=lambda r: (r["limit"], r["seed"]),
        )


def cell(subset, key):
    values = [r[key] for r in subset]
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{statistics.fmean(values):6.3f}+-{sd:5.3f}"


all_rows = rows()
for limit in (0, 4):
    at = [r for r in all_rows if r["limit"] == limit]
    print(f"--- d={limit} ---")
    for label, subset in (
        ("seeds 1-3 (reported)", [r for r in at if r["seed"] <= 3]),
        ("seeds 4-5 (new)", [r for r in at if r["seed"] > 3]),
        ("seeds 1-5 (pooled)", at),
    ):
        print(
            f"  {label:22} n={len(subset)}  score {cell(subset, 'score')}"
            f"  cost {cell(subset, 'cost')}  win {cell(subset, 'winrate')}"
        )
    per = ", ".join(f"s{r['seed']}={r['winrate']:.3f}" for r in at)
    print(f"  per-run winrate: {per}\n")
