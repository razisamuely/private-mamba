# Experiment 5: Lagrangian Real Cost Fix

## Problem
The world model underestimates per-step cost (~0.03 predicted vs ~0.03 actual — correct per step, but `cost_returns` over 15 imagination steps stays near zero due to model confidence).
λ compares imagined `cost_returns.mean()` against `cost_limit=0.1` → sees no violation → backs off.
Real env cost (~0.5/episode) is well above the limit, but λ never reacts.

## Root Cause
Design mismatch: λ uses imagined cost (model-dependent, can be wrong) instead of real env cost.

## Fix
Change λ update from imagined to real:
```python
# Before
self.lagrangian.update(cost_returns.mean())  # imagined

# After
self.lagrangian.update(trajectory_costs.mean())  # real env cost
```
`trajectory_costs` is already computed in `actor_rollout` — no extra overhead.

## Why This Matches MACPO
MACPO updates its constraint using `aver_episode_costs` (real episode cost, mean per-agent).
After this fix, Safe Dreamer uses the same signal → `cost_limit` means the same thing in both.

## Hypothesis
- λ will correctly rise when real cost > `cost_limit`
- `Lag/mean_cost` in WandB will match the scale of `main/cost`
- Agent will learn to actually reduce collisions under the constraint

## Config (same as Exp 4 best)
- Map: `8m`
- `cost_limit`: 0.1
- `laglr`: 1e-4
- `cost_priority`: 0.15
- Seeds: 1, 2
