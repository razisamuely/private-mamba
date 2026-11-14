# #35 — Model error against violations

## Question

Theorem 4.1 splits the real-vs-imagined cost gap into a cost-head term
(`15·ε_c`) and a transition term (`105·c_max·ε_P`). The plan asks whether a
larger under-prediction goes with more cost above the limit — which would turn
the theorem from a decomposition into a measured explanation.

No new training. The plan's 18 reported runs are pulled from W&B; Experiment
11's broader set adds the laglr=1e-04 cells from its existing per-run CSVs.

## Why this is not a repeat of Experiment 11

`11-thesis-ablations/5-theorem1-estimates` measured the same quantities and
concluded:

> "model error alone does NOT explain cost-above-threshold. The bound is
> 50-900× looser than the actual gap."

**That conclusion does not follow from that evidence.** Experiment 11 tested the
*inequality* — is the observed gap below Δ? A worst-case bound being loose says
nothing about whether model error **orders** the runs. Three runs can have
errors of 0.1, 0.2, 0.3 against an allowance of Δ=20 — "negligible" by size,
yet perfectly predictive of which run violates most.

Experiment 11 asked about **magnitude**. This asks about **ranking**.

## Method

Per run: `excess = max(0, real episode cost − d)`.

Two predictors, both measured on real replay transitions and therefore *not*
functions of the episode cost:

- **ε_c** — cost-head error (`Model/cost_loss`)
- **ε_P** — transition error, as the Pinsker TV proxy of the prior/posterior KL
  (`Model/div`)

The test is **within a cell**. ε_c grows with the magnitude of the cost being
predicted, so a d=25 run has a larger ε_c than a d=5 run for reasons unrelated
to safety; pooling across limits would measure that confound. Inside one
(env, limit, laglr) cell the runs differ only by seed, so a pair is clean. The
sign test pools those within-cell pairs; pairs that tie on either side are
dropped, since at a tight limit most runs sit at excess exactly 0.

## Result

### The plan's 18 runs (reported Table 6, laglr=1e-05, code defaults)

17 runs in 6 cells (Ant4x2 d=25 s=2 dropped — crashed at 921k, no cost window).
ε_c and KL pulled from W&B `scan_history`; episode cost from the last-5k window.

| predictor | concordant pairs | p | ties |
|---|---|---|---|
| **ε_c** (cost head) | **8/12 (67%)** | 0.19 | 4 |
| ε_P (transition) | 5/12 (42%) | 0.81 | 4 |

Same direction — ε_c goes the right way, ε_P doesn't — but **not significant**
(p=0.19). Six cells × 3 seeds gives only 16 usable pairs after ties, which is
too few to reach p<0.05 with a sign test. The signed outcome (no ties) is
11/16 (69%), p=0.11.

### Experiment 11's 38 runs (laglr 1e-04 and 1e-05)

The laglr=1e-05 subset is the **same physical runs** as above, extracted
independently 3 months earlier with Exp 11's tail-10% averaging. The 6
laglr=1e-04 cells add 18 more runs:

| predictor | concordant pairs | p | within-cell ρ |
|---|---|---|---|
| **ε_c** (cost head) | **16/20 (80%)** | **0.006** | **+0.46** |
| ε_P (transition) | 10/20 (50%) | 0.59 | −0.05 |
| real − imagined | 18/20 (90%) | 0.0002 | +0.19 |

**Adding the laglr=1e-04 cells — which double the number of informative pairs —
pushes ε_c to significance.** The transition error remains a coin flip.

This is the opposite split from the bound. Experiment 11 found Δ is dominated
by `105·c_max·ε_P` while `15·ε_c ≈ 0.05` is negligible. The term that dominates
the bound is the one with **no** ordering power, and the term dismissed as
negligible is the one that tracks which runs violate.

`real − imagined` scores highest but is **partly circular** — it contains the
same real cost that `excess` is built from, so it is reported for completeness,
not as evidence.

## What this does and does not claim

**Claimed:** ε_c co-varies with excess; ε_P does not. That is the whole result.

**Not claimed — the cost head is inaccurate.** It is not: ε_c ≈ 0.001 against
d=5. The test is about the *ranking* of a tiny error across runs, not its size.
Nothing here says the cost head is bad.

**Not claimed — a fix.** "Improve the cost head" does not follow. Shrinking an
already-negligible error has no reason to reduce violations, and this design
cannot support that recommendation.

**Not claimed — a direction.** The arrow may run the other way: a policy that
drifts into high-cost states would both exceed d *and* hand the cost head
harder targets, producing the same correlation with no causal role for model
error. Separating those needs an intervention, not more of this data.

So the plan's hoped-for conclusion — "turn Theorem 4.1 from a decomposition
into a measured explanation" — is **not** earned. The measurement answers the
question that was asked ("does a larger under-prediction go with more cost
above the limit?") and declines the inference that was hoped for. What it does
buy is narrower and still useful: it says which half of the decomposition is
worth writing about, and it moves Limitation 2 off "average-case only".

## SMAC does not replicate

36 runs, 10 maps: ε_c 32/54 (59%), p=0.11; ε_P 28/54 (52%), p=0.45. No effect.

Two reasons to discount it rather than treat it as a contradiction: every SMAC
run in that export was launched at **d=0**, so `excess` is the whole episode
cost and the row answers a weaker question; and SMAC cost is integer
casualties, so within a 3-seed cell the outcome frequently ties.

A nonzero-limit SMAC replication would need ε_c extracted for the d>0 runs.

## Caveats

- The three pairs from a 3-run cell are not independent, so the p-values are
  mildly optimistic. The effect survives both outcome definitions (censored
  `excess` 80%/p=0.006; signed `real − d` 74%/p=0.001).
- 12 cells, 3 runs each. Indicative, not a powered test.
- The plan's 18 runs alone are underpowered (p=0.19). Significance comes from
  Exp 11's laglr=1e-04 cells. The laglr=1e-05 subset overlaps (same runs),
  but the 1e-04 cells are independent.
- ε_P is a KL-on-latents proxy for TV-on-states, and a low average does not
  certify the theorem's uniform assumption. Carried over from Experiment 11.

## Data

- `model_error.csv` — 74 rows (38 MAMuJoCo + 36 SMAC): `eps_c`, `tv`,
  `imagined_cost`, `real_cost`, `gap`, `excess`.
- `model_error.py` — regenerates the Exp 11 analysis; `--csv PATH` writes the
  rows, stdout is the test table.
- `table6_model_metrics.csv` — 18 rows from the plan's reported runs, pulled
  from W&B (`Model/cost_loss`, `Model/div`, `main/cost`). Ant4x2 d=25 s=2 has
  `nan` cost (crashed at 921k, same as #32).

Inputs for the Exp 11 set:
`11-thesis-ablations/5-theorem1-estimates/theorem1_{mamujoco,smac}_per_run.csv`.
Those hold costs per discounted 15-step window; the script multiplies back by
`episode_length / 13.9` to recover the episode cost that d is compared against.

## Follow-up

Experiment 11's `notes.md` conclusion ("model error alone does NOT explain
cost-above-threshold") is overstated for the same reason this ticket's first
draft was: it reasons from the **size** of the error to its irrelevance. It
should say the *bound* is loose. Not edited here — that file is the record of
what was concluded at the time.

## Status

Data done. Appendix text pending under #40. Limitation 2 can say the
model-error evidence is no longer average-case only, but must not claim the
theorem explains the violations.
