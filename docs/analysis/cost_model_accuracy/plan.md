# Cost Model Accuracy Analysis (AAAI concern #5, reviewer kT97)

**Goal**: show the world model's predicted cost tracks the actual cost — the policy
is not optimized against a broken cost signal. Ties to Theorem 1's eps_c term.
From existing WandB logs, no new runs.

**WandB keys**: `Model/Predicted_average_cost`, `Model/Actual_average_cost`.
**Runs**: same 9 as beta_dynamics (SafeDreamer lr=1e-5, d=25, 3 seeds x 3 envs).

## Steps

| # | Step | Status |
|---|------|--------|
| 1 | Pull `pull_cost_accuracy.py` -> `data/*.csv` (step, predicted, actual) | DONE 2026-07-28 |
| 2 | Plot `plot_cost_accuracy.py` -> `figures/<env>_cost_accuracy.pdf` | DONE 2026-07-28 |
| 3 | Review results with user | DONE 2026-07-28 (predicted ~= actual, all envs) |
| 4 | Tex section + copy data/figures to aaai_additions | DONE 2026-07-28 |

## Notes
- Both keys logged on training rows (wandb `_step` only) — mapped to env steps by
  interpolation, same as beta_dynamics.
- Figures clipped at 1M steps (paper budget).
