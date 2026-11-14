"""Feasibility against interaction budget on SMAC (#33).

For each of the 12 SMAC maps with a nonzero cost limit, and for each method at
each interaction budget, decide whether the method MEETS the limit: the mean
episode cost across seeds is at most d.  Then count how many of the 12 each
method meets at each budget.

No new training.  Every number comes from the CSVs that already back the
thesis tables, so the counts are reproducible from the published data:

* CA-MAMBA      `ca_mamba_measured_100k.csv`              (100k only)
* MACPO         `new_experiments_tracking{,_100k}.csv`    (100k and 5M only)
* MAPPO-Lag     `mappolag_smac_per_seed_<budget>.csv`     (100k..5M)

Budget coverage is uneven and is NOT filled in by extrapolation: CA-MAMBA was
never run past 100k on SMAC and MACPO has no 1M export, so those cells are
reported as "not run" rather than guessed.
"""

import argparse
import collections
import csv
import statistics as st
import sys
from pathlib import Path

THESIS_DATA = Path("/home/corsound/workspace/overleaf/thesis/data")

# d=0 limits are excluded: "mean cost at most zero" is met only by a run that
# never loses a unit, which makes the row degenerate rather than informative.
# The thesis reports the same 12 nonzero limits.
EXPECTED_CONFIGS = 12


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def collect(rows, cost_key="cost", limit_key="cost_limit", map_key="map"):
    """Group per-seed costs by (map, nonzero limit)."""
    out = collections.defaultdict(list)
    for r in rows:
        cost, limit = as_float(r[cost_key]), as_float(r[limit_key])
        if cost is None or limit is None or limit == 0:
            continue
        out[(r[map_key], limit)].append(cost)
    return out


def read_ca_mamba():
    with open(THESIS_DATA / "ca_mamba_measured_100k.csv") as f:
        return {"100k": collect(list(csv.DictReader(f)))}


def read_mappolag():
    out = {}
    for label in ("100k", "500k", "1M", "2M", "5M"):
        with open(THESIS_DATA / f"mappolag_smac_per_seed_{label}.csv") as f:
            out[label] = collect(list(csv.DictReader(f)))
    return out


def read_macpo():
    """MACPO lives in the shared tracking CSVs under algorithm ``SafePO``.

    Those files hold MACPO only -- MAPPO-Lag has its own per-seed exports --
    but the budget is in `metric_step`, not the filename, so each budget has
    to be filtered out of the right file.
    """
    out = {}
    for label, fname, step in (
        ("100k", "new_experiments_tracking_100k.csv", "100000"),
        ("5M", "new_experiments_tracking.csv", "5000000"),
    ):
        with open(THESIS_DATA / fname) as f:
            rows = [r for r in csv.DictReader(f) if r["algorithm"] == "SafePO" and r["metric_step"] == step]
        out[label] = collect(rows)
    return out


def summarize(grouped):
    """(met, total, per-config detail) for one method at one budget."""
    detail, met = [], 0
    for (map_name, limit), costs in sorted(grouped.items()):
        mean_cost = st.mean(costs)
        ok = mean_cost <= limit
        met += ok
        detail.append((map_name, limit, len(costs), mean_cost, ok))
    return met, len(grouped), detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, help="write per-config rows here")
    args = ap.parse_args()

    methods = {
        "CA-MAMBA": read_ca_mamba(),
        "MACPO": read_macpo(),
        "MAPPO-Lag": read_mappolag(),
    }
    budgets = ["100k", "500k", "1M", "2M", "5M"]

    rows = []
    counts = {}
    for method, by_budget in methods.items():
        for budget, grouped in by_budget.items():
            met, total, detail = summarize(grouped)
            counts[(method, budget)] = (met, total)
            if total != EXPECTED_CONFIGS:
                print(
                    f"WARNING {method} {budget}: {total} configs, expected {EXPECTED_CONFIGS}",
                    file=sys.stderr,
                )
            for map_name, limit, n_seeds, mean_cost, ok in detail:
                rows.append([method, budget, map_name, limit, n_seeds, f"{mean_cost:.3f}", int(ok)])

    width = max(len(m) for m in methods)
    print(f"{'method':<{width}} " + " ".join(f"{b:>8}" for b in budgets))
    for method in methods:
        cells = []
        for budget in budgets:
            if (method, budget) in counts:
                met, total = counts[(method, budget)]
                cells.append(f"{met}/{total}")
            else:
                cells.append("-")
        print(f"{method:<{width}} " + " ".join(f"{c:>8}" for c in cells))
    print("\n'-' = not run at that budget, not a zero.")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["method", "budget", "map", "cost_limit", "n_seeds", "mean_cost", "met"])
            w.writerows(rows)
        print(f"\nwrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
