# #21 — Verify the 4 HC job batches used the same code commit

## Problem

Table 6 (HC multiplier rules, `generated/hc_multiplier.tex`) is assembled from four
batches of runs submitted months apart.  If they ran different training code the
table compares apples to oranges.  Three of the four batches had no recorded commit.

## Why we could not recover it ourselves

- Slurm accounting had purged the jobs (`sacct -j 22132722` empty, also with
  `-S 2026-01-01 -a -A brafman`)
- no `.out` files left in the repo on the cluster
- `~/camamba/runs/` does not exist on our account, `/home/shperbsh` is not readable
- the runs are absent from `data/wandb_run_commits.csv` (they never logged to W&B)

So we reran the three unverified rows on a known commit, and asked Shahaf in parallel.

## Answer (Shahaf, email 2026-11-01)

All his HC batches ran **`fde7f82`** ("chore: cluster scripts for theory-check runs
without WandB", branch `feat/aamas-8m-ablation`).

`~/camamba/private-mamba` on the cluster was created once from a git bundle and never
pulled into, so its reflog holds a single `clone:` line — that is why the reflog was
useless.  His only local edits were under `tools/`.

`fde7f82` is an ancestor of `1e54c6a`, and outside `docs/` the diff touches only
`tools/theory_check.py` and its test, `tools/cluster/setup_env.sh`,
`tools/cluster/theory_check_job.sh` and a stray `.playwright-mcp` file.
**Training code identical → the batches belong in one table.**

Covered batches: Learned d=25 `22132722-24`; Parity start + beta=1 (A)
`22313221-30`, `22317679`, `22319394`; Learned d=5 `22400771-74`.

## The 12 reruns

Submitted 2026-10-31 on commit `8cd306a`, branch `feat-aamas`, HalfCheetah 2x3,
1M interactions, all COMPLETED at 1,002,000 samples.  Full Slurm -> seed -> W&B
mapping is in the GitHub comments of #21.

| row | tag | d | Slurm |
|---|---|---|---|
| Learned (`--laglr 1e-05`) | `theory` | 25 | 23739191, 23739192, 23739193 |
| Parity start (`--laglr 1e-05 --lag_init 1.0`) | `warm1` | 5 | 23739194, 23739196, 23739200 |
| Parity start | `warm1` | 25 | 23739203, 23739205, 23739209 |
| beta=1 (A) (`--laglr 0 --lag_init 1.0`) | `fixed1` | 5 | 23739216, 23739222, 23739224 |

### Extraction

These runs have **no `metrics.jsonl`** — they logged to W&B only, so
`scripts/collect_local_endpoints.py` cannot read them.  Route used instead:

1. `docs/experiments/11-thesis-ablations/6-aamas-revision/export_histories.py`
   `--group hc_issue21 --regex "_(23739191|...|23739224)_feat-aamas"`
   -> `csv/hc_issue21/<run_id>_episodes.csv` (1000 episode rows each, last step 1e6)
2. `endpoints21.py` applies the repo's reading rule, mean over episode rows with
   `S-5000 <= steps <= S`, `S = 1e6` -> `rerun_endpoints.csv`

All 12 give **6 episodes** in the window, matching every other Table 6 row.  (Our
earlier hand extraction for #20 used `samples > 995000` and so counted 5.)

Tooling was validated by re-deriving Shahaf's d=5 endpoints from the `metrics.jsonl`
in his emailed zip with `collect_local_endpoints.py`: the output is byte-identical to
the CSV he sent.

## Result

`comparison.txt` (regenerate with `compare21.py`), Shahaf's originals against our
reruns against the two pooled:

```
row              d    ORIGINAL (Shahaf)        RERUN (#21)             POOLED
Learned          5   2321+-535  3.52 +-5.49 (5/6)      --            2321+-535  3.52 +-5.49 (5/6)
Learned         25   2511+-377 10.22 +-4.38 (3/3)  2367+-381 17.22 +-15.4 (2/3)  2439+-348 13.72 +-10.8 (5/6)
Parity start     5   2266+-480  4.00 +-6.07 (2/3)  2412+-273  2.11 +-1.44 (3/3)  2339+-358  3.06 +-4.08 (5/6)
Parity start    25   2605+-235 19.06 +-25.5 (2/3)  2662+-143 21.94 +-17.9 (2/3)  2633+-177 20.50 +-19.8 (4/6)
beta=1 (A)       5   1954+-298  0.61 +-0.25 (3/3)  2578+-48   0.67 +-0.44 (3/3)  2266+-392  0.64 +-0.32 (6/6)
beta=1 (A)      25   2282+-219  2.67 +-1.36 (3/3)      --            2282+-219  2.67 +-1.36 (3/3)
```

The Learned d=5 "original" column is Shahaf's `22400771-74` pooled with our earlier
`23736292-94`, the cell he already changed in the generator.

**No cell flips.**  Every row stays within its limit on the mean, before and after
pooling, so no claim in the paper depends on which set is reported.  Pooling only
widens the error bars and turns the within-counts into n/6.

The one large shift is **beta=1 (A) reward, 1954 -> 2266**: his three runs came in at
2197/1621/2044, ours at 2544/2632/2557.  Expected rather than suspicious — `--seed`
only *labels* a run and seeds nothing (Python, NumPy, Torch, the envs, the Ray
workers), so these are six independent nondeterministic runs and a 600-point spread
is variance.  Pooling is the right response, which is the same argument Shahaf used
for the Learned d=5 cell.

Worth his attention: pooled, beta=1 at d=5 reaches reward 2266 against Learned's
2321 — essentially equal — at far lower cost (0.64 vs 3.52) and 6/6 vs 5/6 within.
That is a weaker, factual version of the claim deleted in #23: not "parity meets a
limit the learned price misses" (both meet it), but "fixed beta=1 meets it more
reliably at the same reward".

## Status

Verification question **answered**; ticket closed.  Table 6 was **not** changed — the
reruns are replication evidence, and whether to fold them in is Shahaf's call since he
owns the pooling design and the surrounding text.

## Files

| file | what |
|---|---|
| `rerun_endpoints.csv` | endpoints of the 12 reruns (tag, d, seed, slurm, n_episodes, score, cost) |
| `endpoints21.py` | W&B episode exports -> endpoints, the `S-5000 <= steps <= S` rule |
| `compare21.py` | builds the comparison above from the thesis CSVs plus the two sets |
| `comparison.txt` | its output |

Raw W&B exports live in
`docs/experiments/11-thesis-ablations/6-aamas-revision/csv/hc_issue21/` (untracked).
Shahaf's zip of his d=5 runs is `~/Downloads/learned_d5_runs.zip`.
