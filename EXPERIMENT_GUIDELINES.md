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

## 5. Cleanup & Maintenance
Before merging a branch back into `main`:
1.  **Delete Junk**: Remove any temporary text files, `cost_points.txt`, or draft scripts.
2.  **Format**: Ensure hooks (`black`, `isort`) have run.
3.  **Consolidate**: Ensure all math/logic classes are in their dedicated files (e.g., `lagrange.py`), not inside `train.py` or `DreamerLearner.py`.
