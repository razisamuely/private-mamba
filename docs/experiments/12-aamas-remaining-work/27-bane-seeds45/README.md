# #27 — bane_vs_bane: add 2 seeds at each of its two limits

## Problem

`bane_vs_bane` at `d=0` ended at win rates **0.19, 0.68, 0.97** — a spread so wide that
the mean of three runs says almost nothing.  The ticket asked for two more seeds at both
limits the map is reported at.

Per the plan's ground rules, new runs only where a result is weak: `d=0` and `d=4` of this
one map got seeds 4 and 5, nothing else changed.

## The 4 runs

Submitted 2026-11-01 on commit `8cd306a`, branch `feat-aamas`, 100k interactions, all
COMPLETED.

| `d` | seed | Slurm | W&B run |
|---|---|---|---|
| 0 | 4 | 23745730 | `..._0.0_bane_vs_bane_s4_date11-01-hr17-15-57_23745730_feat-aamas` |
| 0 | 5 | 23745731 | `..._0.0_bane_vs_bane_s5_date11-01-hr18-27-39_23745731_feat-aamas` |
| 4 | 4 | 23745733 | `..._4.0_bane_vs_bane_s4_date11-01-hr18-51-03_23745733_feat-aamas` |
| 4 | 5 | 23745734 | `..._4.0_bane_vs_bane_s5_date11-02-hr01-18-04_23745734_feat-aamas` |

`23745734` has **two** W&B runs: `date11-01-hr19-08-22` was preempted after 705
interactions and restarted as `date11-02-hr01-18-04`, which is the one that counts.
Both exports are kept here as provenance; only the second was copied into the group
folder, and it would be dropped anyway by that group's existing
`min_max_step = S - WINDOW`.

## Validating the reading rule before pooling

The four new runs only mean something next to the three already published, so
`endpoints27.py` first **re-derives the published seeds 1-3 from their own W&B exports**
and diffs them against `data/ca_mamba_measured_100k.csv`.  All six published rows
(2 limits x 3 seeds) reproduce to three decimals, so the same rule applied to seeds 4 and
5 gives one sample and pooling is legitimate.  Had any row differed, the five runs would
not have been one sample and nothing should have been pooled.

## Extraction

Same route as #21 and #26 (these runs have no `metrics.jsonl`, only W&B):

1. `docs/experiments/11-thesis-ablations/6-aamas-revision/export_histories.py`
   `--group bane_issue27 --regex "_(23745730|23745731|23745733|23745734)_feat-aamas"`
2. `endpoints27.py` applies the reading rule — mean over episode rows with
   `S-5000 <= steps <= S`, `S = 1e5` — into `rerun_endpoints.csv`

Then each run was filed where its row is defined to look.  `ca_mamba_measured_100k.csv`
is **generated** by `analyze_exports.py --measured-only` and verified on every other run,
so the four rows could not simply be appended: the four surviving exports were copied
into `csv/smac_measured_aprmay/` (the group's folder, exactly as #26 did for
`smac_8m_d0_ablation`) and the CSV was then regenerated.  The regenerated rows matched
the hand-computed ones digit for digit.

One note had to go: the preemption of `23745734` was written into that row's `notes`
column, but `notes` is derived (it is `fallback` or empty), so a hand-written value makes
the file fail its own check.  The preemption is recorded here instead.

## Thesis-repo changes

Both are per-configuration widenings of an existing idiom, not new machinery; neither
could be done by widening `EXPECTED_SEEDS`, which the AAAI and AAMAS generators assert
exact equality against.

**`scripts/analyze_exports.py`** — `GroupSpec.seeds` (added by #26) is group-wide, but
`smac_measured_aprmay` spans twelve maps, so allowing seeds 4-5 group-wide would have let
a stray seed-4 run of any map in.  Added `GroupSpec.extra_seeds`, a
`(env, d) -> frozenset[int]` map read through `GroupSpec.seeds_of(env, d)`, with
`SMAC_MEASURED_EXTRA_SEEDS` naming only `bane_vs_bane` at `d=0` and `d=4`.  Also a third
display-name pattern for the group (the reruns are on `feat-aamas`, not
`feat-lag-real-episod`) and a `NON_RUN_FOLDERS` entry for `bane_issue27`.

**`scripts/generate_aamas_tables.py`** — `MEASURED_EXTRA_SEEDS`, mirroring the existing
`CA_TWO_SEED_CONFIGS` idiom (per-config seed deviation), gates `load_measured_ca_100k`;
`_seed_clause` now takes per-config counts and delegates to a new `_extra_seed_phrase`
shared with the hardcoded `smac_macpo` caption, so all four captions derive their own
run-count phrase and are byte-stable where nothing deviates.

**`scripts/plot_smac_curves.py`** — the repo asserts by test that the figure's 100k point
equals the printed table cell, so the figure had to take the two new `d=0` runs too.
`SEEDS` became per-map `MAP_SEEDS`, derived from the table generator's
`MEASURED_EXTRA_SEEDS` so the figure cannot plot a different sample than the table it
must equal.  `--extract` grew `--maps`, because `8m`'s local logs live in neither
repository and a one-map re-extraction must keep the stored rows of the others.

## Result

`comparison.txt` (regenerate with `compare27.py`):

```
--- d=0 ---
  seeds 1-3 (reported)   n=3  score 17.751+-2.824  cost 13.909+-7.112  win  0.616+-0.394
  seeds 4-5 (new)        n=2  score 19.096+-0.038  cost 10.342+-2.141  win  0.831+-0.007
  seeds 1-5 (pooled)     n=5  score 18.289+-2.128  cost 12.482+-5.500  win  0.702+-0.302
  per-run winrate: s1=0.194, s2=0.681, s3=0.972, s4=0.836, s5=0.826

--- d=4 ---
  seeds 1-3 (reported)   n=3  score 19.906+-0.114  cost  6.365+-1.202  win  0.982+-0.017
  seeds 4-5 (new)        n=2  score 19.787+-0.297  cost  6.284+-1.759  win  0.973+-0.034
  seeds 1-5 (pooled)     n=5  score 19.858+-0.181  cost  6.333+-1.224  win  0.979+-0.021
  per-run winrate: s1=0.997, s2=0.964, s3=0.985, s4=0.997, s5=0.949
```

**The fragile cell improves and tightens; nothing flips.**  At `d=0` win rate goes
0.62+-0.39 -> 0.70+-0.30 and cost 13.91+-7.11 -> 12.48+-5.50.  Both new runs landed at
0.836 and 0.826, close to each other and to seed 2, which makes **seed 1 (0.194) the
outlier** rather than the three runs being evenly spread.  `d=4` barely moves
(0.98 -> 0.98, cost 6.37 -> 6.33) — that cell was never weak.

Every count the text derives from these tables was re-checked by regenerating, not by
hand: 23/24 lower cost and 22/24 higher win rate than both baselines at 100k, feasible
5/24, win >= 0.9 10/24, dual-input 15/24 and 14/24, imagined/measured feasible 4 vs 5.
All unchanged, so the sign tests at `05_experiments.tex:55-62` (`p=0.003`, `p=0.02`)
stand untouched.

### Edits downstream of the numbers

| file | change |
|---|---|
| `data/ca_mamba_measured_100k.csv` | 71 -> 75 rows (backup `.bak-20261107`) |
| `data/smac_curves_ca_mamba.csv` | 240 -> 280 rows (backup `.bak-20261107`) |
| `figures/smac_curves.pdf` | redrawn; the `bane_vs_bane` band is now over five runs |
| `generated/aamas_full_results.tex` + 4 more | the two `bane_vs_bane` rows, `n` 3 -> 5, four captions |
| `chapters/05_experiments.tex:148` | `6.37` -> `6.33`, the one inline copy |
| `tests/test_analyze_exports.py` | a per-configuration seed test; `name_measured` grew a November form |
| `tests/test_plot_smac_curves.py` | pinned `bane_vs_bane` 13.91/0.62 -> 12.48/0.70; seed count per map |
| `data/run_manifest.csv` | rebuilt, 530 -> 534 rows |

`05_experiments.tex:57-58` was deliberately left alone: "on `bane_vs_bane` at `d=0`
CA-MAMBA trades win rate for far lower cost" is still true (win 0.70 vs MAPPO-Lag 0.888
and MACPO 0.79; cost 12.48 vs 21.36 and 22.55).

Test suite: back to the same 9 pre-existing failures as before the change (2 are a
missing `pymupdf`, 7 are Shahaf's open asks), with 6 more tests passing.
`check_run_manifest.py` is clean apart from the pre-existing `generated/parity_start`
coverage FAIL, which belongs to #24.

## Status

Done.  The tables and the figure both moved, because the repo enforces their equality at
100k by test.

## Files

| file | what |
|---|---|
| `rerun_endpoints.csv` | endpoints of the 4 new runs (limit, seed, slurm, n_episodes, score, cost, winrate) |
| `endpoints27.py` | re-derives the published seeds 1-3 from W&B, then adds 4-5 by the same rule |
| `compare27.py` | 3 seeds vs 5, read from the CSV the tables read |
| `comparison.txt` | its output |

Raw W&B exports:
`docs/experiments/11-thesis-ablations/6-aamas-revision/csv/bane_issue27/`
(untracked), with the four surviving runs also copied into `csv/smac_measured_aprmay/`.

---

Parent epic: #42.
