# Collision Cost Fix Pilot Grid

## Configuration
- **Cost Type**: `collision`
- **Lagrangian LR**: `1e-3` 
- **Sampling Strategy**: Prioritized (15% High-Cost)
- **Seeds**: `1, 2, 3`

## Execution
To submit these experiments to the BGU cluster, use the following command:
```bash
python sbatch_scripts/submit_experiments.py \
    --envs 8m \
    --seeds 1 2 3 \
    --cost_limits 5.0 10.0 \
    --cost_type collision \
    --laglr 0.001 \
    --cost_priority 0.15
```

## Experiment Matrix
| Map | Cost Limit | Seeds | Purpose |
| :--- | :--- | :--- | :--- |
| `8m` | 5.0 | 1, 2, 3 | Verify if the model can now enforce the tightest constraint. |
| `8m` | 10.0 | 1, 2, 3 | Comparative baseline for stability. |
| `bane_vs_bane` | 5.0 | 1 | Smoke test for high-density units with the new sampling strategy. |m 

## Submissions
- **Submission Time**: 2026-03-19 23:15
- **Job IDs**: `16169165` through `16169246`
- **Branch**: `feat/issue-2-collision-cost-fix`
