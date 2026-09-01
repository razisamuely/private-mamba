# Experiment 11 — Runs

**Branch**: `feat/thesis-experiments`

**Submission**: local `~/workspace/Safe-Policy-Optimization/sbatch_scripts/submit_baseline.py`
with `--template sbatch_scripts/template_mappolag_smac.sbatch --cost_type dead_allies_incremental`
(5M steps, CPU partition). Incremental: one map+limit (3 seeds) per batch,
user approval before each batch.

## Task 1: MAPPO-Lag — missing SMAC maps (easy → hard)

Planned order: 3m → 2s_vs_1sc → 2s3z → 3s_vs_3z → 3s_vs_4z → 3s_vs_5z →
1c3s5z c=4 → MMM → 3s5z_vs_3s6z → (bane_vs_bane after mem fix).

### Batch 1: 3m c=0.0 (submitted 2026-09-01)

| # | Map | Cost Limit | Seed | Slurm ID | Status |
|---|-----|-----------|------|----------|--------|
| 1 | 3m | 0.0 | 1 | 20816199 | RUNNING (verified healthy) |
| 2 | 3m | 0.0 | 2 | 20816200 | RUNNING (verified healthy) |
| 3 | 3m | 0.0 | 3 | 20816202 | RUNNING (verified healthy) |

### Batch 2: 3m c=1.0 (submitted 2026-09-01)

| # | Map | Cost Limit | Seed | Slurm ID | Status |
|---|-----|-----------|------|----------|--------|
| 1 | 3m | 1.0 | 1 | 20816461 | RUNNING (verified healthy) |
| 2 | 3m | 1.0 | 2 | 20816463 | RUNNING (verified healthy) |
| 3 | 3m | 1.0 | 3 | 20816464 | RUNNING (verified healthy) |

### Batches 3–17: bulk submission, 10s gaps (2026-09-01, seeds 1–3 each)

| Map | Cost Limit | Slurm IDs (s1, s2, s3) | Status |
|-----|-----------|------------------------|--------|
| 2s_vs_1sc | 0.0 | ~~20816597/99/602~~ → 20816812/814/816 | RUNNING (resubmitted) |
| 2s_vs_1sc | 1.0 | ~~20816614/616/619~~ → 20816841/844/846 | RUNNING (resubmitted) |
| 2s3z | 0.0 | 20816630/633/636 | RUNNING |
| 2s3z | 4.0 | 20816649/652/655 | RUNNING |
| 3s_vs_3z | 0.0 | 20816666/668/670 | RUNNING |
| 3s_vs_3z | 1.0 | 20816680/682/684 | RUNNING |
| 3s_vs_4z | 0.0 | ~~20816693/695/696~~ → 20816873/875/876 | RUNNING (resubmitted) |
| 3s_vs_4z | 1.0 | ~~20816697/698/699~~ → 20816882/884/886 | RUNNING (resubmitted) |
| 3s_vs_5z | 0.0 | 20816700/701/702 | RUNNING |
| 3s_vs_5z | 1.0 | 20816703/706/709 | RUNNING |
| 1c3s5z | 4.0 | 20816718/720/722 | RUNNING |
| MMM | 0.0 | 20816735/738/740 | RUNNING |
| MMM | 4.0 | 20816751/753/756 | RUNNING |
| 3s5z_vs_3s6z | 0.0 | 20816766/768/771 | RUNNING |
| 3s5z_vs_3s6z | 4.0 | 20816782/784/786 | RUNNING |

**Failure + fix**: first submission of 2s_vs_1sc and 3s_vs_4z crashed in ~10s
("Unrecognized task!") — maps missing from `smac_map` in SafePO
`safepo/utils/config.py`. Fixed on cluster (commit `acbbeff`), resubmitted
with 30s gaps. All 51 mappolag jobs verified RUNNING past the crash window.

**Node failures + auto-restart** (2026-09-01 ~08:16, Slurm controller outage):
`3s_vs_3z c=0 seed3` and `MMM c=0 seed3` crashed and were auto-requeued —
each has a duplicate WandB run (crashed + fresh restart). **At extraction:
keep only the newest run per config.** All 51 jobs verified alive via WandB
heartbeats (~11:38).

**Remaining**: bane_vs_bane c=0.0/4.0 — parked until mem fix (4G → 16-32G, longer walltime).
