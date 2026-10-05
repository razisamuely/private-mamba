# 6-aamas-revision — AAMAS 2027 revision tasks (Shperb, deadline Oct 8)

**Date**: 2026-10-04. Branch `feat/aamas-8m-ablation`.
**GitHub issue**: [#3](https://github.com/razisamuely/private-mamba/issues/3)
**Instructions**: `/home/corsound/Downloads/INSTRUCTIONS.md` (WhatsApp from Shperb)

---

## Step 1: Cluster setup
- [x] `ssh bgu`, checkout `feat/aamas-8m-ablation`, pull

## Step 2: Submit 15 SMAC 8m jobs (d=4, seeds 1-3, 105k steps)

| Arm | Flags | Slurm IDs | Status |
|---|---|---|---|
| Measured-cost basic | `--laglr 1e-5` | 22156904, 22156905, 22156906 | RUNNING |
| PID | `--lag_mode pid --pid_kp 1.0 --pid_ki 1e-5 --pid_kd 1.0` | 22156909, 22156910, 22156912 | 3/3 COMPLETED |
| Fixed λ=1 | `--laglr 0 --lag_init 1.0` | 22156913, 22156917, 22156918 | 1/3 COMPLETED, 2 RUNNING |
| Cost-blind λ=0 | `--laglr 0 --lag_init 0.0` | 22156920, 22156922, 22156923 | RUNNING |
| Imagined-cost basic | `--laglr 1e-5 --lag_signal imagined` | 22156924, 22156926, 22156927 | RUNNING (started late) |

`--max_steps` auto-stop confirmed working (PID stopped at ~105k env steps).

## Step 3: Submit 9 MAPPO-Lag tight-limit MAMuJoCo (10M steps, seeds 1-3)

| Env | d | Slurm IDs | Status |
|---|---|---|---|
| Ant 2x4 | 0.2 | 22157940, 22157941, 22157942 | partially COMPLETED |
| Ant 4x2 | 1.0 | 22157945, 22157946, 22157947 | RUNNING |
| HC 2x3 | 5.0 | 22157832, 22157833, 22157939 | 3/3 COMPLETED |

## Step 4: Verify

- [x] Episodes progressing
- [x] Fixed-λ: `Agent/Lagrangian` stays at 1.0
- [x] PID: `Lag/pid_*` logged
- [ ] Cost-blind λ=0: verify stays at 0 (was queued at verify time)
- [ ] Imagined-cost: verify runs (was queued at verify time)

## Step 5: Answer Shperb's questions

- [ ] Old 8m d=4 runs: does `Agent/Lagrangian` stay near 0? `Lag/mean_cost` range?
- [ ] Wall-clock for 8m to reach 100k steps?
- [ ] HC 2x3 PID jobs (21631933-935) finished?
- [ ] `sacct` compute numbers (wall-clock + memory) for PID, basic, MAPPO-Lag, MACPO

## Step 6: Run exports (`export_histories.py`, output in `csv/<group>/`)

| Group | Selection | Purpose |
|---|---|---|
| `pid_mamujoco` | regex `Velocity-v0_s[0-9]+_pid_` | PID at tight MAMuJoCo limits |
| `basic_mamujoco_tight` | regex `_lag(1e-05\|0.0001)_(0.2\|1.0\|5.0)_Safety` | basic-dual baselines |
| `smac_8m_old` | `ids_smac_8m_old.txt` | check beta ~0 under old update |
| `smac_training_cost` | `ids_smac_training_cost.txt` (`--skip-lag`) | training cost CA-MAMBA vs baselines |
| `smac_8m_new` | regex `_4.0_8m_s[123].*_feat-aamas` | the 15 new 8m runs (after jobs finish) |
| `macpo_mamujoco_tight` | regex `safepo_macpo_.*cost_limit=(0.2\|1.0\|5.0)_Safety` | MACPO at tight limits |
| `mappolag_mamujoco_tight` | regex `safepo_mappolag_.*cost_limit=(0.2\|1.0\|5.0)_Safety` | new MAPPO-Lag tight-limit |

Run from `docs/experiments/11-thesis-ablations/6-aamas-revision/`:
```bash
python export_histories.py --group <group> --regex "<regex>"
# or
python export_histories.py --group <group> --ids <ids_file>
```

## Extra: Paper table swap (not in Shperb's instructions)

- [x] Fixed `wandb_config.py` project name
- [x] Filled 37 empty d>0 rows in `safe_dreamers_runs_adapted.csv`
- [x] Verified multi-step table already had correct measured-cost values
- [x] Swapped paper input CSV, regenerated 3 tex tables, updated prose
- [x] Committed to thesis repo (`737e5a6`)

## Overall status

- [x] Step 1: cluster setup
- [x] Step 2: 15 SMAC jobs submitted
- [x] Step 3: 9 MAPPO-Lag jobs submitted
- [x] Step 4: verified (partial — queued arms not yet checked)
- [ ] Step 5: answer questions
- [ ] Step 6: run exports
- [ ] All jobs completed
