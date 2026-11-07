# #26 — Add seeds 4 and 5 to Table 2's Imagined and Measured rows

## Problem

Table 2 (`generated/mechanism_8m.tex`, SMAC `8m` at `d=0`) compares five ways of
setting the price: Imagined, Measured, PID, `beta=1`, `beta=0`.  Its headline claim is
that the *imagined* cost signal under-prices the constraint relative to the *measured*
one.  That rested on three runs per row, and the two cost gaps it turns on (cost and
beta between those two rows) are small enough that three runs is thin evidence.

Per the plan's ground rules, new runs only where a result is weak: the two learned
rules got seeds 4 and 5, nothing else changed.

## The 4 runs

Submitted 2026-11-01 on commit `8cd306a`, branch `feat-aamas`, SMAC `8m`, `d=0`,
100k interactions, all COMPLETED.

| row | flags | seed | Slurm |
|---|---|---|---|
| Imagined | `--lag_signal imagined` | 4 | 23745574 |
| Imagined | `--lag_signal imagined` | 5 | 23745575 |
| Measured | (default) | 4 | 23745577 |
| Measured | (default) | 5 | 23745578 |

`23745575` has **two** W&B runs: `date11-01-hr15-50-28` stopped before 95k
interactions and was restarted as `date11-01-hr19-11-56`, which is the run that
counts.  Both exports are kept here as provenance; only the second is in the group
folder the table reads.

## Extraction

Same route as #21 (these runs have no `metrics.jsonl`, only W&B):

1. `docs/experiments/11-thesis-ablations/6-aamas-revision/export_histories.py`
   `--group smac_8m_d0_seeds45 --regex "_(23745574|23745575|23745577|23745578)_feat-aamas"`
2. `endpoints26.py` applies the reading rule — mean over episode rows with
   `S-5000 <= steps <= S`, `S = 1e5` — into `rerun_endpoints.csv`

Then each run was filed where its row is defined to look:

- the two **Imagined** exports were copied into `csv/smac_8m_d0_ablation/`, the group
  `analyze_exports.py` reads for that row
- the two **Measured** endpoints were appended to
  `overleaf/thesis/data/local_runs_endpoints.csv` under tag `d0measured`
  (backup: `local_runs_endpoints.csv.bak-20261107`)

## Generator change (thesis repo)

`EXPECTED_SEEDS` is shared by the AAAI and AAMAS generators, which assert exact
equality against it, so it could not be widened.  Instead the seed set became a
property of the group:

- `GroupSpec.seeds: frozenset[int] = EXPECTED_SEEDS`, with `smac_8m_d0_ablation`
  overriding it to `SMAC_8M_D0_SEEDS = EXPECTED_SEEDS | {4, 5}`; `parse_name` and
  `identify_run` gate on `spec.seeds`
- that group also got `min_max_step=SMAC_TARGET - WINDOW`, an existing `GroupSpec`
  idiom, so the aborted attempt is dropped with a warning rather than by name
- `_estimate_cell`'s `assert estimate.n in (2, EXPECTED_SEED_COUNT)` became
  `assert estimate.n >= 2`
- the caption's run-count phrase is now derived by `_mechanism_runs_text` instead of
  the hardcoded "three runs (seeds 1--3)"; with uniform seeds its output is
  byte-identical to before
- three export folders this script never reads were declared in `NON_RUN_FOLDERS`
  (`smac_8m_d0_seeds45`, `hc_issue21`, `parity_start_smac`)

## Result

`comparison.txt` (regenerate with `compare26.py`):

```
--- imagined ---
  seeds 1-3 (reported)   n=3  cost 2.49+-0.43  win 0.95+-0.02  beta 0.22+-0.01
  seeds 4-5 (new)        n=2  cost 3.19+-0.05  win 0.89+-0.02  beta 0.21+-0.01
  seeds 1-5 (pooled)     n=5  cost 2.77+-0.49  win 0.93+-0.03  beta 0.22+-0.01
  per-run cost: s1=2.04, s2=2.90, s3=2.53, s4=3.16, s5=3.22

--- measured ---
  seeds 1-3 (reported)   n=3  cost 2.05+-0.42  win 0.95+-0.02  beta 0.54+-0.02
  seeds 4-5 (new)        n=2  cost 1.93+-0.58  win 0.96+-0.02  beta 0.50+-0.03
  seeds 1-5 (pooled)     n=5  cost 2.00+-0.42  win 0.95+-0.02  beta 0.53+-0.03
  per-run cost: s1=1.58, s2=2.38, s3=2.20, s4=2.34, s5=1.52
```

**Nothing flips, and the story strengthens.**  The imagined-vs-measured cost gap
widens from 0.44 to 0.77, and beta stays 0.22 against 0.53 — the same factor of two
under-pricing, now at five runs.  At `d=0` no rule meets the limit either way, so no
claim depends on the pooling.

Both new imagined runs landed above every seed-1-3 run (3.16, 3.22 vs 2.04-2.90),
which is why that row's sd grows; the measured runs fell inside their old range.

### Edits downstream of the numbers

| file | change |
|---|---|
| `generated/mechanism_8m.tex` | Imagined 2.49->2.77 / 0.95->0.93, Measured 2.05->2.00 / beta 0.54->0.53, caption run count |
| `chapters/05_experiments.tex` | the three inline copies of those numbers (lines 103, 174-176) |
| `tests/test_analyze_exports.py` | `PINNED_8M_D0` values, a new `PINNED_8M_D0_SEEDS` check, the generated-table assertions |
| `data/run_manifest.csv` | rebuilt, 520 -> 530 rows |

A gitignored `thesis/private-mamba` symlink was added so the 12 export-backed tests
stop skipping; `test_analyze_exports.py` is 114 passed.

## Left for the user / Shahaf

`chapters/05_experiments.tex:142` says "at `d=0`, beta reaches only 0.025 to 0.54 ...
on five maps (Appendix D)".  That 0.54 is **not** Table 2's `d0measured` number
(now 0.53) — it traces to `fig:beta-smac` and the `smac_measured_aprmay` batch, a
different measurement that these reruns do not touch.  Left unedited on purpose; if
the coincidence of values is confusing it is a wording question, not a data one.

## Status

Done.  Table 2 **was** updated here (unlike #21): the rows are ours, the pooling is
plain within-row seed pooling, and no other row or claim is affected.

## Files

| file | what |
|---|---|
| `rerun_endpoints.csv` | endpoints of the 4 runs (variant, seed, slurm, n_episodes, score, cost, winrate, beta) |
| `endpoints26.py` | W&B episode exports -> endpoints, the `S-5000 <= steps <= S` rule |
| `compare26.py` | 3 seeds vs 5 seeds, read from the same sources the table reads |
| `comparison.txt` | its output |

Raw W&B exports:
`docs/experiments/11-thesis-ablations/6-aamas-revision/csv/smac_8m_d0_seeds45/`
(untracked), with the two imagined ones also copied into `csv/smac_8m_d0_ablation/`.

---

Parent epic: #42.
