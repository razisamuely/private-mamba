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
