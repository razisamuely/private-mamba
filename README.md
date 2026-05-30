# Safe Dreamers

Anonymous submission. Code for the paper *"Safe Dreamers: Safe Multi-Agent Reinforcement Learning via World Models"*.

## License

MIT

## Requirements

- Python 3.7
- StarCraft II (see installation below)

## Installation

```bash
pip install wheel
pip install -r requirements.txt
```

**Install StarCraft II and SMAC:**

Follow the instructions at https://github.com/oxwhirl/smac#installing-starcraft-ii

## Training

```bash
python train.py \
  --env starcraft \
  --env_name 3m \
  --cost_type dead_allies_incremental \
  --cost_limit 0 \
  --n_workers 4 \
  --seed 1
```

**Key arguments:**

| Argument | Description | Example |
|---|---|---|
| `--env` | Environment | `starcraft` |
| `--env_name` | SMAC map | `3m`, `8m`, `2s3z`, `1c3s5z`, ... |
| `--cost_type` | Safety cost function | `dead_allies_incremental`, `collision` |
| `--cost_limit` | Safety constraint threshold | `0`, `1`, `4` |
| `--n_workers` | Parallel workers | `4` |
| `--seed` | Random seed | `1` |

## Optimal Hyperparameters

Copy configs from `configs/dreamer/optimal/starcraft/` to override defaults:

```bash
cp configs/dreamer/optimal/starcraft/AgentConfig.py configs/dreamer/DreamerAgentConfig.py
cp configs/dreamer/optimal/starcraft/LearnerConfig.py configs/dreamer/DreamerLearnerConfig.py
```

## Code Structure

```
agent/
  controllers/   inference logic
  learners/      learning logic
  memory/        replay buffer
  models/        world model architecture
  optim/         loss optimization
  runners/       multi-worker orchestration
  workers/       environment interaction
configs/         hyperparameter configs
env/             environment wrappers
networks/        neural network architectures
train.py         entry point
```
