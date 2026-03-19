# Draft: Collision Cost Fix (Technical Spec)

## Key Modifications

### 1. Cost-Prioritized Replay Sampling
We will modify the replay buffer sampling logic to ensure that a fixed percentage of transitions in every training batch have a non-zero collision cost.
- **Algorithm**: `Weighted Random Sampling` or `Priority Oversampling`.
- **Ratio**: Start with **15%** of the batch reserved for high-cost transitions.

### 2. Lagrangian Learning Rate (`laglr`)
The previous rate of `1e-05` was too slow.
- **New Value**: `1e-03` for pilot runs, potentially decaying to `1e-04`.

### 3. Integrated Cost Hint (Optional Phase 3)
If prioritized sampling is insufficient, we will add the previous step's `collision_cost` as an auxiliary observation to the `observation_encoder`.

## Parameters
| Parameter | New Value | Motivation |
| :--- | :--- | :--- |
| `laglr` (Lagrangian LR) | `1.0e-3` | Fast reaction to distribution shifts. |
| `sampling_cost_ratio` | `0.15` | Ensures model "sees" enough crashes. | **Ratio**: Start with **15%** of the batch reserved for high-cost
| `cost_limit` | `5.0` | Maintain previous limit for direct comparison. |
