# #28 — 8m at d=4: pool the six runs instead of rerunning

## Problem

`8m` at $d=4$ had been run twice over and the two sets disagreed on whether the
configuration is feasible:

| set | when | commit | runs | cost | win |
|---|---|---|---|---|---|
| A | Apr/May 2026 | `5e8dac56` | `17336298/300/301` | **5.03 ± 0.42** | 0.69 ± 0.10 |
| B | Oct 2026 | `5849df68` | `22156904-906` | **3.98 ± 0.68** | 0.82 ± 0.10 |

Every table printed A alone, so the thesis said 5.03 and a reader with B's logs
would see 3.98.  Shahaf's instruction was to pool rather than rerun: these are
one sample of six, not two results to choose between.

## Which six

A third set exists and must **not** be pooled: `csv/smac_8m_old/` (2025) is the
**imagined-input** batch — the `SafeDreamers` rows of
`new_experiments_tracking_100k.csv` that fill the left half of
`generated/smac_dual_input.tex`.  Its multiplier reads the imagined cost return,
not $\bar C_k$, so it is a different method.

A and B are both measured-input, so the six are A + B.

`endpoints28.py` reads all nine and reproduces the pooled cell exactly
(17.87 ± 1.09, 4.50 ± 0.76, 0.75 ± 0.12).  It also turned up a **pre-existing
problem on the imagined column**, flagged below.

### Are A and B the same code?

`git diff 5e8dac56 5849df68 -- agent/ train.py configs/` is +432 lines, but every
behavioural change is behind a new flag whose default is the earlier behaviour:

| change | flag | default |
|---|---|---|
| PID multiplier | `--lag_mode` | `basic` |
| imagined multiplier input | `--lag_signal` | `measured` (`float(episode_cost)`) |
| continuous actions | `ACTION_TYPE` | `discrete` (all new code skipped) |
| communication ablation | `--comm_mode` | `full` (`nn_mask = None`) |

`TRANSITION_DIAG_EVERY = 50` is on by default, but `transition_diagnostics` is
`@torch.no_grad()`, draws from a dedicated `torch.Generator`, and saves and
restores the global CPU and CUDA RNG state and the critic's train mode — it
cannot move training.  The `learner.step(rollout)` →
`learner.step(rollout, info["cost"])` change is in
`run_one_process_one_env_debug`, a debug path; `DreamerLearner.step` already
took `episode_cost` at `5e8dac56`.

So B trained the same algorithm as A at its defaults, and the six pool.

## The seed-label clash

B was launched as `--seed 1, 2, 3` — the labels A already uses — and
`generate_aamas_tables.py:1194` forbids duplicate seeds within a configuration.
B is therefore **read as seeds 4, 5, 6**.  That is sound because `--seed` only
*names* a run: it seeds neither Python, NumPy, Torch, the environments nor the
Ray workers (#36).  Precedent in the same file: `OLD_NAME_SEED_ALIASES` already
maps 23 → 1.

The relabelling is keyed by **Slurm id**, not by seed or date, so each entry
names exactly one run:

```python
MEASURED_RELABELLED_SEEDS: Mapping[int, int] = MappingProxyType(
    {22156904: 4, 22156905: 5, 22156906: 6}
)
```

applied in `parse_name` under `group == SMAC_MEASURED`.

## Wiring

| file | change |
|---|---|
| `scripts/analyze_exports.py` | `SMAC_MEASURED_EXTRA_SEEDS[("8m", 4.0)] = {1..6}`; new `MEASURED_RELABELLED_SEEDS`, applied in `parse_name` |
| `scripts/generate_aamas_tables.py` | `MEASURED_EXTRA_SEEDS[ConfigKey("8m", 4)] = {1..6}`; `NUMBER_WORDS[6] = "six"` (the caption clause is derived, so it could not name a six-run cell) |
| `data/ca_mamba_measured_100k.csv` | **regenerated** (it is machine-written and verified row-for-row, so a hand-appended row fails the suite) |
| exports | B's 9 files copied `csv/smac_8m_new/` → `csv/smac_measured_aprmay/` |

Backup: `data/ca_mamba_measured_100k.csv.bak-20261108`.

`plot_smac_curves.py` needed nothing: it derives `MAP_SEEDS` from
`MEASURED_EXTRA_SEEDS` but plots `COST_LIMIT = 0` only, and `figures/smac_curves.pdf`
came back byte-identical.

## Result

8m $d=4$, in all five tables that print it:

| | before | after |
|---|---|---|
| score | 17.26 ± 1.04 | 17.87 ± 1.09 |
| cost | 5.03 ± 0.42 | **4.50 ± 0.76** |
| win | 0.69 ± 0.10 | 0.75 ± 0.12 |

**Nothing flips.**  4.50 still misses $d=4$ (the dagger stays) and 0.75 is still
under the 0.9 high-win threshold, so every derived count is unchanged: feasible
5/24, high win 10/24, and all six paired sign-test tallies against MACPO and
MAPPO-Lag.  The three disagreeing INFO summaries are identical before and after.

One statistic did move.  The interaction-multiple bootstrap resamples runs
*within* each configuration, so a six-run cell changes its distribution: the
median exceeds $10\times$ in **99.8%** of 2000 resamples, up from 99%.  Quoted to
a decimal on purpose — integer rounding prints 100%, which would read as *every*
resample when four of the 2000 put the median at exactly $10\times$.  The bucket
counts and the median itself ($20\times$) are unchanged, so
`generated/interaction_multiple.tex` moved by one number in its caption.

### Two stale cells fixed on the way

`generated/parity_start.tex` is **hand-written** — it is the one file
`check_run_manifest.py` reports no runs for, and it has no generator (committed
by hand in `2681564`, #24).  Its baseline column is a copy of the measured
table, and it had drifted:

- `8m` $d=4$: 5.03 ± 0.42 → 4.50 ± 0.76 (this ticket)
- `bane_vs_bane` $d=4$: 6.37 ± 1.20 → 6.33 ± 1.22 (**stale since #27**)

Prose, `chapters/05_experiments.tex:147`, also quoted the parity run's own sd as
`1.31` where the table says `1.36`; recomputing from
`data/parity_start_100k.csv` gives 3.06 ± 1.36, so the prose was the typo.

## Status

Tables and figures regenerated, manifest rebuilt (554 rows, unchanged count —
B was already in it under `exports/smac_8m_new`, and the three rows now merge
both sources and read seeds 4-6 at commit `5849df68`).  `check_run_manifest.py`
is clean except its pre-existing `generated/parity_start` FAIL.  Tests at the
same 7 pre-existing failures.

### For Shahaf

1. **The imagined 8m d=4 cell may not be reproducible.**
   `generated/smac_dual_input.tex` prints the imagined input at 5.25 ± 0.95, from
   three `SafeDreamers` rows of `new_experiments_tracking_100k.csv`.  Those rows
   name the same three W&B runs whose exports are in `csv/smac_8m_old/`, but the
   exports read **4.09 ± 0.47** at the repo's window, and no checkpoint on the
   grid 50k…339k reproduces the 6.248 the CSV holds for the first of them.  Those
   runs reached 339k steps where the measured ones stop at 105k, so the two
   batches' `steps` axes are probably not the same quantity.  **Pre-existing and
   untouched by #28** (which only changes the measured column), but if the
   imagined column is unreproducible then the dual-input comparison is on sand.
   Own ticket?
2. **`generated/parity_start.tex` has no generator** and its baseline column is a
   hand-copy that had already gone stale once (#27).  It will drift again.  It
   should be generated from `data/parity_start_100k.csv` plus the measured CSV —
   which would also clear the manifest's only FAIL.  Worth a ticket?
3. The interaction-multiple caption now quotes **99.8%** rather than an integer.
   If he prefers integers it has to read 100%, which overstates it.

## Files

| file | what |
|---|---|
| `endpoints28.py` | the nine 8m d=4 endpoints (all three sets) computed independently of `analyze_exports.py` |

Raw W&B exports are in
`docs/experiments/11-thesis-ablations/6-aamas-revision/csv/{smac_8m_old,smac_8m_new,smac_measured_aprmay}/`.
