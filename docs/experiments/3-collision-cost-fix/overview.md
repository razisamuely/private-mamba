# Overview: Collision Cost Fix (World Model Accuracy)

## Motivation
The previous experiment (**2-collision-cost**) successfully introduced the clumping penalty logic, but it failed to achieve results because the **World Model** was unable to accurately predict the new cost signal. Specifically, the real environment cost was ~30.0, while the agent's imagination predicted ~1.2. This caused the Lagrangian multiplier to deactivate, rendering the safety constraint useless.

## Hypothesis
By **prioritizing high-cost transitions** during replay buffer sampling and **increasing the Lagrangian learning rate**, we can force the World Model to accurately learn the "clumping" distribution and ensure the safety multiplier reacts fast enough to violations.

## Success Metrics
- **Cost Prediction Accuracy**: The `Model/Predicted_average_cost` in WandB should closely match the actual `main/cost`.
- **Lagrangian Activation**: The Lagrangian multiplier ($\lambda$) should remain active and scale up until the cost limit is met.
- **Converged Spacing**: Agents should learn to maintain tactical distance on the `8m` map while maintaining task reward.
