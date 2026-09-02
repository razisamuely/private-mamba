#!/usr/bin/env python3
"""Generate Theorem 1 empirical check table (LaTeX + PDF).

Reads theorem1_mamujoco_agg.csv → produces table showing eps_c, eps_P (TV),
Delta bound, observed gap, and whether the bound holds per env config.

Usage: python generate_theorem1_table.py
"""

import subprocess
from pathlib import Path
from typing import Optional

import pandas as pd

# --- Paths -------------------------------------------------------------------
OUT_DIR = Path(__file__).parent
AGG_CSV = OUT_DIR / "theorem1_mamujoco_agg.csv"
TEX_FILE = OUT_DIR / "theorem1_mamujoco_table.tex"
PDF_FILE = OUT_DIR / "theorem1_mamujoco_table.pdf"

# --- Display names -----------------------------------------------------------
ENV_SHORT_NAMES = {
    "Safety2x3HalfCheetahVelocity-v0": "HC 2x3",
    "Safety2x4AntVelocity-v0": "Ant 2x4",
    "Safety4x2AntVelocity-v0": "Ant 4x2",
}


def _fmt(val: float, decimals: int = 4) -> str:
    """Format a float to fixed decimals."""
    return f"{val:.{decimals}f}"


def _fmt_pm(mean: float, std: float, decimals: int = 4) -> str:
    """Format mean +/- std."""
    return f"{mean:.{decimals}f} $\\pm$ {std:.{decimals}f}"


def _slack(gap: float, delta: float) -> str:
    """Slack ratio as readable string."""
    if gap == 0:
        return "$\\infty$"
    ratio = delta / gap
    return f"$\\times${ratio:.0f}"


def generate_tex(df: pd.DataFrame) -> str:
    """Build a standalone LaTeX document with the Theorem 1 table."""
    rows = []
    for _, r in df.iterrows():
        env = ENV_SHORT_NAMES.get(r["env"], r["env"])
        d = _fmt(r["cost_limit"], 1)
        laglr = r["laglr"]
        eps_c = _fmt_pm(r["eps_c_mean"], r["eps_c_std"])
        tv = _fmt_pm(r["tv_proxy_mean"], r["tv_proxy_std"])
        delta = _fmt_pm(r["delta_bound_mean"], r["delta_bound_std"], 1)
        gap = _fmt_pm(r["observed_gap_mean"], r["observed_gap_std"])
        holds = "\\cmark" if r["observed_gap_mean"] <= r["delta_bound_mean"] else "\\xmark"
        slack = _slack(r["observed_gap_mean"], r["delta_bound_mean"])
        seeds = int(r["n_seeds"])
        rows.append(
            f"        {env} & {d} & {laglr} & {eps_c} & {tv} " f"& {delta} & {gap} & {holds} & {slack} & {seeds} \\\\"
        )

    body = "\n".join(rows)

    return (
        r"""\documentclass[10pt]{article}
\usepackage[margin=0.5in,landscape]{geometry}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{amssymb}
\newcommand{\cmark}{\checkmark}
\newcommand{\xmark}{$\times$}
\pagestyle{empty}
\begin{document}
\begin{table}[h]
\centering
\caption{Theorem 1 empirical check --- MAMuJoCo (SafeDreamer, full comm).
    Does the bound $\Delta$ cover the actual gap between real and imagined cost?}
\small
\begin{tabular}{llcccccccr}
\toprule
Env & $d$ & lag-lr & $\epsilon_c$ & TV (from KL) & $\Delta$ (bound) & Observed gap & Holds? & Slack & Seeds \\
\midrule
"""
        + body
        + r"""
\bottomrule
\end{tabular}
\end{table}

\vspace{1em}
\noindent\textbf{Formula:}\\
$\Delta = 15\,\epsilon_c + 105 \cdot c_{\max} \cdot \text{TV}$,\quad $c_{\max}=1$ (binary velocity cost, exact from env code).

\vspace{0.8em}
\noindent\textbf{What each column measures:}
\begin{itemize}\setlength\itemsep{0.3em}
  \item $\boldsymbol{\epsilon_c}$ --- \emph{Cost-head error.} How wrong the model prices each step's cost.
        Source: average of \texttt{Model/cost\_loss} over the last 10\% of training rows.
  \item \textbf{TV} --- \emph{Transition error.} How wrong the model's next-state forecast is.
        Source: average of \texttt{Model/div} (KL divergence, prior vs.\ posterior) over the last 10\% of training rows.
        Converted to TV via Pinsker's inequality: $\text{TV} = \sqrt{\text{KL}/2}$.
  \item $\boldsymbol{\Delta}$ \textbf{(bound)} --- The maximum gap Theorem~1 \emph{allows} between real and imagined cost.
  \item \textbf{Observed gap} --- The gap we \emph{actually measured}: $|J_{\text{real}} - \hat{J}_{\text{imag}}|$.\\
        Both sides scaled to a discounted 15-step window ($\times 13.9 = \sum_{t=0}^{14}\gamma^t$, $\gamma=0.99$):\\
        --- Imagined: \texttt{Value/Cost} (per dreamed step) $\times\;13.9$.\\
        --- Real: \texttt{main/cost} (episode total) $\div$ episode length $\times\;13.9$.\\
        Episode length = measured from consecutive \texttt{steps} diffs (not hardcoded).
  \item \textbf{Slack} --- How much room to spare: $\Delta \div \text{gap}$.
\end{itemize}

\vspace{0.8em}
\noindent\textbf{Assumptions \& caveats:}
\begin{itemize}\setlength\itemsep{0.3em}
  \item \textbf{Average, not worst-case.}
        Theorem~1 requires uniform bounds on every state-action pair.
        All values here are training averages.
        This table is a consistency check (``does the data contradict the theorem?''),
        not a worst-case proof.
  \item \textbf{Tail-10\% window.}
        We average each metric over the last 10\% of logged rows,
        assuming the model has converged by that point.
  \item \textbf{Even cost spread.}
        Real per-step cost = episode total $\div$ episode length.
        This assumes cost is spread evenly, but MAMuJoCo cost is binary (0 or 1 per step)
        and likely bursty --- risky windows may have much higher cost than the average suggests.
  \item \textbf{KL $\to$ TV conversion.}
        Pinsker gives a conservative upper bound on TV from KL,
        but both are computed on latent codes, not raw states.
        The theorem is stated over the true state space.
\end{itemize}

\end{document}
"""
    )


def compile_pdf(tex_path: Path) -> Optional[Path]:
    """Compile .tex to .pdf via pdflatex."""
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tex_path.parent), str(tex_path)],
        capture_output=True,
        text=True,
    )
    pdf = tex_path.with_suffix(".pdf")
    if pdf.exists():
        return pdf
    print("pdflatex failed:")
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    return None


def main() -> None:
    df = pd.read_csv(AGG_CSV)
    tex_content = generate_tex(df)
    TEX_FILE.write_text(tex_content)
    print(f"wrote {TEX_FILE}")

    pdf = compile_pdf(TEX_FILE)
    if pdf:
        # clean aux files
        for ext in [".aux", ".log"]:
            aux = TEX_FILE.with_suffix(ext)
            if aux.exists():
                aux.unlink()
        print(f"wrote {pdf}")
    else:
        print("PDF compilation failed — .tex still available")


if __name__ == "__main__":
    main()
