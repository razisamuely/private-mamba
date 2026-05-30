#!/usr/bin/env python3
"""
Pipeline: extract collision metrics → aggregate → render PDF table.

Calls extract_metrics.py for WandB data, parses its stdout, aggregates
mean/std across seeds, and renders a LaTeX/PDF comparison table.
Runs with --test flag use synthetic data (no WandB calls).

Usage:
  python collision_pipeline.py [--test] [--python /path/to/python]
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from extraction_config import (
    AGG_METRICS,
    COLLISION_MAPS_ORDER,
    CSV_COL_ALGORITHM,
    CSV_COL_COST_LIMIT,
    CSV_COL_MAP,
    CSV_COL_REACHED,
    CSV_COL_SEED,
    MACPO_STEP_LABEL,
    TABLE_COL_COST,
    TABLE_COL_SCORE,
    TABLE_COL_WINRATE,
    TABLE_MISSING,
)
from paths_config import (
    COLLISION_AGG_CSV,
    COLLISION_INPUT_CSV,
    COLLISION_TEX,
    DEFAULT_CONFIG_JSON,
)

# ── Extraction ────────────────────────────────────────────────────────────────


def _step_label(step: int) -> str:
    """Convert step int to short label: 100000 → '100k', 5000000 → '5m'."""
    return MACPO_STEP_LABEL.get(step, f"{step // 1000}k")


def run_extraction(python_bin: str, macpo_target: int, sd_target: int) -> str:
    """Run extract_metrics.py on the collision CSV and return its stdout.

    Temporarily patches map_steps_config.json with the given targets.
    """
    import json

    config_path = DEFAULT_CONFIG_JSON
    original = config_path.read_text()
    config = json.loads(original)
    for m in config:
        if isinstance(config[m], dict):
            config[m]["MACPO"] = macpo_target
            config[m]["SafeDreamers"] = sd_target
    config_path.write_text(json.dumps(config, indent=2))
    try:
        script = Path(__file__).parent / "extract_metrics.py"
        result = subprocess.run(
            [python_bin, str(script), "--output", str(COLLISION_INPUT_CSV)],
            capture_output=True,
            text=True,
        )
    finally:
        config_path.write_text(original)  # always restore
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("extract_metrics.py failed")
    return result.stdout


# ── Parsing ───────────────────────────────────────────────────────────────────


def _parse_metric(metrics_line: str, key: str) -> float:
    """Extract a float value for key from a 'Score: X  Cost: Y  WR: Z' line."""
    for tok in metrics_line.split("  "):
        if tok.startswith(key + ":"):
            v = tok.split(":")[1].strip()
            return float(v) if v != "N/A" else np.nan
    return np.nan


def _parse_reached(lines: list[str], header_idx: int) -> bool:
    """Return True if the Target line after header_idx contains ✓."""
    for line in lines[header_idx + 1 : header_idx + 4]:
        if "Target:" in line:
            return "✓" in line
    return True


def _parse_header(line: str) -> tuple[str, str, float, int] | None:
    """Parse 'ALGO MAP cost=C seed=S' header line. Returns None if not a header."""
    parts = line.split()
    if len(parts) >= 4 and "cost=" in line and "seed=" in line:
        try:
            return parts[0], parts[1], float(parts[2].split("=")[1]), int(parts[3].split("=")[1])
        except (ValueError, IndexError):
            return None
    return None


def parse_extraction_output(text: str) -> pd.DataFrame:
    """Parse extract_metrics.py stdout into a per-seed DataFrame.

    Each row has: map, algorithm, cost_limit, seed, score, cost, winrate, reached_target.
    """
    rows = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(("=", "⚠", "Found", "Loaded", " ")):
            continue
        header = _parse_header(stripped)
        if header is None:
            continue
        algo, mp, cost, seed = header
        metrics_line = next(
            (l.strip() for l in lines[i + 1 : i + 4] if l.strip().startswith("Score:")),
            None,
        )
        if metrics_line is None:
            continue
        rows.append(
            {
                CSV_COL_MAP: mp,
                CSV_COL_ALGORITHM: algo,
                CSV_COL_COST_LIMIT: cost,
                CSV_COL_SEED: seed,
                TABLE_COL_SCORE: _parse_metric(metrics_line, "Score"),
                TABLE_COL_COST: _parse_metric(metrics_line, "Cost"),
                TABLE_COL_WINRATE: _parse_metric(metrics_line, "WR"),
                CSV_COL_REACHED: _parse_reached(lines, i),
            }
        )
    return pd.DataFrame(rows)


# ── Aggregation ───────────────────────────────────────────────────────────────


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop seeds that didn't reach target, then compute mean/std per map+algorithm+cost_limit."""
    if CSV_COL_REACHED in df.columns:
        skipped = df[~df[CSV_COL_REACHED]][[CSV_COL_MAP, CSV_COL_ALGORITHM, CSV_COL_SEED]]
        if not skipped.empty:
            print(f"Skipping {len(skipped)} seeds that didn't reach target:")
            print(skipped.to_string(index=False))
        df = df[df[CSV_COL_REACHED]]
    grp = df.groupby([CSV_COL_MAP, CSV_COL_ALGORITHM, CSV_COL_COST_LIMIT])
    agg = grp[AGG_METRICS].agg(["mean", "std"]).round(3)
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    return agg.reset_index()


# ── Rendering ─────────────────────────────────────────────────────────────────


def _fmt(mean: float, std: float) -> str:
    """Format mean±std for LaTeX, or TABLE_MISSING if NaN."""
    if pd.isna(mean):
        return TABLE_MISSING
    return f"{mean:.2f} $\\pm$ {std:.2f}"


def _bold(val: str) -> str:
    """Wrap a LaTeX value string in \\textbf{}."""
    return f"\\textbf{{{val}}}"


def _metric_row(algo: str, mp: str, row: pd.Series | None, steps_label: str) -> str:
    """Build one data row: Algorithm & Scenario & Score & Cost & Winrate & Steps & CostLimit."""
    m_tex = mp.replace("_", "\\_")
    if row is None:
        return f"{algo} & {m_tex} & {TABLE_MISSING} & {TABLE_MISSING} & {TABLE_MISSING} & {steps_label} & 0 \\\\"
    score = _fmt(row[f"{TABLE_COL_SCORE}_mean"], row[f"{TABLE_COL_SCORE}_std"])
    cost = _fmt(row[f"{TABLE_COL_COST}_mean"], row[f"{TABLE_COL_COST}_std"])
    wr = _fmt(row[f"{TABLE_COL_WINRATE}_mean"], row[f"{TABLE_COL_WINRATE}_std"])
    return f"{algo} & {m_tex} & {score} & {cost} & {wr} & {steps_label} & 0 \\\\"


def _bold_winners(sd_row: str, mp_row: str, sd: pd.Series | None, mp: pd.Series | None) -> tuple[str, str]:
    """Bold SafeDreamer cells where it beats MACPO (score↑, winrate↑, cost↓)."""
    if sd is None or mp is None:
        return sd_row, mp_row

    def _apply_bold(row_str: str, col: str, higher_is_better: bool) -> str:
        if pd.isna(sd[f"{col}_mean"]) or pd.isna(mp[f"{col}_mean"]):
            return row_str
        sd_wins = (
            (sd[f"{col}_mean"] > mp[f"{col}_mean"]) if higher_is_better else (sd[f"{col}_mean"] < mp[f"{col}_mean"])
        )
        if not sd_wins:
            return row_str
        val = _fmt(sd[f"{col}_mean"], sd[f"{col}_std"])
        return row_str.replace(val, _bold(val), 1)

    sd_row = _apply_bold(sd_row, TABLE_COL_SCORE, higher_is_better=True)
    sd_row = _apply_bold(sd_row, TABLE_COL_WINRATE, higher_is_better=True)
    sd_row = _apply_bold(sd_row, TABLE_COL_COST, higher_is_better=False)
    return sd_row, mp_row


def _map_block(mp: str, sd_idx: pd.DataFrame, mp_idx: pd.DataFrame, macpo_label: str, sd_label: str) -> str:
    """Build the two-row block (MACPO then SafeDreamer) for one map."""
    sd_series = sd_idx.loc[mp] if mp in sd_idx.index else None
    mp_series = mp_idx.loc[mp] if mp in mp_idx.index else None
    sd_row = _metric_row("Safe Dreamers", mp, sd_series, sd_label)
    mp_row = _metric_row("MACPO", mp, mp_series, macpo_label)
    sd_row, mp_row = _bold_winners(sd_row, mp_row, sd_series, mp_series)
    return f"{mp_row}\n{sd_row}"


def build_latex(agg: pd.DataFrame, macpo_step: int, sd_step: int, standalone: bool = True) -> str:
    """Render aggregated DataFrame as a longtable LaTeX string matching appendix format.

    If standalone=True, wraps in documentclass for PDF compilation.
    If standalone=False, outputs table body only for \\input into thesis.
    """
    macpo_label = _step_label(macpo_step)
    sd_label = _step_label(sd_step)
    sd_idx = agg[agg[CSV_COL_ALGORITHM] == "SafeDreamers"].set_index(CSV_COL_MAP)
    mp_idx = agg[agg[CSV_COL_ALGORITHM] == "MACPO"].set_index(CSV_COL_MAP)
    maps = [m for m in COLLISION_MAPS_ORDER if m in sd_idx.index or m in mp_idx.index]

    header = (
        "\\textbf{Algorithm} & \\textbf{Scenario} & \\textbf{Score} $\\uparrow$ & "
        "\\textbf{Cost} $\\downarrow$ & \\textbf{Winrate} $\\uparrow$ & "
        "\\textbf{Steps} & \\textbf{Cost Limit} \\\\"
    )
    body = "\n\\midrule\n".join(_map_block(m, sd_idx, mp_idx, macpo_label, sd_label) for m in maps)

    table = (
        "\\begin{longtable}{lcccccc}\n"
        f"\\caption{{Collision avoidance cost, cost\\_limit=0: SafeDreamer ({sd_label} steps) vs MACPO ({macpo_label} steps).}}\n"
        "\\label{tab:collision_comparison_100k_1m} \\\\\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        "\\endfirsthead\n"
        "\\multicolumn{7}{c}{{\\bfseries \\tablename\\ \\thetable{} -- continued}} \\\\\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        "\\endhead\n"
        "\\midrule \\multicolumn{7}{r}{{Continued on next page}} \\\\\n"
        "\\endfoot\n"
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
    """Compile tex_path with pdflatex and clean up aux files."""
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


def write_table(agg: pd.DataFrame, tex_path: Path, macpo_step: int, sd_step: int) -> None:
    """Write standalone LaTeX+PDF and thesis-ready table body."""
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(build_latex(agg, macpo_step, sd_step, standalone=True))
    print(f"Wrote {tex_path}")
    render_pdf(tex_path)
    thesis_path = tex_path.parent / (tex_path.stem + "_thesis.tex")
    thesis_path.write_text(build_latex(agg, macpo_step, sd_step, standalone=False))
    print(f"Wrote {thesis_path}")


# ── Fake data ─────────────────────────────────────────────────────────────────


def make_fake_seed_rows() -> pd.DataFrame:
    """Generate synthetic per-seed rows for --test mode (no WandB calls)."""
    rng = np.random.default_rng(42)
    rows = []
    for mp in COLLISION_MAPS_ORDER:
        for algo in ("SafeDreamers", "MACPO"):
            for seed in (1, 2, 3):
                reached = not (mp == "bane_vs_bane" and algo == "MACPO")
                rows.append(
                    {
                        CSV_COL_MAP: mp,
                        CSV_COL_ALGORITHM: algo,
                        CSV_COL_COST_LIMIT: 0,
                        CSV_COL_SEED: seed,
                        TABLE_COL_SCORE: rng.uniform(5, 20),
                        TABLE_COL_COST: rng.uniform(0, 2),
                        TABLE_COL_WINRATE: rng.uniform(0, 1),
                        CSV_COL_REACHED: reached,
                    }
                )
    return pd.DataFrame(rows)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Use fake data, skip WandB")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--macpo-target", type=int, default=5_000_000, help="MACPO target step (default: 5000000)")
    parser.add_argument("--sd-target", type=int, default=100_000, help="SafeDreamer target step (default: 100000)")
    args = parser.parse_args()

    macpo_target = args.macpo_target
    sd_target = args.sd_target
    sd_lbl = _step_label(sd_target)
    mp_lbl = _step_label(macpo_target)
    tex_path = COLLISION_TEX.parent / f"collision_safedreamer_{sd_lbl}_vs_macpo_{mp_lbl}.tex"

    if args.test:
        print("=== TEST MODE: using fake data ===")
        seed_df = make_fake_seed_rows()
    else:
        print("Step 1: Extracting from WandB...")
        stdout = run_extraction(args.python, macpo_target, sd_target)
        print(stdout)
        seed_df = parse_extraction_output(stdout)
        if seed_df.empty:
            raise RuntimeError("Parsed 0 rows from extraction output")

    print(f"Parsed {len(seed_df)} seed rows")

    agg = aggregate(seed_df)
    COLLISION_AGG_CSV.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(COLLISION_AGG_CSV, index=False)
    print(f"Saved aggregated CSV → {COLLISION_AGG_CSV}")

    write_table(agg, tex_path, macpo_target, sd_target)


if __name__ == "__main__":
    main()
