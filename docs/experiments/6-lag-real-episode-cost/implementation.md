# Experiment 6: Implementation Plan

## Changes

### 1. `agent/runners/DreamerRunner.py`
Pass real episode cost to the learner:
```python
# Before
self.learner.step(rollout)

# After
self.learner.step(rollout, info["cost"])
```

### 2. `agent/learners/DreamerLearner.py`
Accept and forward episode cost:
```python
# Before
def step(self, rollout):
    ...
    self.train_agent(samples)

# After
def step(self, rollout, episode_cost=None):
    ...
    self.train_agent(samples, episode_cost)
```

Pass to `train_agent` and use in λ update:
```python
# Before
def train_agent(self, samples):
    ...
    mean_cost = trajectory_costs.mean()
    self.lagrangian.update(mean_cost)

# After
def train_agent(self, samples, episode_cost=None):
    ...
    mean_cost = torch.tensor(episode_cost) if episode_cost is not None else trajectory_costs.mean()
    self.lagrangian.update(mean_cost)
```

## Tests to Verify

### 1. Scale alignment
- Log both `Lag/mean_cost` and `main/cost` — they should now be on the same scale (~0.2)
- Previously `Lag/mean_cost` was ~0.4, `main/cost` ~0.2

### 2. λ convergence
- λ should rise when `main/cost > cost_limit` and fall when below
- Should not oscillate or overshoot as in exp 5

### 3. Fallback safety
- If `episode_cost=None` (e.g. unit tests), falls back to `trajectory_costs.mean()` — no regression

### 4. Unit test
```python
# tests/test_lagrangian_update.py
def test_lagrangian_uses_episode_cost():
    lag = BasicLagrange(cost_limit=0.1, lagrangian_multiplier_init=0.0, lr=1e-3)
    lag.update(torch.tensor(0.5))  # real episode cost > limit
    assert lag.lambda_ > 0, "λ should rise when cost > cost_limit"

def test_lagrangian_does_not_rise_below_limit():
    lag = BasicLagrange(cost_limit=0.1, lagrangian_multiplier_init=0.0, lr=1e-3)
    lag.update(torch.tensor(0.05))  # below limit
    assert lag.lambda_ == 0, "λ should stay at 0 when cost < cost_limit"
```
