# Theorem 1 empirical check — plan (MAMuJoCo first)

## Why

Theorem 1 says: |real cost − imagined cost| ≤ Δ = 15·ε_c + 105·c_max·ε_P.
We check if the data is consistent with this: measure both sides from
existing WandB logs. Zero new compute. Supervisor point 5.

## What (per Exp 8 SafeDreamer run: HC 2x3, Ant 2x4, Ant 4x2 × limits × seeds)

Pull 5 metrics (end-of-training average, not last point):

| Quantity | WandB metric |
|---|---|
| ε_c (cost-head error) | `Model/cost_loss` |
| ε_P proxy (forecast error, KL) | `Model/div` → TV ≈ sqrt(KL/2) (Pinsker) |
| imagined cost per step | `Value/Cost` |
| real episode cost | `main/cost` |
| c_max | `Value/Max cost` (+ env definition check) |

## How (the computation)

1. Same scale for both sides — cost per 15 steps (×13.9 = Σγ^t, γ=0.99):
   - imagined = `Value/Cost` × 13.9
   - real = (`main/cost` ÷ episode length) × 13.9
     ASSUMPTION (stated): cost spread evenly over episode.
     Episode length NOT hardcoded (1000 is only the MAMuJoCo default) —
     measure it: diff of `steps` between consecutive logged episodes.
     Verified in code (`agent/runners/DreamerRunner.py:41-48`): logging is
     once per episode; `main/cost` = episode total; `steps` = cumulative →
     steps-diff = episode length. (n_workers>1 interleaves episodes but each
     row still adds exactly one episode's steps — diffs stay valid.)
2. Observed gap = |real − imagined|.
3. Bound Δ = 15·ε_c + 105·c_max·sqrt(`Model/div`/2).
4. Table per env (mean ± std over seeds): ε_c, ε_P, Δ, gap, d.

## Success criteria / expected outcome

- gap ≤ Δ everywhere → data consistent with theorem.
- Report tightness honestly: sanity run (HC c=25 s1) gives gap ≈ 0.09 vs
  Δ ≈ 19 → bound holds but loose, ε_P term dominates (as thesis predicts).

## Steps

1. [ ] Script `extract_theorem1_mamujoco.py` in this folder: pull metrics for
       all Exp 8 SafeDreamer full-comm runs (names
       `safedreamer_dai_safety_gym_lag*_Safety*` + `fix-logprob` HC runs;
       exclude `_nocomm`).
2. [x] Verify episode length + c_max per env from env code.
       c_max = 1.0 exactly (safety-gymnasium velocity cost =
       `float(velocity > threshold)`, binary, same for all agents; worker
       averages over agents → team step cost in {0,1}). Episode length:
       measured from `steps` diffs (see above). `Value/Max cost`≈1.08 =
       model overshoot, consistent.
3. [ ] Compute table, save CSV here.
4. [ ] Writeup in notes.md; then repeat for SMAC (expect larger Δ → candidate
       explanation for point 3 threshold violations).
5. [ ] When final: copy artifacts to
       `overleaf/thesis/thesis_experiments/5-theorem1-estimates/`.
