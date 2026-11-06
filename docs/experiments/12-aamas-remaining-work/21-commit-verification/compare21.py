"""Table 6 cells from Shahaf's original runs, our #21 reruns, and the two pooled."""

import csv
import statistics
from pathlib import Path

THESIS = Path("/home/corsound/workspace/overleaf/thesis")
ROW_LABEL = {"theory": "Learned", "warm1": "Parity start", "fixed1": "beta=1 (A)"}


def load(path, keep=None):
    cells = {}
    with path.open() as handle:
        for row in csv.DictReader(handle):
            if not row["score"] or "HalfCheetah" not in row.get("env", "HalfCheetah"):
                continue
            if keep is not None and row["slurm_id"] not in keep:
                continue
            key = (row["tag"], float(row["cost_limit"]))
            cells.setdefault(key, []).append((int(row["slurm_id"]), float(row["score"]), float(row["cost"])))
    return cells


OURS = {str(r["slurm_id"]) for r in csv.DictReader(Path("/tmp/issue21_endpoints.csv").open())}
existing = load(THESIS / "data" / "local_runs_endpoints.csv")
mine = load(Path("/tmp/issue21_endpoints.csv"))
# Shahaf's d=5 Learned set, from his zip
shahaf_d5 = load(Path("/tmp/shahaf_d5/reproduced.csv"))
existing[("theory", 5.0)] = existing.get(("theory", 5.0), []) + shahaf_d5[("learned", 5.0)]


def fmt(runs, limit):
    if not runs:
        return "            --            "
    rewards = [r for _, r, _ in runs]
    costs = [c for _, _, c in runs]
    within = sum(c <= limit for c in costs)
    sd_r = statistics.stdev(rewards) if len(rewards) > 1 else 0.0
    sd_c = statistics.stdev(costs) if len(costs) > 1 else 0.0
    flag = "*" if statistics.fmean(costs) > limit else " "
    return (
        f"{statistics.fmean(rewards):6.0f}+-{sd_r:<4.0f} "
        f"{statistics.fmean(costs):6.2f}{flag}+-{sd_c:<5.2f} ({within}/{len(costs)})"
    )


print(f"{'row':14} {'d':>3}  {'ORIGINAL (Shahaf)':^28} {'RERUN (#21)':^28} {'POOLED':^28}")
print("-" * 108)
for tag in ("theory", "warm1", "fixed1"):
    for limit in (5.0, 25.0):
        old = existing.get((tag, limit), [])
        new = [r for r in mine.get((tag, limit), [])]
        old = [r for r in old if str(r[0]) not in OURS]
        if not old and not new:
            continue
        print(f"{ROW_LABEL[tag]:14} {limit:3g}  {fmt(old, limit)} {fmt(new, limit)} " f"{fmt(old + new, limit)}")
print("\n* = mean cost above d.  '+-' is the sample standard deviation over runs.")
print("Learned d=5 ORIGINAL pools Shahaf's 22400771-74 with our earlier 23736292-94 (6 runs).")
