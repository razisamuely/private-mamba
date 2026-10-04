# HANDOFF — Thesis Ablations (Experiment 11)

**Written**: 2026-10-04. For a collaborator (and their AI) starting with zero context.
All paths are relative to the repo root (`private-mamba`) unless stated otherwise.

## 1. What this project is

SafeDreamer: model-based safe multi-agent RL — a DreamerV2-style world model with a
Lagrangian constraint applied in imagination. Benchmarks: SMAC (StarCraft,
`dead_allies_incremental` cost) and MAMuJoCo (velocity cost). The project is becoming
a CS master thesis. The thesis itself lives in a **separate git repo**:
`~/workspace/overleaf/thesis/` (AAAI paper format, chapters/01-06).

Experiment 11 = 5 supervisor-assigned tasks, tracked in
`docs/experiments/11-thesis-ablations/` (this folder): `overview.md`, `plan.md`,
`runs.md`, per-task subfolders `1-...` to `5-...` each with `notes.md`, and a daily
log in `log/YYYY-MM-DD.md` (short bullets; keep updating — user convention).

## 2. The story (read this first)

SafeDreamer violates the cost limit on hard SMAC maps. Why?

1. **Task 5 (done)** — Theorem 1 empirical check: the model-error bound
   Δ = 15·ε_c + 105·c_max·TV holds everywhere with ×58–×939 slack.
   → **Model error does NOT explain the violations.**
2. **Task 3 (done)** — β (Lagrangian multiplier) dynamics: with the basic
   integral-only update (λ += lr·(cost−limit), lag-lr=1e-5), β rises linearly and
   never converges within the 100k budget.
   → **The bottleneck is Lagrangian convergence speed.**
3. **Task 4 (IN PROGRESS — this is where work stopped)** — the fix: PID-Lagrangian
   (Stooke et al. 2020, arXiv:2007.03964). Code done, cluster runs partially done.

Tasks 1–2 are supporting baselines/audits for the comparison tables.

## 3. Per-task matrix

| # | Task | Status | Branch | Folder |
|---|------|--------|--------|--------|
| 1 | MAPPO-Lag baseline, all envs | ~done (minor leftovers) | feat/thesis-experiments | `1-mappo-lag-all-envs/` |
| 2 | Comm audit (train/inference) | done | feat/thesis-experiments | `2-comm-audit/` |
| 3 | β dynamics diagnosis | done | feat/thesis-experiments | `3-safedreamer-smac-threshold/` |
| 4 | PID-Lagrangian | **in progress** | `feat/pid-lagrangian` | `4-pid-lagrangian/` |
| 5 | Theorem 1 estimates | done | feat/thesis-experiments | `5-theorem1-estimates/` |

### Task 1 — MAPPO-Lag all envs
- **What**: MAPPO-Lagrangian baseline on all 12 SMAC maps (SafePO repo, 5M steps;
  cluster repo `~/workspace/Safe-Policy-Optimization-Modified`).
- **Script**: `1-mappo-lag-all-envs/extract_mappolag_smac.py` (WandB → CSVs in `csv/`,
  5 checkpoints: 100k/500k/1M/2M/5M). bane_vs_bane s1 timed out at 4.52M/5M —
  user decided "use as is".
- **Result tables**: appendix table from `docs/tmp/aggregated/smac/dead_allies_agg.csv`
  (120 rows) and the **main table** `docs/tmp/tables/multi_step_comparison/multi_step_comparison.pdf`
  from `docs/tmp/aggregated/smac/dead_allies_all_steps.csv` (264 rows). Regenerate:
  `python3 docs/tmp/extraction/scripts/dead_allies_pipeline.py --csv docs/tmp/aggregated/smac/dead_allies_all_steps.csv --output docs/tmp/tables/multi_step_comparison/multi_step_comparison.tex --color`
  (colors: red = worse than SafeDreamer, green = better).
- **Leftovers**: MAMuJoCo seed-count check (Exp 8 CSV has only 1 MAPPO-Lag row/env);
  stale `docs/experiments/6-*/baseline_runs.md`.

### Task 2 — Comm audit
- Done 2026-09-01; see `2-comm-audit/notes.md` (notes only, no scripts).
- PyTorch attention masks: True = blocked; no-comm mask = `~torch.eye(n).bool()`.

### Task 3 — β dynamics diagnosis
- **What**: pull β (`Agent/Lagrangian`) + cost curves for 5 SMAC maps
  (3 violators: MMM, 1c3s5z, 8m; 2 clean: 3m, 2m_vs_1z), 3 seeds each, ≤100k steps.
- **Files**: `3-safedreamer-smac-threshold/` — `pull_and_plot_beta.py`,
  `runs_config_smac.json`, `data/*.csv`, `figures/*_beta_dynamics.pdf`,
  **deliverable** `beta_diagnosis.tex` + `.pdf` (compile with 2× pdflatex).
- **Result**: on violators β reaches only ~0.1–0.5 while cost sits 3–8 above limit —
  β never converges → motivates task 4.
- **Note**: MAMuJoCo β analysis was done earlier (2026-07-28) in
  `docs/analysis/beta_dynamics/` — older results can live outside this folder.

### Task 4 — PID-Lagrangian (CURRENT)
- **Everything is in** `4-pid-lagrangian/notes.md` — read it fully. Summary:
  - Code DONE on branch `feat/pid-lagrangian`: `LagMode` enum, `PIDLagrangian`
    (plain args, rewritten from unused OmniSafe copy in `lagrange.py`), selection in
    `agent/learners/DreamerLearner.py`, flags `--lag_mode --pid_kp --pid_ki --pid_kd`
    in `train.py`, `_pid` run-name suffix, `Lag/pid_*` WandB logging.
  - 5 unit tests (`tests/test_pid_lagrangian.py`) + local smoke run done.
  - Cluster runs (MAMuJoCo, gains kp=1.0 ki=1e-5 kd=1.0, 3 seeds, GPU):
    Ant2x4 cl=0.2 (21631854-856, done to 1.7-2.3M, cancelled), Ant4x2 cl=1.0
    (21631898-900, done, cancelled), HC2x3 cl=5.0 (**21631933-935, still running**).
  - Baselines for comparison: Exp 8 Phase 3 runs #21-29 (same configs, basic
    Lagrange). Read everything at 1M (comparison target: supplement_aaai.pdf Table 4).
  - Watchpoint: `Lag/pid_i` climbs steeply — check integral windup / β saturation
    (penalty_max=100).
- **Remaining**: HC runs reach 1M → pull β/`Lag/pid_*`/cost/score curves (reuse
  `docs/analysis/beta_dynamics/` script patterns) → analysis + writeup (tex+pdf, like
  task 3) → PR into `feat/thesis-experiments` + CI green (`gh run list` / `gh run watch`).

### Task 5 — Theorem 1 estimates
- **Files**: `5-theorem1-estimates/` — `extract_theorem1.py --env mamujoco|smac`
  (WandB → `theorem1_{env}_per_run.csv` / `_agg.csv`),
  `generate_theorem1_table.py --env ...` → `theorem1_{env}_table.tex/.pdf`.
  Method + results in `notes.md` and `plan.md`.
- **Result**: bound holds for all configs (MAMuJoCo + 36 SMAC runs), slack ×58–×939.
  ε_c 0.001–0.016, TV (Pinsker from KL) 0.15–0.37. Caveat: average-case consistency
  check, not worst-case proof; KL on latents.

## 4. Exact stopping point (2026-10-04)

- Current branch: `feat/pid-lagrangian`. Waiting on HC2x3 jobs **21631933-935**
  to reach 1M env steps, then do task 4 "Remaining" above.
- **Uncommitted local changes** (reviewed, safe to commit; confirm with user first):
  task-1 script + CSVs (bane_vs_bane added), `dead_allies_agg.csv` +
  `dead_allies_all_steps.csv` (+ `.backup_20260915.csv` backups), regenerated
  multi_step + appendix tables, `4-pid-lagrangian/notes.md`, `log/2026-09-15.md`,
  `log/2026-09-24.md`, `.gitignore` (`wandb-runs/`).
- End-of-project step deliberately deferred: copy frozen final artifacts per task to
  `~/workspace/overleaf/thesis/thesis_experiments/<task>/` (folder not created yet).
- Old open TODO: theory walkthrough of `overleaf/thesis/chapters/04_theory.tex`
  (Theorem 1 + dual calibration) with the user.

## 5. Infra & conventions

**WandB**: entity/project `raz-shmueli-corsound-ai/private-mamba`. Find runs via
`api.runs(..., filters={"display_name": {"$regex": ...}})` — display names, not IDs.
Metrics logged in separate `wandb.log` calls must be fetched per key via
`run.history(keys=[...])`; interpolate env steps from anchor rows. Run names capped
at 128 chars. Walltime-killed runs show state "failed"/"crashed" — can still be valid.
Gotcha: the repo-root run dir is `wandb-runs/` (renamed from `wandb/` because it
shadowed the `wandb` package import — do not recreate `wandb/`).

**Cluster (SLURM)**: `ssh bgu` (slurm.bgu.ac.il, needs BGU VPN:
`snx -s vpn.bgu.ac.il -u razshmue@vpn`); repo at `~/workspace/private-mamba`.
Submit from LOCAL machine: `python sbatch_scripts/submit_experiments.py`.
After any code fix: commit, push, `ssh bgu 'cd ~/workspace/private-mamba && git pull'`
BEFORE resubmitting. Jobs "COMPLETED" in ~10s = crashed at startup — check `.err`
files in the cluster repo root. Verify jobs alive ~2 min after submit. Watch disk
quota (old `wandb/run-*` dirs fill it). bane_vs_bane needs 128G RAM.

**Local envs**: `venv310` for smoke runs (`--n_workers 1`; 0 workers fails),
`venv` (py3.7) for pytest. Pre-commit: `~/.local/bin/pre-commit`.

**Workflow rules** (user's, strict):
- Follow `.claude/dev-workflow/SKILL.md`; conventional commits; per-task branches
  off integration branch `feat/thesis-experiments` (off main); PRs into it, CI green.
- NEVER commit/push or edit code without explicit user permission.
- Always back up result CSVs before appending/overwriting (pattern:
  `*.backup_YYYYMMDD.csv`).
- Document every phase and failure in the task's `notes.md` before proceeding.
- Update the daily log `log/YYYY-MM-DD.md` (short bullets).
- Out of scope (user decisions): Shadow-hand Exp 10 (parked on `feat/shadow-hand`),
  Exp 9 no-comm (deprioritized).

## 6. Quick orientation for an AI

1. `git checkout feat/pid-lagrangian` — this branch has the current task's code and
   is where work stopped (done tasks live on `feat/thesis-experiments`).
2. Read this file, then `4-pid-lagrangian/notes.md` (current task), then
   `overview.md`/`plan.md` in this folder.
3. Check HC job status: `ssh bgu 'sacct -j 21631933,21631934,21631935 --format=JobID,State,Elapsed'`.
4. The main results table users care about:
   `docs/tmp/tables/multi_step_comparison/multi_step_comparison.pdf`.
5. Ask the user before any commit, push, submit, or destructive action.
