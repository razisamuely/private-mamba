# Private-Mamba (SafeDreamer)

Safe multi-agent RL using world models (Mamba-based). Compares against MACPO/MAPPO-Lag baselines.

## Key Paths

| What | Where |
|------|-------|
| Experiment registry | `docs/experiments/README.md` |
| Submission how-to | `docs/planning/submission_skill.md` |
| Swimmer/continuous env | `docs/generalization/` |
| Table generation | `docs/planning/table_generation.md` |
| Extraction pipelines | `docs/tmp/extraction/README.md` |
| Changelog | `CHANGELOG.md` |
| Baseline repo (MACPO) | `/home/corsound/workspace/Safe-Policy-Optimization` |

## Workflow

- **One branch per experiment** (e.g. `feat/swimmer-baseline-comparison`)
- **Track runs** in `docs/experiments/<N>-<name>/runs.md` with Slurm IDs and WandB run names
- **Never commit directly to main** — merge after experiment completes
- **Commit convention**: conventional commits (`feat:`, `fix:`, `docs:`)

## Submission

- **SafeDreamer**: `private-mamba` repo, `./venv310/bin/python3`, GPU
- **MACPO**: `Safe-Policy-Optimization` repo, `conda activate safepo`, CPU
- Cluster: `razshmue@slurm.bgu.ac.il`
- See `docs/planning/submission_skill.md` for full commands

## Architecture

- Action space: **discrete** (OneHotCategorical) — continuous envs are discretized via wrappers
- Safety: Lagrangian constraint with real episode cost (`trajectory_costs.mean()`)
- Envs: SMAC (StarCraft), Safety-Gymnasium (Swimmer, HalfCheetah, Ant), Flatland, VMAS

## MACPO Paper Reference (arXiv:2110.02793)

- Tested: HalfCheetah (2x3, 3x2, 6x1), Ant (2x3, 3x2, 6x1, 2x4d, 4x2) — no Swimmer
- Upstream default: `cost_limit: 25` (verified in `safepo/multi_agent/marl_cfg/macpo/config.yaml` before our commit `2d4ccec`)
- Cost: binary per-step (0/1), distance threshold from origin
- Convergence: ~800k–1M steps
