"""Endpoints of the #21 reruns from their W&B episode exports, with the repo's reading rule."""

import csv
import re
import statistics
from pathlib import Path

CSV_DIR = Path(
    "/home/corsound/workspace/private-mamba/docs/experiments/" "11-thesis-ablations/6-aamas-revision/csv/hc_issue21"
)
CHECKPOINT = 1_000_000
WINDOW = 5_000

NAME = re.compile(
    r"_lag(?P<laglr>[\d.e-]+)_(?P<limit>[\d.]+)_Safety2x3HalfCheetahVelocity-v0"
    r"_s(?P<seed>\d+)(?:_init(?P<init>[\d.]+))?_"
)


def tag_of(laglr: str, init: str | None) -> str:
    if float(laglr) == 0.0:
        return "fixed1"
    return "warm1" if init and float(init) == 1.0 else "theory"


rows = []
for name_file in sorted(CSV_DIR.glob("*.name")):
    display = name_file.read_text().strip()
    match = NAME.search(display)
    assert match, display
    episodes = CSV_DIR / f"{name_file.stem}_episodes.csv"
    window = []
    with episodes.open() as handle:
        for row in csv.DictReader(handle):
            step = float(row["steps"])
            if CHECKPOINT - WINDOW <= step <= CHECKPOINT:
                window.append((float(row["main/score"]), float(row["main/cost"])))
    assert window, display
    rows.append(
        {
            "tag": tag_of(match["laglr"], match["init"]),
            "cost_limit": float(match["limit"]),
            "seed": int(match["seed"]),
            "slurm_id": display.split("_")[-2],
            "n_episodes": len(window),
            "score": round(statistics.fmean(s for s, _ in window), 4),
            "cost": round(statistics.fmean(c for _, c in window), 4),
        }
    )

rows.sort(key=lambda r: (r["tag"], r["cost_limit"], r["seed"]))
print(f"{'tag':8} {'d':>5} {'seed':>4} {'slurm':>9} {'eps':>4} {'reward':>10} {'cost':>8}")
for r in rows:
    print(
        f"{r['tag']:8} {r['cost_limit']:5g} {r['seed']:4d} {r['slurm_id']:>9} "
        f"{r['n_episodes']:4d} {r['score']:10.1f} {r['cost']:8.2f}"
    )

with Path("/tmp/issue21_endpoints.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print("\nwrote /tmp/issue21_endpoints.csv")
