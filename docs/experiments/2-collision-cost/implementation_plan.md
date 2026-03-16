# Implementation Plan: Collision Cost Experiment (StarCraft)

This plan follows the "Skeleton-First" approach.

## Phase 1: Skeleton & Setup
- [ ] Add `get_cost_collision` stub to `StarCraft_safe.py` (returning 0.0).
- [ ] Add `collision` to `get_cost` selection logic.
- [ ] Launch a "Dry Run" using `submit_experiments.py` with 1 seed and 100 steps to verify sbatch generation and remote syncing.

## Phase 2: Logic Implementation
- [ ] Implement distance calculation in `get_cost_collision`.
- [ ] Add unit test in `if __name__ == "__main__":` block of `StarCraft_safe.py` to verify pairwise distance logic with dummy unit positions.

## Phase 3: Pilot Run
- [ ] Submit a pilot experiment (1 seed, `map=3m`, `cost_limit=5.0`).
- [ ] Verify `Cost/Collision` is being logged correctly in WandB.

## Phase 4: Full Grid Execution
- [ ] Submit full grid: 3 seeds, 2 maps (3m, 8m), varied cost limits (2.0, 5.0, 10.0).
- [ ] Analyze results and update `walkthrough.md`.
