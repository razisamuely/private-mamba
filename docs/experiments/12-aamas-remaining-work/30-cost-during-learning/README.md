# #30 — Cost paid during learning (cumulative excess)

## Question

The thesis reports cost at the checkpoint, i.e. the cost of the *final* policy.
It says nothing about what was paid on the way there. For each run, at the
method's own checkpoint step K:

- **E_K** = cumulative excess = sum over episodes of `max(0, C_e - d)`
- **V_K** = number of violating episodes (`C_e > d`)

## Runs

36 runs, no new training — all from existing logs. 12 configs x 3 methods,
seed 1 only:

| benchmark | configs | limits | checkpoint |
|---|---|---|---|
| SMAC | 3m, 8m, bane_vs_bane | d=0 and the map's loose limit | 100k |
| MAMuJoCo | HC2x3, Ant2x4, Ant4x2 | tight and d=25 | 1M |

Same representative subset as #31, and the same runs: selection is pinned to
the manifest rows that back the reported tables (`aamas_main_results`,
`smac_mappolag`, `mamujoco_main`/`mamujoco_tight`) with `variant` empty and
the default lagrangian lr.

## Headline: raw E_K is not comparable across methods

CA-MAMBA logs **one row per episode**. The baselines log a **mean every 10k
steps**, so one baseline row stands for ~10 episodes but contributes a single
value. Over the same 100k steps CA-MAMBA produces ~4800 rows and the
baselines 20-30.

Raw E_K therefore measures logging granularity, not safety, and dividing by
steps does not fix it — the baseline rows are already averages. The sound
comparison is **per-episode**: mean excess per episode, and % of episodes
violating. Both are rates, so they are invariant to how often a method logs.

Raw `E_K`, `V_K` and `episodes` are kept in `excess.csv` for provenance only.

## Results — excess per episode / % episodes violating

### SMAC (at 100k steps)

| map | d | CA-MAMBA | MACPO | MAPPO-Lag |
|---|---|---|---|---|
| 3m | 0 | **0.66** / 40% | 3.00 / 100% | 3.00 / 100% |
| 3m | 1 | **0.42** / 25% | 2.00 / 100% | 2.00 / 100% |
| 8m | 0 | **3.36** / 91% | 8.00 / 100% | 8.00 / 100% |
| 8m | 4 | **1.48** / 50% | 4.00 / 100% | 4.00 / 100% |
| bane_vs_bane | 0 | **19.65** / 100% | 22.51 / 100% | 22.11 / 100% |
| bane_vs_bane | 4 | **4.49** / 58% | 18.52 / 100% | 18.22 / 100% |

CA-MAMBA pays less per episode in **all 6 cells**, and is the only method
whose violation rate ever drops below 100%. The baselines violate on every
logged episode at every limit.

### MAMuJoCo (at 1M steps)

| env | d | CA-MAMBA | MACPO | MAPPO-Lag |
|---|---|---|---|---|
| HC2x3 | 5 | 6.96 / 37% | **0.00** / 0% | **0.00** / 0% |
| HC2x3 | 25 | 19.79 / 21% | **0.00** / 0% | **0.00** / 0% |
| Ant2x4 | 0.2 | 18.31 / 54% | 0.195 / 61% | **0.055** / 22.5% |
| Ant2x4 | 25 | 0.00 / 0% | 0.00 / 0% | 0.00 / 0% |
| Ant4x2 | 1 | **0.040** / 2% | 0.042 / 13% | 0.026 / 5% |
| Ant4x2 | 25 | 0.00 / 0% | 0.00 / 0% | 0.00 / 0% |

MAMuJoCo does **not** favour CA-MAMBA, and the HC column must not be read as
a safety result. The baselines pay zero velocity cost there because they
never learn to move: at d=5 CA-MAMBA's reward at 1M is **1519** against
MACPO's **143**. A policy that stands still is trivially under any velocity
limit. Ant4x2 d=1 is the one cell where the methods are actually comparable
in reward, and there CA-MAMBA has the lowest violation rate (2% vs 13% and
5%).

At d=25 the limit is loose enough that nobody violates, so those rows carry
no information.

## Honest reading

On SMAC, CA-MAMBA is cheaper during learning as well as at the checkpoint —
the strongest version of the claim. On MAMuJoCo it is not, and the headline
gap on HalfCheetah is a reward/cost tradeoff rather than a safety failure of
the baselines. Report both, and report the reward alongside the HC cost or
the table is misleading.

Single seed per cell, so these are indicative, not tested. Nothing here is
pooled across seeds and no number feeds a thesis table yet.

## Data

- `excess.csv` — 36 rows. `excess_per_episode` and `V_K_pct` are the
  comparable columns; `E_K`, `V_K`, `episodes` are raw provenance.
- `compute_excess.py` — regenerates it. Reads local episode exports under
  `11-thesis-ablations/6-aamas-revision/csv/` where present, else streams
  W&B `scan_history` and breaks at the checkpoint.

## Gotchas found here

- Matching a manifest run by name **prefix** is unsafe: the CA-MAMBA SMAC
  names agree on their first ~50 characters and differ only in the map, so a
  loose match silently returns one map's data for every map.
- A cell has up to 10 seed-1 manifest rows because every ablation lives
  there too. Filtering on method/config/limit/seed alone picked the fixed-beta
  run for HC d=25 and reported an excess of 604957 instead of 19792. Always
  filter on the reported-table tag plus `variant`/`laglr`.
- `run.history(samples=N)` downsamples over the run's whole length. Several
  runs continued far past the checkpoint (HC d=25 reaches 33M steps / 1.5M
  rows), so only ~293 sampled rows fell under 1M and the cumulative sum came
  out 3x too low. Use `scan_history` with an early break instead.

## Status

Data done. Appendix table pending under #40, together with #31's compute
table — both are "cost of training" evidence and belong in the same place.
