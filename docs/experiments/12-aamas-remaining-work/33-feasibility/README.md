# #33 — Feasibility against interaction budget (SMAC)

## Question

Of the 12 SMAC maps with a nonzero cost limit, how many does each method
*meet* at each interaction budget? A method meets a limit when its mean
episode cost across seeds is at most d.

§5.3 already states four of these counts in prose, with no script or CSV
behind them. This ticket verifies them and fills in the rest of the grid.

No new training. Every number comes from the CSVs that already back the
thesis tables.

## Result

| method | 100k | 500k | 1M | 2M | 5M |
|---|---|---|---|---|---|
| CA-MAMBA | **5/12** | – | – | – | – |
| MACPO | 0/12 | – | – | – | 5/12 |
| MAPPO-Lag | 0/12 | 3/12 | 5/12 | 7/12 | 8/12 |

`–` is "not run at that budget", not a zero: CA-MAMBA was never run past 100k
on SMAC and MACPO has no 1M export. Those cells are left empty rather than
extrapolated.

The four counts §5.3 asserts all reproduce exactly: CA-MAMBA 5 at 100k,
MAPPO-Lag 5 at 1M, MACPO 5 at 5M, MAPPO-Lag 8 at 5M.

## What the empty-by-prose cells add

At the **matched** 100k budget both baselines meet **0 of 12** while CA-MAMBA
meets 5. The prose never says this, and it is the cleanest statement of the
result: MAPPO-Lag needs ~1M interactions (10x) merely to draw level, MACPO
needs 5M (50x) to draw level, and only MAPPO-Lag ever overtakes, at 5M with
8/12.

The intermediate MAPPO-Lag budgets show the curve rather than two endpoints:
0 -> 3 -> 5 -> 7 -> 8 over 100k -> 500k -> 1M -> 2M -> 5M.

## Per-map detail

Mean cost; `*` marks the limit met.

| map | d | CA-MAMBA 100k | MACPO 5M | MAPPO-Lag 1M | MAPPO-Lag 5M |
|---|---|---|---|---|---|
| 1c3s5z | 4 | 4.83 | 9.00 | 2.08* | 0.37* |
| 2m_vs_1z | 1 | 0.14* | 0.00* | 0.01* | 0.00* |
| 2s3z | 4 | 2.98* | 1.94* | 2.26* | 0.18* |
| 2s_vs_1sc | 1 | 0.31* | 0.16* | 0.18* | 0.10* |
| 3m | 1 | 0.60* | 0.27* | 0.05* | 0.02* |
| 3s5z_vs_3s6z | 4 | 7.54 | 8.00 | 8.08 | 8.00 |
| 3s_vs_3z | 1 | 0.92* | 0.82* | 3.01 | 0.01* |
| 3s_vs_4z | 1 | 2.47 | 3.00 | 3.02 | 3.00 |
| 3s_vs_5z | 1 | 2.67 | 3.00 | 3.02 | 3.00 |
| 8m | 4 | 4.50 | 8.00 | 5.96 | 1.10* |
| MMM | 4 | 7.88 | 10.00 | 10.11 | 1.41* |
| bane_vs_bane | 4 | 6.33 | 11.80 | 9.13 | 5.22 |

Observations worth keeping:

- The 5 that CA-MAMBA meets are exactly the 5 MACPO meets at 5M.
- MAPPO-Lag's 8 at 5M are CA-MAMBA's 5 plus `1c3s5z`, `8m` and `MMM`.
- Nobody meets `3s5z_vs_3s6z`, `3s_vs_4z`, `3s_vs_5z` or `bane_vs_bane` at
  any budget. On the three `3s_vs_*` maps every baseline sits at exactly 3.00
  = all three allies lost, i.e. it never survives.
- `8m` d=4 is the near miss: CA-MAMBA 4.50 against d=4 (see #28, where
  pooling six runs moved it 5.03 -> 4.50 without flipping it).

## Caveat carried to #37

MAPPO-Lag's `MMM` cost reads **10.11** at 1M on a map with ten allied units,
so its cost accounting admits values above the unit count. That is already
#37's second bullet. It does not change any count here (10.11 and a corrected
value below 10 both miss d=4), but the number should not be quoted as-is.

## Data

- `feasibility.csv` — 96 rows, one per (method, budget, map): `n_seeds`,
  `mean_cost`, `met`.
- `feasibility.py` — regenerates it. `--csv PATH` writes the rows; stdout is
  the summary grid.

Sources, all under the thesis repo's `data/`:

| method | budgets | file |
|---|---|---|
| CA-MAMBA | 100k | `ca_mamba_measured_100k.csv` |
| MACPO | 100k, 5M | `new_experiments_tracking{_100k,}.csv`, `algorithm == SafePO`, filtered on `metric_step` |
| MAPPO-Lag | 100k–5M | `mappolag_smac_per_seed_<budget>.csv` |

Gotcha: the two tracking CSVs hold **MACPO only** — MAPPO-Lag has its own
per-seed exports — and the budget lives in `metric_step`, not the filename,
so `new_experiments_tracking.csv` mixes 200k, 500k and 5M rows.

Seed counts are uneven and are recorded per row: mostly 3, but 6 for
CA-MAMBA and MACPO at 100k on `8m` (#28's pooling).

## Status

Done. Appendix/§5.3 table pending under #40, with #30's and #31's.
