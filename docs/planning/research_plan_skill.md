# Research Planning & Experiment Workflow

Adapted from the global Project Planning Process to optimize RL research and hardware-heavy experimenting.

## 1. Branching & Issue Policy

*   **Branch Mandatory**: No development or experiment submission ever happens on `main`.
*   **Issue Linking**: Every branch MUST be created for and linked to a specific GitHub Issue (e.g., `feat/issue-4-new-cost-loss`).
*   **Cleanup and Merge**: Merging to `main` only happens after the experiment is concluded, documentation is finalized, and code is consolidated.

## 2. Process Flow (Per Branch)

Every branch must contain its own planning folder (e.g., `docs/experiments/<issue-number>-<description>/`) with the following four mandatory files:

### Phase A: Draft (Discuss + Decide)
1.  **`draft.md`**: The source of truth for scope, requirements, and the specific experiment grid (Seeds, Envs, Cost Limits).
2.  **`integration_plan.md`**: Detailed mapping of which files will be modified, where hooks will be added, and how remote cluster sync will be handled.

### Phase B: Full Documentation (Outside-In)
3.  **`overview.md`**: High-level explanation of the hypothesis, the "why" behind the change, and key expected results.
4.  **`implementation_plan.md`**: A phased TDD plan. Phase 1 is always a "Skeleton" (wiring only, no logic). Phase 2+ is the actual implementation and training.

### Phase C: Implementation & Execution
10. **Skeleton Run**: Verify sbatch generation and remote file sync with zero training steps.
11. **Pilot Run**: Execute a single seed to verify WandB group names and metric tracking.
12. **Grid Launch**: Full submission via automation script.
13. **Analysis & Synthesis**: Post-processing CSVs and WandB reports into a final result summary.

## 2. Key Principles for Research

*   **Decide Before Running**: Never launch a grid until the `draft.md` is locked and logic is merged.
*   **Tables Over Prose**: Keep experiment definitions in dense tables for quick comparison.
*   **Infrastructure First**: Ensure GPU availability and memory thresholds are checked before logic implementation.
*   **Atomic Logic**: Keep algorithm changes (e.g., in `lagrange.py`) modular so they can be easily toggled.
*   **Baseline Discipline**: Always include a "vanilla" or "previous best" in every new grid for direct comparison.
*   **Traceability**: Every run must link back to a git branch to ensure reproducibility.
