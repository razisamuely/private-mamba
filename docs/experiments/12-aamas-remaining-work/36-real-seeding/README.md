# #36 — make `--seed` actually seed everything

## Problem

`--seed` only *named* a run. The value reached `Experiment.random_seed`
(`train.py:327`) and stopped there: nothing outside the retired Flatland path
ever read it, and nothing in the repo called `random.seed`, `np.random.seed`,
`torch.manual_seed` or passed a seed to an environment.

Runs still differed from one another — the unseeded numpy/torch/CUDA
generators and the SC2 game seed supply plenty of randomness, which is why
`8m` at $d=4$ gave cost 5.51 / 4.76 / 4.81 across "seeds" 1/2/3 — but **no run
could be repeated**, and the three runs of a configuration were three draws
from one unseeded distribution rather than three named samples.

That is exactly why #26/#27/#28 could pool batches and relabel their seed
numbers: the labels carried no information.

## What changed

`seeding.py` is new and holds one function:

```python
def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
```

| file | change |
|---|---|
| `seeding.py` | **new** — `seed_everything` |
| `train.py` | calls it on `args.seed` before any config or env is built; passes `exp.random_seed` into `DreamerRunner` and the debug worker |
| `agent/runners/DreamerRunner.py` | `DreamerRunner`/`DreamerServer` take `seed`; worker *i* gets `seed + i` |
| `agent/workers/DreamerWorker.py` | each actor calls `seed_everything` and `env_config.set_seed` before `create_env` |
| `configs/Config.py` | `set_seed` base no-op |
| `configs/EnvConfigs.py` | `EnvCurriculumConfig.set_seed` forwards to its children |
| `env/starcraft/StarCraft_safe.py` | `env_seed` ctor arg → `StarCraft2Env(seed=...)`; `set_seed`; propagated by `create_env` |
| `env/safety_gym/MAMuJoCoWrapper.py` | `env_seed` ctor arg → `env.reset(seed=...)` on the **first** reset only; `set_seed`; propagated by `create_env` |

Three decisions worth keeping:

- **Worker *i* is seeded `seed + i`, not `seed`.** Identical seeds would make
  every worker draw the same action noise and collect near-identical episodes —
  a silent loss of exploration, worse than no seeding at all.
- **A Ray actor is its own process**, so the driver's seeding does not reach it;
  each actor seeds itself. The actor mutates its own copy of the env config, so
  `set_seed` there cannot affect the other workers.
- **MAMuJoCo is seeded on the first reset only.** Gymnasium reseeds on every
  `reset(seed=...)`, so passing it each episode would restart every episode from
  the same initial state.

`set_seed` is a no-op on the base `Config`, so the retired Flatland and VMAS
paths are untouched. `seed=None` leaves `StarCraft2Env`'s protobuf field unset,
which is what every pre-#36 run did.

## Verification

Measured on `Safety2x4AntVelocity-v0`, `--max_steps 800`, `WANDB_MODE=offline`,
comparing the full printed episode trace (reward, cost, score per episode):

| check | result |
|---|---|
| same seed twice, 1 worker | **byte-identical** |
| seed 5 vs seed 6, 1 worker | differ |
| same seed twice, **4 workers** | **byte-identical** |
| env seeding through `EnvCurriculumConfig` | same seed → same initial state; other seed → different |
| `seed_everything` on Python/numpy/torch | reproducible, and sensitive to the seed |

The 4-worker result is stronger than expected and should not be read as a
guarantee: the learner consumes rollouts in the order `ray.wait` returns them,
and that order depends on how the workers are scheduled. Under cluster load it
may well diverge. The per-process seeding is what is guaranteed.

`tests/test_seeding.py` is new (4 tests). Suite: **41 passed**, up from 37, no
failures. Run with `venv310/bin/python -m pytest tests/` (`venv` is py3.7 and
errors on collection).

## Consequences for the data

**No run is rerun and no table changes.** Every recorded run is unseeded, and
Appendix C already says so.

The thing to watch: seeding changes *which* sample a given seed label draws, so
**a seeded run and an unseeded run of the same configuration must not be
pooled**. Any future pooling (as in #26/#27/#28) has to check this commit
boundary first, not just the training-code diff.

## Files

| file | what |
|---|---|
| `seeding.py` (repo root) | the one function |
| `tests/test_seeding.py` | the two properties that were missing |
