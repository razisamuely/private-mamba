# Experiment 6: Lagrangian Real Episode Cost

## Background
Exp 5 (`feat/lag-real-cost-fix`) changed the λ update signal from `cost_returns.mean()` (imagined per-step) to `trajectory_costs.mean()` (`cost_returns.sum(dim=0).mean()`, imagined 15-step sum). This improved λ responsiveness — λ rises, agent reduces cost, `main/cost` decreases.

## Why Exp 5 Is Not the Full Fix
`trajectory_costs` is still imagined (summed over 15 horizon steps), not a true per-episode cost. The scale still doesn't match `cost_limit`, which the user defines in real episode-cost terms (e.g. 0.1 collisions/episode). This causes λ to over- or under-shoot depending on episode length vs horizon mismatch.

The two signals are fundamentally different:
- `trajectory_costs` ~ 0.4 (imagined, 15-step sum, batch-averaged)
- `main/cost` ~ 0.2 (real, full episode, env-averaged)

## Intuition
λ is a thermostat — it should react to the real temperature (actual episode cost), not a model's prediction of it. `cost_limit` is defined in real episode-cost scale, so the signal driving λ must be on the same scale.

## Fix
`total_episode_cost` already exists in `DreamerWorker.py` and flows through `info["cost"]` in the runner. It just needs to reach the learner:

1. `DreamerRunner.py` — pass `info["cost"]` to `learner.step()`: `self.learner.step(rollout, info["cost"])`
2. `DreamerLearner.py` — accept `episode_cost` in `step()`, pass it to `train_agent()`, use it in `lagrangian.update()` instead of `trajectory_costs.mean()`

## Role of the World Model (unchanged)
The world model's cost prediction remains essential for policy shaping via `cost_adv` in the policy gradient. Only the λ update signal changes.

## Hypothesis
- λ update and `cost_limit` will be on the same scale
- λ will converge more stably without overshoot
- `main/cost` will reliably track toward `cost_limit`

## Config
- Map: `8m`
- `cost_limit`: 0.1
- `laglr`: 1e-5
- `cost_priority`: 0.15
- Seeds: 1, 2
