# Experiment 5: Lagrangian Cost Scale Fix

## Problem
`cost_limit` is defined in real episode-cost scale (e.g. 0.1 collisions/episode), but λ was updated with `cost_returns.mean()` — imagined per-step returns over 15 steps, a completely different scale. This is a **scaling mismatch**, not a model accuracy issue.

## Fix
Change λ update from `cost_returns.mean()` (imagined, per-step scale) to `trajectory_costs.mean()` (`cost_returns.sum(dim=0).mean()`, closer to episode scale):
```python
# Before
self.lagrangian.update(cost_returns.mean())

# After
mean_cost = trajectory_costs.mean()
self.lagrangian.update(mean_cost)
```

## Limitation
`trajectory_costs` is still imagined (summed over 15 horizon steps), not a true per-episode cost. It brings the scale closer to `main/cost` but doesn't fully match it. A proper fix would pass real episode cost from the worker directly to `lagrangian.update()`.

## Comparison to MACPO
MACPO updates λ using `aver_episode_costs` (real episode cost, mean per-agent). This fix moves Safe Dreamer closer to that signal by using a summed imagined cost (`trajectory_costs`) instead of per-step `cost_returns.mean()`. Full alignment would require using real episode cost directly.

## Role of the World Model
The world model's cost prediction is still essential — it computes `cost_returns` → `cost_adv` → shapes the policy gradient (`lagrangian_adv = adv - λ * cost_adv`). This is separate from the λ update signal.

## Hypothesis
- λ will rise when `trajectory_costs > cost_limit`
- `main/cost` will decrease as the agent learns to avoid costs
- λ and cost will converge rather than oscillate

## Config (same as Exp 4 best)
- Map: `8m`
- `cost_limit`: 0.1
- `laglr`: 1e-5
- `cost_priority`: 0.15
- Seeds: 1, 2
