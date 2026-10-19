# #24 — Parity start on the configurations that miss their limit

Issue: https://github.com/razisamuely/private-mamba/issues/24
Plan section: §2 of `docs/planning/remaining_work_2026-10-15.pdf`

## Problem

At 100k interactions CA-MAMBA meets only **5 of the 12 nonzero SMAC limits**. This is the first
thing a reviewer will hold against the paper.

The paper's own diagnosis (RQ2) is that the learned price is too slow. It starts at
`beta_0 = 1e-4` and the dual step `alpha_beta = 1e-5` cannot lift it far within 100k: at `d=0` on
`8m`, beta only reaches 0.025-0.54 by the end, and a price fixed at 1 beats it on both cost and
win rate (1.75 / 0.97 against 2.05 / 0.95).

## Hypothesis

Start the multiplier at parity, `beta_0 = 1`, and keep the learned update. Both the reward and
cost advantages are standardized, so `beta = 1` weighs them equally from the first step; the
update is then free to move in either direction.

Evidence it behaves sensibly: on HalfCheetah the same rule settles at 0.32-0.51 when the limit is
loose (`d=25`) and stays at 0.87-1.01 when it binds (`d=5`). It relaxes when it can and holds when
it must.

## What changes

Only `--lag_init`, from the default `1e-4` to `1.0`. Everything else is the method's default.
This stays a **variant**, not the new default, so nothing already reported needs rerunning.

### Settings, exactly

Three flags are passed, but only one of them is a change:

| Flag | Value | Why |
|---|---|---|
| `--lag_init` | `1.0` | **the variable** — default is `1e-4` |
| `--laglr` | `1e-5` | already the default, passed explicitly for the record |
| `--max_steps` | `100000` | matches the baseline checkpoint |

The paper's tuned optimizer flags (`--actor_lr 3e-5 --model_lr 1e-4 --value_lr 1e-4
--grad_clip 10 --grad_clip_policy 5`) are **deliberately not passed**. Mixing them in is what made Table 6
uninterpretable (ground rule 2, §1 of the plan). The SMAC baseline in
`ca_mamba_measured_100k.csv` also ran on code defaults, so the comparison is like for like.

Walltime is 7 days but `--max_steps` is what ends each run, not the clock.

## Baseline — which configurations miss

Computed from `overleaf/thesis/data/ca_mamba_measured_100k.csv`, mean cost over 3 seeds at the
100k checkpoint. 12 nonzero limits, 5 met, 7 missed:

| Map | d | mean cost | met |
|---|---|---|---|
| `2m_vs_1z` | 1 | 0.14 | yes |
| `2s_vs_1sc` | 1 | 0.31 | yes |
| `3m` | 1 | 0.60 | yes |
| `3s_vs_3z` | 1 | 0.92 | yes |
| `2s3z` | 4 | 2.98 | yes |
| **`3s_vs_4z`** | **1** | **2.47** | **no** |
| **`3s_vs_5z`** | **1** | **2.67** | **no** |
| **`1c3s5z`** | **4** | **4.83** | **no** |
| **`3s5z_vs_3s6z`** | **4** | **7.54** | **no** |
| **`8m`** | **4** | **5.03** | **no** |
| **`MMM`** | **4** | **7.88** | **no** |
| **`bane_vs_bane`** | **4** | **6.37** | **no** |

## Runs

8 configurations x 3 seeds = **24 runs**, 100k interactions each.

| Group | Maps | d | Runs |
|---|---|---|---|
| Table 2 row | `8m` | 0 | 3 |
| Missed, tight | `3s_vs_4z`, `3s_vs_5z` | 1 | 6 |
| Missed, loose | `1c3s5z`, `3s5z_vs_3s6z`, `8m`, `MMM`, `bane_vs_bane` | 4 | 15 |

`bane_vs_bane` OOMed before on the **CPU** partition. This template targets `rtx3090` with 64G,
so no extra memory flag is needed.

## Submit commands

From the local machine, after the cluster checkout is on the same commit:

```bash
# d=0, the new Table 2 row
python sbatch_scripts/submit_experiments.py \
    --envs 8m --cost_limits 0 --seeds 1 2 3 \
    --laglr 1e-5 --lag_init 1.0 --max_steps 100000

# d=1, the two tight maps that miss
python sbatch_scripts/submit_experiments.py \
    --envs 3s_vs_4z 3s_vs_5z --cost_limits 1 --seeds 1 2 3 \
    --laglr 1e-5 --lag_init 1.0 --max_steps 100000

# d=4, the five looser maps that miss
python sbatch_scripts/submit_experiments.py \
    --envs 1c3s5z 3s5z_vs_3s6z 8m MMM bane_vs_bane --cost_limits 4 --seeds 1 2 3 \
    --laglr 1e-5 --lag_init 1.0 --max_steps 100000
```

Add `--dry_run` first to inspect the generated sbatch files.

## Success criterion

The variant meets more of the 7 limits **without lowering the win rate**. If it does, RQ2 stops
being "the method often misses its limits" and becomes "it misses for a reason we identified, and
this is the fix the diagnosis predicts".

If win rate drops materially, report it as a trade-off rather than a fix.

## Status

| Step | State |
|---|---|
| Baseline configurations identified | done |
| Cluster checkout synced | done — `8cd306a` (was `1e54c6a`) |
| Jobs submitted | done — 24/24, 2026-10-19 |
| Jobs verified alive (~2 min after submit) | done — 9 RUNNING, 15 PENDING |
| Runs finished | 6/24 as of 2026-10-19 — 9 running, 9 queued |
| Endpoints extracted | pending — waits for all 24 |
| Written into RQ2 | pending |

While the queue drains the cluster checkout must stay on `8cd306a`. Pending jobs read `train.py`
at launch, so a push would split this comparison across two code versions.

## Run log

| Date | Jobs | Group | Notes |
|---|---|---|---|
| 2026-10-19 | 23347908-910 | `8m` d=0, s1-3 | RUNNING |
| 2026-10-19 | 23347928-930 | `3s_vs_4z` d=1, s1-3 | **COMPLETED** — 100.7k/100.8k/100.7k samples |
| 2026-10-19 | 23348289-291 | `3s_vs_5z` d=1, s1-3 | **COMPLETED** — 101.3k/101.0k/101.1k samples |
| 2026-10-19 | 23348292, 294, 295 | `1c3s5z` d=4, s1-3 | PENDING (GPU queue) |
| 2026-10-19 | 23348296-298 | `3s5z_vs_3s6z` d=4, s1-3 | PENDING |
| 2026-10-19 | 23348299-301 | `8m` d=4, s1-3 | PENDING |
| 2026-10-19 | 23348303, 306, 307 | `MMM` d=4, s1-3 | PENDING |
| 2026-10-19 | 23348308-310 | `bane_vs_bane` d=4, s1-3 | PENDING |

All on commit `8cd306a`, branch `feat/aamas-8m-ablation`, partition `rtx3090`, 64G,
`--laglr 1e-5 --lag_init 1.0 --max_steps 100000`.
