#!/usr/bin/env python3
"""
Pipeline: extract MAMuJoCo metrics → aggregate → render PDF table.

Reuses extract_metrics.py for WandB data fetching.
Extracts SafeDreamer at 100k/500k/700k/800k/900k/1M, MACPO at 10M final.
Appends paper reference values (MACPO Paper, SafePO Paper).
Outputs CSV + LaTeX/PDF comparison table.

Usage:
  python mamujoco_pipeline_experiment8.py [--test] [--render-only FILE]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from extract_metrics import (
    average_metrics_in_env_step_window,
    extract_run_id_from_url,
    fetch_run_history_as_dataframe,
)
from extraction_config import (
    CSV_COL_ALGORITHM,
    CSV_COL_COST_LIMIT,
    CSV_COL_SEED,
    CSV_COL_WANDB_LINK,
    TABLE_COL_COST,
    TABLE_COL_SCORE,
    TABLE_MISSING,
    WINDOW_SIZE,
)
from paths_config import _TMP
from wandb_config import WANDB_PROJECT, WANDB_TIMEOUT

# ── Imports from existing extraction infrastructure ──────────────────────────
# NOTE: all shared logic lives in extract_metrics.py, extraction_config.py,
# paths_config.py, wandb_config.py. This pipeline only adds MAMuJoCo-specific
# orchestration (multiple target steps, paper reference rows, laglr grouping, table layout).


# ── Constants ────────────────────────────────────────────────────────────────

INPUT_CSV = Path(__file__).parent.parent / "inputs" / "mamujoco_runs_experiment8.csv"
OUTPUT_DIR = _TMP / "tables" / "mamujoco_comparison_experiment8"
AGG_CSV = _TMP / "aggregated" / "mamujoco_agg_experiment8.csv"

# SafeDreamer target steps (with window size for averaging)
SD_TARGET_STEPS = [100_000, 500_000, 700_000, 800_000, 900_000, 1_000_000]
# MACPO: use final value (extract at very high target, fallback gets last rows)
MACPO_TARGET_STEP = 10_000_000
DEFAULT_LAGLR = 1e-5

# Column name for env (replaces "map" in SMAC pipelines)
COL_ENV = "env"
COL_STEPS = "target_steps"
COL_SOURCE = "source"
COL_LAGLR = "laglr"

# Source labels
SRC_MACPO_PAPER = "MACPO Paper"
SRC_SAFEPO_PAPER = "SafePO Paper"
SRC_MACPO_RUN = "MACPO Run"
ALGO_SD = "SafeDreamer"
ALGO_MACPO = "MACPO"

# ── Paper / GitHub reference values (Step 2) ─────────────────────────────────
# Visual estimates from GitHub figures (github.com/chauncygu/Multi-Agent-Constrained-Policy-Optimisation)
# and README text. All marked approximate (~).

PAPER_REFERENCE = [
    # MACPO paper (chauncygu repo, GitHub figures, cost limits 0.2/1.0/5.0, at 10M steps, approximate)
    {
        "env": "Safety2x4AntVelocity-v0",
        "cost_limit": 0.2,
        "source": "MACPO Paper ~",
        "target_steps": 10_000_000,
        "score": 900,
        "cost": 15,
    },
    {
        "env": "Safety4x2AntVelocity-v0",
        "cost_limit": 1.0,
        "source": "MACPO Paper ~",
        "target_steps": 10_000_000,
        "score": 650,
        "cost": 15,
    },
    {
        "env": "Safety2x3HalfCheetahVelocity-v0",
        "cost_limit": 5.0,
        "source": "MACPO Paper ~",
        "target_steps": 10_000_000,
        "score": 2250,
        "cost": 40,
    },
    # SafePO paper (Table 5b, arXiv 2310.12567, cost_limit=25, 10M steps, exact)
    {
        "env": "Safety2x4AntVelocity-v0",
        "cost_limit": 25.0,
        "source": "SafePO Paper",
        "target_steps": 10_000_000,
        "score": 1099.23,
        "cost": 3.39,
    },
    {
        "env": "Safety4x2AntVelocity-v0",
        "cost_limit": 25.0,
        "source": "SafePO Paper",
        "target_steps": 10_000_000,
        "score": 815.77,
        "cost": 0.0,
    },
    {
        "env": "Safety2x3HalfCheetahVelocity-v0",
        "cost_limit": 25.0,
        "source": "SafePO Paper",
        "target_steps": 10_000_000,
        "score": 1637.29,
        "cost": 52.10,
    },
]


# ── CSV loader ───────────────────────────────────────────────────────────────


def load_runs(csv_path: Path) -> list[dict]:
    """Load experiment runs from CSV. Returns list of dicts with run_id, env, algorithm, seed, cost_limit."""
    runs = []
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        run_id = extract_run_id_from_url(row[CSV_COL_WANDB_LINK])
        if run_id:
            runs.append(
                {
                    "run_id": run_id,
                    "env": row[COL_ENV],
                    "algorithm": row[CSV_COL_ALGORITHM],
                    "seed": int(row[CSV_COL_SEED]),
                    "cost_limit": float(row[CSV_COL_COST_LIMIT]),
                    COL_LAGLR: float(row.get(COL_LAGLR, DEFAULT_LAGLR)),
                }
            )
    return runs


# ── Extraction ───────────────────────────────────────────────────────────────


def extract_at_step(api, run_id: str, target_step: int, algo: str = ALGO_SD) -> dict | None:
    """Extract score/cost at target_step using 5k window average.
    For MACPO final values, uses run.summary (different metric keys).
    Returns dict with score, cost, max_step, reached_target or None on failure.
    """
    try:
        import urllib.parse

        run_id = urllib.parse.unquote(run_id)
        run = api.run(f"{WANDB_PROJECT}/{run_id}")

        # MACPO: use summary (final values)
        if algo == ALGO_MACPO:
            rew = run.summary.get("main/score", run.summary.get("average_episode_reward", np.nan))
            cost = run.summary.get("main/cost", run.summary.get("average_episode_cost", np.nan))
            max_step = run.summary.get("steps", run.summary.get("_step", 0))
            return {
                "score": rew,
                "cost": cost,
                "max_step": max_step,
                "reached_target": max_step >= target_step * 0.9,
            }

        # SafeDreamer: use parquet artifact / history with env steps
        df = fetch_run_history_as_dataframe(run, target_step)
        result = average_metrics_in_env_step_window(df, target_step, WINDOW_SIZE)
        return {
            "score": result.get("avg_score", np.nan),
            "cost": result.get("avg_cost", np.nan),
            "max_step": result.get("max_step", 0),
            "reached_target": result.get("reached_target", False),
        }
    except Exception as e:
        print(f"  Warning: {run_id} @ {target_step}: {e}", file=sys.stderr)
        return None


def extract_all(api, runs: list[dict]) -> pd.DataFrame:
    """Extract metrics for all runs at their target steps.
    SafeDreamer: 100k, 500k, 1M. MACPO: 10M.
    Returns per-seed DataFrame.
    """
    rows = []
    for exp in runs:
        algo = exp["algorithm"]
        targets = SD_TARGET_STEPS if algo == ALGO_SD else [MACPO_TARGET_STEP]
        if algo == ALGO_SD:
            lr = exp.get(COL_LAGLR, DEFAULT_LAGLR)
            source = f"SafeDreamer (lr={lr})"
        else:
            source = SRC_MACPO_RUN

        for target in targets:
            print(f"Extracting {algo} {exp['env']} c={exp['cost_limit']} s{exp['seed']} @ {target}...")
            result = extract_at_step(api, exp["run_id"], target, algo=algo)
            if result is None:
                continue
            score = result["score"] if result["score"] != "N/A" else np.nan
            cost = result["cost"] if result["cost"] != "N/A" else np.nan
            rows.append(
                {
                    COL_ENV: exp["env"],
                    COL_SOURCE: source,
                    CSV_COL_COST_LIMIT: exp["cost_limit"],
                    CSV_COL_SEED: exp["seed"],
                    COL_STEPS: target,
                    TABLE_COL_SCORE: float(score) if not pd.isna(score) else np.nan,
                    TABLE_COL_COST: float(cost) if not pd.isna(cost) else np.nan,
                    COL_LAGLR: exp.get(COL_LAGLR, DEFAULT_LAGLR),
                }
            )
    return pd.DataFrame(rows)


# ── Aggregation ──────────────────────────────────────────────────────────────


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean +- std per (env, cost_limit, source, target_steps, laglr)."""
    grp_cols = [COL_ENV, CSV_COL_COST_LIMIT, COL_SOURCE, COL_STEPS]
    if COL_LAGLR in df.columns:
        grp_cols.append(COL_LAGLR)
    grp = df.groupby(grp_cols)
    agg = grp[[TABLE_COL_SCORE, TABLE_COL_COST]].agg(["mean", "std", "count"]).round(1)
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    return agg.reset_index()


def append_paper_reference(agg: pd.DataFrame) -> pd.DataFrame:
    """Append hardcoded paper/GitHub reference rows."""
    ref_rows = []
    for ref in PAPER_REFERENCE:
        ref_rows.append(
            {
                COL_ENV: ref["env"],
                CSV_COL_COST_LIMIT: ref["cost_limit"],
                COL_SOURCE: ref["source"],
                COL_STEPS: ref["target_steps"],
                f"{TABLE_COL_SCORE}_mean": ref["score"],
                f"{TABLE_COL_SCORE}_std": np.nan,
                f"{TABLE_COL_SCORE}_count": 0,
                f"{TABLE_COL_COST}_mean": ref["cost"],
                f"{TABLE_COL_COST}_std": np.nan,
                f"{TABLE_COL_COST}_count": 0,
            }
        )
    return pd.concat([agg, pd.DataFrame(ref_rows)], ignore_index=True)


# ── Rendering ────────────────────────────────────────────────────────────────


def _fmt(mean: float, std: float) -> str:
    """Format mean+-std, or TABLE_MISSING if NaN."""
    if pd.isna(mean):
        return TABLE_MISSING
    if pd.isna(std) or std == 0:
        return f"{mean:.1f}"
    return f"{mean:.1f} $\\pm$ {std:.1f}"


def _step_label(steps: int) -> str:
    if steps >= 1_000_000:
        return f"{steps // 1_000_000}M"
    return f"{steps // 1000}k"


def _short_env(env: str) -> str:
    """Shorten env name for table display."""
    return env.replace("Safety", "").replace("Velocity-v0", "").replace("_", "\\_")


def build_latex(agg: pd.DataFrame, standalone: bool = True) -> str:
    """Render aggregated DataFrame as LaTeX longtable."""
    header = (
        "\\textbf{Env} & \\textbf{CL} & \\textbf{Source} & "
        "\\textbf{Steps} & \\multicolumn{1}{r}{\\textbf{Reward} $\\uparrow$} & "
        "\\multicolumn{1}{r}{\\textbf{Cost} $\\downarrow$} \\\\"
    )
    body_lines = []
    # Sort: env, cost_limit, source order (paper first, then our MACPO, then our SD by steps)
    source_order = {
        f"{SRC_MACPO_PAPER} ~": 0,
        SRC_SAFEPO_PAPER: 1,
        SRC_MACPO_RUN: 2,
        f"{ALGO_SD} (lr=1e-5)": 3,
        f"{ALGO_SD} (lr=1e-4)": 4,
        ALGO_SD: 3,
    }
    agg = agg.copy()
    agg["_sort_source"] = agg[COL_SOURCE].map(source_order).fillna(9)
    sort_cols = [COL_ENV, CSV_COL_COST_LIMIT, "_sort_source"]
    if COL_LAGLR in agg.columns:
        sort_cols.append(COL_LAGLR)
    sort_cols.append(COL_STEPS)
    agg = agg.sort_values(sort_cols)

    # Find best reward (highest) and best cost (lowest) per (env, cost_limit)
    best = {}
    for (env, cl), grp in agg.groupby([COL_ENV, CSV_COL_COST_LIMIT]):
        scores = grp[f"{TABLE_COL_SCORE}_mean"].dropna()
        costs = grp[f"{TABLE_COL_COST}_mean"].dropna()
        best[(env, cl)] = {
            "best_score": scores.max() if len(scores) > 0 else np.nan,
            "best_cost": (
                costs[costs > 0].min() if len(costs[costs > 0]) > 0 else costs.min() if len(costs) > 0 else np.nan
            ),
        }

    def _bold(val: str) -> str:
        return f"\\textbf{{{val}}}"

    prev_env_cl = None
    for _, row in agg.iterrows():
        env_cl = (row[COL_ENV], row[CSV_COL_COST_LIMIT])
        if prev_env_cl is not None and env_cl != prev_env_cl:
            body_lines.append("\\midrule")
        prev_env_cl = env_cl

        env_tex = _short_env(str(row[COL_ENV]))
        score_val = row[f"{TABLE_COL_SCORE}_mean"]
        cost_val = row[f"{TABLE_COL_COST}_mean"]
        score = _fmt(score_val, row.get(f"{TABLE_COL_SCORE}_std", np.nan))
        cost = _fmt(cost_val, row.get(f"{TABLE_COL_COST}_std", np.nan))

        # Bold best per group
        b = best.get(env_cl, {})
        if not pd.isna(score_val) and not pd.isna(b.get("best_score")) and score_val == b["best_score"]:
            score = _bold(score)
        if not pd.isna(cost_val) and not pd.isna(b.get("best_cost")) and cost_val == b["best_cost"]:
            cost = _bold(cost)

        steps = _step_label(int(row[COL_STEPS]))
        body_lines.append(
            f"{env_tex} & {row[CSV_COL_COST_LIMIT]} & {row[COL_SOURCE]} & " f"{steps} & {score} & {cost} \\\\"
        )

    body = "\n".join(body_lines)
    table = (
        "\\begin{longtable}{l r l r r r}\n"
        "\\caption{Experiment 8: SafeDreamer vs MACPO on MAMuJoCo (continuous actions).}\n"
        "\\label{tab:mamujoco_experiment8} \\\\\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        "\\endfirsthead\n"
        "\\multicolumn{6}{c}{{\\bfseries \\tablename\\ \\thetable{} -- continued}} \\\\\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        "\\endhead\n"
        "\\bottomrule\n"
        "\\endlastfoot\n"
        f"{body}\n"
        "\\end{longtable}\n"
    )

    if standalone:
        return (
            "\\documentclass{article}\n"
            "\\usepackage{booktabs,geometry,longtable}\n"
            "\\geometry{margin=1.5cm}\n"
            "\\begin{document}\n" + table + "\\end{document}\n"
        )
    return table


def render_pdf(tex_path: Path) -> None:
    """Compile tex to PDF. Imported pattern from collision_pipeline."""
    import subprocess

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path.name],
        cwd=tex_path.parent,
        capture_output=True,
        text=True,
    )
    for ext in (".aux", ".log"):
        tex_path.with_suffix(ext).unlink(missing_ok=True)
    if result.returncode != 0:
        print("pdflatex error:", result.stderr[-500:], file=sys.stderr)
    else:
        print(f"Wrote {tex_path.with_suffix('.pdf')}")


# ── Fake data ────────────────────────────────────────────────────────────────


def make_fake_data() -> pd.DataFrame:
    """Generate synthetic data for --test mode (no WandB calls)."""
    rng = np.random.default_rng(42)
    rows = []
    for env, cl in [
        ("Safety2x4AntVelocity-v0", 0.2),
        ("Safety4x2AntVelocity-v0", 1.0),
        ("Safety2x3HalfCheetahVelocity-v0", 5.0),
    ]:
        for seed in (1, 2, 3):
            for target in SD_TARGET_STEPS:
                rows.append(
                    {
                        COL_ENV: env,
                        COL_SOURCE: "Our SafeDreamer",
                        CSV_COL_COST_LIMIT: cl,
                        CSV_COL_SEED: seed,
                        COL_STEPS: target,
                        TABLE_COL_SCORE: rng.uniform(500, 3000),
                        TABLE_COL_COST: rng.uniform(0, 2),
                    }
                )
            rows.append(
                {
                    COL_ENV: env,
                    COL_SOURCE: "Our MACPO",
                    CSV_COL_COST_LIMIT: cl,
                    CSV_COL_SEED: seed,
                    COL_STEPS: MACPO_TARGET_STEP,
                    TABLE_COL_SCORE: rng.uniform(500, 1500),
                    TABLE_COL_COST: rng.uniform(1, 10),
                }
            )
    return pd.DataFrame(rows)


# ── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Use fake data, skip WandB")
    parser.add_argument("--input", type=str, default=str(INPUT_CSV), help="Input CSV path")
    parser.add_argument("--render-only", type=str, default=None, help="Re-render from existing CSV (no WandB)")
    args = parser.parse_args()

    if args.render_only:
        print(f"=== RENDER-ONLY from {args.render_only} ===")
        agg = pd.read_csv(args.render_only)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        tex_path = OUTPUT_DIR / "comparison_table.tex"
        tex_path.write_text(build_latex(agg, standalone=True))
        print(f"Wrote {tex_path}")
        render_pdf(tex_path)
        thesis_path = OUTPUT_DIR / "comparison_table_thesis.tex"
        thesis_path.write_text(build_latex(agg, standalone=False))
        print(f"Wrote {thesis_path}")
        return

    if args.test:
        print("=== TEST MODE: using fake data ===")
        seed_df = make_fake_data()
    else:
        import wandb

        api = wandb.Api(timeout=WANDB_TIMEOUT)
        runs = load_runs(Path(args.input))
        print(f"Loaded {len(runs)} runs from {args.input}")
        seed_df = extract_all(api, runs)
        if seed_df.empty:
            raise RuntimeError("Extracted 0 rows")

    print(f"Extracted {len(seed_df)} seed-level rows")

    agg = aggregate(seed_df)
    agg = append_paper_reference(agg)

    # Save CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AGG_CSV.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(AGG_CSV, index=False)
    print(f"Saved aggregated CSV -> {AGG_CSV}")

    csv_out = OUTPUT_DIR / "comparison_table.csv"
    agg.to_csv(csv_out, index=False)
    print(f"Saved -> {csv_out}")

    # Render LaTeX + PDF
    tex_path = OUTPUT_DIR / "comparison_table.tex"
    tex_path.write_text(build_latex(agg, standalone=True))
    print(f"Wrote {tex_path}")
    render_pdf(tex_path)

    # Thesis-ready (no documentclass wrapper)
    thesis_path = OUTPUT_DIR / "comparison_table_thesis.tex"
    thesis_path.write_text(build_latex(agg, standalone=False))
    print(f"Wrote {thesis_path}")


if __name__ == "__main__":
    main()
