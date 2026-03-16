# Collision Cost Pilot Grid (12 Runs)

## Configuration
- **Cost Type**: `collision` (Cumulative, Moving Agents Only)
- **Algorithm**: `safedreamer`
- **Seeds**: `1, 2, 3`

## Experiment Matrix
| Map | Cost Limit | Seeds | Purpose |
| :--- | :--- | :--- | :--- |
| `8m` | 5.0 | 1, 2, 3 | Evaluate clumping prevention in a standard 8-agent squad. |
| `8m` | 10.0 | 1, 2, 3 | High tolerance baseline for comparison. |
| `bane_vs_bane` | 5.0 | 1, 2, 3 | Critical test for clumping in a high-density, high-casualty environment (24 vs 24). |
| `bane_vs_bane` | 10.0 | 1, 2, 3 | Baseline for large-scale unit formations. |

## Submissions
- **Submission Time**: 2026-03-16 17:50
- **Job IDs**: `15932538` through `15932611`
- **Branch**: `feat/issue-2-collision-cost`
