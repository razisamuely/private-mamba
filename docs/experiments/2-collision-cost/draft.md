# Draft: Collision Cost Experiment (StarCraft)

## Technical Specification

### 1. Logic (Existing vs. Proposed)
-   **Current SafetyGym Logic**: Binary contact indicator. Cost = 1 if the agent's physics body overlaps with a "Hazard" or "Obstacle" geom.
-   **Proposed StarCraft Logic**: Pairwise Proximity Violation.
    -   Function: `get_cost_collision(info)`
    -   Implementation: For every unique pair of alive allies $(i, j)$:
        $$Cost = \sum_{i<j} \mathbb{1}(dist(pos_i, pos_j) < threshold)$$
    -   **Binary vs Cumulative Example**:
        -   *Binary*: A cluster of 3 agents = Cost 1.
        -   *Cumulative*: A cluster of 3 agents = Cost 3 (Pairs A-B, A-C, B-C).
    -   *Decision*: Use **Cumulative** to penalize larger "blobs" more heavily.

### 2. Parameters
| Parameter | Proposed Value | Motivation |
| :--- | :--- | :--- |
| `collision_threshold` | `1.0` | Standard units in SC2. Marine radius is ~0.375, so 0.75 is touching. 1.0 gives a small buffer. |
| `cost_limit` | `5.0` | High enough to allow some tactical bunching, low enough to penalize massive stacks. |
| `weight_in_combined` | `0.2` | Balanced against `aggressive_positioning` and `dead_allies`. |

### 3. Open Questions
-   [ ] Should the cost be binary (1 if any pair collides) or cumulative (count of all colliding pairs)?
    -   *Recommendation*: Cumulative, to penalize larger "blobs" more heavily.
-   [x] Should we exclude agents that are currently "dead" or "stationary"?
    -   *Decision*: **Exclude both**. Only moving allies are penalized for clumping. This prevents penalizing agents that are holding a defensive position or waiting for orders.

## Integration Points
-   **File**: `env/starcraft/StarCraft_safe.py`
-   **Method**: New `get_cost_collision(self, info)` method.
-   **Selection**: Add `elif self.cost_type == "collision":` in `get_cost`.
