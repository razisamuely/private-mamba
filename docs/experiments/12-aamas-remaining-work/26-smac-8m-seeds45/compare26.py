"""Table 2's Imagined and Measured rows at 3 seeds vs 5 seeds."""

import csv
import re
import statistics
from pathlib import Path

BASE = Path("/home/corsound/workspace/private-mamba/docs/experiments/" "11-thesis-ablations/6-aamas-revision/csv")
THESIS = Path("/home/corsound/workspace/overleaf/thesis")
TARGET = 100_000
WINDOW = 5_000
NAME = re.compile(r"_0\.0_8m_s(?P<seed>\d+)(?P<imag>_imag)?_date.*_(?P<slurm>\d+)_feat-aamas$")


def from_exports(folder, want_imagined):
    """Endpoints of a d=0 export folder, one dict per run of the wanted variant."""
    out = []
    for name_file in sorted((BASE / folder).glob("*.name")):
        display = name_file.read_text().strip()
        match = NAME.search(display)
        if match is None or bool(match["imag"]) is not want_imagined:
            continue
        window = [
            (float(r["main/cost"]), float(r["main/winrate"]))
            for r in csv.DictReader((BASE / folder / f"{name_file.stem}_episodes.csv").open())
            if TARGET - WINDOW <= float(r["steps"]) <= TARGET
        ]
        if not window:
            continue
        lag = BASE / folder / f"{name_file.stem}_lag.csv"
        betas = []
        if lag.exists():
            for row in csv.DictReader(lag.open()):
                value, step = row.get("Agent/Lagrangian", ""), row.get("steps", "")
                if value not in ("", "nan") and step not in ("", "nan") and float(step) <= TARGET:
                    betas.append(float(value))
        out.append(
            {
                "seed": int(match["seed"]),
                "slurm": match["slurm"],
                "cost": statistics.fmean(c for c, _ in window),
                "winrate": statistics.fmean(w for _, w in window),
                "beta": betas[-1] if betas else float("nan"),
            }
        )
    return out


def from_local_csv(tag):
    out = []
    for row in csv.DictReader((THESIS / "data" / "local_runs_endpoints.csv").open()):
        if row["tag"] == tag:
            out.append(
                {
                    "seed": int(row["seed"]),
                    "slurm": row["slurm_id"],
                    "cost": float(row["cost"]),
                    "winrate": float(row["winrate"]),
                    "beta": float(row["beta_end"]),
                }
            )
    return out


def cell(runs):
    def ms(key):
        values = [r[key] for r in runs]
        sd = statistics.stdev(values) if len(values) > 1 else 0.0
        return f"{statistics.fmean(values):.2f}+-{sd:.2f}"

    return f"n={len(runs)}  cost {ms('cost'):14} win {ms('winrate'):14} beta {ms('beta'):14}"


# Read what the table itself reads: the Imagined row comes from the export folder,
# the Measured one from LOCAL_RUNS_CSV.  Both now hold all five seeds, so the
# three-seed column is the partition seed <= 3, not a separate source.
runs = {
    "imagined": from_exports("smac_8m_d0_ablation", want_imagined=True),
    "measured": from_local_csv("d0measured"),
}

for variant in ("imagined", "measured"):
    all_runs = sorted(runs[variant], key=lambda r: r["seed"])
    old = [r for r in all_runs if r["seed"] <= 3]
    new = [r for r in all_runs if r["seed"] > 3]
    print(f"--- {variant} ---")
    for label, subset in (
        ("seeds 1-3 (reported)", old),
        ("seeds 4-5 (new)", new),
        ("seeds 1-5 (pooled)", all_runs),
    ):
        print(f"  {label:22} {cell(subset)}")
    seeds = ", ".join(f"s{r['seed']}={r['cost']:.2f}" for r in all_runs)
    print(f"  per-run cost: {seeds}\n")
