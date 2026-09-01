# 2-comm-audit — Is communication active in training AND inference?

**Date**: 2026-09-01. Code audit, no compute. Supervisor point 2.

## Short answer

**Yes.** Cross-agent communication (multi-head attention) is active in all
three phases — real-env rollouts, world-model training, and imagination —
and there is no separate inference path that could silently disable it.
Caveats below.

## Where communication lives

The comm mechanism is `AttentionEncoder` (`networks/transformer/layers.py:31`),
instantiated in 3 places:

| Site | File | Used in | Comm? |
|------|------|---------|-------|
| RSSM prior (3-layer attn) | `networks/dreamer/rnns.py:48,63` (`RSSMTransition.forward`) | all phases | **Yes — the main comm channel** |
| Reward critic | `networks/dreamer/critic.py:28` | training only (centralized critic, CTDE) | Yes |
| Cost critic | `networks/dreamer/critic_cost.py:24` | training only | Yes |
| ~~AttentionActor~~ | `networks/dreamer/action.py:48` | **UNUSED** | — |

The actual actor is the plain per-agent MLP `Actor` (`networks/dreamer/action.py:32`;
used at `agent/learners/DreamerLearner.py:64`, `agent/controllers/DreamerController.py:18`).
So comm enters action selection **only through the shared latent state**
(RSSM attention over agents' stoch states), not through the policy head.

## Phase-by-phase trace

1. **Real-env rollouts (acting/inference)**:
   `DreamerWorker._select_actions` (`agent/workers/DreamerWorker.py:35-70`) →
   `DreamerController.step` (`DreamerController.py:60-78`) →
   `DreamerModel.forward` → `RSSMRepresentation` → `RSSMTransition` attention.
   - SMAC/MAMuJoCo full-comm mode: `nn_mask=None` → unrestricted attention → **comm active**.
   - `COMM_MODE="none"`: `nn_mask = ~torch.eye(n)` (True=blocked) → cross-agent
     attention blocked, self-attention kept (`DreamerWorker.py:39-40`) — correct.
   - Flatland: mask starts blocked, unblocked per encountered agents (local comm).

2. **World-model training**: `rollout_representation` (`rnns.py:114`) calls the
   representation model with **no mask** → full comm.

3. **Imagination (actor-critic training)**: `rollout_policy` (`rnns.py:154`)
   advances via `transition_model(action, state)` with **no mask** → full comm
   in dreamed rollouts; critics also attend across agents.

## Caveats / findings

- **No dedicated eval path**: reported `main/winrate|cost|score`
  (`DreamerRunner.py:46-48`) come from the *training* rollout episodes.
  Actions are **sampled** from the policy (not greedy/argmax), but there is no
  extra exploration noise: `DreamerController.exploration()` exists and is
  **never called** — rollouts are pure on-policy samples. So "inference"
  metrics use exactly the same comm-active path as training.
- ⚠️ **Bug in no-comm mode**: `DreamerWorker.py:39-44` builds the no-comm /
  Flatland mask but the training side (`rollout_representation` /
  `rollout_policy`) always passes `mask=None` — i.e. even with
  `COMM_MODE="none"`, comm is only blocked in real rollouts, **not** in
  world-model training or imagination. Affects Exp 9 no-comm ablation
  interpretation (comm ablated at acting time only). Not a problem for the
  main (full-comm) results.

## Fix design (for later no-comm retrain — NOT implemented)

Goal: apply the no-comm mask (`~torch.eye(n)`, True=blocked) in world-model
training + imagination, matching acting time.

1. `DreamerLearner` (`agent/learners/DreamerLearner.py`): build
   `self.nn_mask = ~torch.eye(n_agents).bool()` when `config.COMM_MODE == "none"`,
   else `None`; pass into `actor_rollout` / `model_loss` via config or arg.
2. `actor_rollout` (`agent/optim/loss.py:76-84`): pass mask to both
   `rollout_representation(...)` (line 82) and `rollout_policy(...)` (line 84).
3. `rollout_representation` (`networks/dreamer/rnns.py:102`): add `mask=None`
   param, forward to `representation_model(obs_embed[t], action[t], prev_states, mask)`
   (line 114).
4. `rollout_policy` (`rnns.py:124`): add `mask=None` param, forward to
   `transition_model(action, state, mask)` (line 154).
5. Same for the model-learning path in `model_loss` (wherever
   `rollout_representation` is called for the KL/reconstruction losses).
6. Mask must be broadcast to the flattened batch dims used inside
   `RSSMTransition` (batch*n_agents reshapes) — same expansion as
   `DreamerWorker.py:67` (`unsqueeze(0).repeat(batch, 1, 1)`).

Estimated diff: ~10-15 lines. Retrain: rerun Exp 9 no-comm configs after fix.

## Rerun plan (after fix) — affected no-comm runs

All runs below used `--comm_mode none` and are affected by the bug
(trained WITH comm, acted WITHOUT). Rerun same configs on a branch with the fix.

### How no-comm is wired (code pointers)

- CLI flag: `train.py:95` (`--comm_mode full/none`), set into config at
  `train.py:126` (SMAC) and `train.py:198` (MAMuJoCo); run-name suffix
  `_nocomm` at `train.py:245`
- Mask built (acting only): `agent/workers/DreamerWorker.py:39-44`
- Bug location (mask never passed): `agent/optim/loss.py:82,84` →
  `networks/dreamer/rnns.py:114,154` (see Fix design above)

### 1. Exp 9 — SMAC no-comm (6 runs)

- Docs: `docs/experiments/9-smac-comm-ablation/{overview,runs}.md`
- Branch: `fix/comm-mask-inversion`, laglr=1e-5, cost=dead_allies_incremental
- Configs: 8m c=0.0 seeds 1-3 (Slurm 19539781/783/784),
  MMM c=0.0 seeds 1-3 (19539785/786/787)
- Full-comm baselines (Exp 6, reusable as-is): 8m 17209123-125, MMM 17198319-321
- WandB: runs with `_nocomm` suffix in raz-shmueli-corsound-ai/private-mamba

### 2. Exp 8 Phase 5 — MAMuJoCo no-comm (results already in tables!)

- Docs: `docs/experiments/8-continuous-action-mamujoco/{overview,plan,runs}.md`
  (Phase 5); results in main CSV
  `docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table_real_*.csv`
  (source label `... nocomm`)
- Configs: Ant 2x4, HalfCheetah 2x3, Ant 4x2 (SafeDreamer lr=1e-5, nocomm)
- ⚠️ The claimed finding "comm helps 2-agent envs, no benefit Ant4x2" is based
  on these buggy runs → really measures "comm cut at inference only".
  Must rerun before using this claim in the thesis.

### Rerun checklist

1. [ ] Implement fix (see Fix design), branch off `feat/thesis-experiments`
2. [ ] Local smoke test (venv310, `--n_workers 1`, `--comm_mode none`),
       verify mask reaches `RSSMTransition` in learner (print/assert)
3. [ ] Resubmit Exp 9: 6 SMAC jobs (same configs as above)
4. [ ] Resubmit Exp 8 Phase 5: nocomm configs (same envs/seeds as CSV rows)
5. [ ] Re-extract, replace nocomm rows in tables, update Exp 8/9 docs

## Deliverable status

- [x] Code audit + writeup (this file)
- [ ] (Optional) runtime sanity check: hook attention weights in a smoke run,
      confirm nonzero cross-agent attention at act time
- [ ] Copy final writeup to `overleaf/thesis/thesis_experiments/2-comm-audit/`
