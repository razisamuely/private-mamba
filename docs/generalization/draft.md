# Experiment Draft: Generalization to Swimmer

## Scope & Requirements
Port `Safety2x1SwimmerVelocity-v0` from the SafePO library to Safe Dreamer to verify architectural generalization.

## Experiment Grid
| Env | Env Name | Algo | Cost Limit | Seeds | Workers |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `safety_gym` | `Safety2x1SwimmerVelocity-v0` | `safedreamer` | 0.0, 0.1 | 1, 2 | 4 |

## Technical Constraints
- Requires `safety-gymnasium` and `mujoco` in the environment.
- Observation space must be flattened for the Dreamer World Model.
- Action space must be mapped (Discrete 9 -> MuJoCo Continuous) or use a continuous controller.
- Horizon: 100 steps for local trial, 1000 steps for cluster.
