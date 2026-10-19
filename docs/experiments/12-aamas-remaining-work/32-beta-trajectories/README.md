# #32 — Redraw the beta trajectories from the reported runs

Issue: https://github.com/razisamuely/private-mamba/issues/32
Plan section: §6 of `docs/planning/remaining_work_2026-10-15.pdf`

## Claim in the ticket

The beta-trajectory figures come from older runs than the ones the paper reports, so they
should be redrawn.

## How it was checked

There is no run manifest yet (#29), so the question is decided from the figure data itself.
`verify_beta_provenance.py` applies the paper's reading rule (mean over each run's episodes in
the last 5k interactions before the checkpoint, then mean and sample sd over runs) to the series
behind each figure and compares the result with the published cell. Agreeing to one decimal on
six numbers identifies the runs; the series and the table would otherwise have to match by
coincidence.

```bash
python docs/experiments/12-aamas-remaining-work/32-beta-trajectories/verify_beta_provenance.py
```

Run ids were also read off the figure configs:

| Figure | Source config | Run ids |
|---|---|---|
| MAMuJoCo beta | `docs/analysis/beta_dynamics/runs_config.json` | Ant2x4 `18362835/36/38`, Ant4x2 `18362839/40/41`, HC2x3 `18174008/09/10` |
| SMAC beta | `docs/experiments/11-thesis-ablations/3-safedreamer-smac-threshold/runs_config_smac.json` | MMM `17273374-76`, 1c3s5z `17261617-19`, 3m `17261629-31`, 2m_vs_1z `17261620-22`, 8m `17209123-25` |

The reported run ids come from `overleaf/thesis/data/ca_mamba_measured_100k.csv`, the CSV behind
`tab:full-results-aamas`:

| Map | Reported | Behind the figures | Same |
|---|---|---|---|
| MMM | 17273374-76 | 17273374-76 | yes |
| 1c3s5z | 17261617-19 | 17261617-19 | yes |
| 3m | 17261629-31 | 17261629-31 | yes |
| 2m_vs_1z | 17261620-22 | 17261620-22 | yes |
| 8m | 22316491 / 22316562 / 22314136 (Oct) | 17209123-125 (Apr) | **no** |

This is what the plan saw: `8m` at $d=0$ was rerun in October for the Table 2 ablation and the
exported beta series was never refreshed. It generalized to all the figures, but only `8m` moved.

The MAMuJoCo side was checked against the live source: `mamujoco_experiment8_phase5_full.csv` has
no overriding row for the $d=25$, 1M CA-MAMBA cells in `mamujoco_reruns_from_exports.csv`, and its
values are the ones `generated/mamujoco_main.tex` prints.

## Result

**The claim does not hold for any figure. No beta figure needs redrawing.**

MAMuJoCo — reconstructing cost at 1M from the figure series returns the published cell:

| Task | From the figure series | Published | Verdict |
|---|---|---|---|
| HalfCheetah 2x3 | 16.61 +- 2.01 | 16.6 +- 2.0 | match |
| Ant 2x4 | 17.40 +- 15.10 | 17.4 +- 15.1 | match |
| Ant 4x2 | 0.70 +- 0.99 (2 seeds) | 0.5 +- 0.8 | consistent, see below |

SMAC — every quoted endpoint reproduces from its own series:

| Map | From the series | Quoted | Verdict |
|---|---|---|---|
| MMM | 0.5039 | 0.50 | match |
| 1c3s5z | 0.3022 | 0.30 | match |
| 3m | 0.1279 | 0.13 | match |
| 2m_vs_1z | 0.0250 | 0.025 | match |
| 8m | 0.5054 | 0.54 | differs |

## The two real findings

**1. `data/smac_beta/8m_s*.csv` is stale, but nothing is plotted from it.**
The appendix's `8m` value of `0.54` is correct: the reported runs `22314136`, `22316491`,
`22316562` end at beta `0.5533`, `0.5218`, `0.5526`, mean `0.5426`. The CSVs in
`overleaf/thesis/data/smac_beta/8m_s*.csv` are the April runs `17209123-125`, which the paper
does not report and which would give `0.51`. The plotted SMAC beta figures are MMM and 1c3s5z,
so the wrong file never reaches a figure — it is a trap for whoever regenerates next, not a
published error.

No fix is possible by re-export: the reported `8m` runs are Shahaf's offline runs
(`local:camamba/runs/d0measured_8m_d0.0_s1_22316491`, under `/home/shperbsh/camamba`, which is
permission-denied), so only endpoints exist, in `data/local_runs_endpoints.csv`. There is no
time series to plot.

**2. The Ant 4x2 band near 1M rests on 2 seeds.**
`docs/analysis/beta_dynamics/data/ant4x2_s2.csv` stops at step 921335 (4686 rows) while seeds 1
and 3 run to about 5M. The two seeds that do reach 1M give 1.4 and 0.0, consistent with the
published 0.5 +- 0.8 over 3 seeds, so the table is fine; the figure's shaded band is thinner
than it looks past 921k.

## Actions

| Action | Where | Status |
|---|---|---|
| Delete `smac_beta/8m_s*.csv` | thesis `069c252` | done |
| Note the Ant 4x2 seed-2 truncation in the figure caption | `overleaf/thesis/appendix.tex` | batched into #20 |
| Feed the run ids above into the manifest | #29 | pending |

The `8m` deletion means `check_smac` in the script can no longer recompute the `0.51`; it was run
before the deletion, and the April runs `17209123-125` are still on W&B if it has to be repeated.

## Status

| Step | State |
|---|---|
| Provenance decided | done — every figure uses the reported runs |
| Redraw needed | no |
| Stale 8m CSV deleted | done |
| Ant 4x2 caption note | batched into #20 |
| Run ids handed to #29 | pending |

Ticket closed 2026-10-19.
