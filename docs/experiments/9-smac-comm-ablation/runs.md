# Experiment 9 — Runs

## Baselines (full comm, from Experiment 6, branch feat/lag-real-episode-cost)

| Map | Cost type | CL | Seed | Slurm ID |
|-----|-----------|----|------|----------|
| 8m | dead_allies_incremental | 0.0 | 1 | 17209123 |
| 8m | dead_allies_incremental | 0.0 | 2 | 17209124 |
| 8m | dead_allies_incremental | 0.0 | 3 | 17209125 |
| MMM | dead_allies_incremental | 0.0 | 1 | 17198319 |
| MMM | dead_allies_incremental | 0.0 | 2 | 17198320 |
| MMM | dead_allies_incremental | 0.0 | 3 | 17198321 |

## No-comm jobs (branch fix/comm-mask-inversion, --comm_mode none, laglr=1e-5)

Submitted 2026-07-25. Verified `comm_mode=none, action_type=discrete` in logs.
Note: had to free cluster disk first (deleted 80 wandb run dirs >8 months old, ~61 GB;
quota exceeded blocked git pull).

| # | Map | CL | Seed | Slurm ID | Status |
|---|-----|----|------|----------|--------|
| 1 | 8m | 0.0 | 1 | 19539781 | RUNNING |
| 2 | 8m | 0.0 | 2 | 19539783 | RUNNING |
| 3 | 8m | 0.0 | 3 | 19539784 | RUNNING |
| 4 | MMM | 0.0 | 1 | 19539785 | RUNNING |
| 5 | MMM | 0.0 | 2 | 19539786 | RUNNING |
| 6 | MMM | 0.0 | 3 | 19539787 | PENDING (QOS GPU limit) |
