#!/usr/bin/env python3
"""
Pipeline: extract SafeDreamer dead_allies metrics → merge SafePO → render appendix PDF.

Calls extract_metrics.py for SafeDreamer WandB data, merges with pre-aggregated
SafePO from all_agg_corrected.csv, and renders a longtable appendix PDF.
Runs with --test flag use synthetic data (no WandB calls).

Usage:
  python dead_allies_pipeline.py [--test] [--python /path/to/python]
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from extraction_config import (
    AGG_METRICS,
    CSV_COL_ALGORITHM,
    CSV_COL_COST_LIMIT,
    CSV_COL_MAP,
    CSV_COL_REACHED,
    CSV_COL_SEED,
    DEAD_ALLIES_MAPS_ORDER,
    SAFEPO_STEP_LABEL,
    SD_STEP_LABEL,
    TABLE_COL_COST,
    TABLE_COL_SCORE,
    TABLE_COL_WINRATE,
    TABLE_MISSING,
)
from paths_config import (
    DEAD_ALLIES_AGG_CSV,
    DEAD_ALLIES_TEX_DIR,
    SAFE_DREAMERS_INPUT_CSV,
    SAFEPO_AGG_CSV,
)

# ── Extraction ────────────────────────────────────────────────────────────────


def run_extraction(python_bin: str) -> str:
    """Run extract_metrics.py on the SafeDreamer dead_allies CSV and return stdout."""
    script = Path(__file__).parent / "extract_metrics.py"
    result = subprocess.run(
        [python_bin, str(script), "--output", str(SAFE_DREAMERS_INPUT_CSV)],
        capture_output=True,
        text=True,
    )
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


def aggregate_sd(df: pd.DataFrame) -> pd.DataFrame:
    """Drop seeds that didn't reach target, compute mean/std per map+cost_limit."""
    if CSV_COL_REACHED in df.columns:
        skipped = df[~df[CSV_COL_REACHED]][[CSV_COL_MAP, CSV_COL_COST_LIMIT, CSV_COL_SEED]]
        if not skipped.empty:
            print(f"Skipping {len(skipped)} SafeDreamer seeds that didn't reach target:")
            print(skipped.to_string(index=False))
        df = df[df[CSV_COL_REACHED]]
    grp = df.groupby([CSV_COL_MAP, CSV_COL_ALGORITHM, CSV_COL_COST_LIMIT])
    agg = grp[AGG_METRICS].agg(["mean", "std"]).round(3)
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    return agg.reset_index()


def load_safepo(safepo_path: Path) -> pd.DataFrame:
    """Load pre-aggregated SafePO data from all_agg_corrected.csv."""
    df = pd.read_csv(safepo_path)
    df = df[df[CSV_COL_ALGORITHM] == "SafePO"].copy()
    df.columns = [c.replace("score_mean", "score_mean").replace("score_std", "score_std") for c in df.columns]
    return df


# ── Rendering ─────────────────────────────────────────────────────────────────


def _fmt(mean: float, std: float) -> str:
    """Format mean±std for LaTeX, or TABLE_MISSING if NaN."""
    if pd.isna(mean):
        return TABLE_MISSING
    return f"{mean:.2f} $\\pm$ {std:.2f}"


def _bold(val: str) -> str:
    """Wrap a LaTeX value string in \\textbf{}."""
    return f"\\textbf{{{val}}}"


def _data_row(algo: str, mp: str, row: pd.Series | None, steps_label: str, cost_limit: float) -> str:
    """Build one data row: Algorithm & Scenario & Score & Cost & Winrate & Steps & CostLimit."""
    m_tex = mp.replace("_", "\\_")
    cl_int = int(cost_limit)
    if row is None:
        return f"{algo} & {m_tex} & {TABLE_MISSING} & {TABLE_MISSING} & {TABLE_MISSING} & {steps_label} & {cl_int} \\\\"
    score = _fmt(row[f"{TABLE_COL_SCORE}_mean"], row[f"{TABLE_COL_SCORE}_std"])
    cost = _fmt(row[f"{TABLE_COL_COST}_mean"], row[f"{TABLE_COL_COST}_std"])
    wr = _fmt(row[f"{TABLE_COL_WINRATE}_mean"], row[f"{TABLE_COL_WINRATE}_std"])
    return f"{algo} & {m_tex} & {score} & {cost} & {wr} & {steps_label} & {cl_int} \\\\"


def _bold_top2(entries, col, higher_is_better):
    """Given list of (row_str, series_or_None), bold the top 2 values for col in-place."""
    vals = []
    for i, (row_str, s) in enumerate(entries):
        if s is not None and not pd.isna(s.get(f"{col}_mean", float("nan"))):
            vals.append((i, s[f"{col}_mean"], s[f"{col}_std"]))
    if len(vals) < 2:
        return
    vals.sort(key=lambda x: x[1], reverse=higher_is_better)
    for idx, mean, std in vals[:2]:
        val = _fmt(mean, std)
        row_str, s = entries[idx]
        entries[idx] = (row_str.replace(val, _bold(val), 1), s)


def _color_green(val: str) -> str:
    return f"\\textcolor{{green!60!black}}{{{val}}}"


def _color_red(val: str) -> str:
    return f"\\textcolor{{red!70!black}}{{{val}}}"


def _color_vs_sd(entries, col, higher_is_better):
    """Color entries green if better than SafeDreamers, red if worse."""
    # Find SafeDreamers value
    sd_val = None
    sd_idx = None
    for i, (row_str, s, algo) in enumerate(entries):
        if algo == "SafeDreamers" and s is not None:
            sd_val = s.get(f"{col}_mean", float("nan"))
            sd_idx = i
            break
    if sd_val is None or pd.isna(sd_val):
        return

    for i, (row_str, s, algo) in enumerate(entries):
        if i == sd_idx or s is None:
            continue
        val_mean = s.get(f"{col}_mean", float("nan"))
        if pd.isna(val_mean):
            continue
        val_str = _fmt(val_mean, s[f"{col}_std"])
        if val_str == TABLE_MISSING:
            continue
        if higher_is_better:
            is_better = val_mean > sd_val
        else:
            is_better = val_mean < sd_val
        colored = _color_red(val_str) if is_better else _color_green(val_str)
        entries[i] = (row_str.replace(val_str, colored, 1), s, algo)


def _algo_display(algo_name: str) -> tuple[str, str]:
    """Return (display_name, steps_label) from algorithm column value."""
    if algo_name == "SafeDreamers":
        return "Safe Dreamers", SD_STEP_LABEL
    if algo_name == "SafePO":
        return "SafePO", SAFEPO_STEP_LABEL
    # Handle names like "SafePO-100k", "MAPPO-Lag-500k"
    for sep in ("-",):
        parts = algo_name.rsplit(sep, 1)
        if len(parts) == 2 and parts[1].replace(".", "").replace("k", "").replace("M", "").isdigit():
            return parts[0], parts[1]
    return algo_name, ""


def _map_cost_block(
    mp: str, cl: float, algo_indices: dict[str, pd.DataFrame], algo_order: list[str], use_color: bool = False
) -> str:
    """Build the block for one map+cost_limit across all algorithms."""
    key = (mp, cl)
    entries = []
    for algo_name in algo_order:
        idx = algo_indices[algo_name]
        s = idx.loc[key] if key in idx.index else None
        display, steps_label = _algo_display(algo_name)
        entries.append((_data_row(display, mp, s, steps_label, cl), s, algo_name))

    if use_color:
        _color_vs_sd(entries, TABLE_COL_SCORE, higher_is_better=True)
        _color_vs_sd(entries, TABLE_COL_COST, higher_is_better=False)
        _color_vs_sd(entries, TABLE_COL_WINRATE, higher_is_better=True)
    else:
        # Strip algo from entries for _bold_top2 compatibility
        entries_2 = [(r, s) for r, s, _ in entries]
        _bold_top2(entries_2, TABLE_COL_SCORE, higher_is_better=True)
        _bold_top2(entries_2, TABLE_COL_COST, higher_is_better=False)
        _bold_top2(entries_2, TABLE_COL_WINRATE, higher_is_better=True)
        entries = [(r, s, a) for (r, s), (_, _, a) in zip(entries_2, entries)]

    return "\n".join(row_str for row_str, _, _ in entries)


def _algo_sort_key(name: str) -> tuple:
    """Sort algorithms: SafePO variants first, then MAPPO-Lag variants, SafeDreamers last."""
    if name.startswith("SafePO"):
        group = 0
    elif name.startswith("MAPPO"):
        group = 1
    elif name == "SafeDreamers":
        group = 9
    else:
        group = 5
    # Extract step number for sub-sorting
    step = 0
    for suffix in ("100k", "200k", "500k", "1M", "2M", "5M", "10M"):
        if name.endswith(suffix):
            step = int(suffix.replace("k", "000").replace("M", "000000"))
            break
    return (group, step, name)


def build_latex(agg: pd.DataFrame, standalone: bool = True, use_color: bool = False) -> str:
    """Render combined DataFrame as appendix longtable LaTeX.

    Auto-detects all algorithm names from the CSV.
    If use_color=True, colors cells green/red vs SafeDreamers baseline.
    If standalone=True, wraps in documentclass for PDF compilation.
    If standalone=False, outputs table body only for \\input into thesis.
    """
    algo_names = sorted(agg[CSV_COL_ALGORITHM].unique(), key=_algo_sort_key)
    algo_indices = {
        name: agg[agg[CSV_COL_ALGORITHM] == name].set_index([CSV_COL_MAP, CSV_COL_COST_LIMIT]) for name in algo_names
    }

    all_keys_set = set()
    for idx in algo_indices.values():
        all_keys_set.update(idx.index.tolist())
    all_keys = sorted(
        all_keys_set,
        key=lambda x: (DEAD_ALLIES_MAPS_ORDER.index(x[0]) if x[0] in DEAD_ALLIES_MAPS_ORDER else 99, x[1]),
    )

    header = (
        "\\textbf{Algorithm} & \\textbf{Scenario} & \\textbf{Score} $\\uparrow$ & "
        "\\textbf{Cost} $\\downarrow$ & \\textbf{Winrate} $\\uparrow$ & "
        "\\textbf{Steps} & \\textbf{Cost Limit} \\\\"
    )
    body = "\n\\midrule\n".join(
        _map_cost_block(mp, cl, algo_indices, algo_names, use_color=use_color) for mp, cl in all_keys
    )

    table = (
        "\\begin{longtable}{lcccccc}\n"
        "\\caption{Complete performance comparison across algorithms and step budgets.}\n"
        "\\label{tab:complete_performance_comparison_100k} \\\\\n"
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
            "\\usepackage{booktabs,geometry,longtable,xcolor}\n"
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


def write_table(agg: pd.DataFrame, tex_path: Path, use_color: bool = False) -> None:
    """Write standalone LaTeX+PDF and thesis-ready table body."""
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    # Standalone PDF
    tex_path.write_text(build_latex(agg, standalone=True, use_color=use_color))
    print(f"Wrote {tex_path}")
    render_pdf(tex_path)
    # Thesis-ready (no document wrapper)
    thesis_path = tex_path.parent / (tex_path.stem + "_thesis.tex")
    thesis_path.write_text(build_latex(agg, standalone=False, use_color=use_color))
    print(f"Wrote {thesis_path}")


# ── Fake data ─────────────────────────────────────────────────────────────────


def make_fake_seed_rows() -> pd.DataFrame:
    """Generate synthetic SafeDreamer per-seed rows for --test mode."""
    rng = np.random.default_rng(42)
    cost_limits = {
        "1c3s5z": [0, 4],
        "2m_vs_1z": [0, 1],
        "2s3z": [0, 4],
        "2s_vs_1sc": [0, 1],
        "3m": [0, 1],
        "3s5z_vs_3s6z": [0, 4],
        "3s_vs_3z": [0, 1],
        "3s_vs_4z": [0, 1],
        "3s_vs_5z": [0, 1],
        "8m": [0, 4],
        "MMM": [0, 4],
        "bane_vs_bane": [0, 4],
    }
    rows = []
    for mp, cls in cost_limits.items():
        for cl in cls:
            for seed in (1, 2, 3):
                rows.append(
                    {
                        CSV_COL_MAP: mp,
                        CSV_COL_ALGORITHM: "SafeDreamers",
                        CSV_COL_COST_LIMIT: cl,
                        CSV_COL_SEED: seed,
                        TABLE_COL_SCORE: rng.uniform(5, 20),
                        TABLE_COL_COST: rng.uniform(0, 5),
                        TABLE_COL_WINRATE: rng.uniform(0, 1),
                        CSV_COL_REACHED: not (mp == "bane_vs_bane" and cl == 4),
                    }
                )
    return pd.DataFrame(rows)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Use fake data, skip WandB")
    parser.add_argument(
        "--render-only", action="store_true", help="Skip extraction; render table from existing aggregated CSV"
    )
    parser.add_argument("--csv", type=Path, default=None, help="Custom input CSV (implies --render-only)")
    parser.add_argument("--output", type=Path, default=None, help="Output tex/pdf path (default: alongside CSV)")
    parser.add_argument("--color", action="store_true", help="Color cells green/red vs SafeDreamers")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    if args.csv:
        agg = pd.read_csv(args.csv)
        print(f"Custom CSV: loaded {len(agg)} rows from {args.csv}")
        print(f"Algorithms: {sorted(agg[CSV_COL_ALGORITHM].unique())}")
        out = args.output or args.csv.with_suffix(".tex")
        write_table(agg, out, use_color=args.color)
        return

    if args.render_only:
        agg = pd.read_csv(DEAD_ALLIES_AGG_CSV)
        print(f"Render-only: loaded {len(agg)} rows from {DEAD_ALLIES_AGG_CSV}")
        out = args.output or (DEAD_ALLIES_TEX_DIR / "appendix_table_corrected.tex")
        write_table(agg, out, use_color=args.color)
        return

    if args.test:
        print("=== TEST MODE: using fake data ===")
        sd_seed_df = make_fake_seed_rows()
    else:
        print("Step 1: Extracting SafeDreamer from WandB...")
        stdout = run_extraction(args.python)
        print(stdout)
        sd_seed_df = parse_extraction_output(stdout)
        if sd_seed_df.empty:
            raise RuntimeError("Parsed 0 rows from extraction output")

    print(f"Parsed {len(sd_seed_df)} SafeDreamer seed rows")

    sd_agg = aggregate_sd(sd_seed_df)
    sp_agg = load_safepo(SAFEPO_AGG_CSV)
    agg = pd.concat([sd_agg, sp_agg], ignore_index=True)

    DEAD_ALLIES_AGG_CSV.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(DEAD_ALLIES_AGG_CSV, index=False)
    print(f"Saved aggregated CSV → {DEAD_ALLIES_AGG_CSV}")

    tex_path = DEAD_ALLIES_TEX_DIR / "appendix_table_corrected.tex"
    write_table(agg, tex_path)


if __name__ == "__main__":
    main()
