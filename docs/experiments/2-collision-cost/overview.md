# Overview: Collision Cost Experiment (StarCraft)

## Hypothesis
Implementing an **Ally-Ally Proximity Cost** (referred to as "Collision Cost") will improve agent survivability against area-of-effect (AoE) effects and prevent "clumping" behaviors that are suboptimal in tactical combat.

## Motivation
In the current StarCraft implementation, agents primarily care about proximity to enemies (`aggressive_positioning`) or staying close to the team (`formation_breaking`). However:
1.  **Splash Damage**: Many StarCraft units (notably Psionic Storms, Siege Tanks, or Colossi) deal splash damage. Clumping makes the entire squad vulnerable.
2.  **Pathing Efficiency**: While SC2 handle unit collisions internally, RL agents often learn to "stack" units if not penalized, leading to bottlenecks.
3.  **Safety Parity**: This brings the StarCraft environment closer to the safety standards of benchmarks like SafetyGym, where physical contact is a primary cost signal.

## Success Metrics
-   **Lower Average Proximity**: Allies should maintain a minimum tactical distance from each other.
-   **Stable Task Reward**: The agent should learn to win battles while respecting the spacing constraint.
-   **WandB Visualization**: A clear decrease in `Cost/Collision` over training time.
