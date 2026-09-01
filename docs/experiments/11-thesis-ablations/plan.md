# Experiment 11 — Plan

Order of work (cheap/analysis first, compute last):

1. **Check cluster + extract pending runs** — SMAC MAPPO-Lag 19601155-173,
   Exp 9 no-comm 19539781-787, HC c=5.0 seeds 19563313-314. Backup CSVs
   before appending.
2. **Comm audit (point 2)** — code reading, no compute. Deliverable: short
   writeup in this dir of where comm is active (train rollout / imagination /
   eval) and how the no-comm mask is applied.
3. **SafeDreamer SMAC diagnosis (point 3)** — analyze existing WandB data
   (reuse `docs/analysis/beta_dynamics/` tooling).
4. **PID-Lagrangian (point 4)** — implement, smoke-test locally
   (venv310, `--n_workers 1`), then SMAC runs: vanilla vs PID, plus
   pessimistic-threshold variants from point 3.
5. **MAPPO-Lag env gaps (point 1)** — submit whatever is still missing after
   step 1 extraction.
6. **Theorem 1 estimates (point 5)** — after theory walkthrough with user.

Details to be filled per step as work starts, inside each task subfolder's
`notes.md`.

## Final step per task

Once a task is complete: copy final artifacts (figures/tables/summary) to
`~/workspace/overleaf/thesis/thesis_experiments/<task>/` — see overview.md.
