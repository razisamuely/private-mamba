# Experiment 7 — Runs

**Branch**: `feat/swimmer-baseline-comparison` (private-mamba), `feat/collision-cost-comparison` (SafePO)
**Fix**: Switched `train.py` to use `SwimmerWrapper` (old `SafetyGymWrapper` had registration error).

---
## Swimmer (Safety2x1SwimmerVelocity-v0)

## SafeDreamer (cost_limit=25)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942525 | | RUNNING |
| 2 | 17942527 | | RUNNING |
| 3 | 17942528 | | RUNNING |

## SafeDreamer (cost_limit=10)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942529 | | RUNNING |
| 2 | 17942530 | | RUNNING |
| 3 | 17942531 | | RUNNING |

## MACPO (cost_limit=25)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942323 | | RUNNING |
| 2 | 17942324 | | RUNNING |
| 3 | 17942325 | | RUNNING |

## MACPO (cost_limit=10)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942488 | | SUBMITTED |
| 2 | 17942489 | | SUBMITTED |
| 3 | 17942490 | | SUBMITTED |

---
## HalfCheetah (Safety2x3HalfCheetahVelocity-v0)

### MACPO (cost_limit=25)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942603 | | SUBMITTED |
| 2 | 17942607 | | SUBMITTED |

### SafeDreamer (cost_limit=25)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942610 | | SUBMITTED |
| 2 | 17942611 | | SUBMITTED |

---
## Ant (Safety2x4AntVelocity-v0)

Note: `Safety2x3AntVelocity-v0` not in SafePO config map (failed). Upstream uses 2x4. Cancelled 17942608/09 (MACPO) and 17942612/13 (SafeDreamer).

### MACPO (cost_limit=25)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942620 | | SUBMITTED |
| 2 | 17942621 | | SUBMITTED |

### SafeDreamer (cost_limit=25)

| Seed | Slurm ID | WandB Run | Status |
|------|----------|-----------|--------|
| 1 | 17942623 | | SUBMITTED |
| 2 | 17942624 | | SUBMITTED |

---
## Submission Commands

**SafeDreamer** (run locally, SCPs to cluster):
```bash
cd /home/corsound/workspace/private-mamba
./venv310/bin/python3 sbatch_scripts/submit_experiments.py \
    --envs Safety2x1SwimmerVelocity-v0 \
    --seeds 1 2 3 \
    --cost_limits 25 \
    --env_type safety_gym \
    --laglr 0.00001 \
    --algo_name safedreamer
```

**MACPO** (run locally, SCPs to cluster):
```bash
cd /home/corsound/workspace/Safe-Policy-Optimization
python3 sbatch_scripts/submit_baseline.py \
    --tasks Safety2x1SwimmerVelocity-v0 \
    --seeds 1 2 3 \
    --cost_limits 25 \
    --template sbatch_scripts/template_macpo_mamujoco.sbatch
```
