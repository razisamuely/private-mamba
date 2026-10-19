# Experiment 12 — AAMAS remaining work (thesis + rebuttal)

Work after the AAMAS 2027 submission (OpenReview #1039). Driven by the supervisor's plan of
2026-10-15, `docs/planning/remaining_work_2026-10-15.pdf`.

Board: epic [#42](https://github.com/razisamuely/private-mamba/issues/42), children #20-#41,
labeled `plan-<section>-<slug>`.

## Ground rules

1. The method's defaults do not change. Improvements are reported as *variants* on the
   configurations where they matter, never as a new default.
2. All runs inside one comparison use the same settings. This already broke Table 6 once: the
   paper lists tuned optimizer flags (`--actor_lr 3e-5 --model_lr 1e-4 --value_lr 1e-4
   --grad_clip 10 --grad_clip_policy 5`) that the code does not apply by default.
3. Every new run records its full config and code commit next to its logs, and is seeded.
4. Results are read as the mean over each run's episodes in the last 5k interactions before the
   checkpoint, reported as mean +/- sample standard deviation over runs.

## Subfolders

| Folder | Issue | What |
|---|---|---|
| `21-verify-hc-commits/` | #21 | Which code commit each Table 6 batch ran on |
| `24-parity-start/` | #24 | Parity start on the SMAC configurations that miss their limit |

## Status

- **#21** blocked on Shahaf (emailed 2026-10-19): his batches ran from `~/camamba/private-mamba`,
  offline, with no commit recorded. Our 24 runs are verified on `1e54c6a`.
- **#20** (rebuild Table 6) waits on #21.
- **#24** running: 24 jobs submitted 2026-10-19 on `8cd306a` (9 running, 15 queued). See its folder.
