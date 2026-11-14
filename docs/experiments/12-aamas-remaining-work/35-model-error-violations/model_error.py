"""Does model error predict which runs exceed the limit? (#35)

Theorem 4.1 decomposes the real-vs-imagined cost gap into a cost-head term
(15*eps_c) and a transition term (105*c_max*eps_P).  Experiment 11's
`5-theorem1-estimates` checked the *inequality* -- is the observed gap below
the bound Delta? -- and found it holds with 50-900x slack, concluding model
error was too small to matter.

That conclusion does not follow.  A loose worst-case bound says nothing about
whether model error *orders* the runs.  This script asks the ordering question
instead: across runs, does more model error go with more cost above d?

Scale matters, so the test is WITHIN a cell.  eps_c grows with the magnitude of
the cost being predicted, so a d=25 run has a larger eps_c than a d=5 run for
reasons that have nothing to do with safety.  Pooling across limits would
measure that confound.  Inside one (env, limit, laglr) cell the runs differ
only by seed, so comparing two of them is clean; the sign test pools those
within-cell pairs.

No new training and no W&B: both inputs are Experiment 11's per-run CSVs,
which already carry eps_c, the TV proxy for eps_P, and both cost sides.
"""

import argparse
import collections
import csv
import itertools
import math
import statistics as st
from pathlib import Path

EXP11 = Path(__file__).resolve().parents[2] / "11-thesis-ablations" / "5-theorem1-estimates"

# Experiment 11 reports costs per discounted 15-step imagination window.  The
# real side was built as episode_cost / episode_length * DISCOUNTED_HORIZON, so
# multiplying back by episode_length / DISCOUNTED_HORIZON recovers the episode
# cost that the limit d is actually compared against.
DISCOUNTED_HORIZON = 13.9  # sum of gamma^t over 15 steps at gamma=0.99

# eps_c is the cost-head error and tv the Pinsker proxy for the transition
# error eps_P.  Both are measured on real replay transitions, so neither is a
# function of the episode cost -- that independence is what makes the test
# meaningful.  `gap` is the direct real-minus-imagined difference: it predicts
# well but is partly circular, since it contains the real cost that `excess` is
# also built from.  It is reported for completeness, not as evidence.
PREDICTORS = ("eps_c", "tv", "gap")


def read(path, limit_override=None):
    """Per-run records with the episode-scale cost restored.

    `limit_override` exists because the SMAC export carries one limit (0) for
    every row and the per-run limit lives in the filename, not the data.
    """
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            d = float(r["cost_limit"]) if limit_override is None else limit_override
            length = float(r["episode_length"])
            scale = length / DISCOUNTED_HORIZON
            real = float(r["real_cost_15step"]) * scale
            imag = float(r["imag_cost_15step"]) * scale
            out.append(
                {
                    "env": r["env"],
                    "cost_limit": d,
                    "laglr": r["laglr"],
                    "seed": r["seed"],
                    "eps_c": float(r["eps_c"]),
                    "tv": float(r["tv_proxy"]),
                    "gap": real - imag,
                    "imagined_cost": imag,
                    "real_cost": real,
                    "excess": max(0.0, real - d),
                }
            )
    return out


def by_cell(records):
    cells = collections.defaultdict(list)
    for r in records:
        cells[(r["env"], r["cost_limit"], r["laglr"])].append(r)
    return cells


def sign_test(cells, predictor, outcome):
    """Concordant within-cell pairs and the one-sided binomial p.

    A pair in which either side ties carries no ordering information and is
    dropped rather than counted as a disagreement: at a tight limit most runs
    sit at excess exactly 0, so counting those ties would swamp the signal.
    """
    concordant = discordant = ties = 0
    for group in cells.values():
        for a, b in itertools.combinations(group, 2):
            dx = a[predictor] - b[predictor]
            dy = a[outcome] - b[outcome]
            if dx == 0 or dy == 0:
                ties += 1
            elif dx * dy > 0:
                concordant += 1
            else:
                discordant += 1
    n = concordant + discordant
    p = sum(math.comb(n, k) for k in range(concordant, n + 1)) / 2 ** n if n else float("nan")
    return concordant, n, ties, p


def spearman_within(cells, predictor, outcome):
    """Spearman correlation after removing each cell's mean from both sides."""
    xs, ys = [], []
    for group in cells.values():
        mx = st.fmean(r[predictor] for r in group)
        my = st.fmean(r[outcome] for r in group)
        xs += [r[predictor] - mx for r in group]
        ys += [r[outcome] - my for r in group]

    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0] * len(values)
        for rank, i in enumerate(order):
            out[i] = rank
        return out

    rx, ry = ranks(xs), ranks(ys)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def report(name, records):
    cells = by_cell(records)
    print(f"\n{name}: {len(records)} runs, {len(cells)} cells")
    print(f"  {'predictor':<10}{'concordant':>12}{'p':>10}{'ties':>7}{'rho':>8}")
    for predictor in PREDICTORS:
        c, n, ties, p = sign_test(cells, predictor, "excess")
        rho = spearman_within(cells, predictor, "excess")
        pct = f"{c}/{n} ({100 * c / n:.0f}%)" if n else "-"
        print(f"  {predictor:<10}{pct:>12}{p:>10.4f}{ties:>7}{rho:>+8.3f}")
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, help="write per-run rows here")
    args = ap.parse_args()

    mamujoco = read(EXP11 / "theorem1_mamujoco_per_run.csv")
    # Every SMAC run in that export was launched at d=0, so `excess` there is
    # the whole episode cost and the row answers a weaker question than the
    # MAMuJoCo rows do.  Kept as a replication attempt, not as headline.
    smac = read(EXP11 / "theorem1_smac_per_run.csv")

    report("MAMuJoCo", mamujoco)
    report("SMAC (d=0 only)", smac)

    if args.csv:
        rows = [dict(r, benchmark=b) for b, rs in (("MAMuJoCo", mamujoco), ("SMAC", smac)) for r in rs]
        fields = [
            "benchmark",
            "env",
            "cost_limit",
            "laglr",
            "seed",
            "eps_c",
            "tv",
            "imagined_cost",
            "real_cost",
            "gap",
            "excess",
        ]
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows({k: r[k] for k in fields} for r in rows)
        print(f"\nwrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
