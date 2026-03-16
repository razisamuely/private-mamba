# Experiment & Development Guidelines

This document outlines the professional workflow for developing and running experiments in the `private-mamba` repository.

## 1. Branching & Submission Policy

### ⚠️ THE GOLDEN RULE
**Never submit experiments or commit logic changes directly to `main`.**

*   **`main` Branch**: Reserved for stable, verified, and cleaned-up code. It should always be "production-ready."
*   **Feature Branches**: All new features, bug fixes, or experiment configurations MUST be developed on a dedicated branch (e.g., `feat/new-cost-function` or `issue-5-debug`).
*   **Submission**: Only run `submit_experiments.py` from your feature branch. This ensures that the code running on the cluster is the exact version you are testing, without risk of polluting the stable history.

---

## 2. Standardized Experiment Naming

To ensure experiments are distinguishable across different algorithms, researchers, and timeframes, eEvery run must follow this strict naming convention:

`{ALGO}_{COST_TYPE}_{ENV}_lag{LAGLR}_{COST_LIMIT}_{MAP}_s{SEED}_{TIMESTAMP}_{SLURM_ID}_{BRANCH}`

### Example:
`safedreamer_dead_allies_incremental_starcraft_lag1e-05_10.0_3m_s3_date03-16-hr16-05-04_15925096_main`

*   **ALGO**: The algorithm identifier (e.g., `safedreamer`, `mamba`).
*   **LAGLR**: The Lagrangian learning rate (crucial for stability).
*   **SLURM_ID**: Automatically appended at runtime to link WandB logs directly to cluster output files.
*   **BRANCH**: The git branch name from which the experiment was launched.

---

## 3. Automation Workflow

### Launching Experiments
Use the automation script from your local machine to generate sbatch files and submit them to the BGU cluster:

```bash
python3 sbatch_scripts/submit_experiments.py \
    --algo_name safedreamer \
    --envs 3m 8m \
    --seeds 1 2 3 \
    --cost_limits 5.0 10.0 \
    --n_workers 4
```

### Experiment Tracking
*   **WandB**: All runs are logged in real-time to the `private-mamba` project.
*   **Local History**: A "paper trail" of every submission is automatically saved to `sbatch_scripts/logs/experiments_history.csv`.
*   **Cluster Logs**: Output and error files are generated on the cluster as `{RUN_NAME}-id-%J.out`.

---

## 4. Remote Synchronization

Whenever you update your code locally:
1.  **Commit & Push** your feature branch to GitHub.
2.  **Sync Remote**: Coordinate the cluster to match your branch:
    ```bash
    ssh razshmue@slurm.bgu.ac.il "cd workspace/private-mamba && git fetch origin && git checkout <your-branch> && git reset --hard origin/<your-branch>"
    ```
3.  **Deploy**: Run the submission script locally.

---

## 5. Git & Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. This helps in maintaining a clean and searchable history.

```
<type>(<scope>): <short description>

[optional body]
```

**Types:**
- `feat` - New feature or algorithm modification
- `fix` - Bug fix in the environment or agent
- `refactor` - Code restructuring (e.g., moving classes to `lagrange.py`)
- `docs` - Documentation updates
- `test` - Adding or updating tests
- `chore` - Tooling, config, dependencies
- `perf` - Performance optimization

**Scopes:**
- `learner`, `worker`, `runner`, `model`, `networks`, `env`, `config`, `sbatch`

---

## 6. Python Code Style

Maintain high code quality and consistency across the repository:

- **Naming**: 
  - `snake_case` for functions/variables.
  - `PascalCase` for classes (e.g., `DreamerLearner`).
  - `UPPER_SNAKE` for constants and config parameters.
- **Formatting**: Use `black` and `isort` for formatting. All code should be formatted before pushing.
- **Imports**: standard library → third-party (torch, ray, etc.) → local modules.
- **Type hints**: Use type hints on function signatures wherever possible.

---

## 7. Testing

Verification is key to experiment integrity:

- **New Features**: Write unit tests for new logic (e.g., new Lagrangian update law).
- **Run verification**: Before launching a large 8-worker experiment on the cluster, always perform a short local test run to verify WandB and basic logging:
  ```bash
  python train.py --env starcraft --env_name 3m --n_workers 1 --debug
  ```

---

## 8. Cleanup & Maintenance
Before merging a branch back into `main`:
1.  **Delete Junk**: Remove any temporary text files, draft scripts, or experimental `.sbatch` files generated locally.
2.  **Format**: Ensure pre-commit hooks have passed.
3.  **Consolidate**: Ensure logic is modular (e.g., move `BasicLagrange` to `lagrange.py`).
