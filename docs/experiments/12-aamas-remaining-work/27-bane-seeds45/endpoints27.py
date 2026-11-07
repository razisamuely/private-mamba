"""bane_vs_bane endpoints: validate the window rule on seeds 1-3, then add 4-5.

The four #27 runs only mean something next to the three already published, so this
first re-derives the published seeds 1-3 from their own W&B exports.  If the rule
reproduces them, the same rule applied to seeds 4 and 5 is comparable; if it does
not, the five runs are not one sample and nothing should be pooled.
"""

import csv
import re
import statistics
from pathlib import Path

BASE = Path("/home/corsound/workspace/private-mamba/docs/experiments/" "11-thesis-ablations/6-aamas-revision/csv")
PUBLISHED = Path("/home/corsound/workspace/overleaf/thesis/data/ca_mamba_measured_100k.csv")
TARGET = 100_000
WINDOW = 5_000
NAME = re.compile(r"_(?P<limit>[\d.]+)_bane_vs_bane_s(?P<seed>\d+)_date(?P<date>[\d\-a-z]+)_(?P<slurm>\d+)_")


def endpoints(folder):
    """One dict per run of ``folder``, by the S-5000 <= steps <= S rule."""

    out = []
    for name_file in sorted((BASE / folder).glob("*.name")):
        display = name_file.read_text().strip()
        match = NAME.search(display)
        if match is None:
            continue  # smac_measured_aprmay holds all 12 maps; NAME selects this one

        window = [
            (float(r["main/score"]), float(r["main/cost"]), float(r["main/winrate"]))
            for r in csv.DictReader((BASE / folder / f"{name_file.stem}_episodes.csv").open())
            if TARGET - WINDOW <= float(r["steps"]) <= TARGET
        ]
        if not window:
            print(f"[skip] {display}: nothing in the window (preempted attempt)")
            continue
        out.append(
            {
                "limit": int(float(match["limit"])),
                "seed": int(match["seed"]),
                "slurm": match["slurm"],
                "n_episodes": len(window),
                "score": statistics.fmean(s for s, _, _ in window),
                "cost": statistics.fmean(c for _, c, _ in window),
                "winrate": statistics.fmean(w for _, _, w in window),
            }
        )
    return out


def published():
    """The bane_vs_bane rows the tables currently read, keyed by (limit, seed)."""

    return {
        (int(float(r["cost_limit"])), int(r["seed"])): r
        for r in csv.DictReader(PUBLISHED.open())
        if r["map"] == "bane_vs_bane"
    }


old, new = endpoints("smac_measured_aprmay"), endpoints("bane_issue27")
rows = sorted(old + new, key=lambda r: (r["limit"], r["seed"]))
table = published()

print("\n--- the window rule against the published rows (seeds 1-3) ---")
print(f"{'d':>2} {'seed':>4} {'eps':>4}  {'recomputed':>26}  {'published':>26}")
agree = True
for row in rows:
    key = (row["limit"], row["seed"])
    mine = f"{row['score']:7.3f} {row['cost']:8.3f} {row['winrate']:6.3f}"
    if key not in table:
        print(f"{row['limit']:2d} {row['seed']:4d} {row['n_episodes']:4d}  {mine:>26}  {'(new)':>26}")
        continue
    ref = table[key]
    theirs = f"{float(ref['score']):7.3f} {float(ref['cost']):8.3f} {float(ref['winrate']):6.3f}"
    same = mine == theirs
    agree &= same
    print(
        f"{row['limit']:2d} {row['seed']:4d} {row['n_episodes']:4d}  {mine:>26}  {theirs:>26}"
        f"  {'ok' if same else 'DIFFERS'}"
    )
print(f"\nwindow rule reproduces the published seeds 1-3: {agree}")


def cell(subset, key):
    values = [r[key] for r in subset]
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{statistics.fmean(values):6.3f}+-{sd:5.3f}"


print("\n--- 3 seeds vs 5, per limit ---")
for limit in (0, 4):
    at = [r for r in rows if r["limit"] == limit]
    print(f"d={limit}")
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

out = Path(__file__).with_name("rerun_endpoints.csv")
with out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(r for r in rows if r["seed"] > 3)
print(f"wrote {out}")
