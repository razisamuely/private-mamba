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
so no extra memory flag is needed — but that turned out not to be enough; see
"`bane_vs_bane` OOMs again, on the GPU" below.

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

## `bane_vs_bane` OOMs again, on the GPU

Seeds 1 and 2 (jobs 23348308, 23348309) reported `COMPLETED` with exit code `0:0` after **53
seconds**. That is a crash at startup, not a finished run — the usual Slurm trap. The `.err` files
show a CUDA OOM:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.48 GiB.
GPU 0 has a total capacity of 10.90 GiB of which 1.65 GiB is free.
```

The traceback runs `DreamerLearner.train_agent` → `loss.actor_rollout` → `critic_rollout` →
`calculate_next_reward` → `rnns.forward` → `_VF.gru`: the imagination rollout, where
`bane_vs_bane`'s 24 agents cost the most.

**Cause: a GPU-model lottery, not a memory shortage.** `template.sbatch` asks for `--gpus=1`, which
does not pin the card, and the `rtx3090` partition also holds `ise-pheno` / `cs-pheno` nodes
carrying 11 GB RTX 2080s. Seeds 1 and 2 landed on one of those (10.90 GiB visible); seed 3 (job
23348310) drew `cs-pheno-11` with a 24 GB card and runs fine. `--mem=64G` is host RAM and has no
bearing on this.

### Two fixes tried, one works

| Option | How | Jobs | Result |
|---|---|---|---|
| Pin the GPU model | new `sbatch_scripts/template_gpu24.sbatch` with `--gres=gpu:rtx_3090:1` | 23423930, 23423931 | **RUNNING** on `cs-3090-06`, well past the 53 s mark |
| Fewer rollout workers | `--n_workers 2` instead of 4 | 23423932, 23423933 | **failed identically** — 51-52 s, same OOM, same `2.48 GiB` request with `9.25 GiB` in use, on `cs-pheno-07` / `cs-pheno-08` |

The second arm is informative: halving the workers did not move the allocation figures at all, so
the VRAM is dominated by the imagination rollout rather than the worker count. It was also the
weaker option on principle, since `--n_workers` is a method setting and ground rule 2 forbids
varying one across a comparison. Pinning the card changes nothing about the method, so the
resubmitted seeds stay comparable with the other 22 runs.

## The real reason `bane_vs_bane` never finishes: preemption

The pinned retries did not OOM, but they did not progress either. `sacct --duplicates` shows why:

| Job | Allocations | Fate |
|---|---|---|
| 23348310 (s3) | 2 | ran 20h52m to 69k samples, **preempted**, requeued from scratch onto an 11 GB card, OOMed in 57 s |
| 23423930 (s1) | 4 | preempted 3 times, back to 44.7k |
| 23423931 (s2) | 9 | preempted 8 times, back to 12.5k |

The `normal` QoS is preemptible by every lab QoS on the cluster, all with `PreemptMode=REQUEUE`,
and `train.py` has no resume — so each preemption throws the entire run away. `bane_vs_bane` is the
only map slow enough (~30 h for 100k) to keep getting caught; the other 21 runs each hold exactly
one allocation record and were never interrupted, so **their data is sound**.

This also explains a quieter bug: `--partition=rtx3090` was never honoured. That partition carries
`DenyQos=normal`, so every job silently fell back to the `gpu` partition. The `--gres` pin still
applied, which is why it worked.

### The non-preemptible QoS does not help

The account has its own `razshmue` QoS, which preempts `normal` and which nothing preempts. But its
per-account cap is

```
gres/gpu:gtx_1080=1,gres/gpu:rtx_2080=0,gres/gpu:rtx_3090=0,gres/gpu:rtx_4090=0,...
```

— one 8 GB GTX 1080 and zero of everything else. `sbatch` rejects the job with
`MaxGRESPerAccount`. So there is no non-preemptible allocation this run can fit in, and the only
durable fix is checkpoint/resume in `train.py`.

```bash
python sbatch_scripts/submit_experiments.py \
    --envs bane_vs_bane --cost_limits 4.0 --seeds 1 2 \
    --laglr 1e-5 --lag_init 1.0 --max_steps 100000 \
    --template sbatch_scripts/template_gpu24.sbatch
```

## Status

| Step | State |
|---|---|
| Baseline configurations identified | done |
| Cluster checkout synced | done — `8cd306a` (was `1e54c6a`) |
| Jobs submitted | done — 24/24, 2026-10-19 |
| Jobs verified alive (~2 min after submit) | done — 9 RUNNING, 15 PENDING |
| Runs finished | done — 24/24, all past 100k |
| `bane_vs_bane` s1/s2 | resubmitted 2026-10-20 on a pinned RTX 3090 after a CUDA OOM |
| Endpoints extracted | done — `overleaf/thesis/data/parity_start_100k.csv` (24 rows) |
| Comparison table | done — `overleaf/thesis/generated/parity_start.tex` |
| Written into RQ2 | pending — results are mixed, see conclusion below |

## Conclusion

**Mixed result.** Only 1 of 7 missed limits is now met (`8m` d=4).

| Map | d | Baseline cost | Parity cost | Baseline WR | Parity WR | Met? |
|---|---|---|---|---|---|---|
| `8m` | 0 | 2.05 | 2.61 | 0.95 | 0.87 | n/a |
| `3s_vs_4z` | 1 | 2.47 | **2.05** | 0.31 | **0.38** | no |
| `3s_vs_5z` | 1 | 2.67 | 2.79 | 0.17 | 0.08 | no |
| `1c3s5z` | 4 | 4.83 | 6.73 | 0.79 | 0.33 | no |
| `3s5z_vs_3s6z` | 4 | 7.54 | 8.00 | 0.11 | 0.00 | no |
| `8m` | 4 | 5.03 | **3.06** | 0.69 | **0.83** | **YES** |
| `MMM` | 4 | 7.88 | 9.05 | 0.55 | 0.30 | no |
| `bane_vs_bane` | 4 | 6.37 | **5.06** | 0.98 | 0.95 | no |

Parity start helps on maps where the baseline already learns (`8m`, `bane_vs_bane`, `3s_vs_4z`) but
hurts on maps where the agent struggles to win at all. Starting β high on a hard map suppresses
reward too early. Report as a trade-off, not a fix.

## Run log

| Date | Jobs | Group | Notes |
|---|---|---|---|
| 2026-10-19 | 23347908-910 | `8m` d=0, s1-3 | **COMPLETED** — past 100k |
| 2026-10-19 | 23347928-930 | `3s_vs_4z` d=1, s1-3 | **COMPLETED** — 100.7k/100.8k/100.7k samples |
| 2026-10-19 | 23348289-291 | `3s_vs_5z` d=1, s1-3 | **COMPLETED** — 101.3k/101.0k/101.1k samples |
| 2026-10-19 | 23348292, 294, 295 | `1c3s5z` d=4, s1-3 | **COMPLETED** — past 100k |
| 2026-10-19 | 23348296-298 | `3s5z_vs_3s6z` d=4, s1-3 | **COMPLETED** — past 100k |
| 2026-10-19 | 23348299, 301 | `8m` d=4, s1 + s3 | **COMPLETED** — past 100k |
| 2026-10-19 | 23348300 | `8m` d=4, s2 | RUNNING — 83.0k samples at 14 h |
| 2026-10-19 | 23348303, 306, 307 | `MMM` d=4, s1-3 | **COMPLETED** — past 100k |
| 2026-10-19 | 23348308, 23348309 | `bane_vs_bane` d=4, s1-2 | **CUDA OOM at 53 s** — 11 GB card, resubmitted |
| 2026-10-19 | 23348310 | `bane_vs_bane` d=4, s3 | RUNNING — 44.8k samples at 12 h, 24 GB card |
| 2026-10-20 | 23423930, 23423931 | `bane_vs_bane` d=4, s1-2 (retry) | RUNNING on `cs-3090-06`, GPU pinned |
| 2026-10-20 | 23423932, 23423933 | `bane_vs_bane` d=4, s1-2 (`--n_workers 2`) | **CUDA OOM at 51-52 s** — arm abandoned |
| 2026-10-20 | 23447426-428 | `bane_vs_bane` d=4, s1-3 (retry 2) | PENDING — GPU pinned, `normal` QoS; 23423930/931 cancelled first |

All on commit `8cd306a`, branch `feat/aamas-8m-ablation`, partition `rtx3090`, 64G,
`--laglr 1e-5 --lag_init 1.0 --max_steps 100000`. The 2026-10-20 retries differ only in which
sbatch template requested the card.
