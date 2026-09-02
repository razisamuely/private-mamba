# 3-safedreamer-smac-threshold — working notes

Supervisor point 3: why does SafeDreamer exceed the cost threshold?

## The question (clarified)

SafeDreamer violates the cost limit — not just on SMAC, also on MAMuJoCo
with tight limits (see `5-theorem1-estimates/notes.md` observation table).
**Why does the constraint mechanism fail to keep cost under budget?**

Two candidate causes (may coexist, may differ per env):

1. **World model not accurate enough (ε_P)**
   - Imagination says "safe" but reality isn't.
   - Check: run Theorem 1 ε_P analysis on SMAC runs (same script as MAMuJoCo).
   - If ε_P is higher on SMAC → model error is a bigger factor there.

2. **Lagrangian multiplier (β) too low / too slow**
   - β doesn't rise fast enough to penalize violations → policy keeps
     violating until β eventually catches up (or never does).
   - Check: plot `Agent/Lagrangian` over training from existing WandB runs.
   - If β is still rising at end of training → not converged, needs more
     time or faster updates (→ PID-Lagrangian, point 4).

## What the supervisor suggested to try

- **More pessimistic threshold** — aim at `d − Δ` instead of `d`
  (Theorem 1 margin). Reduces allowed imagined cost → should help if
  cause 1 dominates.
- **Multiplier too big?** — supervisor also asked if β overshoots.
  Check: does β spike → cost drops to 0 → reward collapses?
  (oscillation = classic Lagrangian instability → PID smooths it, point 4).

## Analysis plan (no new compute)

1. [ ] ε_P on SMAC — adapt Theorem 1 extraction script to SMAC runs.
2. [ ] β dynamics — pull `Agent/Lagrangian` curves per env from WandB,
       compare SMAC vs MAMuJoCo (rising? converged? oscillating?).
3. [ ] Cross-reference: envs with high ε_P AND rising β = both causes.
4. [ ] Connect findings to fixes: pessimistic threshold (if ε_P dominates),
       PID-Lagrangian (if β dynamics dominate), or both.
