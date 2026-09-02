# 5-theorem1-estimates — working notes

Theorem 1 ("Conditional cost transfer") lives in
`~/workspace/overleaf/thesis/chapters/04_theory.tex`.

## Theorem 1 in plain terms (walkthrough 2026-09-01)

- Constraint is enforced in imagination; if the world model is wrong,
  "safe in dream" != "safe in reality". Bound on the gap:
  `|J_real − J_imagined| ≤ Δ`, with `Δ ≤ 15·ε_c + 105·c_max·ε_P`
  (H_im=15, γ=0.99; 15 = Σγ^t ≤ H, 105 = Σt·γ^t ≤ H(H−1)/2).
- **ε_c** = cost-head error (`DreamerModel.cost_model`,
  `agent/models/DreamerModel.py:22`): wrong price for the right situation.
  Cost units. Linear in horizon (×15).
- **ε_P** = transition/RSSM error (`DreamerModel.transition`, line 19):
  wrong next state entirely — the dream drifts, compounds over steps.
  Unitless TV distance; ×c_max converts to cost units. Quadratic (×105) → dominates.
- Practical use: to guarantee real cost ≤ d, imagination must target
  `d − Δ` (pessimistic threshold) → directly feeds supervisor point 3.

## ε_P explained (walkthrough details)

**Definition**: at each state+action, the real env and the model each define a
forecast (probability distribution) over "what happens next". ε_P = worst-case
TV distance between the two forecasts. Unitless, 0-1. Intuition: fraction of
probability mass the model puts on wrong futures (e.g., real: marine dies 90%;
model: dies 40% → off by 0.5, dreams an optimistic world where the ally-death
cost never even appears — ε_c can be 0 and imagined cost still wrong).
Compounds over imagined steps (drift ≤ t·ε_P) → the ×105 quadratic term.

**Why measurable despite continuous states**: the model never forecasts raw
(infinite) states. Encoder squashes every observation into a finite discrete
code — N_CATEGORICALS "boxes" × N_CLASSES values each
(`DiscreteLatentDist`, `networks/dreamer/rnns.py:23-37`, `OneHotCategorical`).
Forecasts are small per-box percentage tables; comparison is table-vs-table.
(Discreteness is a DreamerV2 design choice, not required — Gaussian latents
would allow closed-form KL too.)

**How it's measured (proxy — real forecast unknowable, only outcomes seen)**:
on real replay transitions compare, per step:
- **prior** = forecast before seeing the new obs
  (`RSSMTransition._stochastic_prior_model`, rnns.py:50,67)
- **posterior** = same step encoded WITH the real obs
  (`RSSMRepresentation._stochastic_posterior_model`, rnns.py:77,97)
- disagreement = KL, `state_divergence_loss` (`agent/optim/utils.py:90-97`),
  computed at `agent/optim/loss.py:53` and **already logged to WandB as
  `Model/div`** every training step → first-pass ε_P estimate needs zero new
  compute. (Similarly ε_c ← `Model/cost_loss`, loss.py:42.)

Caveat: KL on latents is a proxy for TV on states, and a low *average* does
not certify the theorem's *uniform* assumption (04_theory.tex:114-116).

## Empirical estimates to produce (supervisor point 5)

1. **ε_c**: cost-head prediction error on held-out real transitions.
   Partially done — thesis cites ~0.004 on MAMuJoCo → 15·0.004 = 0.06 vs d=25.
   Redo per env (incl. SMAC) as a measured average.
2. **ε_P**: transition-error proxy on real data (e.g., prior-vs-posterior KL /
   next-latent prediction error; TV itself not directly measurable).
3. Compute Δ per env; compare against observed real-vs-imagined cost gap —
   does it explain SMAC threshold violations (point 3)?

## MAMuJoCo check — feasibility confirmed (2026-09-01)

- All needed metrics exist in Exp 8 SafeDreamer WandB logs (sample run
  HC2x3 c=25 lag1e-4 s1): `Model/cost_loss`=0.0049 (ε_c), `Model/div`=0.064
  (ε_P proxy), `Value/Cost`=0.0125 (imagined cost/step), `main/cost`=19
  (real episode total), `Value/Max cost`≈1.08 (c_max estimate).
- Logging verified per episode (`DreamerRunner.py:41-48`) → episode length =
  `steps` diff between consecutive rows.
- Sanity calc (per-15-step scale, ×13.9): imagined ≈ 0.175, real ≈ 0.27 →
  gap ≈ 0.09; Δ ≈ 19 (ε_P term dominates via Pinsker TV≈0.18) → bound holds
  but very loose, as thesis predicts ("ε_P is what binds").
- Full plan: `plan.md` in this folder. Next: extraction script for all runs.

### Limitation (state in writeup)

We compare **average** 15-step windows (real side = episode cost ÷ episode
length × 13.9). But MAMuJoCo cost is binary and bursty (0/1 per step, step 2
finding) — violations cluster. A risky window inside a burst can have cost
~15 while the average says ~0.3. So the "observed gap" understates the worst
case; the check is consistency-on-average, not worst-case verification
(matches the theorem's own caveat: average ≠ uniform, 04_theory.tex:114-116).

## MAMuJoCo results (2026-09-01) — plan steps 1-3 DONE

Script: `extract_theorem1_mamujoco.py` → `theorem1_mamujoco_per_run.csv`
(38 runs), `theorem1_mamujoco_agg.csv` (12 env x limit x laglr groups).
Note: WandB `run.history(keys=[...])` returns only rows where ALL keys
co-occur — metrics logged in separate wandb.log calls must be fetched
per key (bug found + fixed in first version).

**Findings** (all per discounted 15-step window, tail-10% averages):

- **Theorem consistent, bound very loose**: observed gap 0.006-0.14 vs
  Δ 21-44 → holds with x200-x3000 slack. The imagined constraint tracks
  real cost far better than worst case.
- **ε_c ≈ 0.0004-0.006** — confirms thesis "~0.004" claim; 15·ε_c ≈ 0.05,
  negligible vs d.
- **ε_P (KL proxy) is env-dependent and dominates Δ**:
  HC 2x3 ≈ 0.08-0.10; Ant (2x4, 4x2) ≈ 0.25-0.35 (3x harder dynamics).
  Δ is essentially 105·TV (Pinsker).
- Next comparison point: SMAC ε_P — if higher, candidate explanation for
  threshold violations (point 3).

## Calculation flow (each step, with averaging + assumptions)

```
INPUTS (per run, from WandB logs)
│
│  A. Model/cost_loss      (cost-head error, per training step)
│  B. Model/div            (prior-vs-posterior KL divergence, per training step)
│  C. Value/Cost           (dreamed cost, per dreamed step)
│  D. main/cost            (real cost, TOTAL per episode)
│  E. steps                (cumulative env steps, one row per episode)
│
▼
STEP 1 — tail averaging (all of A-D)
│  take the LAST 10% of each metric's logged rows → mean
│  WHY: end-of-training value, single last point too noisy
│  ASSUMPTION: model is converged in the last 10%
│
├──────────────── LEFT BRANCH: the BOUND Δ ─────────────────┐
▼                                                            ▼
STEP 2a — ε_c                                    STEP 2b — ε_P proxy
│  ε_c = tail-mean(A)                            │  KL = tail-mean(B)
│  e.g. 0.004                                    │  TV = sqrt(KL/2)   [Pinsker]
│  ASSUMPTION: average loss                      │  e.g. KL=0.08 → TV=0.2
│  stands in for worst-case ε_c                  │  ASSUMPTION: KL on latents
│                                                │  ~ TV on states; avg~worst
└────────────┬───────────────────────────────────┘
             ▼
STEP 3 — Δ = 15·ε_c + 105·c_max·TV     (c_max = 1, exact from env code)
│  e.g. Δ = 0.06 + 21 ≈ 21
│
├──────────────── RIGHT BRANCH: the OBSERVED GAP ───────────┐
▼                                                            ▼
STEP 4a — imagined side                          STEP 4b — real side
│  per-step = tail-mean(C), e.g. 0.0125          │  episode cost = tail-mean(D), e.g. 19
│  × 13.9 (= Σγ^t, 15 steps)                     │  episode length = mean steps-diff (E)
│  → 0.17 per 15-step window                     │  per-step = 19/~1000 = 0.019
│                                                │  ASSUMPTION: cost spread evenly
│                                                │  (weak — cost is bursty 0/1!)
│                                                │  × 13.9 → 0.27 per window
└────────────┬───────────────────────────────────┘
             ▼
STEP 5 — gap = |real − imagined| ≈ 0.1
             ▼
STEP 6 — check: gap ≤ Δ?   0.1 ≤ 21 ✓ consistent, slack ×200 → loose
             ▼
STEP 7 — aggregate over seeds: mean ± std per env × cost_limit × laglr
```

Why TV: the theorem states ε_P in TV (`D_TV ≤ ε_P`, 04_theory.tex:28-34)
because TV directly bounds differences of expectations of bounded functions
(forecast off by X → cost off by ≤ c_max·X). KL is just what training logs;
Pinsker (TV ≤ sqrt(KL/2)) is the conservative bridge.

## Observation: MAMuJoCo also violates tight limits (2026-09-02)

Not SMAC-specific — SafeDreamer exceeds cost on MAMuJoCo too when d is tight:

| Env | d (limit) | SafeDreamer cost @1M | Violates? |
|---|---|---|---|
| HC 2x3 | 5.0 | 35.8 | **yes, ×7** |
| HC 2x3 | 25.0 | 16.6 | no |
| Ant 2x4 | 0.2 | 24.3 | **yes, ×120** |
| Ant 2x4 | 25.0 | 17.4 | no |
| Ant 4x2 | 1.0 | 2.5 | **yes, ×2.5** |
| Ant 4x2 | 25.0 | 11.5 | no |

(Source: `docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table_real_*.csv`,
SafeDreamer lr=1e-5 @1M steps.)

Pattern: tight limits violated massively; loose limits (d=25) roughly ok.
Meanwhile, Theorem 1 gap is tiny everywhere — the model is accurate on
average but the Lagrangian constraint enforcement fails with tight budgets.
Connects to supervisor points 3 (pessimistic threshold) and 4 (PID-Lagrangian).

## TODO — missing citation in thesis (do NOT edit paper yet)

Theorem 1's proof is the classic **simulation lemma** template, but the thesis
has no reference for it. Add when editing the paper:
- Kearns & Singh (2002), "Near-optimal reinforcement learning in polynomial
  time" — original simulation lemma.
- Janner et al. (2019), "When to Trust Your Model" (MBPO) — model-error →
  return-gap bound in deep MBRL.
Suggested sentence: "the argument follows the simulation-lemma template
[Kearns & Singh 2002], extended to constrained cost over a finite imagination
horizon."
