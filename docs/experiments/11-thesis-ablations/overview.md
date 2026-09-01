# Experiment 11 — Thesis Ablations & Completions

Supervisor notes (2026-09-01) — work needed to complete the CS master thesis.

## Points

1. **MAPPO-Lag on all environments** — the baseline was only run on MAMuJoCo
   (incl. matched-budget 1M). Fill gaps: SMAC maps (jobs 19601155-173 may
   already cover this — verify/extract first), remaining MAMuJoCo partitions,
   shadow-hand (Exp 10) when ready.
2. **Communication audit: training vs inference** — verify whether the
   comm/attention mechanism is active during training (rollouts, world-model
   learning, imagination) and at eval/inference. Audit
   `agent/workers/DreamerWorker.py`, `agent/runners/DreamerRunner.py`,
   attention-mask injection, eval path.
3. **SafeDreamer above cost threshold on SMAC** — diagnose why the cost limit
   is violated (multiplier/λ dynamics, cost curves). Remedies to test:
   more pessimistic training threshold (c' < c); check multiplier too
   big/oscillating.
4. **PID-Lagrangian** — replace gradient-ascent λ update with a PID controller
   (Stooke et al. 2020). Ablation: vanilla vs PID, especially SMAC.
5. **Theorem 1 empirical estimates** — estimate the theorem's quantities
   (`overleaf/thesis/chapters/04_theory.tex`) from runs; compare measured
   violations to the predicted bound. Prereq: theory walkthrough.
   Related: `docs/analysis/cost_model_accuracy/`.

## Branching

- Integration branch: `feat/thesis-experiments` (off `main`)
- Per-task branches off it (e.g. `feat/pid-lagrangian`), merged back when done
- Analysis-only points (2, 3-diagnosis) need no code branch

## Folder structure

One subfolder per task; all analysis, scripts, and raw outputs live there:

```
11-thesis-ablations/
├── 1-mappo-lag-all-envs/
├── 2-comm-audit/
├── 3-safedreamer-smac-threshold/
├── 4-pid-lagrangian/
└── 5-theorem1-estimates/
```

Each has a `notes.md` (working notes, findings, links to jobs/WandB runs).

## Moving results to the thesis

When a task is **fully done**, copy only the final artifacts (figures,
tables, short summary) to `~/workspace/overleaf/thesis/thesis_experiments/<task>/`
(create that folder on first copy). The thesis-repo copy is frozen — any
further changes happen here first, then re-copy.

## Status

See `plan.md` for detailed plans and `runs.md` for job logs.
