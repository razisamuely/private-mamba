# #31 — Wall-clock compute from W&B timestamps

## Method

Each run logs `_timestamp` per row in W&B. Wall-clock = timestamp at the
method's checkpoint step minus the first row's timestamp. One seed per config.

Checkpoints (each method's own, as reported in the thesis tables):
- **CA-MAMBA SMAC**: 100k steps
- **MACPO SMAC**: 5M steps (the thesis compares baselines at 1M and 5M)
- **Both on MAMuJoCo**: 1M steps

Fetched via `run.history(samples=2000)` — W&B downsamples server-side. For SMAC
runs with dense logging this is exact to within one 5k-step bin.

## Results

### SMAC (CA-MAMBA 100k, baselines 5M)

| map | d | CA-MAMBA (100k) | MACPO (5M) | MAPPO-Lag (5M) |
|---|---|---|---|---|
| 3m | 0 | 21.3h | 5.4h | 18.4h |
| 3m | 1 | 43.8h | 8.7h | 18.8h |
| 8m | 0 | 12.6h | 20.5h | 40.2h |
| 8m | 4 | 16.5h | 12.0h | 41.9h |
| bane | 0 | 4.8h | 42.4h | 167.8h* |
| bane | 4 | 22.8h | 43.2h | 80.8h |

*bane d=0 MAPPO-Lag hit walltime at 4.52M steps (168h = 7 days).

CA-MAMBA's world model makes it slower per step (~1 step/sec on 3m vs MACPO's
~260 steps/sec), but it trains at 50× fewer steps. On large maps (bane_vs_bane),
CA-MAMBA at 100k is cheaper than both baselines at 5M.

### MAMuJoCo (both at 1M)

| env | d | CA-MAMBA | MACPO |
|---|---|---|---|
| HC | 5 | 3.9h | 1.2h |
| HC | 25 | 4.2h | 1.0h |
| Ant2x4 | 0.2 | 5.1h | 1.2h |
| Ant2x4 | 25 | 4.0h | 0.8h |
| Ant4x2 | 1 | 4.1h | 1.3h |
| Ant4x2 | 25 | 6.5h | 1.4h |

CA-MAMBA is 3–5× slower at the same step count on MAMuJoCo.

## Part 2: time for MACPO to reach CA-MAMBA's 100k winrate

For each of the 24 SMAC configs, CA-MAMBA's mean winrate at 100k is the target.
MACPO's learning curve (smoothed over 20 rows) is scanned for the first point
that matches. MACPO ran to 10M steps.

### MACPO

**Catches up on 8 of 24, never on 16.** On most of those its max winrate stays
at 0.000 (never wins a single battle through 10M steps).

Where it catches up:

| config | d | CA-MAMBA win | MACPO step | MACPO hours |
|---|---|---|---|---|
| 2m_vs_1z | 0 | 0.948 | 4.86M | 3.8h |
| 2m_vs_1z | 1 | 0.950 | 1.75M | 1.0h |
| 2s3z | 4 | 0.630 | 2.79M | 4.8h |
| 2s_vs_1sc | 1 | 0.920 | 2.52M | 2.2h |
| 3m | 1 | 0.956 | 2.41M | 4.2h |
| 3s5z_vs_3s6z | 0 | 0.000 | 25k | 0.1h |
| 3s_vs_3z | 1 | 0.951 | 5.51M | 8.0h |
| bane_vs_bane | 0 | 0.702 | 25k | 0.2h |
| bane_vs_bane | 4 | 0.979 | 2.75M | 23.5h |

Never catches up (max winrate): 1c3s5z d=0 (0.000), 1c3s5z d=4 (0.000),
2s3z d=0 (0.000), 2s_vs_1sc d=0 (0.003), 3m d=0 (0.001),
3s5z_vs_3s6z d=4 (0.000), 3s_vs_3z d=0 (0.000), 3s_vs_4z d=0 (0.000),
3s_vs_4z d=1 (0.000), 3s_vs_5z d=0 (0.000), 3s_vs_5z d=1 (0.000),
8m d=0 (0.000), 8m d=4 (0.000), MMM d=0 (0.000), MMM d=4 (0.000).

### MAPPO-Lag

**Catches up on 19 of 24, never on 5.** Much stronger than MACPO — matches
CA-MAMBA on most maps but needs 0.5M–3M steps (1–20h).

Where it catches up:

| config | d | CA-MAMBA win | MAPPO-Lag step | MAPPO-Lag hours |
|---|---|---|---|---|
| 1c3s5z | 0 | 0.820 | 755k | 3.8h |
| 1c3s5z | 4 | 0.790 | 615k | 7.2h |
| 2m_vs_1z | 0 | 0.948 | 450k | 1.6h |
| 2m_vs_1z | 1 | 0.950 | 345k | 1.3h |
| 2s3z | 0 | 0.767 | 770k | 6.6h |
| 2s3z | 4 | 0.630 | 775k | 6.3h |
| 2s_vs_1sc | 0 | 0.962 | 545k | 3.8h |
| 2s_vs_1sc | 1 | 0.920 | 620k | 5.0h |
| 3m | 0 | 0.966 | 780k | 5.0h |
| 3m | 1 | 0.956 | 530k | 4.2h |
| 3s5z_vs_3s6z | 0 | 0.000 | 25k | 0.2h |
| 3s_vs_3z | 0 | 0.956 | 1.79M | 6.8h |
| 3s_vs_3z | 1 | 0.951 | 2.05M | 6.7h |
| 8m | 0 | 0.947 | 1.74M | 12.8h |
| 8m | 4 | 0.754 | 980k | 7.7h |
| MMM | 0 | 0.595 | 3.06M | 16.2h |
| MMM | 4 | 0.550 | 3.10M | 20.0h |
| bane_vs_bane | 0 | 0.702 | 25k | 0.7h |
| bane_vs_bane | 4 | 0.979 | 1.38M | 19.3h |

Never catches up (max winrate): 3s5z_vs_3s6z d=4 (0.000),
3s_vs_4z d=0 (0.002), 3s_vs_4z d=1 (0.000),
3s_vs_5z d=0 (0.000), 3s_vs_5z d=1 (0.000).

## What's missing

- **Peak memory**: needs `sacct` on the cluster; old jobs may be purged.

## Data

- `wall_clock.csv` — 30 rows (12 CA-MAMBA, 6 MACPO SMAC, 6 MACPO MAMuJoCo, 6 MAPPO-Lag SMAC).
- `catchup.csv` — 24 rows, when (if ever) MACPO matches CA-MAMBA's 100k winrate.
- `catchup_mappolag.csv` — 24 rows, same for MAPPO-Lag.

## Status

Part 1 (wall-clock) and part 2 (catch-up) done for both baselines on all 24
SMAC configs. Peak memory not started.
