# Swimmer Experiment Runs

## Pilot Runs (2026-03-25)

First SafeDreamer vs MACPO comparison on continuous env (`Safety2x1SwimmerVelocity-v0`).

| Algo | WandB Run Name | Cost Type | Cost Limit | Notes |
|------|---------------|-----------|------------|-------|
| SafeDreamer | `safedreamer_dead_allies_incremental_safety_gym_lag1e-05_25.0_Safety2x1SwimmerVelocity-v0_s23_date03-25-hr21-09-13_none_f` | dead_allies_incremental | 25.0 | laglr=1e-05, seed=23 |
| MACPO (SafePO) | `safepo_macpo_None_cost_limit=1.0_Safety2x1SwimmerVelocity-v0_1_time_20260324_131835` | N/A | 1.0 | Baseline from SafePO repo |

### Context
- Ran right after building `SwimmerWrapper.py` (discretized 9 actions → continuous torques).
- MACPO submitted March 24, SafeDreamer March 25.
- Different cost limits (25 vs 1) — not directly comparable, initial feasibility test.
