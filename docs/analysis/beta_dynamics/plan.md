# Beta Dynamics Analysis (AAAI concern #6, reviewer kT97)

**Goal**: show the Lagrange multiplier β behaves sensibly during training —
rises while cost exceeds the limit, then stabilizes. From existing WandB logs, no new runs.

**WandB keys**: `Agent/Lagrangian` (β), `main/cost` (episode cost).
**Runs**: SafeDreamer lr=1e-5, d=25, 3 seeds × 3 envs (Ant2x4, Ant4x2, HC2x3) — see `runs_config.json`.

## Steps

| # | Step | Status |
|---|------|--------|
| 1 | Find β key in WandB (`Agent/Lagrangian`) | DONE 2026-07-28 |
| 2 | `pull_beta_timeseries.py` → `data/*.csv` (step, beta, cost) | DONE 2026-07-28 |
| 3 | `plot_beta_dynamics.py` → `figures/<env>_beta_dynamics.pdf` (β top, cost+limit bottom, seed mean) | DONE 2026-07-28 |
| 4 | tex section `aaai_additions/sections/beta_dynamics.tex` + copy data/figures | DONE 2026-07-28 |

## Notes
- SafeDreamer only (MACPO has no β).
- Data pulled via parquet history artifact (same helpers as violation_curves).
- β and cost are logged on different rows; merged on `steps` with NaNs kept per column.
