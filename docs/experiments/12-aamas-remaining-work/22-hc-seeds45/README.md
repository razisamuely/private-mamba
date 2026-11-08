# #22 — Add seeds 4 and 5 to every Table 6 row (3 -> 5 runs per cell)

## Problem

Table 6 (`generated/hc_multiplier.tex`) reported three runs per cell.  Three runs give
error bars too wide to separate the multiplier rules, and `--seed` only *labels* a run
(nothing in Python, NumPy, Torch, the envs or the Ray workers is actually seeded), so
the spread is real run-to-run variation and more runs is the only fix.

Shahaf's instruction was plain: run two more seeds per row and pool all five.  Nothing
is being verified here — #21 already settled that the batches share one training code.

## The 22 reruns

Submitted 2026-10-31 on commit `8cd306a`, branch `feat-aamas`, HalfCheetah 2x3, 1M
interactions, all COMPLETED.  Full Slurm -> seed -> W&B mapping is in the GitHub
comments of #22.

| row | flags | d | Slurm (s4, s5) |
|---|---|---|---|
| Learned | `--laglr 1e-05` | 5 | 23739341, 23739342 |
| Learned | | 25 | 23739348, 23739350 |
| Parity start | `--laglr 1e-05 --lag_init 1.0` | 5 | 23739351, 23739352 |
| Parity start | | 25 | 23739358, 23739359 |
| Imagined | `--lag_signal imagined` | 5 | 23739366, 23739367 |
| Imagined | | 25 | 23739368, 23739369 |
| PID | `--lag_mode pid` | 5 | 23739387, 23739388 |
| PID | | 25 | 23739380, 23739381 |
| beta=1 (B) | `--laglr 0 --lag_init 1.0` | 5 | 23739360, 23739361 |
| beta=0 | `--laglr 0` | 5 | 23739408, 23739409 |
| *(unfiled)* | `--laglr 0 --lag_init 1.0` | **5, meant for 25** | 23739394, 23739395 |

`23739374/375` were submitted without `--lag_mode pid` so PID was inactive; they were
cancelled and replaced by `23739387/388`.  **Do not read them.**

### Two gaps, on the record

- `23739394/395` were meant as beta=1 (B) seeds 4-5 at d=25 but were launched with
  `--cost_limit 5`.  Their names say `_5.0_` and that is what they trained on, and
  seeds 4-5 of beta=1 d=5 already exist (`23739360/361`), so they are duplicates of a
  cell rather than runs of the one they were for.  **beta=1 (B) d=25 stays at 3.**
- **beta=0 d=25 got no reruns at all** and stays at 3.
- beta=1 (A) was deliberately not rerun (#21 covered it) and stays at 3.

10 of the table's 14 cells therefore hold five runs; 4 hold three.

## Extraction

These runs have no `metrics.jsonl`, so `collect_local_endpoints.py` cannot read them.
Route:

1. `docs/experiments/11-thesis-ablations/6-aamas-revision/export_histories.py
   --group hc_issue22 --regex "_(23739341|...)_feat-aa"` -> `csv/hc_issue22/`
2. the 12 ablation runs (imagined / pid / fixed1 / fixed0) were **copied into
   `csv/hc_ablation_d5/` and `csv/hc_ablation_d25/`** and `data/hc_ablation_endpoints.csv`
   **regenerated** — that CSV is machine-written and verified row-for-row by
   `DeliveredAnalysisTest`, so a hand-appended row fails the suite
3. the 8 learned / parity runs were **appended** to `data/local_runs_endpoints.csv`,
   which is hand-maintained

All 22 give **6 episodes** in the window `S-5000 <= steps <= S`, `S = 1e6`.

`endpoints22.py` recomputes all 22 endpoints independently of `analyze_exports.py` and
diffs each against the thesis CSV row it produced: **20 filed, 2 unfiled, 0 mismatches**
(`rerun_endpoints.csv`).

### Side correction

Re-reading the three published **Learned d=5** runs (`23736292-94`) with the correct
window changed them: those rows had been hand-extracted for #20 with `samples > 995000`,
giving 5 episodes instead of 6.  Costs 1.80 -> 2.67, 3.20 -> 3.33, 0.60 -> 0.83; rewards
1555.6 -> 1550.6, 2707.4 -> 2717.5, 1716.8 -> 1722.4.  Shahaf's complaint about the
5-episode rows was correct and those rows are now fixed.

## Code changes (thesis repo)

Where a cell's run count lives was the one design question.  `analyze_exports.py`
gates what a *group* may hold, and its `GroupSpec.seeds` / `extra_seeds` keys cannot
tell the arms of the HC ablation apart (they all share `HC_ENV` and the group's limit).
So:

- `analyze_exports.py`: both HC ablation groups get group-wide
  `seeds=HC_ABLATION_SEEDS = {1..5}`
- `generate_hc_multiplier_table.py`: `EXPECTED_RUNS = 3` replaced by
  `FIVE_RUN_CELLS`, naming per `(row, d)` which cells must hold five; `_cell` takes the
  expected seed set.  The caption's run-count phrase is now derived from the cells so it
  cannot drift.

Two incidental fixes in `analyze_exports.py`:

- `_AAMAS` — W&B caps a display name at 128 characters, so `_feat-aamas` arrives cut to
  `_feat-aa` or `_feat-a`.  Nothing reads the tag, so any prefix matches.
- `DEFAULT_LAG_INIT = 1e-4` — `--lag_init 1e-4` restates
  `LAGRANGIAN_MULTIPLIER_INIT` (`configs/dreamer/DreamerLearnerConfig.py:31`), the
  code's own default, so an `_init0.0001` suffix implies no fixed arm.  The four
  Imagined reruns carry it; their published seeds 1-3 do not.

## Result

Before -> after, Table 6:

| row | d | before | after |
|---|---|---|---|
| Learned | 5 | 1993+-624, 1.9+-1.3 (3/3) | 2026+-606, 2.6+-1.2 (5/5) |
| Learned | 25 | 2511+-377, 10.2+-4.4 (3/3) | 2521+-328, **14.3+-15.3 (4/5)** |
| Parity start | 5 | 2266+-480, 4.0+-6.1 (2/3) | 2051+-520, 3.3+-4.6 (4/5) |
| Parity start | 25 | 2605+-235, 19.1+-25.5 (2/3) | 2210+-578, 18.2+-18.1 (4/5) |
| Imagined | 5 | 1971+-310, 29.1+-48.0 (2/3) | 2178+-359, 18.1+-37.1 (4/5) |
| Imagined | 25 | 1913+-395, 87.0+-75.0 (1/3) | 1862+-290, 101.4+-103.4 (2/5) |
| PID | 5 | 2077+-45, 6.1+-4.4 (1/3) | 2274+-298, 5.2+-3.3 (3/5) |
| PID | 25 | 1555+-22, 25.3+-9.1 (2/3) | 1748+-279, **20.2+-11.0 (4/5)** |
| beta=1 (A) | both | unchanged | unchanged |
| beta=1 (B) | 5 | 1985+-560, 2.4+-2.1 (3/3) | 1990+-468, 1.6+-1.9 (5/5) |
| beta=0 | 5 | 2683+-1402, 473.7+-318.4 (0/3) | 2956+-1197, 522.5+-270.8 (0/5) |

**Nothing flips.**  Two cells change qualitatively:

- **Learned d=25 loses its clean sweep, 3/3 -> 4/5**: seed 5 (`23739350`) ends at cost
  40 against d=25.  The cell mean, 14.3, is still well under the limit.
- **PID d=25 loses its dagger**, mean cost 25.3 -> 20.2, i.e. it now meets its limit on
  the mean where before it did not.

Every other change is a tightening or loosening of error bars.  Prose edits were
therefore numeric only: three figures in `chapters/05_experiments.tex` (2.6, 1990/2026,
522) and two sentences in `appendix.tex` (the PID comparison numbers, plus a note on
which cells keep three runs).

## Status

Data filed, Table 6 regenerated, manifest rebuilt (534 -> 554 rows), tests at
7 failed / 277 passed — two *fewer* failures than before the change, because two stale
pins from #20 (`learned.reward_mean == 1974`, the 10% gap) were corrected along the way.
The remaining 7 are pre-existing and all on Shahaf's open-asks list.

### For Shahaf

1. beta=1 (B) d=25 and beta=0 d=25 are still three runs — the two runs meant for the
   former went out at `--cost_limit 5` and the latter got none.  Rerun or leave?
2. Learned d=25 is no longer 3/3.  The mean is comfortably inside the limit, but if a
   sentence leans on "all runs within" at d=25 it needs softening.  §5.3 is his.
3. The 8 rows appended to `local_runs_endpoints.csv` carry no commit in
   `run_manifest.csv` — `build_run_manifest.py` has no slurm -> W&B-name map for that
   file, and building one is unsafe because one Slurm id can own two W&B runs
   (`23745575` does).  Left as is.

## Files

| file | what |
|---|---|
| `endpoints22.py` | the 22 exports -> endpoints, each diffed against the thesis row it became |
| `rerun_endpoints.csv` | its output |
| `local_rows22.py` | emits the 11 `local_runs_endpoints.csv` rows in that file's column format |

Raw W&B exports live in
`docs/experiments/11-thesis-ablations/6-aamas-revision/csv/hc_issue22/` (untracked),
with `hc_issue22_published_d5/` holding the re-export of the three published Learned
d=5 runs.
