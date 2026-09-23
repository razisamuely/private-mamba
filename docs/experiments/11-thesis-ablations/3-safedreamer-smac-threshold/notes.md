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

1. [x] ε_P on SMAC — done in task 5. Model is accurate (bound holds 58-939× slack).
2. [x] β dynamics — pulled `Agent/Lagrangian` for 5 maps (MMM, 8m, 1c3s5z,
       2m_vs_1z, 3m), 3 seeds each. See `data/`, `figures/`, `beta_diagnosis.pdf`.
3. [x] Cross-reference: ε_P is fine everywhere; β is the sole bottleneck.
4. [x] Conclusion: PID-Lagrangian (task 4) is the right fix.

## Results (2026-09-15)

β rises **linearly and never converges** on all 5 maps at 100k steps.
No plateau, no oscillation — gradient-ascent lag-lr=1e-5 is too slow.

| Map | β at 100k | Cost at 100k | Initial cost | Verdict |
|-----|-----------|-------------|-------------|---------|
| MMM | 0.50 | ~7-8 | ~10 | worst — cost barely moves |
| 1c3s5z | 0.30 | ~4-5 | ~9 | bad — dropping but far from 0 |
| 8m | 0.50 | ~3 | ~8 | medium — dropping, β still rising |
| 3m | 0.13 | ~0.5 | ~3 | mild — almost there |
| 2m_vs_1z | 0.025 | ~0.2 | ~2 | best — low cost, low β needed |

**Conclusion**: cost-above-threshold is a Lagrangian convergence problem,
not model error. On hard maps, β=0.3-0.5 at 100k isn't enough to outweigh
the reward signal. PID-Lagrangian (task 4) should fix this with faster
multiplier response.

Deliverable: `beta_diagnosis.tex` / `beta_diagnosis.pdf` with figures.

## MAMuJoCo β dynamics (done earlier, 2026-07-28)

β dynamics were already analyzed for MAMuJoCo (AAAI reviewer concern #6):
Ant2x4, Ant4x2, HC2x3 (lr=1e-5, d=25, 3 seeds each). Lives OUTSIDE this
folder: `docs/analysis/beta_dynamics/` (plan.md, scripts, `figures/*.pdf`).
There β rises while cost > limit then stabilizes — behaves sensibly with
a loose limit (d=25). So task 3 β diagnosis covers **both envs**:
MAMuJoCo (`docs/analysis/beta_dynamics/`) + SMAC (here).
