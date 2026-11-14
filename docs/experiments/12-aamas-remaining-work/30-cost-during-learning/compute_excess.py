"""Compute cumulative excess cost E_K and violating episodes V_K (#30).

For each run, at the method's checkpoint step:
  E_K = sum over episodes e with step <= checkpoint of max(0, C_e - d)
  V_K = count of episodes where C_e > d

Uses local CSV exports where available, falls back to W&B scan_history.
"""

import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config: representative subset (same as #31)
# ---------------------------------------------------------------------------
SMAC_MAPS = ["3m", "8m", "bane_vs_bane"]
SMAC_LIMITS = {"3m": [0, 1], "8m": [0, 4], "bane_vs_bane": [0, 4]}
MUJOCO_ENVS = [
    "Safety2x3HalfCheetahVelocity-v0",
    "Safety2x4AntVelocity-v0",
    "Safety4x2AntVelocity-v0",
]
MUJOCO_LIMITS = {
    "Safety2x3HalfCheetahVelocity-v0": [5, 25],
    "Safety2x4AntVelocity-v0": [0.2, 25],
    "Safety4x2AntVelocity-v0": [1, 25],
}
METHODS = ["CA-MAMBA", "MACPO", "MAPPO-Lag"]

SMAC_CHECKPOINT = 100_000
MUJOCO_CHECKPOINT = 1_000_000
# Baselines ran to 5M+ but we compare at the SAME checkpoint as CA-MAMBA
# so the comparison is: who violates more over the SAME training horizon?

CSV_ROOT = Path(__file__).resolve().parent.parent.parent / "11-thesis-ablations" / "6-aamas-revision" / "csv"
MANIFEST = Path("/home/corsound/workspace/overleaf/thesis/data/run_manifest.csv")
PROJECT = "raz-shmueli-corsound-ai/private-mamba"


def load_manifest():
    with open(MANIFEST) as f:
        return list(csv.DictReader(f))


def find_local_csv(wandb_run):
    """Search for a local episode CSV whose stem is exactly this run's name.

    A prefix match is NOT safe: the CA-MAMBA SMAC names agree on their first
    ~50 characters and differ only in the map, so a loose match silently
    returns one map's data for every map.
    """
    target = f"{wandb_run}_episodes"
    for p in CSV_ROOT.rglob("*_episodes.csv"):
        if p.stem == target:
            return p
    return None


def read_episodes_local(path):
    """Read (steps, cost) pairs from a local CSV."""
    with open(path) as f:
        reader = csv.DictReader(f)
        return [(float(r["steps"]), float(r["main/cost"])) for r in reader]


def read_episodes_wandb(wandb_run, checkpoint):
    """Read every (steps, cost) row up to `checkpoint` from W&B.

    `history(samples=N)` cannot be used: it downsamples server-side over the
    run's whole length, and several runs continued far past the checkpoint
    (the HC d=25 run reaches 33M steps / 1.5M rows), so only a few hundred
    sampled rows landed under 1M and the cumulative sum came out far too low.
    `scan_history` streams every row in order instead, and breaking at the
    checkpoint means only the run's first few percent is ever fetched.

    Lookup goes through `runs(filters=...)` because baseline display names
    contain `=`, which `api.run()` URL-encodes and then fails to find.
    """
    import wandb

    api = wandb.Api(timeout=120)
    try:
        runs = api.runs(PROJECT, filters={"display_name": wandb_run})
    except Exception:
        return None
    for run in runs:
        episodes = []
        for row in run.scan_history(keys=["steps", "main/cost"], page_size=10000):
            s, c = row.get("steps"), row.get("main/cost")
            if s is None or c is None:
                continue
            if float(s) > checkpoint:
                break
            episodes.append((float(s), float(c)))
        return episodes
    return None


# Table each (benchmark, method) pair's headline runs are reported in.  The
# manifest holds up to ten seed-1 rows per cell because every ablation lives
# there too, so matching on method/config/limit/seed alone silently picks an
# ablation: HC d=25 came back with the fixed-beta run (cost 754-935) instead
# of the reported one.  MAMuJoCo splits its headline numbers over two tables,
# tight limits in one and d=25 in the other.
MAIN_TABLES = {
    ("SMAC", "CA-MAMBA"): ["aamas_main_results"],
    # Not smac_macpo: that tag also covers the earlier 4M bane_vs_bane run.
    ("SMAC", "MACPO"): ["aamas_main_results"],
    ("SMAC", "MAPPO-Lag"): ["smac_mappolag"],
    ("MAMuJoCo", "CA-MAMBA"): ["mamujoco_main", "mamujoco_tight"],
    ("MAMuJoCo", "MACPO"): ["mamujoco_main", "mamujoco_tight"],
    ("MAMuJoCo", "MAPPO-Lag"): ["mamujoco_main", "mamujoco_tight"],
}

# The lagrangian learning rate the thesis reports; 1e-04 is the laglr ablation.
DEFAULT_LAGLR = {"", "1e-05"}


def select_runs(manifest, bench, cfg, cost_limit, method):
    """The reported seed-1 runs for one cell, ablations excluded.

    Deduplicated on the run name: a run cited by two sources gets one
    manifest row per source, which is not a real ambiguity.
    """
    tags = MAIN_TABLES[(bench, method)]
    out, seen = [], set()
    for r in manifest:
        if (
            r["method"] == method
            and r["config"] == cfg
            and r["cost_limit"] == str(cost_limit)
            and r["seed"] == "1"
            and r["variant"] == ""
            and r["laglr"] in DEFAULT_LAGLR
            and any(t in r["tables"].split(";") for t in tags)
            and r["wandb_run"] not in seen
        ):
            seen.add(r["wandb_run"])
            out.append(r)
    return out


def compute_metrics(episodes, cost_limit, checkpoint):
    """Compute E_K and V_K up to checkpoint steps.

    E_K is the raw cumulative excess over the logged rows.  It is NOT
    comparable across methods: CA-MAMBA logs one row per episode while the
    baselines log a mean every 10k steps, so a baseline row stands for many
    episodes but contributes a single value.  Divide by `total` before
    comparing (see the per-episode columns in the output).
    """
    excess = 0.0
    violations = 0
    total = 0
    for steps, cost in episodes:
        if steps > checkpoint:
            break
        total += 1
        over = cost - cost_limit
        if over > 0:
            excess += over
            violations += 1
    return excess, violations, total


def main():
    manifest = load_manifest()
    writer = csv.writer(sys.stdout)
    writer.writerow(
        [
            "benchmark",
            "config",
            "cost_limit",
            "method",
            "seed",
            "checkpoint",
            "episodes",
            "E_K",
            "V_K",
            "V_K_pct",
            "excess_per_episode",
            "source",
        ]
    )

    configs = []
    for m in SMAC_MAPS:
        for d in SMAC_LIMITS[m]:
            configs.append(("SMAC", m, d, SMAC_CHECKPOINT))
    for e in MUJOCO_ENVS:
        for d in MUJOCO_LIMITS[e]:
            configs.append(("MAMuJoCo", e, d, MUJOCO_CHECKPOINT))

    for bench, cfg, d, checkpoint in configs:
        for method in METHODS:
            candidates = select_runs(manifest, bench, cfg, d, method)
            if not candidates:
                print(f"  SKIP {method:10} {cfg} d={d} (no manifest row)", file=sys.stderr, flush=True)
                continue

            wandb_run, local = candidates[-1]["wandb_run"], None
            for r in candidates:
                hit = find_local_csv(r["wandb_run"]) if r["wandb_run"] else None
                if hit:
                    wandb_run, local = r["wandb_run"], hit
                    break

            if local:
                episodes = read_episodes_local(local)
                source = "local"
            else:
                print(f"  W&B  {method:10} {cfg} d={d} ...", file=sys.stderr, end="", flush=True)
                episodes = read_episodes_wandb(wandb_run, checkpoint) if wandb_run else None
                source = "wandb"

            if not episodes:
                print(" FAILED", file=sys.stderr, flush=True)
                continue

            excess, violations, total = compute_metrics(episodes, d, checkpoint)
            v_pct = 100 * violations / total if total > 0 else 0
            per_ep = excess / total if total > 0 else 0

            writer.writerow(
                [
                    bench,
                    cfg,
                    d,
                    method,
                    1,
                    checkpoint,
                    total,
                    f"{excess:.2f}",
                    violations,
                    f"{v_pct:.1f}",
                    f"{per_ep:.3f}",
                    source,
                ]
            )
            sys.stdout.flush()

            status = f"E={excess:.1f} V={violations}/{total} ({v_pct:.0f}%)"
            if source == "wandb":
                print(f" {status}", file=sys.stderr, flush=True)
            else:
                print(f"  local {method:10} {cfg} d={d} {status}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
