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

## Step 4: Commit + push + pull on cluster

## Step 5: Submit 6 jobs
`python sbatch_scripts/submit_experiments.py --envs 8m MMM --cost_limits 0.0 \
  --seeds 1 2 3 --env_type starcraft --cost_type dead_allies_incremental \
  --laglr 0.00001 --comm_mode none`
- Validate: squeue after 2 min, logs show `comm_mode=none`, wandb runs appear with `_nocomm`

## Step 6: Extract and compare
- Full comm sources: exp-6 runs (`wandb_runs.json`)
- Compare reward (battle won rate / return) and cost at matched steps
- Output: comparison table (full vs no comm per map) + update overview.md

## Final result
Table: SafeDreamer full comm vs no comm on 8m and MMM — completes the
communication-ablation story (MAMuJoCo + SMAC).
