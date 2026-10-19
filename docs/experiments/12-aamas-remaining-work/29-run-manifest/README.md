# #29 — A run manifest behind every reported number

Issue: https://github.com/razisamuely/private-mamba/issues/29
Plan section: §5 of `docs/planning/remaining_work_2026-10-15.pdf`

## What the ticket asks for

One place that says, for every number in the paper, which runs produced it and from which
commit. Nothing collected that, so answering it meant re-deriving the chain by hand each
time — which is how the stale `8m` beta series survived into the submission (#32).

## What was built

Two scripts in the thesis repo and one CSV:

| File | Role |
|---|---|
| `scripts/fetch_wandb_commits.py` | Walks the W&B project once, caches `data/wandb_run_commits.csv` |
| `scripts/build_run_manifest.py` | Walks every source, writes `data/run_manifest.csv` |
| `scripts/check_run_manifest.py` | Fails if the manifest no longer matches the sources |

The manifest lives in the thesis repo because that is where the tables are generated and
where a reviewer or a future reader looks. Nothing in this repo reads it.

## The CSV

`overleaf/thesis/data/run_manifest.csv` — **520 runs**, one row each:

```
benchmark,config,cost_limit,method,variant,seed,slurm_id,wandb_run,wandb_id,commit,laglr,lag_init,tables,sources
```

`tables` and `sources` are `;`-separated sets: the tables and figures a run feeds, and the
files that name it. 501 of the 520 carry a git commit, across 21 distinct commits. The 19
without one are the offline runs (`local_runs_endpoints.csv`, `theory_check_local_runs.csv`)
plus one phase-5 row whose link was never filled in; they never reached W&B, so no commit
is recoverable and an empty cell is the honest answer rather than a guess.

Runs per table:

| Table or figure | Runs |
|---|---|
| `aamas_full_results` | 252 |
| `aamas_main_results` | 219 |
| `interaction_multiple` | 217 |
| `smac_macpo` | 178 |
| `fig:catchup` | 143 |
| `mechanism_8m` | 126 |
| `mamujoco_tight` | 98 |
| `hc_multiplier` | 80 |
| `mamujoco_main` / `_laglr` / `_nocomm` / `_schedule` | 80 each |
| `model_error` | 74 |
| `smac_mappolag` | 72 |
| `fig:smac-curves` | 71 |
| `mamujoco_pid_tight`, `transition_diagnostics` | 62 |
| `model_error_local` | 18 |
| `fig:beta-smac` | 15 |
| `app:remaining-evidence` | 11 |
| `fig:beta-hc` / `-ant2x4` / `-ant4x2` | 9 each |

## Why the commit column is complete

W&B stores the git commit of the checkout that launched each run. All 1032 runs in the
project carry one, so `fetch_wandb_commits.py` caches them in one pass and the manifest
build needs no network.

## What the check guarantees

`check_run_manifest.py` rebuilds the manifest from the sources in memory and diffs it
against the committed CSV, then checks three properties:

| Check | Guarantee |
|---|---|
| one row per run | no run counted twice under two identifiers |
| manifest against the sources | a run added to any source without a rebuild is an error, not a silent omission |
| run identity | every row has a Slurm job id or a W&B name |
| table coverage | every `generated/*.tex` the paper `\input`s has at least one run behind it |

It does not recompute the paper's numbers — that is what the generator scripts do. It
answers the narrower question the ticket asks: is the run list complete and current.
Verified by deleting one row and confirming the drift check names the missing run.

```bash
cd ../overleaf/thesis
python scripts/fetch_wandb_commits.py   # only when new runs have appeared
python scripts/build_run_manifest.py
python scripts/check_run_manifest.py
```

## Not done, by decision

The plan's §5 also asks that the generator scripts read the manifest instead of their own
sources. That was dropped: the manifest is derived *from* those sources, so inverting the
direction is a rewrite of five scripts that buys nothing the drift check does not already
give. The check fails the moment a source and the manifest disagree, which is the property
§5 wanted.

## Problems found while building it

| Finding | Action |
|---|---|
| `new_experiments_tracking_4M.csv` holds 93 rows still `pending` or `running`, with no id and no score | builder skips rows without a score; they back no reported number |
| `ca_mamba_measured_100k.csv` gives `local:` paths for the three offline `8m` runs, and one phase-5 row reads `TODO_update_when_logged` | neither is a W&B name; builder treats both as absent |
| `data/ablation_study_experiments.csv` backs nothing any more — its rows are the safety-mechanism appendix deleted in #39 | deliberately not a source; noted in the builder |
| `generated/model_error.tex` and `generated/mamujoco_tight.tex` are generated but never `\input`; `tab:model-error` resolves to `model_error_local` instead | out of scope here — flagged for #20 |
| Two tracking rows name runs the W&B project does not have (`2m_zs_1z` typo, a `3s_vs_4z` MACPO run), both `running` with no score | dropped by the score filter; nothing reported depends on them |

## Status

| Step | State |
|---|---|
| Commit cache | done — 1032 runs, all with a commit |
| `run_manifest.csv` | done — 520 runs, 501 with a commit |
| `check_run_manifest.py` | done — passes, and fails on a stale manifest |
| Generators read the manifest | dropped, see above |
