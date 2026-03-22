# Pilot Runs Grid: Experiment 4

## Grid Matrix
| Map | Cost Limit | LagLR | Seeds | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `8m` | 0.1 | 1e-4 | 1, 2 | Strict constraint + Moderate response. |
| `8m` | 0.5 | 1e-4 | 1, 2 | Loose constraint + Moderate response. |
| `8m` | 0.1 | 1e-5 | 1, 2 | Strict constraint + Slow/Stable response. |
| `8m` | 0.5 | 1e-5 | 1, 2 | Loose constraint + Slow/Stable response. |

## Execution Commands
```bash
# Matrix 1 & 2 (1e-4)
python sbatch_scripts/submit_experiments.py --envs 8m --seeds 1 2 --cost_limits 0.1 0.5 --cost_type collision --laglr 0.0001 --cost_priority 0.15

# Matrix 3 & 4 (1e-5)
python sbatch_scripts/submit_experiments.py --envs 8m --seeds 1 2 --cost_limits 0.1 0.5 --cost_type collision --laglr 0.00001 --cost_priority 0.15
```
