"""Endpoints of the #26 runs (SMAC 8m, d=0, seeds 4-5) from their W&B exports."""

import csv
import re
import statistics
from pathlib import Path

CSV_DIR = Path(
    "/home/corsound/workspace/private-mamba/docs/experiments/"
    "11-thesis-ablations/6-aamas-revision/csv/smac_8m_d0_seeds45"
)
TARGET = 100_000
WINDOW = 5_000
NAME = re.compile(r"_0\.0_8m_s(?P<seed>\d+)(?P<imag>_imag)?_date.*_(?P<slurm>\d+)_feat-aamas$")


def series(path, key):
    out = []
    with path.open() as handle:
        for row in csv.DictReader(handle):
            value, step = row.get(key, ""), row.get("steps", "")
            if value not in ("", "nan") and step not in ("", "nan"):
                out.append((float(step), float(value)))
    return out


rows = []
for name_file in sorted(CSV_DIR.glob("*.name")):
    display = name_file.read_text().strip()
    match = NAME.search(display)
    assert match, display
    episodes = CSV_DIR / f"{name_file.stem}_episodes.csv"
    window = [
        (float(r["main/score"]), float(r["main/cost"]), float(r["main/winrate"]))
        for r in csv.DictReader(episodes.open())
        if TARGET - WINDOW <= float(r["steps"]) <= TARGET
    ]
    if not window:
        print(f"[skip] {display}: nothing in the window (aborted attempt)")
        continue
    lag = CSV_DIR / f"{name_file.stem}_lag.csv"
    betas = [v for s, v in series(lag, "Agent/Lagrangian") if s <= TARGET] if lag.exists() else []
    rows.append(
        {
            "variant": "imagined" if match["imag"] else "measured",
            "seed": int(match["seed"]),
            "slurm_id": match["slurm"],
            "n_episodes": len(window),
            "score": round(statistics.fmean(s for s, _, _ in window), 4),
            "cost": round(statistics.fmean(c for _, c, _ in window), 4),
            "winrate": round(statistics.fmean(w for _, _, w in window), 4),
            "beta_end": round(betas[-1], 4) if betas else "",
        }
    )

rows.sort(key=lambda r: (r["variant"], r["seed"]))
print(f"\n{'variant':9} {'seed':>4} {'slurm':>9} {'eps':>4} {'score':>8} {'cost':>7} {'win':>6} {'beta':>7}")
for r in rows:
    print(
        f"{r['variant']:9} {r['seed']:4d} {r['slurm_id']:>9} {r['n_episodes']:4d} "
        f"{r['score']:8.2f} {r['cost']:7.3f} {r['winrate']:6.3f} {r['beta_end']:>7}"
    )

out = Path(__file__).with_name("rerun_endpoints.csv")
with out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print(f"\nwrote {out}")
