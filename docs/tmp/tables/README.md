# tables

## bug_fix_step_axis/
Step-axis bug impact: old results used `_step` (internal counter) instead of real env steps.

| File | Description |
|------|-------------|
| `bug_impact_100k.{tex,pdf}` | Old (_step=100k) vs corrected 100k env steps |
| `bug_impact_150k.{tex,pdf}` | Old vs corrected 150k |
| `bug_impact_200k.{tex,pdf}` | Old vs corrected 200k |

## lag_fix_comparison/
SafeDreamer performance: `feat/lag-real-cost-fix` vs `feat/lag-real-episode-cost`, cost_limit=0, 100k steps, dead_allies_incremental.

| File | Description |
|------|-------------|
| `lag_cost_fix_vs_lag_episode_cost.{tex,pdf}` | Per-map diff (green=improvement, red=degradation) |

**Key findings**: cost reduced on most maps; WR degraded on hard maps (3s_vs_4z −72%, 3s_vs_5z −39%, bane_vs_bane −22%).

## collision_comparison/
SafeDreamers vs MACPO on collision cost, cost_limit=0, 100k steps.

| File | Description |
|------|-------------|
| `collision_safedreamer_vs_macpo.{tex,pdf}` | Side-by-side comparison across maps |
