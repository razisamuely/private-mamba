---
name: experiment-workflow
description: >
  Standard workflow for running SafeDreamer experiments on SLURM cluster.
  Covers: plan, implement, test locally, commit/push/pull, submit jobs,
  track results, extract metrics, generate comparison tables.
  Use when adding new environments, running sweeps, or comparing against baselines.
---

# Experiment Workflow

## 1. Plan

- Create experiment folder: `docs/experiments/{N}-{short-name}/`
- Write `overview.md`: goal, envs, config, baselines
- Write `plan.md`: decomposed steps with prerequisites, inputs, outputs, validation
- Write `runs.md`: empty job table with columns: #, Env, Algo, Config, Seed, Slurm ID, WandB Run, Status

**Prerequisite**: None
**Output**: 3 markdown files in experiment folder
**Validate**: All envs listed, all configs defined, table has correct number of rows

## 2. Implement

- Create/modify code on a dedicated branch (`feat/` or `fix/`)
- Only change algorithm code if needed; keep logistics separate
- Add new envs to `ENV_REGISTRY` in wrapper
- Add CLI args to `train.py` if new config overrides needed
- Update `submit_experiments.py` + sbatch templates if submission flow changes

**Prerequisite**: Plan approved
**Output**: Working code on branch
**Validate**: `git diff --stat` shows only expected files changed

## 3. Test Locally

- Run env probe: verify obs_dim, action_dim, n_agents for each env
- Run 3 episodes end-to-end (collect + train) on CPU with `WANDB_MODE=disabled`
- Check: no crashes, no NaN, shapes correct, reward/cost logged
- Do NOT skip this — cluster debugging is 100x slower

**Prerequisite**: Code implemented
**Output**: Console output showing 3 episodes completed
**Validate**: No errors, reward values are finite numbers

## 4. Commit / Push / Pull

- `git add` only relevant files (no wandb/, no venv/, no generated sbatch)
- Commit with descriptive message
- Push to remote
- SSH to cluster, `git pull` on correct branch
- Verify: `git log --oneline -1` matches local

**Prerequisite**: Local tests pass
**Output**: Cluster on same commit as local
**Validate**: Commit hash matches on both sides

## 5. Submit Jobs

- Use `submit_experiments.py` with correct flags
- SafeDreamer: GPU partition
- MACPO: CPU partition (via SafePO repo `submit_baseline.py`)
- SafeDreamer is GPU-only — never submit to CPU partition
- Wait 2 min, run `squeue -u razshmue` to verify jobs alive
- If jobs die immediately, check `.err` file on cluster

**Prerequisite**: Cluster on correct branch, envs verified
**Output**: Slurm IDs for all jobs
**Validate**: `squeue` shows all jobs RUNNING after 2 min

## 6. Update Docs

- Fill Slurm IDs in `runs.md`
- Note any failed/resubmitted jobs with reason
- Update `overview.md` status

**Prerequisite**: Jobs submitted
**Output**: `runs.md` with all Slurm IDs filled
**Validate**: Row count matches number of submitted jobs

## 7. Monitor

- Check `squeue` periodically
- Query WandB for early results
- Log metrics using `main/score`, `main/cost`, `main/winrate` (matches `DreamerRunner`)
- If jobs crash, check `.err` on cluster, fix, re-commit, re-push, re-pull, resubmit

**Prerequisite**: Jobs running
**Output**: Updated status in `runs.md`

## 8. Extract Metrics

- Create input CSV: `docs/tmp/extraction/inputs/{name}_experiment{N}.csv`
- Create pipeline: `docs/tmp/extraction/scripts/{name}_pipeline_experiment{N}.py`
- Reuse existing `extract_metrics.py` for WandB fetching
- SafeDreamer: extract at target steps (e.g. 100k, 500k, 1M) with 5k window avg
- MACPO: extract final values via `run.summary` (our SafePO fork uses `main/score`/`main/cost`, fallback to `average_episode_reward`/`average_episode_cost`)
- Include hardcoded reference values (paper, GitHub) marked with `~`
- Aggregate across seeds: mean +- std

**Prerequisite**: Runs finished (or reached target steps)
**Input**: CSV with wandb_link, env, algorithm, seed, cost_limit
**Output**: `docs/tmp/tables/{name}_experiment{N}/comparison_table.{csv,tex,pdf}`
**Validate**: All `?` values filled or marked `—`, cross-check 2-3 values against WandB UI

## 9. Final Update

- Update `runs.md` with WandB run IDs and final status
- Update `overview.md` with results summary
- Reference output table
- Commit all

**Prerequisite**: Extraction complete
**Output**: Experiment fully documented

## Common Pitfalls

- **Forgetting to `git pull` on cluster** after push — jobs run old code
- **Submitting SafeDreamer to CPU** — crashes (needs CUDA)
- **Wrong cost_limit** — check paper vs SafePO default (can differ 100x)
- **WandB metric names** — use `main/score`, `main/cost`, `main/winrate` (not `reward`/`cost`)
- **Ray worker path differs from local** — test with `n_workers=0` locally, but cluster uses `n_workers=4`
- **Generated sbatch files in .gitignore** — use `git add -f` if needed
- **Pre-commit hooks** — use venv310 for mypy, not venv (Python 3.7)
