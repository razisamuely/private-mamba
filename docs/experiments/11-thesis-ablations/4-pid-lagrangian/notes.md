# 4-pid-lagrangian — working notes

**Date**: 2026-09-23. Supervisor point 4. Follows from task 3 diagnosis:
β (gradient-ascent, lag-lr=1e-5) rises too slowly → cost stays above threshold.
Fix: PID controller on the multiplier (Stooke et al. 2020, arXiv:2007.03964).

## What exists already

- `lagrange.py:67` — `PIDLagrangian` class, copied from OmniSafe, **never used**.
  Correct vs the paper when extras are OFF (`sum_norm`, `diff_norm`,
  `use_cost_decay`). Expects `config.pid.*` — needs adapting to plain args.
- `BasicLagrange` (`lagrange.py:9`) is the one in use:
  `λ += lr·(cost − limit)` — integral-only.
- Wiring: `agent/learners/DreamerLearner.py:55` (init), `:185`
  (`adv − λ·cost_adv`), `:215` (`update(mean_cost)` per training step).
- No loss change needed. Deliberately NOT adding the paper's `/(1+λ)`
  objective normalization — one variable at a time (λ stays small here).

## Plan

1. **Code** (branch `feat/pid-lagrangian` off `feat/thesis-experiments`)
   - Central enum: `LagMode(Enum): BASIC, PID` (next to the existing `Env`
     enum) — no raw `"basic"`/`"pid"` strings at call sites.
   - `lagrange.py`: `PIDLagrangian.__init__(cost_limit, kp, ki, kd, ...)`
     plain args, extras off by default; expose `.lambda_` + `.update(cost)`
     (same interface as `BasicLagrange`). Type hints on all new/changed
     signatures.
   - `train.py`: `--lag_mode` (choices from `LagMode`, default BASIC — zero
     change to existing behavior) + `--pid_kp --pid_ki --pid_kd`.
   - `DreamerLearner`: instantiate by `config.LAG_MODE` (enum compare);
     WandB-log β and the P/I/D components.
2. **Test**
   - `tests/test_pid_lagrangian.py`, names per convention
     `test_<what>_<expected_behavior>`:
     - `test_pid_update_sustained_violation_increases_beta`
     - `test_pid_update_cost_below_limit_relaxes_beta_nonnegative`
     - `test_pid_i_only_matches_basic_lagrange`
   - Pre-commit hook (isort/autoflake/black/pyupgrade) runs on commit.
   - Local smoke run (venv310, `--n_workers 1`, PID mode).
3. **Runs — MAMuJoCo**
   - Envs: Ant2x4 + HC2x3, tight cost limit (where basic-Lagrange violates).
   - 3 seeds, `--lag_mode pid`, otherwise identical to existing baselines
     (basic runs already exist → free comparison).
   - Initial gains: kp=1.0, ki=1e-5 (≈ current lag-lr), kd=1.0; tune if needed.
4. **Evaluate**
   - Pull β + cost curves (reuse `docs/analysis/beta_dynamics/` scripts).
   - Success = cost reaches/holds the limit faster than basic, score not worse.
5. **Ship** (per dev-workflow SKILL)
   - Conventional commits; push branch; verify CI (`gh run list` →
     `gh run watch`, fix failures before proceeding).
   - PR into `feat/thesis-experiments` with Summary / Changes / Test plan.

## Status

- [x] Investigation (this file)
- [x] Implementation (2026-09-23, branch `feat/pid-lagrangian`): `LagMode` enum,
      `PIDLagrangian` plain-args rewrite (extras removed), learner selection,
      `--lag_mode/--pid_kp/ki/kd` flags, `_pid` run-name suffix, `Lag/pid_*` logging
- [x] Unit test (5 tests, incl. I-only == BasicLagrange) + local smoke run
      (Ant2x4, cpu, offline wandb — PID metrics logged, no crash).
      Note: venv310 was broken by OS upgrade (python3.10 gone) — reinstalled
      via deadsnakes + relinked `venv310/bin/python`.
- [x] Cluster runs submitted 2026-09-23 (~18:12), branch `feat/pid-lagrangian`,
      GPU (rtx3090), gains kp=1.0 ki=1e-5 kd=1.0, laglr=1e-5, 3 seeds each:
      | Env | CL | Slurm IDs |
      |-----|----|-----------|
      | Ant 2x4 | 0.2 | 21631854-856 |
      | Ant 4x2 | 1.0 | 21631898-900 |
      | HC 2x3 | 5.0 | 21631933-935 |
      Verified alive +2min (RUNNING, episodes progressing). WandB runs carry
      `_pid` suffix. Baselines = Exp 8 Phase 3 runs #21-29 (same configs, basic).
- [x] Runs reached 1M (2026-09-24): Slurm quota allowed 6 concurrent; Ant runs
      cancelled past 1M (Ant2x4 1.7-2.3M, Ant4x2 1.7-2.0M) to free quota, HC2x3
      then started (21631933-935, healthy). Comparison target: supplement_aaai.pdf
      Table 4 (tight limits, all methods read at 1M).
      Watchpoint: `Lag/pid_i` climbs steeply — check for integral windup /
      β saturation (penalty_max=100) in analysis.
- [ ] HC runs reach 1M
- [ ] Analysis + writeup
- [ ] PR + CI green
