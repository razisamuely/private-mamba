# Experiment 9 — Plan

## Step 1: Wire COMM_MODE for SMAC -- DONE
`train.py` `prepare_starcraft_configs`: added `config.COMM_MODE = args.comm_mode`.

## Step 2: Pick baseline grid -- DONE
8m + MMM, dead_allies_incremental, c=0.0, seeds 1-3 (mirrors Exp 6 baselines).

## Step 3: Local smoke test -- DONE (2026-07-24)
- Ran 8m locally 5 min, venv310, `--comm_mode none --n_workers 1`
  (`--n_workers 0` fails: Ray actors can't be instantiated directly)
- Verified: `DreamerWorker[0]: comm_mode=none, action_type=discrete`, episodes ran
- Mask logic (`~eye`) is the same code path proven empirically in Exp 8 Phase 5

## Step 4: Commit + push + pull on cluster -- DONE (2026-07-25)
Committed `090f184`, pushed, pulled on cluster (after freeing 61 GB disk — deleted
80 wandb run dirs >8 months old).

## Step 5: Submit 6 jobs -- DONE (2026-07-25)
Slurm IDs: 19539781/783/784/785/786/787
Verified: 5 RUNNING, 1 PENDING (MMM s3, GPU quota); logs show
`comm_mode=none, action_type=discrete`. Committed `3e6cc82`.

## Step 6: Extract and compare
**Status**: waiting for jobs to complete (~days)
- Full comm sources: exp-6 runs (`wandb_runs.json`)
- Compare reward (battle won rate / return) and cost at matched steps
- Output: comparison table (full vs no comm per map) + update overview.md

## Possible expansion (discussed, not yet submitted)
Additional no-comm runs on maps with existing exp-6 baselines:
- 3s_vs_3z (collision, c=0.0 + c=0.5) — 6 jobs
- 3s5z_vs_3s6z (collision, c=0.0) — 3 jobs
Would add 3-agent and 8-agent data points + a non-zero cost limit.

## Final result
Table: SafeDreamer full comm vs no comm on SMAC — completes the
communication-ablation story (MAMuJoCo + SMAC).
