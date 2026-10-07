# Ablation hyperparameters

Default config classes: `configs/dreamer/` (DreamerLearnerConfig, DreamerAgentConfig, DreamerControllerConfig).
CLI overrides per arm are listed below. All other params use defaults from `train.py`.

## 5 multiplier arms

| Arm | CLI overrides |
|---|---|
| Measured-cost basic | `--laglr 1e-5` |
| PID | `--lag_mode pid --pid_kp 1.0 --pid_ki 1e-5 --pid_kd 1.0` |
| Fixed λ=1 | `--laglr 0 --lag_init 1.0` |
| Cost-blind λ=0 | `--laglr 0 --lag_init 0.0` |
| Imagined-cost basic | `--laglr 1e-5 --lag_signal imagined` |

## Per-experiment shared params

| Experiment | `--cost_limit` | `--max_steps` | Other |
|---|---|---|---|
| SMAC 8m d=4 | 4.0 | 105000 | `--env_name 8m` |
| SMAC 8m d=0 | 0.0 | 105000 | `--env_name 8m` |
| HC 2x3 d=5.0 | 5.0 | 1050000 | `--env_name Safety2x3HalfCheetahVelocity-v0` |
| HC 2x3 d=25 | 25.0 | 1050000 | `--env_name Safety2x3HalfCheetahVelocity-v0` |

All runs use 3 seeds (s1, s2, s3).

## Config class locations

- `configs/dreamer/DreamerLearnerConfig.py` — learning rates, batch size, sequence length, horizon
- `configs/dreamer/DreamerAgentConfig.py` — model architecture, latent dims
- `configs/dreamer/DreamerControllerConfig.py` — actor-critic, entropy, discount
- `configs/dreamer/optimal/starcraft/` — SMAC-specific overrides
- `configs/EnvConfigs.py` — env wrappers, obs/action spaces
- `train.py:77-106` — Lagrangian / PID / cost CLI arguments with defaults
