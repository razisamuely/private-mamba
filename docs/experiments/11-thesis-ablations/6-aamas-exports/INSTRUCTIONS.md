# AAMAS 2027 resubmission: runs and exports

Everything below is on the new branch **`feat/aamas-8m-ablation`**
(off `feat/pid-lagrangian`). It adds three flags, `--lag_init`, `--max_steps` and `--lag_signal`, plus a WandB export
script in `docs/experiments/11-thesis-ablations/6-aamas-exports/`. `notes.md` in that folder has
the details.

## Why

The SMAC casualty runs in the paper (Oct 2025 – Jan 2026) updated λ from `cost_returns.mean()`,
which is the imagined cost. The paper describes the measured-episode-cost update, which only
entered the code in April (`6c05450`, `1ef8faa`). We therefore want 8m with five multiplier
variants on the current code, including the old imagined input.

## 1. Update the cluster checkout

```bash
cd ~/workspace/private-mamba && git fetch && git checkout feat/aamas-8m-ablation && git pull
```

## 2. Launch 15 jobs

From your local machine, on the same branch. All runs are 8m, d=4, seeds 1–3, and each stops
itself at 105k steps. Submit in this order: the measured and PID jobs run first, then the
imagined-input jobs, then the fixed-λ jobs, queued under the 6-job limit.

```bash
# measured-cost basic multiplier
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --laglr 1e-5 --max_steps 105000
# PID multiplier
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --lag_mode pid --pid_kp 1.0 --pid_ki 1e-5 --pid_kd 1.0 --max_steps 105000
# imagined-cost input (the pre-April update, reproduced on the current code)
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --laglr 1e-5 --lag_signal imagined --max_steps 105000
# fixed penalty, lambda = 1
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --laglr 0 --lag_init 1.0 --max_steps 105000
# cost-blind, lambda = 0
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --laglr 0 --lag_init 0.0 --max_steps 105000
```

## 3. MAPPO-Lag at the tight MAMuJoCo limits (CPU, 9 jobs)

A reviewer asked for tight-limit comparisons against *all* baselines. MACPO already has
tight-limit runs, but MAPPO-Lag does not. These run on the CPU partition, so they don't compete
with the 8m GPU jobs.

From `Safe-Policy-Optimization-Modified` on the cluster, submit them exactly like Exp 8 Phase 6
(`template_mappolag_mamujoco.sbatch`, conda env `safepo`, 10M steps, 5 parallel envs), changing
only the cost limit. Use seeds 1–3 for each:

| Env | Cost limit |
|---|---|
| Safety2x4AntVelocity-v0 | 0.2 |
| Safety4x2AntVelocity-v0 | 1.0 |
| Safety2x3HalfCheetahVelocity-v0 | 5.0 |

At d=25 these took about 2 days to reach 10M. We need 1M for sure, and 10M if it finishes in time.

## 4. Checks

- About 5 minutes after each job starts:
  - episodes are progressing;
  - `Agent/Lagrangian` stays at exactly 1.0 and 0.0 in the two fixed-λ variants;
  - PID runs log `Lag/pid_*`.
- Record the Slurm job IDs in `notes.md`.
- The automatic stop at `--max_steps` is new and untested on the cluster. If a job is still RUNNING
  more than ~10 minutes after its WandB `steps` pass 105k, `scancel` it and let me know.

## 5. Quick facts from WandB and Slurm

1. In the old 8m d=4 runs (`..._cost_lim=4.0_8m_{23,2,3}_time_2025...`), does `Agent/Lagrangian`
   stay near 0 throughout? What range is `Lag/mean_cost` in?
2. How long (wall-clock) does an 8m run take to reach 100k steps?
3. Did the HalfCheetah 2×3 PID jobs (21631933–935) finish?
4. Compute numbers for the paper (a reviewer asked for wall-clock and memory). Please paste the
   output of:
   ```bash
   sacct -j 21631854,21631898,21631933,19583387 --format=JobID,JobName%45,Partition,Elapsed,MaxRSS,AllocTRES%45,State
   ```
   Also run it for one of the new 8m jobs once it finishes, and for one SMAC MAPPO-Lag job and one
   MACPO MAMuJoCo job (any seed).

## 6. Exports

Run these from `docs/experiments/11-thesis-ablations/6-aamas-exports/`. Output goes to `csv/<group>/`.

```bash
python export_histories.py --group pid_mamujoco --regex "Velocity-v0_s[0-9]+_pid_"
python export_histories.py --group basic_mamujoco_tight --regex "_lag(1e-05|0.0001)_(0.2|1.0|5.0)_Safety"
python export_histories.py --group smac_8m_old --ids ids_smac_8m_old.txt
python export_histories.py --group macpo_mamujoco_tight --regex "safepo_macpo_.*cost_limit=(0.2|1.0|5.0)_Safety" --skip-lag
python export_histories.py --group smac_training_cost --ids ids_smac_training_cost.txt --skip-lag
```

- The last command covers about 220 runs, so run it in the background.
- When the 15 jobs finish, run:
  ```bash
  python export_histories.py --group smac_8m_new --regex "_4.0_8m_s[123].*_feat-aamas"
  ```
- When the MAPPO-Lag tight-limit jobs pass 1M (and again when they finish), run:
  ```bash
  python export_histories.py --group mappolag_mamujoco_tight --regex "safepo_mappolag_.*cost_limit=(0.2|1.0|5.0)_Safety" --skip-lag
  ```
- Commit `csv/` to the branch and push after each batch.