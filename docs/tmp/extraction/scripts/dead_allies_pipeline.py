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


def _bold_sd_winners(sd_row: str, sp_row: str, sd: pd.Series | None, sp: pd.Series | None) -> tuple[str, str]:
    """Bold SafeDreamer cells where it beats SafePO (score↑, winrate↑, cost↓)."""
    if sd is None or sp is None:
        return sd_row, sp_row

    def _apply(row_str: str, col: str, higher_is_better: bool) -> str:
        if pd.isna(sd[f"{col}_mean"]) or pd.isna(sp[f"{col}_mean"]):
            return row_str
        wins = (sd[f"{col}_mean"] > sp[f"{col}_mean"]) if higher_is_better else (sd[f"{col}_mean"] < sp[f"{col}_mean"])
        if not wins:
            return row_str
        val = _fmt(sd[f"{col}_mean"], sd[f"{col}_std"])
        return row_str.replace(val, _bold(val), 1)

    sd_row = _apply(sd_row, TABLE_COL_SCORE, True)
    sd_row = _apply(sd_row, TABLE_COL_WINRATE, True)
    sd_row = _apply(sd_row, TABLE_COL_COST, False)
    return sd_row, sp_row


def _map_cost_block(mp: str, cl: float, sd_idx: pd.DataFrame, sp_idx: pd.DataFrame) -> str:
    """Build the two-row block (SafePO then SafeDreamer) for one map+cost_limit."""
    key = (mp, cl)
    sd_s = sd_idx.loc[key] if key in sd_idx.index else None
    sp_s = sp_idx.loc[key] if key in sp_idx.index else None
    sd_row = _data_row("Safe Dreamers", mp, sd_s, SD_STEP_LABEL, cl)
    sp_row = _data_row("SafePO", mp, sp_s, SAFEPO_STEP_LABEL, cl)
    sd_row, sp_row = _bold_sd_winners(sd_row, sp_row, sd_s, sp_s)
    return f"{sp_row}\n{sd_row}"


def build_latex(agg: pd.DataFrame, standalone: bool = True) -> str:
    """Render combined SafeDreamer+SafePO DataFrame as appendix longtable LaTeX.

    If standalone=True, wraps in documentclass for PDF compilation.
    If standalone=False, outputs table body only for \\input into thesis.
    """
    sd_idx = agg[agg[CSV_COL_ALGORITHM] == "SafeDreamers"].set_index([CSV_COL_MAP, CSV_COL_COST_LIMIT])
    sp_idx = agg[agg[CSV_COL_ALGORITHM] == "SafePO"].set_index([CSV_COL_MAP, CSV_COL_COST_LIMIT])

    all_keys = sorted(
        set(sd_idx.index.tolist() + sp_idx.index.tolist()),
        key=lambda x: (DEAD_ALLIES_MAPS_ORDER.index(x[0]) if x[0] in DEAD_ALLIES_MAPS_ORDER else 99, x[1]),
    )

    header = (
        "\\textbf{Algorithm} & \\textbf{Scenario} & \\textbf{Score} $\\uparrow$ & "
        "\\textbf{Cost} $\\downarrow$ & \\textbf{Winrate} $\\uparrow$ & "
        "\\textbf{Steps} & \\textbf{Cost Limit} \\\\"
    )
    body = "\n\\midrule\n".join(_map_cost_block(mp, cl, sd_idx, sp_idx) for mp, cl in all_keys)

    table = (
        "\\begin{longtable}{lcccccc}\n"
        "\\caption{Complete performance comparison at 100k steps vs SafePO at 5M steps.}\n"
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


def write_table(agg: pd.DataFrame, tex_path: Path) -> None:
    """Write standalone LaTeX+PDF and thesis-ready table body."""
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    # Standalone PDF
    tex_path.write_text(build_latex(agg, standalone=True))
    print(f"Wrote {tex_path}")
    render_pdf(tex_path)
    # Thesis-ready (no document wrapper)
    thesis_path = tex_path.parent / (tex_path.stem + "_thesis.tex")
    thesis_path.write_text(build_latex(agg, standalone=False))
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
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

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
