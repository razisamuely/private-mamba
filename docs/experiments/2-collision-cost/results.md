# Results Summary: Collision Cost Experiment (StarCraft)

## Summary of Work
- Implemented `get_cost_collision` in `StarCraft_safe.py` to penalize ally-ally clumping for moving agents.
- Integrated the new cost type into the `SafeDreamer` training pipeline.
- Verified the pairwise distance logic with unit tests (`tests/test_collision_logic.py`).
- Executed pilot runs on `8m` and `bane_vs_bane` maps with cost limits of 5.0 and 10.0.

## Key Results
- **Cost Violation**: The agents consistently exceeded the cost limits. In `8m`, the average collision cost hovered around **30.0**, despite limits of 5.0 and 10.0.
- **World Model Failure**: The world model significantly **under-predicted** the collision cost, estimating it at ~1.2 while the actual environment cost was ~30.0.
- **Lagrangian Multiplier**: Because the predicted cost was below the limit, the Lagrangian multiplier ($\lambda$) repeatedly collapsed to zero, effectively disabling the safety constraint.
- **Lagrangian Learning Rate**: The learning rate (`1e-05`) was found to be too slow to react to the massive distribution shift between reality and imagination.

## Conclusion
The experiment successfully implemented the cost logic, but the Safe RL mechanism failed due to the world model's inability to accurately predict the new collision signal. Future work must focus on fixing the cost-prediction branch of the world model.
