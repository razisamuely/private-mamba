# Changelog

## feat/lag-real-episode-cost → main (2026-05-30)
**Pre-merge main**: `f1b2541` — revert with `git reset --hard f1b2541`

### Core Changes
- **Lagrangian uses real episode cost**: Switched from `cost_returns.mean()` (imagined discounted) to `trajectory_costs.mean()` (real env cost). Aligns the Lagrangian signal with MACPO's approach.
- **Removed cost-prioritized sampling**: Simplified replay buffer by removing `COST_PRIORITY_RATIO` logic.
- **Wandb run name length fix**: Truncated to stay under 128 char limit.

### Results & Analysis
- Submitted SafeDreamer + MACPO comparison across maps: 8m, MMM, 3s5z_vs_3s6z, bane_vs_bane, 3s_vs_5z.
- Cost types: `dead_allies_incremental`, `collision` (cost_limit=0, 0.5).
- Extraction pipelines: `collision_pipeline.py`, `dead_allies_pipeline.py` for WandB metric extraction.
- Comparison tables (LaTeX/PDF): collision at multiple MACPO step targets (100k-5M vs SafeDreamer 100k/200k).
- Appendix full comparison table (dead_allies_incremental).
- Step axis fix: corrected `_step` vs `steps` measurement bug in extraction.

### Repo Cleanup
- Updated LICENSE to anonymous authors (paper submission).
- Trimmed `requirements.txt` (removed unused deps).
- Added `*.sbatch`, `*.log` to `.gitignore`.
- Added compute profiling script (`docs/profiling/profile_compute.py`).
- Deleted `paper_text.txt`.

### Not Included
- MAX_STEPS cost scaling (superseded by real episode cost approach)

---

## Swimmer cherry-pick from feat/swimmer-action-fix (2026-05-30)
**Pre-cherry-pick main**: `1a9cbe5` — revert with `git reset --hard 1a9cbe5`

### Added
- `env/safety_gym/SwimmerWrapper.py` — Discretized continuous Swimmer env (9 discrete actions mapped to continuous torques).
- `agent/workers/DreamerWorker.py` — reward signal for `SAFETY_GYM` env type.
- `docs/generalization/` — integration plan and status docs for Swimmer port.

### Skipped (from feat/swimmer-action-fix)
- `DreamerLearner.py` MAX_STEPS scaling — redundant with real episode cost.
- `DreamerLearnerConfig.py` MAX_STEPS config — same reason.
- `train.py` import changes — would break SMAC.

---

## main (2026-03-22)

### Baseline
- Discrete action support (OneHotCategorical) for SMAC environments.
- Lagrangian safety with imagined cost returns.
- Cost types: damage, dead_allies, dead_allies_incremental, collision.
- Envs: SMAC (StarCraft), Flatland, VMAS, Safety-Gymnasium (partial).
