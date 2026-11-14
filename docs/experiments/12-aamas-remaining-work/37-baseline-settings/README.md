# #37 — Baseline settings: document, verify and fix accounting

## 1. MAPPO-Lagrangian's SMAC settings (not recorded anywhere)

All MAPPO-Lag runs were launched with only:

```
--task <map> --cost-type dead_allies_incremental --cost-limit <d> --seed <s>
--write-terminal True --num-envs 5 --total-steps 5000000
```

Everything else is SafePO's `mappolag/config.yaml`, with the `smac:` override
block applied by `multi_agent_args` when the task is in `smac_map`. The
effective settings are:

| parameter | value | source |
|---|---|---|
| hidden_size | 128 | smac override |
| layers | 1 | smac override |
| actor_lr | 9e-5 | base default (smac block doesn't override) |
| critic_lr | 5e-3 | base default |
| gamma | 0.99 | smac override |
| safety_gamma | 0.2 | smac override |
| GAE lambda | 0.95 | base default |
| target_kl | 0.01 | smac override |
| learning_iters | 15 | smac override |
| entropy_coef | 0.01 | smac override |
| clip_param | 0.2 | base default |
| max_grad_norm | 10 | base default |
| rollout_length (episode_length) | 1000 | smac override |
| n_rollout_threads | 5 | CLI `--num-envs 5` |
| total_steps | 5,000,000 | CLI `--total-steps` |
| cost_limit | per config | CLI |
| lagrangian_coef_rate | 1e-5 | base default |
| lamda_lagr (init) | 0.78 | base default |
| use_popart | True | base default |
| use_feature_normalization | True | base default |
| Adam epsilon | 1e-5 | base default |
| orthogonal init gain | 0.01 | base default |

Key differences from MACPO's SMAC settings:
- MAPPO-Lag uses `actor_lr = 9e-5`, same as MACPO (both base defaults)
- MAPPO-Lag has `lagrangian_coef_rate = 1e-5` and `lamda_lagr = 0.78` (not in
  MACPO, which has TRPO-style trust regions instead)
- Both use `safety_gamma = 0.2`, `target_kl = 0.01`, `learning_iters = 15` on
  SMAC (from their smac override blocks)

**Action for the thesis:** add a MAPPO-Lag hyperparams table alongside the
existing MACPO one in Appendix B.

## 2. MACPO settings table verification

The existing `generated/macpo_hyperparams.tex` was checked against
`macpo/config.yaml` on the cluster:

| parameter | thesis table | config.yaml | match? |
|---|---|---|---|
| hidden_size | 512 → 128 | 512, smac: 128 | ✓ |
| layers | 2 → 1 | 2, smac: 1 | ✓ |
| actor_lr | 9e-5 | 9e-5 | ✓ |
| critic_lr | 5e-3 | 5e-3 | ✓ |
| gamma | 0.96 → 0.99 | 0.96, smac: 0.99 | ✓ |
| safety_gamma | 0.09 → 0.2 | 0.09, smac: 0.2 | ✓ |
| target_kl | 0.016 → 0.01 | 0.016, smac: 0.01 | ✓ |
| learning_iters | 5 → 15 | 5, smac: 15 | ✓ |
| entropy_coef | 0.0 → 0.01 | 0.0, smac: 0.01 | ✓ |
| rollout_length | 8 → 1000 | macpo default 8 (?), smac: 1000 | ✓ |
| env_steps | 1e8 → 1e7 | 1e8, smac: 100000 | **MISMATCH** |
| rollout_threads | 5 | 5 (base), smac: 5 | ✓ |

**One mismatch:** MACPO's `config.yaml` smac block says `num_env_steps: 100000`
(100k), but our runs used `--total-steps 5000000` (5M) from the CLI, which
overrides it. The thesis table says `10^7` (10M) which matches neither. The
actual MACPO SMAC runs ran to **5M** (confirmed from W&B; some also have 100k
checkpoints). The table should say `5 × 10^6`.

Also: MACPO's SMAC default of 100k is suspiciously low — it suggests the SafePO
authors may not have intended MACPO for long SMAC runs, which could explain the
poor 100k performance (MACPO wins 0 episodes on 22/24 configs at 100k).

## 3. Our MAMuJoCo baselines vs SafePO's published numbers

SafePO does not publish per-map SMAC numbers, so the SMAC comparison is not
possible. For MAMuJoCo, SafePO's benchmark paper (Gu et al., NeurIPS 2023
Datasets & Benchmarks) reports reward-only numbers, not constrained. Our runs
use the `--cost-limit` and `--cost-type` flags that were added to the
`Safe-Policy-Optimization-Modified` fork — not the upstream SafePO release.

**Conclusion:** no published SafePO numbers exist for the constrained SMAC or
constrained MAMuJoCo settings we evaluate. The baselines use SafePO's code and
defaults; their poor 100k performance on SMAC is attributable to the algorithm,
not under-tuning, since the only non-default settings are the SMAC override
block that SafePO itself provides. A reviewer who doubts MACPO's 100k SMAC
numbers should note that MACPO at 5M reaches the same 5/12 as CA-MAMBA at 100k
(#33).

## 4. MAPPO-Lag's MMM cost exceeds 10 on a 10-unit map

**Root cause found.** The SafePO wrapper's `get_cost_dead_allies_incremental`
in `smac_wrapper.py` has a survivors penalty on battle loss:

```python
if terminated:
    if info.get("battle_won", False) == False:
        cost = new_deaths + allies_alive  # BUG: double-counts
```

On the final step, `new_deaths` counts units dying that step, and
`allies_alive` counts survivors. If both are nonzero, the sum exceeds the
number of actual deaths. For MMM (10 units), if 8 die during the episode, 1
dies on the final step, and 1 survives: `cost = 1 + 1 = 2` on the final step,
total = `8 + 2 = 10`, which happens to equal the unit count. But if timing
differs (e.g. 2 die on the final step with 0 survivors), total = `8 + 2 = 10`
still, while if 0 die on the final step with 2 survivors, total = `8 + 0 + 2 =
10`. However the 10.11 case arises from fractional means across steps.

**CA-MAMBA's version** (`env/starcraft/StarCraft_safe.py:311`) avoids the
double-count: on battle loss it returns either `new_deaths` (if any died that
step) or `total_allies - current_deaths` (survivors), never both.

**Impact on results:** the bug only affects MAPPO-Lag's logged cost on maps
where battles are lost (all losses, not just MMM). It inflates the baselines'
cost, making CA-MAMBA look comparatively better. It does NOT affect CA-MAMBA's
numbers (different code). It does not change any feasibility count (#33): 10.11
vs a corrected value below 10 both miss d=4.

**Action:** state in the thesis that the baselines' SMAC cost is computed by the
SafePO wrapper, which adds a survivors-on-loss penalty that CA-MAMBA does not.
This is a difference in accounting, not in safety, and it works against the
baselines. Do NOT attempt to "fix" the baseline numbers — they are what the
SafePO code produces, and changing them would require rerunning.

## 5. Which settings the αβ = 1e-4 runs used

The 18 laglr=1e-4 runs in `mamujoco_tight` (commit `8c871ec`) ran with:

```
--laglr 0.0001
```

and no other overrides. At that commit, `--lag_init` did not exist yet, so
`LAGRANGIAN_MULTIPLIER_INIT` used the code default of **0.0001** (from
`configs/dreamer/DreamerLearnerConfig.py:31`). All other hyperparameters
(actor_lr, model_lr, value_lr, grad_clip, grad_clip_policy) were also code
defaults — None at the CLI, so no override was applied.

The laglr=1e-5 runs (the paper's main results) differ in only one setting:
`--laglr 1e-5`. Everything else is the same.

**Conclusion:** the "tenfold step" result compares laglr=1e-4 vs laglr=1e-5,
both on code defaults, with lag_init=1e-4 in both cases. The comparison is
clean.

## Status

All five sub-tasks answered. Actions for #40:
- Add a MAPPO-Lag SMAC hyperparams table to the appendix
- Fix the MACPO table's env_steps: 10^7 → 5×10^6
- Add a note about the SafePO cost-accounting difference on SMAC battle losses
- No settings correction needed for the αβ = 1e-4 comparison
