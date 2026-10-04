# Addendum: export the April–May 2026 SMAC runs (main table)

Thanks for the answers. We're switching the paper's main SMAC table to the April–May 2026 runs
(`feat/lag-real-episode-cost`, measured-cost multiplier). The Oct 2025 runs become the comparison
with the imagined-cost input on all 24 configurations.

Per-seed 100k values for the May runs (d=1 and d=4) aren't in git: they exist only in WandB. Both
`safe_dreamers_runs_adapted.csv` and `docs/results/safe_dreamers_runs_lag_real_episode_cost.csv` have
empty score/cost/winrate for those 40 rows. So we need the run histories.

## 1. Export (from `docs/experiments/11-thesis-ablations/6-aamas-exports/`)

```bash
python export_histories.py --group smac_measured_aprmay --ids ids_smac_measured_aprmay.txt
```

The id list (71 runs) comes from `docs/tmp/extraction/inputs/safe_dreamers_runs_adapted.csv`. Keep
the multiplier columns (no `--skip-lag`). Commit `csv/` and push.

## 2. Gaps to fill (please add the missing run ids to the id list and re-export)

- `3s_vs_3z`, d=1: the seed-1 row points to the seed-2 run
  (`..._1.0_3s_vs_3z_s2_date05-05-hr11-00-59_17336253_...`). Which run is seed 1?
- `bane_vs_bane`, d=0, seed 3 (`..._17289848_...`): no metrics anywhere. Did it reach 100k?
- Any configuration with fewer than 3 seeds that reached 100k.

We use the same reading rule as the paper (mean over episodes with steps in [95k, 100k]); we
compute it from the exported histories.

## 3. One rerun: 8m, d=0, measured-cost multiplier (3 jobs, ~100k steps each)

The three 8m d=0 runs in the list (`17209123`–`17209125`, 26 April) were launched with
`cost_priority=0.15` according to `6-lag-real-episode-cost/runs.md`. No other main-table run uses
cost-prioritized replay, so we drop them. Please rerun on `feat/aamas-8m-ablation` (the default
`--lag_signal` is `measured`; there is no cost priority on this branch):

```bash
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 0.0 --seeds 1 2 3 --laglr 1e-5 --max_steps 105000
```

Export when done:

```bash
python export_histories.py --group smac_8m_d0_rerun --regex "_0.0_8m_s[123].*_feat-aamas"
```

Question: did any *other* run in `ids_smac_measured_aprmay.txt` use `--cost_priority` > 0? (We
also dropped the 26 April MMM and 3s_vs_5z batches, which were duplicates of later runs.)

## 4. Export the SMAC no-communication runs (Exp 9)

Six runs on `fix/comm-mask-inversion`: 8m and MMM, d=0, seeds 1–3 (Slurm 19539781/783/784 and
19539785/786/787), names ending in `_nocomm`:

```bash
python export_histories.py --group smac_nocomm --regex "starcraft.*_(8m|MMM)_s[123]_nocomm"
```

## 5. One more 8m arm: fixed penalty λ = 5 (3 jobs)

The fixed λ = 1 arm weights normalized cost and reward equally. A reviewer will ask whether
weighting cost *above* reward reaches the limit, which separates "the multiplier is too slow" from
"the model cannot rank actions by cost". Same branch, same settings as the other d=4 arms:

```bash
python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --laglr 0 --lag_init 5.0 --max_steps 105000
```

Check: `Agent/Lagrangian` stays at exactly 5.0. The run names end in `_init5.0`, so the
`smac_8m_new` export regex in `INSTRUCTIONS.md` already picks them up.

## 6. Queue order and one timing number

That makes 21 GPU jobs (15 + 3 + 3) under the 6-job limit. If they don't all fit, this order keeps
the main claims safe:

1. measured-cost and PID at d=4 (`INSTRUCTIONS.md` §2, first two commands)
2. the 8m d=0 rerun (§3 above)
3. imagined-input at d=4
4. fixed λ = 5 (§5 above)
5. fixed λ = 1
6. cost-blind λ = 0

Please send us one number as soon as you have it: the wall-clock time for the first 8m job to reach
20k steps. We'll use it to decide whether the last arms will make the deadline (paper due 8 Oct AoE).
