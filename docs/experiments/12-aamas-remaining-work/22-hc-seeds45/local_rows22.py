"""The ``data/local_runs_endpoints.csv`` rows of the #22 learned and parity reruns.

``hc_ablation_endpoints.csv`` is generated and verified by ``analyze_exports.py``, so
the imagined, PID and fixed arms of Table 6 take their new seeds by copying exports
into the group folders.  The Learned and Parity-start rows read
``local_runs_endpoints.csv`` instead, which is hand-maintained, so their rows are
printed here and pasted in -- with the same column meanings
``scripts/collect_local_endpoints.py`` documents:

* ``score``/``cost`` -- mean over the episode rows with ``S-5000 <= steps <= S``;
* ``beta_end``       -- the last multiplier logged before the first row past ``S``;
* ``max_step``       -- the largest step the run logged.

The three published Learned d=5 rows are reprinted too.  They were read by hand for
#20 over ``samples > 995000``, which took five episodes where every other row of the
file has six, so their score and cost are slightly off and are corrected here.
"""

import csv
import math
import statistics
from pathlib import Path

ROOT = Path("/home/corsound/workspace/private-mamba/docs/experiments")
CSV_ROOT = ROOT / "11-thesis-ablations/6-aamas-revision/csv"
ENV = "Safety2x3HalfCheetahVelocity-v0"
CHECKPOINT = 1_000_000
WINDOW = 5_000
DIGITS = 4
BETA = "Agent/Lagrangian"

# (tag, d, seed) -> (export folder, Slurm id).  Learned is the `theory` tag and
# Parity start the `warm1` tag, the two ROW_SOURCES entries of
# scripts/generate_hc_multiplier_table.py that read this file.
RUNS = {
    ("theory", 5.0, 1): ("hc_issue22_published_d5", "23736292"),
    ("theory", 5.0, 2): ("hc_issue22_published_d5", "23736293"),
    ("theory", 5.0, 3): ("hc_issue22_published_d5", "23736294"),
    ("theory", 5.0, 4): ("hc_issue22", "23739341"),
    ("theory", 5.0, 5): ("hc_issue22", "23739342"),
    ("theory", 25.0, 4): ("hc_issue22", "23739348"),
    ("theory", 25.0, 5): ("hc_issue22", "23739350"),
    ("warm1", 5.0, 4): ("hc_issue22", "23739351"),
    ("warm1", 5.0, 5): ("hc_issue22", "23739352"),
    ("warm1", 25.0, 4): ("hc_issue22", "23739358"),
    ("warm1", 25.0, 5): ("hc_issue22", "23739359"),
}
LAG_INIT = {"theory": "", "warm1": "1.0"}


def export(folder: str, slurm: str) -> Path:
    """The export stem of the run ``slurm`` holds, by the Slurm id in its name."""

    stems = [path.stem for path in (CSV_ROOT / folder).glob("*.name") if f"_{slurm}_feat" in path.read_text()]
    assert len(stems) == 1, (folder, slurm, stems)
    return CSV_ROOT / folder / stems[0]


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def endpoint(stem: Path) -> tuple[int, float, float, float, int]:
    """``(n_episodes, score, cost, beta_end, max_step)`` of one run."""

    episodes = read(stem.with_name(f"{stem.name}_episodes.csv"))
    window = [
        (float(row["main/score"]), float(row["main/cost"]))
        for row in episodes
        if CHECKPOINT - WINDOW <= float(row["steps"]) <= CHECKPOINT
    ]
    assert window, stem.name
    steps = [float(row["steps"]) for row in episodes]

    # beta is logged on its own rows, so the two exports interleave by step.
    beta = None
    for row in sorted(read(stem.with_name(f"{stem.name}_lag.csv")), key=lambda r: float(r["steps"])):
        if float(row["steps"]) > CHECKPOINT:
            break
        if row[BETA]:
            beta = float(row[BETA])
    assert beta is not None and math.isfinite(beta), stem.name
    return (
        len(window),
        statistics.fmean(s for s, _ in window),
        statistics.fmean(c for _, c in window),
        beta,
        int(max(steps + [float(row["steps"]) for row in read(stem.with_name(f"{stem.name}_lag.csv"))])),
    )


def number(value: float) -> str:
    """The file's number format, that of collect_local_endpoints.py."""

    return str(round(value, DIGITS))


for (tag, limit, seed), (folder, slurm) in RUNS.items():
    episodes, score, cost, beta, max_step = endpoint(export(folder, slurm))
    print(
        ",".join(
            [
                tag,
                ENV,
                f"{limit:g}" + ("" if limit != int(limit) else ".0"),
                str(seed),
                slurm,
                str(CHECKPOINT),
                str(episodes),
                number(score),
                number(cost),
                "",  # winrate: MAMuJoCo
                number(beta),
                str(max_step),
                "1e-05",
                LAG_INIT[tag],
            ]
        )
    )
