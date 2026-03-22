# Experiment 4: Collision Scale and Stability

## Overview
Based on results from Experiment 3, the world model is now accurate (predicting 0.75-1.0 per step), but the `cost_limit` of 5.0 was too high to trigger a response. This experiment fine-tunes the **Scale** and **Stability** of the constraint.

## Hypothesis
Lowering the `cost_limit` to 0.1/0.5 will align the safety target with the world model's per-step predictions. Lowering `laglr` to 1e-4/1e-5 will stabilize the agent's behavior and eliminate oscillations.

## Success Metrics
- Average step-cost below 0.5.
- Multiplier $\lambda$ stabilizes above zero (no spikes/crashes).
- Continuous spacing maintained during combat.
